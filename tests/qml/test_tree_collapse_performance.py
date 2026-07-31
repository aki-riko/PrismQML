# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Tree collapse batching regressions. 树节点折叠批处理回归测试。"""

from pathlib import Path

import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import configure_qml_environment, register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE = b"""
import QtQuick
import PrismQML

TreeWidget {
    width: 360
    height: 260

    function seed(childCount) {
        var children = []
        for (var index = 0; index < childCount; ++index)
            children.push({ text: "Child " + index })
        model = [{ text: "Root", expanded: true, children: children }]
    }

    function selectChild(index) {
        setSelectionMode(multiSelection)
        _handleItemClick(index, Qt.LeftButton, Qt.NoModifier)
    }

    function collapseRoot() {
        toggleExpandAt(0)
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


def test_tree_collapse_removes_descendants_in_one_model_batch(qapp):
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    component = None
    widget = None
    try:
        register_types(engine)
        component = QQmlComponent(engine)
        component.setData(
            SCENE,
            QUrl.fromLocalFile(str(ROOT / "tests/qml/tree-collapse-performance.qml")),
        )
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        widget = component.create(engine.rootContext())
        assert widget is not None, [error.toString() for error in component.errors()]

        child_count = 40
        widget.seed(child_count)
        assert widget.count() == child_count + 1
        models = [
            child
            for child in widget.findChildren(QObject)
            if "QQmlListModel" in child.metaObject().className()
            and child.rowCount() == child_count + 1
        ]
        assert len(models) == 1
        flat_model = models[0]

        widget.selectChild(10)
        assert widget.property("currentIndex") == 10
        assert len(_variant(widget.selectedItems())) == 1

        removed_ranges = []
        collapsed_items = []
        flat_model.rowsRemoved.connect(
            lambda _parent, first, last: removed_ranges.append((first, last))
        )
        widget.itemCollapsed.connect(collapsed_items.append)

        widget.collapseRoot()

        assert widget.count() == 1
        assert removed_ranges == [(1, child_count)]
        assert widget.property("currentIndex") == -1
        assert _variant(widget.selectedItems()) == []
        assert len(collapsed_items) == 1
        assert _variant(widget.topLevelItem(0))["expanded"] is False

        widget.seed(0)
        removed_ranges.clear()
        collapsed_items.clear()
        widget.collapseRoot()
        assert widget.count() == 1
        assert removed_ranges == []
        assert len(collapsed_items) == 1
        assert _variant(widget.topLevelItem(0))["expanded"] is False
    finally:
        _release(qapp, widget, component, engine)
