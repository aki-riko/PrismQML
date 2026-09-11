# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
from scroll_bar_conventions_scenes import (
    SCENE_SOURCE,
)

# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ScrollBar component group runtime contracts. ScrollBar 组件组运行时合同。"""

from pathlib import Path, PurePosixPath

import pytest

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPoint,
    QPointF,
    QTimer,
    QUrl,
    Qt,
)

from PySide6.QtGui import QGuiApplication, QWheelEvent

from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from PySide6.QtQuick import QQuickItem, QQuickWindow

from PySide6.QtTest import QTest

from prismqml import register_types

from scripts.qml_conventions import scan_source_text

ROOT = Path(__file__).resolve().parents[2]

SOURCE_DIR = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "containers"
    / "ScrollBar"
)

SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "scroll-bar-conventions.qml")
)

def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()

def _wait_for(predicate, timeout_ms: int = 1500) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()

def _wait_for_stable(predicate, stable_checks: int = 5, timeout_ms: int = 1500) -> bool:
    elapsed = 0
    consecutive_matches = 0
    while elapsed < timeout_ms:
        QCoreApplication.processEvents(QEventLoop.AllEvents)
        consecutive_matches = consecutive_matches + 1 if predicate() else 0
        if consecutive_matches >= stable_checks:
            return True
        QTest.qSleep(10)
        elapsed += 10
    return False

def _smooth_scroll_helper(item: QQuickItem, orientation: Qt.Orientation) -> QQuickItem:
    return next(
        child
        for child in item.findChildren(QQuickItem)
        if "SmoothScrollHelper" in child.metaObject().className()
        and child.property("orientation") == orientation.value
    )

def _send_wheel(window: QQuickWindow, item: QQuickItem, delta: int) -> QWheelEvent:
    position = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    global_position = QPointF(
        window.x() + position.x(),
        window.y() + position.y(),
    )
    event = QWheelEvent(
        position,
        global_position,
        QPoint(0, 0),
        QPoint(0, delta),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    assert QGuiApplication.sendEvent(window, event)
    return event

def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is accepted for accepted in allowed)
    ]

def _outward_excursions(trajectory, boundary, at_start, tolerance=0.5):
    """Count separate outward legs beyond one boundary. 统计越界外移腿的段数。"""
    excursions = 0
    was_outside = False
    for value in trajectory:
        outside = (
            value < boundary - tolerance if at_start else value > boundary + tolerance
        )
        if outside and not was_outside:
            excursions += 1
        was_outside = outside
    return excursions

def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    _pump()
    items = {
        name: window.findChild(QQuickItem, name)
        for name in (
            "verticalFlick",
            "horizontalFlick",
            "popupFlick",
            "scrollBar",
            "scrollBarEntry",
            "defaultArea",
            "listArea",
            "gridArea",
        )
    }
    assert all(items.values())
    return engine, component, window, items, warnings

def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()

@pytest.fixture
def scroll_scene(qapp):
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    try:
        yield (*scene[2:], windows_before)
    finally:
        _dispose_scene(scene[0], scene[1], scene[2])
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before
