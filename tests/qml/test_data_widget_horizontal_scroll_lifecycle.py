# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""DataWidget horizontal-scroll lifecycle regressions. 数据组件横向滚动生命周期回归。"""

from pathlib import Path

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QPointF,
    QTimer,
    Qt,
    QtMsgType,
    QUrl,
    qInstallMessageHandler,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import configure_qml_environment, register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: host

    function activateHorizontalScroll() {
        widget.contentTotalWidth = 720
        widget.listView.contentX = 96
    }

    function deactivateHorizontalScroll() {
        widget.contentTotalWidth = 0
    }

    width: 420
    height: 280
    visible: true
    color: Enums.backgroundColor

    DataWidgetCore {
        id: widget

        objectName: "widget"
        x: 20
        y: 20
        width: 380
        height: 240
        animated: false
        showShadow: false
        showHeader: true
        contentTotalWidth: 0
        listModel: ["Alpha", "Beta", "Gamma", "Delta"]

        headerContent: Rectangle {
            objectName: "headerMarker"
            color: Enums.headerColor

            Row {
                anchors.fill: parent

                Repeater {
                    model: 6

                    Rectangle {
                        required property int index

                        width: 120
                        height: parent.height
                        color: index % 2 === 0 ? Enums.selectedColor : Enums.headerColor

                        Text {
                            anchors.centerIn: parent
                            text: "Column " + (index + 1)
                            color: Enums.textColor.primary
                            font.family: Enums.fontFamily
                            font.pixelSize: Enums.typography.body
                        }
                    }
                }
            }
        }

        contentDelegate: Rectangle {
            required property int index
            required property var modelData

            width: ListView.view ? ListView.view.contentWidth : 0
            height: 36
            color: index % 2 === 0 ? Enums.cardColor : Enums.alternateRowColor

            Text {
                x: Enums.spacing.m
                anchors.verticalCenter: parent.verticalCenter
                text: modelData
                color: Enums.textColor.primary
                font.family: Enums.fontFamily
                font.pixelSize: Enums.typography.body
            }
        }
    }
}
"""
INITIAL_OVERFLOW_SCENE_SOURCE = SCENE_SOURCE.replace(
    b"contentTotalWidth: 0",
    b"contentTotalWidth: 720",
)
QT_FAILURE_TYPES = {
    QtMsgType.QtWarningMsg,
    QtMsgType.QtCriticalMsg,
    QtMsgType.QtFatalMsg,
}
KNOWN_ENVIRONMENT_WARNING_PREFIXES = (
    "QFontDatabase: Cannot find font directory",
)


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1_500) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _class_stem(obj: QObject) -> str:
    return obj.metaObject().className().split("_QMLTYPE_")[0]


def _horizontal_mixins(widget: QQuickItem) -> list[QObject]:
    return [
        obj
        for obj in widget.findChildren(QObject)
        if _class_stem(obj) == "HorizontalScrollMixin"
    ]


def _horizontal_scroll_bars(widget: QQuickItem) -> list[QQuickItem]:
    return [
        obj
        for obj in widget.findChildren(QQuickItem)
        if _class_stem(obj) == "ScrollBar"
        and obj.property("orientation") == Qt.Orientation.Horizontal.value
    ]


def _header_offset(widget: QQuickItem) -> float:
    marker = widget.findChild(QQuickItem, "headerMarker")
    assert marker is not None
    return marker.mapToItem(widget, QPointF()).x()


def _create_scene(source: bytes = SCENE_SOURCE):
    configure_qml_environment()
    messages = []
    previous_handler = qInstallMessageHandler(
        lambda mode, _context, message: messages.append((mode, str(message)))
    )
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        source,
        QUrl.fromLocalFile(
            str(ROOT / "tests" / "qml" / "data-widget-horizontal-scroll.qml")
        ),
    )
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    widget = window.findChild(QQuickItem, "widget")
    assert widget is not None
    _pump(80)
    return engine, component, window, widget, messages, previous_handler


def _dispose_scene(qapp, engine, component, window, previous_handler) -> None:
    window.close()
    for item in (window, component, engine):
        if item is not None and shiboken6.isValid(item):
            item.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()
    qInstallMessageHandler(previous_handler)


def _qt_failures(messages) -> list[str]:
    return [
        message
        for mode, message in messages
        if mode in QT_FAILURE_TYPES
        and not message.startswith(KNOWN_ENVIRONMENT_WARNING_PREFIXES)
    ]


def test_initial_horizontal_overflow_preloads_before_user_input(qapp):
    """Initial real overflow must preload its interactive branch. 初始真实溢出须预热交互分支。"""
    scene = _create_scene(INITIAL_OVERFLOW_SCENE_SOURCE)
    engine, component, window, widget, messages, previous_handler = scene
    try:
        mixins = _horizontal_mixins(widget)
        assert len(mixins) == 1
        assert widget.property("_horizontalScrollRequested") is True
        assert widget.property("_horizontalScrollMixin") is mixins[0]
        horizontal_bars = _horizontal_scroll_bars(widget)
        assert len(horizontal_bars) == 1
        assert horizontal_bars[0].isVisible()
    finally:
        _dispose_scene(qapp, engine, component, window, previous_handler)

    assert _qt_failures(messages) == []


def test_horizontal_scroll_preserves_pixels_header_and_instance_across_cycles(qapp):
    """Width cycles must preserve visible output and the active mixin. 宽度循环须保持画面和已激活 mixin。"""
    scene = _create_scene()
    engine, component, window, widget, messages, previous_handler = scene
    try:
        initial_mixins = _horizontal_mixins(widget)
        assert initial_mixins == []
        assert widget.property("_horizontalScrollRequested") is False
        assert widget.property("_horizontalScrollMixin") is None
        idle_header_offset = _header_offset(widget)
        idle_image = window.grabWindow()

        assert QMetaObject.invokeMethod(window, "activateHorizontalScroll")
        active_mixins = _horizontal_mixins(widget)
        assert len(active_mixins) == 1
        active_mixin = active_mixins[0]
        assert widget.property("_horizontalScrollRequested") is True
        assert widget.property("_horizontalScrollMixin") is active_mixin
        horizontal_bar_ready = _wait_for(
            lambda: len(_horizontal_scroll_bars(widget)) == 1
            and _horizontal_scroll_bars(widget)[0].isVisible()
        )
        assert horizontal_bar_ready, [
            (
                _class_stem(obj),
                obj.property("orientation"),
                obj.isVisible(),
            )
            for obj in widget.findChildren(QQuickItem)
            if "ScrollBar" in _class_stem(obj)
        ]
        assert _header_offset(widget) == idle_header_offset - 96
        active_image = window.grabWindow()
        assert active_image != idle_image

        assert QMetaObject.invokeMethod(window, "deactivateHorizontalScroll")
        assert _wait_for(lambda: _header_offset(widget) == idle_header_offset)
        assert _horizontal_mixins(widget) == [active_mixin]
        assert widget.property("_horizontalScrollMixin") is active_mixin
        assert window.grabWindow() == idle_image

        assert QMetaObject.invokeMethod(window, "activateHorizontalScroll")
        assert _wait_for(
            lambda: _header_offset(widget) == idle_header_offset - 96
        )
        assert _horizontal_mixins(widget) == [active_mixin]
        assert window.grabWindow() == active_image
    finally:
        _dispose_scene(qapp, engine, component, window, previous_handler)

    assert _qt_failures(messages) == []
