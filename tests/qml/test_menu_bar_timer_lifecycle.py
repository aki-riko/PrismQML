# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""MenuBar close timer lifecycle regressions. 菜单栏关闭计时器生命周期回归。"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    Qt,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "navigation"
    / "MenuBar.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "menu-bar-timer-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 640
    height: 240
    visible: true
    color: Enums.backgroundColor

    MenuBar {
        objectName: "interactionMenuBar"
        x: 40
        y: 40
        items: [
            {
                "text": "File",
                "children": [
                    { "text": "New" },
                    { "text": "Open" },
                    { "text": "Save" }
                ]
            }
        ]
    }

    MenuBar {
        objectName: "measuredMenuBar"
        x: 40
        y: 120
        items: [
            { "text": "File", "children": [{ "text": "New" }] },
            { "text": "Edit", "children": [{ "text": "Undo" }] },
            { "text": "View", "children": [{ "text": "Zoom" }] },
            { "text": "Help", "children": [{ "text": "About" }] }
        ]
    }
}
"""


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


def _visual_descendants(item: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(item.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def _timers(menu_bar: QQuickItem) -> list[QObject]:
    timers = {}
    for owner in [menu_bar, *_visual_descendants(menu_bar)]:
        if owner.metaObject().indexOfProperty("_closeTimer") >= 0:
            close_timer = owner.property("_closeTimer")
            if close_timer is not None:
                pointer = shiboken6.getCppPointer(close_timer)[0]
                timers[pointer] = close_timer
        for child in owner.findChildren(QObject):
            if child.metaObject().className() == "QQmlTimer":
                pointer = shiboken6.getCppPointer(child)[0]
                timers[pointer] = child
    return list(timers.values())


def _object_count(menu_bar: QQuickItem) -> int:
    objects = {}
    for owner in [menu_bar, *_visual_descendants(menu_bar)]:
        for child in owner.findChildren(QObject):
            pointer = shiboken6.getCppPointer(child)[0]
            objects[pointer] = child
    return len(objects)


def _menu_button(menu_bar: QQuickItem, text: str) -> QQuickItem:
    matches = [
        item
        for item in _visual_descendants(menu_bar)
        if item.metaObject().indexOfProperty("contentAlignment") >= 0
        and item.property("text") == text
    ]
    assert len(matches) == 1
    return matches[0]


def _popup_core(menu_bar: QQuickItem) -> QQuickItem:
    matches = [
        item
        for item in _visual_descendants(menu_bar)
        if item.metaObject().indexOfProperty("_cachedWidth") >= 0
        and item.metaObject().indexOfProperty("isOpen") >= 0
    ]
    assert len(matches) == 1
    return matches[0]


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _image_hash(image: QImage) -> str:
    normalized = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return hashlib.sha256(bytes(normalized.bits())).hexdigest()


def _create_scene():
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
    interaction_menu_bar = window.findChild(QQuickItem, "interactionMenuBar")
    measured_menu_bar = window.findChild(QQuickItem, "measuredMenuBar")
    assert interaction_menu_bar is not None
    assert measured_menu_bar is not None
    assert _wait_for(window.isExposed)
    return (
        engine,
        component,
        window,
        interaction_menu_bar,
        measured_menu_bar,
        warnings,
    )


def _dispose_scene(qapp, engine, component, window) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def test_menu_bar_close_timer_and_native_popup_lifecycle(qapp):
    """Each menu keeps the close delay and native popup behavior.

    每个菜单必须保留关闭延迟与原生弹层行为。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    (
        engine,
        component,
        window,
        menu_bar,
        measured_menu_bar,
        warnings,
    ) = _create_scene()
    try:
        QTest.mouseMove(window, QPoint(window.width() - 5, window.height() - 5))
        _pump(500)
        initial_timers = _timers(measured_menu_bar)
        interaction_timers = _timers(menu_bar)
        initial_objects = _object_count(measured_menu_bar)
        initial_hash = _image_hash(window.grabWindow())
        file_button = _menu_button(menu_bar, "File")
        click_position = file_button.mapToScene(
            QPointF(file_button.width() / 2, file_button.height() / 2)
        ).toPoint()

        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            click_position,
        )
        assert _wait_for(lambda: menu_bar.property("activeIndex") == 0)
        assert _wait_for(
            lambda: len(_new_visible_windows(windows_before, window)) == 1
        )
        popup = _popup_core(menu_bar)
        assert popup.property("popupHeight") >= 3 * 32

        assert QMetaObject.invokeMethod(popup, "close")
        closing_timers = _timers(menu_bar)
        QTest.mouseMove(window, QPoint(window.width() - 5, window.height() - 5))
        assert _wait_for(
            lambda: _new_visible_windows(windows_before, window) == []
        )
        assert _wait_for(lambda: menu_bar.property("activeIndex") == -1)
        _pump(500)
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qapp.processEvents()
        restored_timers = _timers(measured_menu_bar)
        restored_interaction_timers = _timers(menu_bar)
        restored_objects = _object_count(measured_menu_bar)
        restored_hash = _image_hash(window.grabWindow())

        print(
            "MENU_BAR_TIMER",
            f"measured_timers={len(initial_timers)}/{len(restored_timers)}",
            f"interaction_timers={len(interaction_timers)}/"
            f"{len(closing_timers)}/{len(restored_interaction_timers)}",
            f"objects={initial_objects}/{restored_objects}",
            f"hashes={initial_hash}/{restored_hash}",
        )

        assert len(initial_timers) == 16
        assert len(restored_timers) == 16
        assert len(interaction_timers) == 4
        assert len(closing_timers) == 5
        assert len(restored_interaction_timers) == 4
        # Four unopened menus no longer instantiate one native Window each.
        # 四个未打开菜单不再各自提前实例化一个原生 Window。
        if os.name == "nt":
            assert initial_objects == 363
        else:
            assert initial_objects > 0
        assert restored_objects == initial_objects
        assert restored_hash == initial_hash
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(qapp, engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_menu_bar_source_creates_close_timer_on_demand():
    """Each menu creates its close timer only while needed.

    每个菜单仅在需要时创建自己的关闭计时器。
    """
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert "id: closeTimer\n" not in source
    assert "id: closeTimerComponent" in source
    assert "closeTimerComponent.createObject(" in source
    assert "if (!menuButton.hovered)" in source
    assert "ownerItem._closeTimer = null" in source
    assert "destroy()" in source
