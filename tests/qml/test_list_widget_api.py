# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ListWidget public API regressions. ListWidget 公开 API 回归。"""

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

ListWidget {
    width: 300
    height: 220

    function seedSortItems() {
        addItem({
            text: "Beta", icon: "Home", data: { key: 2 },
            checkable: true, checkState: 2, selected: false, flags: 7
        })
        addItem({
            text: "Alpha", icon: "Star", data: { key: 1 },
            checkable: false, checkState: 0, selected: true, flags: 3
        })
        addItem({
            text: "Gamma", icon: "Settings", data: { key: 3 },
            checkable: true, checkState: 1, selected: false, flags: 5
        })
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


def _item(widget, row: int) -> dict:
    return _variant(widget.item(row))


def test_sort_items_preserves_complete_rows_without_qml_warnings(qapp):
    """Sorting must move complete live rows without invalidating roles. 排序须移动完整实时行且不得使角色失效。"""
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
            QUrl.fromLocalFile(str(_ROOT / "tests/qml/list-widget-api.qml")),
        )
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        widget = component.create(engine.rootContext())
        assert widget is not None, [error.toString() for error in component.errors()]
        _pump()
        messages.clear()

        widget.seedSortItems()
        widget.setSelectionMode(2)
        widget.setItemSelected(0, True)
        widget.setItemSelected(2, True)
        widget.setCurrentRow(0, None)
        widget.setItemSelected(2, True)
        widget.sortItems(0)
        ascending = [_item(widget, row) for row in range(3)]
        assert [item["text"] for item in ascending] == ["Alpha", "Beta", "Gamma"]
        assert [item["icon"] for item in ascending] == ["Star", "Home", "Settings"]
        assert [item["data"]["key"] for item in ascending] == [1, 2, 3]
        assert [item["checkState"] for item in ascending] == [0, 2, 1]
        assert [item["flags"] for item in ascending] == [3, 7, 5]
        assert _variant(widget.currentItem())["text"] == "Beta"
        assert [_variant(item)["text"] for item in _variant(widget.selectedItems())] == [
            "Beta",
            "Gamma",
        ]

        widget.sortItems(1)
        descending = [_item(widget, row) for row in range(3)]
        assert [item["text"] for item in descending] == ["Gamma", "Beta", "Alpha"]

        widget.insertItem(1, "Delta")
        widget.insertItems(2, ["Epsilon", "Zeta"])
        assert widget.property("count") == 6
        assert _item(widget, 1)["text"] == "Delta"
        assert [_variant(item)["text"] for item in _variant(widget.findItems("ta", 1))] == [
            "Delta",
            "Zeta",
            "Beta",
        ]

        widget.setItemText(0, "Omega")
        widget.setItemIcon(0, "ChevronRight")
        widget.setItemData(0, "updated", 42)
        widget.setItemCheckState(0, 2)
        updated = _item(widget, 0)
        assert updated["text"] == "Omega"
        assert updated["icon"] == "ChevronRight"
        assert widget.itemData(0, "updated") == 42
        assert widget.itemCheckState(0) == 2

        widget.setSelectionMode(2)
        widget.clearSelection()
        widget.setItemSelected(0, True)
        widget.setItemSelected(2, True)
        assert [_variant(item)["text"] for item in _variant(widget.selectedItems())] == [
            "Omega",
            "Epsilon",
        ]
        widget.setCurrentRow(1, None)
        assert widget.currentRow() == 1
        assert _variant(widget.currentItem())["text"] == "Delta"

        taken = _variant(widget.takeItem(1))
        assert taken["text"] == "Delta"
        assert widget.property("count") == 5
        widget.clearSelection()
        assert _variant(widget.selectedItems()) == []
        widget.clear()
        assert widget.property("count") == 0
        assert widget.currentRow() == -1
    finally:
        _release(qapp, widget, component, engine)
        qInstallMessageHandler(previous_handler)

    failures = [
        message for mode, message in messages if mode in _QT_FAILURE_TYPES
    ]
    assert failures == []
