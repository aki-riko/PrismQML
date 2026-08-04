# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ViewportCulling window lifecycle regressions. 视口裁剪窗口生命周期回归。"""

from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QTimer,
    QtMsgType,
    QUrl,
    qInstallMessageHandler,
)
from PySide6.QtGui import QGuiApplication, QImage, QWindow
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QSignalSpy

from prismqml import register_types


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "viewport-culling-window-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: host

    width: 320
    height: 240
    visible: true
    color: Enums.backgroundColor

    Flickable {
        id: flick

        objectName: "flick"
        anchors.fill: parent
        contentWidth: width
        contentHeight: contentColumn.height
        clip: true

        Column {
            id: contentColumn

            width: flick.width

            Repeater {
                model: 12

                Item {
                    required property int index

                    objectName: "hostItem-" + index
                    width: contentColumn.width
                    height: 120

                    ViewportCulling {
                        id: culling

                        objectName: "culling-" + parent.index
                        buffer: 0
                    }

                    Rectangle {
                        anchors.fill: parent
                        visible: culling.inViewport
                        color: parent.index % 2 === 0
                            ? Enums.selectedColor
                            : Enums.cardColor
                    }
                }
            }
        }
    }
}
"""
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


def _wait_for(predicate, timeout_ms: int = 2_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _stable_window_image(window: QQuickWindow) -> QImage:
    previous = QImage()
    stable_frames = 0
    for _ in range(30):
        current = window.grabWindow()
        assert not current.isNull()
        if current == previous:
            stable_frames += 1
            if stable_frames == 3:
                return current
        else:
            stable_frames = 0
        previous = current
        _pump(20)
    raise AssertionError("ViewportCulling frame did not stabilize within 600 ms")


def _image_hash(image: QImage) -> str:
    rgba = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return sha256(bytes(rgba.constBits())).hexdigest()


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _qt_failures(messages) -> list[str]:
    return [
        message
        for mode, message in messages
        if mode in QT_FAILURE_TYPES
        and not message.startswith(KNOWN_ENVIRONMENT_WARNING_PREFIXES)
    ]


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    descendants = []
    pending = list(root.childItems())
    while pending:
        item = pending.pop()
        descendants.append(item)
        pending.extend(item.childItems())
    return descendants


def _culling_items(window: QQuickWindow) -> list[QQuickItem]:
    items = [
        item
        for item in _visual_descendants(window.contentItem())
        if item.objectName().startswith("culling-")
    ]
    assert len(items) == 12
    return items


def _culling_timers(items: list[QQuickItem]) -> list[QObject]:
    timers = []
    for item in items:
        matches = [
            obj
            for obj in item.findChildren(QObject)
            if obj.metaObject().className() == "QQmlTimer"
            and obj.property("interval") == 150
            and obj.property("repeat") is True
        ]
        assert len(matches) == 1
        timers.extend(matches)
    return timers


def _create_scene():
    messages = []
    previous_handler = qInstallMessageHandler(
        lambda mode, _context, message: messages.append((mode, str(message)))
    )
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    engine.addImportPath(str(ROOT / "prismqml"))
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    flick = window.findChild(QQuickItem, "flick")
    assert flick is not None
    assert _wait_for(window.isExposed)
    culling_items = _culling_items(window)
    timers = _culling_timers(culling_items)
    return (
        engine,
        component,
        window,
        flick,
        culling_items,
        timers,
        warnings,
        messages,
        previous_handler,
    )


def _dispose_scene(qapp, engine, component, window, previous_handler) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()
    qInstallMessageHandler(previous_handler)


def test_hidden_scroll_restores_the_first_culled_frame(qapp):
    """Hidden scrolling must restore the correct first visible frame.

    隐藏期间滚动后恢复的首个可见帧必须正确。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    (
        engine,
        component,
        window,
        flick,
        culling_items,
        timers,
        warnings,
        messages,
        previous_handler,
    ) = scene
    try:
        assert all(timer.property("running") is True for timer in timers)
        assert _wait_for(
            lambda: sum(bool(item.property("inViewport")) for item in culling_items)
            == 2
        )
        top_image = _stable_window_image(window)

        spies = [QSignalSpy(timer.triggered) for timer in timers]
        _pump(360)
        visible_wakeups = sum(spy.count() for spy in spies)
        assert visible_wakeups >= 24

        window.hide()
        assert _wait_for(
            lambda: window.visibility() == QWindow.Visibility.Hidden
        )
        hidden_start = [spy.count() for spy in spies]
        flick.setProperty("contentY", 840)
        _pump(360)
        hidden_wakeups = sum(
            spy.count() - initial for spy, initial in zip(spies, hidden_start)
        )
        hidden_running_count = sum(
            bool(timer.property("running")) for timer in timers
        )

        window.show()
        assert _wait_for(window.isExposed)
        assert all(timer.property("running") is True for timer in timers)
        first_restored_image = window.grabWindow()
        assert not first_restored_image.isNull()
        restored_image = _stable_window_image(window)
        assert first_restored_image == restored_image
        assert restored_image != top_image
        assert sum(
            bool(item.property("inViewport")) for item in culling_items
        ) == 2
        assert warnings == []
        assert _qt_failures(messages) == []
        assert _new_visible_windows(windows_before, window) == []

        print(
            "VIEWPORT_CULLING_WINDOW",
            f"hashes={_image_hash(top_image)}/{_image_hash(restored_image)}",
            f"wakeups={visible_wakeups}/{hidden_wakeups}",
            f"hiddenRunning={hidden_running_count}",
        )
    finally:
        _dispose_scene(qapp, engine, component, window, previous_handler)
        assert _new_visible_windows(windows_before) == []
