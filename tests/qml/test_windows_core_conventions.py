# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""WindowsCore geometry and lifecycle contracts. 窗口核心几何与生命周期合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QPointF,
    QTimer,
    QUrl,
    Slot,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

import prismqml.python.window as window_module
from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "prismqml" / "PrismQML" / "WindowsCore.qml"
METRICS_PATH = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "windows-core-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

WindowsCore {
    objectName: "window"
    readonly property int topLayout: Enums.windowType.title_bar_top
    readonly property int leftLayout: Enums.windowType.title_bar_left
    readonly property int noShadow: Enums.windowShadow.mode_none
    readonly property int qmlShadow: Enums.windowShadow.mode_qml
    readonly property int navPanelMinWidth: Enums.window.navPanelMinWidth
    readonly property int dividerWidth: Enums.border.thin
    readonly property int resizeDelay: Enums.window.resizeHandlesDelayMs

    width: 720
    height: 520
    visible: true
    shadowMode: Enums.windowShadow.mode_none
    windowTitle: "WindowsCore Contract"

    Item {
        objectName: "contentProbe"
        width: 20
        height: 20
    }

    leftPanelContent: [
        Item {
            objectName: "leftProbe"
            width: 16
            height: 16
        }
    ]
}
"""


class _FakeNativeWindow(QObject):
    @Slot(QObject, result=bool)
    def finalizeAttach(self, _window):
        return True

    @Slot(QObject, result=bool)
    def detach(self, _window):
        return True


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2200) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        item = pending.pop()
        result.append(item)
        pending.extend(item.childItems())
    return result


def _resize_areas(window: QQuickWindow) -> list[QQuickItem]:
    return [
        item
        for item in _visual_descendants(window.contentItem())
        if item.metaObject().className().startswith("ResizeArea")
        and item.metaObject().indexOfProperty("edge") >= 0
    ]


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _create_scene(monkeypatch):
    engine = QQmlApplicationEngine()
    native_window = _FakeNativeWindow(engine)
    monkeypatch.setattr(
        window_module, "get_native_window_hook", lambda: native_window
    )
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
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(window.isActive)
    content = window.findChild(QQuickItem, "contentContainer")
    content_probe = window.findChild(QQuickItem, "contentProbe")
    left_probe = window.findChild(QQuickItem, "leftProbe")
    assert (
        content is not None
        and content_probe is not None
        and left_probe is not None
    )
    assert content_probe.parentItem() is content
    return engine, component, window, content, left_probe, warnings


def _dispose_scene(engine, component, window) -> None:
    window.setVisible(False)
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def test_windows_core_top_left_and_qml_shadow_geometry(monkeypatch, qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, content, left_probe, warnings = _create_scene(
        monkeypatch
    )
    try:
        assert window.title() == "WindowsCore Contract"
        assert window.property("titleBarPosition") == window.property("topLayout")
        assert window.property("margin") == 0
        assert content.y() == pytest.approx(window.property("titleBarHeight"))
        assert content.x() == pytest.approx(0)
        assert not left_probe.parentItem().parentItem().isVisible()

        window.setProperty("titleBarPosition", window.property("leftLayout"))
        assert _wait_for(lambda: content.y() == pytest.approx(0))
        expected_left = max(
            window.property("leftPanelWidth"), window.property("navPanelMinWidth")
        ) + window.property("dividerWidth")
        assert content.x() == pytest.approx(expected_left)
        assert left_probe.parentItem().parentItem().isVisible()

        window.setProperty("shadowMode", window.property("qmlShadow"))
        assert _wait_for(
            lambda: window.property("margin") == window.property("shadowSize")
            and window.property("_animScale") == 1.0
            and window.property("_animOpacity") == 1.0
        )
        mapped = content.mapToItem(window.contentItem(), QPointF())
        assert mapped.x() == pytest.approx(
            window.property("margin") + expected_left, abs=0.001
        )
        assert mapped.y() == pytest.approx(window.property("margin"), abs=0.001)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_windows_core_deferred_resize_handles_load_once(monkeypatch, qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, content, left_probe, warnings = _create_scene(
        monkeypatch
    )
    try:
        assert not window.property("_resizeHandlesReady")
        assert _wait_for(lambda: bool(window.property("_resizeHandlesReady")))
        assert _wait_for(lambda: len(_resize_areas(window)) == 4)
        resize_areas = _resize_areas(window)
        assert len(resize_areas) == 4
        _pump(window.property("resizeDelay") // 4)
        assert len(_resize_areas(window)) == 4
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_windows_core_source_conventions_and_timing_tokens():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    assert "interval: Enums.window.resizeHandlesDelayMs" in source
    assert "_animationStartTimer" not in source
    assert "interval: 100" not in source
    assert "interval: 1200" not in source
    metrics = METRICS_PATH.read_text(encoding="utf-8")
    assert "readonly property int resizeHandlesDelayMs: 1200" in metrics
