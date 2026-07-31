# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Tree flattening regressions. 树模型拍平回归测试。"""

from pathlib import Path

import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import configure_qml_environment, register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE = b"""
import QtQuick
import PrismQML

TreeWidget {
    property var lastInput: []

    function flatten(value) {
        lastInput = value
        return _flattenModel(lastInput, 0, [])
    }
}
"""


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _release(qapp, *objects) -> None:
    for item in objects:
        if item is not None and shiboken6.isValid(item):
            item.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def test_tree_flatten_preserves_order_depth_paths_and_collapsed_branches(qapp):
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    component = None
    widget = None
    try:
        register_types(engine)
        component = QQmlComponent(engine)
        component.setData(
            SCENE,
            QUrl.fromLocalFile(str(ROOT / "tests/qml/tree-flatten-performance.qml")),
        )
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        widget = component.create(engine.rootContext())
        assert widget is not None, [error.toString() for error in component.errors()]

        source = [
            {
                "text": "Root",
                "expanded": True,
                "children": [
                    {
                        "text": "Branch",
                        "expanded": True,
                        "children": [{"text": "Leaf"}],
                    },
                    {"text": "Collapsed", "expanded": False, "children": [{"text": "Hidden"}]},
                ],
            },
            {"text": "Sibling", "expanded": False, "children": [{"text": "Hidden sibling"}]},
        ]

        flattened = _variant(widget.flatten(source))
        assert [item["text"] for item in flattened] == [
            "Root",
            "Branch",
            "Leaf",
            "Collapsed",
            "Sibling",
        ]
        assert [item["depth"] for item in flattened] == [0, 1, 2, 1, 0]
        assert [item["path"] for item in flattened] == [
            [0],
            [0, 0],
            [0, 0, 0],
            [0, 1],
            [1],
        ]
        input_after = _variant(widget.property("lastInput"))
        assert input_after[0]["depth"] == 0
        assert input_after[0]["children"][0]["depth"] == 1
        assert input_after[0]["children"][0]["children"][0]["depth"] == 2
        assert input_after[0]["children"][1]["depth"] == 1
        assert input_after[1]["depth"] == 0
    finally:
        _release(qapp, widget, component, engine)
