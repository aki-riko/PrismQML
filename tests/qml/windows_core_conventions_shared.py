# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
from windows_core_conventions_scenes import (
    SCENE_SOURCE,
)

# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""WindowsCore geometry and lifecycle contracts. 窗口核心几何与生命周期合同。"""

from pathlib import Path, PurePosixPath

import pytest

from PySide6.QtCore import (
    QCoreApplication,
    QEasingCurve,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    QTimer,
    Qt,
    QUrl,
    Slot,
)

from PySide6.QtGui import QGuiApplication, QWindow

from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from PySide6.QtQuick import QQuickItem, QQuickWindow

from PySide6.QtTest import QTest

import prismqml.python.runtime.window_services as window_services_module

from prismqml import register_types

from scripts.qml_conventions import scan_source_text

ROOT = Path(__file__).resolve().parents[2]

SOURCE_PATH = ROOT / "prismqml" / "PrismQML" / "WindowsCore.qml"

# Enums.windowShadow.mode_qml, kept in sync with PrismEnums/WindowShadow.qml.
# 与 PrismEnums/WindowShadow.qml 保持同步。
_WINDOW_SHADOW_MODE_QML = 2

WINDOW_FRAME_PATH = (
    ROOT / "prismqml" / "PrismQML" / "_internal" / "WindowsCoreFrame.qml"
)

RESIZE_HANDLES_TIMER_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "_internal"
    / "WindowsResizeHandlesTimer.qml"
)

WINDOW_ICON_DEFERRED_TIMER_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "_internal"
    / "WindowIconDeferredLoadTimer.qml"
)

ANIMATION_HELPER_PATH = (
    ROOT / "prismqml" / "PrismQML" / "_internal" / "WindowAnimationHelper.qml"
)

WINDOW_CLOSE_FRAME_WAITER_PATH = (
    ROOT / "prismqml" / "PrismQML" / "_internal" / "WindowCloseFrameWaiter.qml"
)

WINDOW_DRAG_HANDLE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "utils"
    / "WindowDragHandle.qml"
)

WINDOW_LEAF_PATHS = [
    ROOT / "prismqml" / "PrismQML" / "_internal" / name
    for name in (
        "QmlShadowHost.qml",
        "ResizeArea.qml",
        "WindowIcon.qml",
        "CaptionButton.qml",
        "TitleBarActionButton.qml",
        "ContentFrame.qml",
        "WindowsCoreFrame.qml",
    )
]

STARTUP_DIAGNOSTIC_PATHS = [
    ROOT / "prismqml" / "PrismQML" / "NavigationWindowCore.qml",
    ROOT / "prismqml" / "PrismQML" / "_internal" / "WindowsBar.qml",
    ROOT / "prismqml" / "PrismQML" / "_internal" / "WindowsBarContent.qml",
    ANIMATION_HELPER_PATH,
    *WINDOW_LEAF_PATHS,
]

WINDOW_BUILDER_PATH = (
    ROOT / "prismqml" / "python" / "window" / "_window_builder.py"
)

METRICS_PATH = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"

ENUMS_PATH = ROOT / "prismqml" / "PrismQML" / "Enums.qml"

CAPTION_BUTTON_PATH = (
    ROOT / "prismqml" / "PrismQML" / "_internal" / "CaptionButton.qml"
)

REMOVED_CLOSE_EFFECT_PATHS = [
    ROOT / "prismqml" / "PrismQML" / relative_path
    for relative_path in (
        "_internal/WindowCloseDissolve.qml",
        "_internal/CloseRippleAnimator.qml",
        "_internal/CloseRippleDissolve.qml",
        "_internal/CloseRippleFrame.qml",
        "shaders/window_close_ripple.frag",
        "shaders/window_close_ripple.frag.qsb",
    )
]

SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "windows-core-conventions.qml")
)

class _FakeNativeWindow(QObject):
    def __init__(self, events, parent=None):
        super().__init__(parent)
        self._events = events

    @Slot(QObject, result=bool)
    def finalizeAttach(self, _window):
        self._events.append("native-finalized")
        return True

    @Slot(QObject, result=bool)
    def detach(self, _window):
        return True

    @Slot(QObject, result=bool)
    def requestMaximize(self, window):
        self._events.append("native-maximize")
        window.showMaximized()
        return True

    @Slot(QObject, result=bool)
    def requestRestore(self, window):
        self._events.append("native-restore")
        window.showNormal()
        return True

class _FakeWindowHelper(QObject):
    def __init__(self, events, parent=None):
        super().__init__(parent)
        self._events = events

    @Slot(str)
    def setAppIcon(self, icon):
        assert icon
        self._events.append("icon")

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

def _create_scene(
    monkeypatch,
    *,
    initial_left_layout: bool = False,
    custom_close: bool = False,
    none_close: bool = False,
):
    engine = QQmlApplicationEngine()
    startup_events = []
    native_window = _FakeNativeWindow(startup_events, engine)
    window_helper = _FakeWindowHelper(startup_events, engine)
    monkeypatch.setattr(
        window_services_module, "get_native_window_hook", lambda: native_window
    )
    monkeypatch.setattr(
        window_services_module, "get_window_helper", lambda: window_helper
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
    window = component.createWithInitialProperties(
        {
            "initialLeftLayout": initial_left_layout,
            "customClose": custom_close,
            "noneClose": none_close,
        },
        engine.rootContext(),
    )
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
    return (
        engine,
        component,
        window,
        content,
        left_probe,
        warnings,
        startup_events,
    )

def _dispose_scene(engine, component, window) -> None:
    window.setVisible(False)
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()
