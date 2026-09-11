# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
from timeline_conventions_scenes import (
    SCENE_SOURCE,
)

# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""TimelineCore runtime contracts. TimelineCore 运行时合同。"""

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

SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "containers"
    / "TimelineCore.qml"
)

GRAPH_SOURCE_PATH = SOURCE_PATH.with_name("TimelineGraphLayer.qml")

GRAPH_LABELS_SOURCE_PATH = SOURCE_PATH.with_name("TimelineGraphLabels.qml")

VIRTUAL_ROW_SOURCE_PATH = SOURCE_PATH.parent / "_internal" / "TimelineVirtualRow.qml"

SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "timeline-conventions.qml")
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

def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is accepted for accepted in allowed)
    ]

def _visual_descendants(item):
    descendants = []
    for child in item.childItems():
        descendants.append(child)
        descendants.extend(_visual_descendants(child))
    return descendants

def _named_visible_descendants(item, object_name):
    return [
        child
        for child in _visual_descendants(item)
        if child.objectName() == object_name and child.isVisible()
    ]

def _send_wheel(window, item, delta):
    position = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    global_position = QPointF(window.x() + position.x(), window.y() + position.y())
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
    timeline = window.findChild(QQuickItem, "timeline")
    virtual_timeline = window.findChild(QQuickItem, "virtualTimeline")
    assert timeline is not None
    assert virtual_timeline is not None
    _pump()
    return engine, component, window, timeline, virtual_timeline, warnings

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
def timeline_scene(qapp):
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    try:
        yield (*scene[2:], windows_before)
    finally:
        _dispose_scene(scene[0], scene[1], scene[2])
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before

def _virtual_viewport_and_helper(owner):
    list_view = next(
        item
        for item in owner.findChildren(QQuickItem)
        if item.objectName() == "timelineVirtualViewport"
    )
    helper = next(
        item
        for item in owner.findChildren(QQuickItem)
        if "SmoothScrollHelper" in item.metaObject().className()
    )
    return list_view, helper
