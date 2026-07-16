# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""TreeWidget public API regressions. TreeWidget 公开 API 回归。"""

from pathlib import Path

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QTimer,
    QtMsgType,
    QUrl,
    qInstallMessageHandler,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import configure_qml_environment, register_types


_ROOT = Path(__file__).resolve().parents[2]
_SCENE = b"""
import QtQuick
import PrismQML

TreeWidget {
    property var heldItem: null

    width: 360
    height: 260

    function seedItems() {
        model = [
            {
                text: "Beta", icon: "Home", data: { key: 2 },
                checkable: true, checkState: 2, expanded: true,
                children: [
                    { text: "Beta Child", icon: "Star", data: { key: 21 } }
                ]
            },
            { text: "Alpha", icon: "Settings", data: { key: 1 } },
            { text: "Gamma", icon: "Info", data: { key: 3 } }
        ]
    }

    function mutateFirstTopLevel() {
        var item = topLevelItem(0)
        setItemText(item, 0, "Beta Updated")
        setItemIcon(item, 0, "ChevronRight")
        setItemData(item, 0, "updated", 42)
        setItemCheckState(item, 0, 1)
    }

    function selectGammaAndBeta() {
        setSelectionMode(multiSelection)
        _handleItemClick(3, Qt.LeftButton, Qt.NoModifier)
        _handleItemClick(0, Qt.LeftButton, Qt.NoModifier)
    }

    function holdCurrentItem() {
        heldItem = currentItem()
    }

    function mutateHeldItem() {
        setItemText(heldItem, 0, "Beta Held")
    }

    function seedDuplicateItems() {
        model = [
            { text: "Same", data: { key: 1 } },
            { text: "Same", data: { key: 2 } }
        ]
    }

    function mutateSecondDuplicate() {
        var item = topLevelItem(1)
        setItemText(item, 0, "Second")
        setItemData(item, 0, "updated", 99)
    }
}
"""
_QT_FAILURE_TYPES = {
    QtMsgType.QtWarningMsg,
    QtMsgType.QtCriticalMsg,
    QtMsgType.QtFatalMsg,
}


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _release(qapp, *objects) -> None:
    for item in objects:
        if item is not None and shiboken6.isValid(item):
            item.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    qapp.processEvents()


def test_tree_widget_public_items_and_sort_preserve_identity(qapp):
    """Public item mutation and sorting must preserve item identity. 公开项修改与排序须保持条目身份。"""
    configure_qml_environment()
    messages = []
    previous_handler = qInstallMessageHandler(
        lambda mode, _context, message: messages.append((mode, str(message)))
    )
    engine = QQmlApplicationEngine()
    component = None
    widget = None
    try:
        register_types(engine)
        component = QQmlComponent(engine)
        component.setData(
            _SCENE,
            QUrl.fromLocalFile(str(_ROOT / "tests/qml/tree-widget-api.qml")),
        )
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        widget = component.create(engine.rootContext())
        assert widget is not None, [error.toString() for error in component.errors()]
        _pump()
        messages.clear()

        widget.seedItems()
        _pump()
        assert widget.topLevelItemCount() == 3
        assert widget.count() == 4

        widget.mutateFirstTopLevel()
        first = _variant(widget.topLevelItem(0))
        assert first["text"] == "Beta Updated"
        assert first["icon"] == "ChevronRight"
        assert first["data"]["updated"] == 42
        assert first["checkState"] == 1

        widget.selectGammaAndBeta()
        assert _variant(widget.currentItem())["text"] == "Beta Updated"
        assert [
            _variant(item)["text"] for item in _variant(widget.selectedItems())
        ] == ["Gamma", "Beta Updated"]

        widget.holdCurrentItem()
        widget.sortItems(0, 0)
        assert [
            _variant(widget.topLevelItem(row))["text"] for row in range(3)
        ] == ["Alpha", "Beta Updated", "Gamma"]
        assert _variant(widget.currentItem())["text"] == "Beta Updated"
        assert [
            _variant(item)["text"] for item in _variant(widget.selectedItems())
        ] == ["Gamma", "Beta Updated"]
        widget.mutateHeldItem()
        assert [
            _variant(widget.topLevelItem(row))["text"] for row in range(3)
        ] == ["Alpha", "Beta Held", "Gamma"]

        widget.clear()
        widget.seedDuplicateItems()
        _pump()
        widget.mutateSecondDuplicate()
        duplicate_first = _variant(widget.topLevelItem(0))
        duplicate_second = _variant(widget.topLevelItem(1))
        assert duplicate_first["text"] == "Same"
        assert duplicate_first["data"] == {"key": 1}
        assert duplicate_second["text"] == "Second"
        assert duplicate_second["data"] == {"key": 2, "updated": 99}
    finally:
        _release(qapp, widget, component, engine)
        qInstallMessageHandler(previous_handler)

    failures = [
        message for mode, message in messages if mode in _QT_FAILURE_TYPES
    ]
    assert failures == []
