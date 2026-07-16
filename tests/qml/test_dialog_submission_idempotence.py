# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Dialog submission idempotence regressions. 对话框提交幂等回归。"""

from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPoint,
    QPointF,
    QTimer,
    Qt,
    QUrl,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "dialog-submission.qml"))

DIALOG_BOX_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    property int acceptedCount: 0
    property int rejectedCount: 0

    function reopen() { dialog.open() }

    width: 640
    height: 480
    visible: true

    DialogBoxCore {
        id: dialog
        objectName: "dialog"
        contentWidth: 200
        onAccepted: root.acceptedCount++
        onRejected: root.rejectedCount++

        footer: Component {
            Row {
                property var dialog
                spacing: Enums.spacing.l

                ButtonCore {
                    objectName: "acceptButton"
                    text: "Accept"
                    width: Enums.dialog.buttonWidth
                    height: Enums.dialog.buttonHeight
                    onClicked: dialog.accept()
                }

                ButtonCore {
                    objectName: "rejectButton"
                    text: "Reject"
                    width: Enums.dialog.buttonWidth
                    height: Enums.dialog.buttonHeight
                    onClicked: dialog.reject()
                }
            }
        }

        Rectangle {
            width: 200
            height: 80
            color: Enums.transparent
        }
    }

    Component.onCompleted: dialog.open()
}
"""

CONFIRM_DIALOG_SCENE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    property int acceptedCount: 0
    property int rejectedCount: 0
    property int confirmedCount: 0
    property int cancelledCount: 0

    function reopen() { dialog.open() }

    width: 640
    height: 480
    visible: true

    ConfirmDialog {
        id: dialog
        objectName: "dialog"
        title: "Submit"
        message: "Submit once"
        confirmText: "Commit"
        cancelText: "Cancel"
        onAccepted: root.acceptedCount++
        onRejected: root.rejectedCount++
        onConfirmed: root.confirmedCount++
        onCancelled: root.cancelledCount++
    }

    Component.onCompleted: dialog.open()
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1200) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump(10)
        elapsed += 10
    return predicate()


def _create_scene(source: bytes):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(source, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(lambda: window.isActive())
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(20)


def _click(window: QQuickWindow, item: QQuickItem) -> None:
    point = item.mapToItem(
        window.contentItem(), QPointF(item.width() / 2, item.height() / 2)
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        pos=QPoint(round(point.x()), round(point.y())),
    )


def _rapid_double_click(window: QQuickWindow, item: QQuickItem) -> None:
    _click(window, item)
    _click(window, item)


def _button_by_text(window: QQuickWindow, text: str) -> QQuickItem:
    matches = [
        item
        for item in window.findChildren(QQuickItem)
        if item.metaObject().className().startswith("ButtonCore")
        and item.metaObject().indexOfProperty("text") >= 0
        and item.property("text") == text
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def test_dialog_box_footer_submits_once_per_open(qapp):
    engine, component, window, warnings = _create_scene(DIALOG_BOX_SCENE)
    try:
        dialog = window.findChild(QQuickItem, "dialog")
        accept_button = window.findChild(QQuickItem, "acceptButton")
        reject_button = window.findChild(QQuickItem, "rejectButton")
        assert dialog is not None
        assert accept_button is not None
        assert reject_button is not None

        _rapid_double_click(window, accept_button)
        assert window.property("acceptedCount") == 1

        assert QMetaObject.invokeMethod(window, "reopen")
        _rapid_double_click(window, accept_button)
        assert window.property("acceptedCount") == 2

        assert QMetaObject.invokeMethod(window, "reopen")
        _rapid_double_click(window, reject_button)
        assert window.property("rejectedCount") == 1
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_confirm_dialog_derived_signals_submit_once(qapp):
    engine, component, window, warnings = _create_scene(CONFIRM_DIALOG_SCENE)
    try:
        commit_button = _button_by_text(window, "Commit")
        cancel_button = _button_by_text(window, "Cancel")

        _rapid_double_click(window, commit_button)
        assert window.property("acceptedCount") == 1
        assert window.property("confirmedCount") == 1

        assert QMetaObject.invokeMethod(window, "reopen")
        _rapid_double_click(window, cancel_button)
        assert window.property("rejectedCount") == 1
        assert window.property("cancelledCount") == 1
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
