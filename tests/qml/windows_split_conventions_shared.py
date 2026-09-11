# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""WindowsSplit loading and page-transfer contracts. 分栏窗口加载与页面转移合同。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import (
    Q_ARG,
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    Property,
    qInstallMessageHandler,
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

INTERNAL_PATH = ROOT / "prismqml" / "PrismQML" / "_internal"

SOURCE_PATH = INTERNAL_PATH / "WindowsSplit.qml"

STARTUP_TIMER_PATH = INTERNAL_PATH / "WindowsSplitStartupTimer.qml"

FILLED_SOURCE_PATH = INTERNAL_PATH / "WindowsFilled.qml"

FILLED_STARTUP_TIMER_PATH = INTERNAL_PATH / "WindowsFilledStartupTimer.qml"

BAR_SOURCE_PATH = INTERNAL_PATH / "WindowsBar.qml"

BAR_STARTUP_TIMER_PATH = INTERNAL_PATH / "WindowsBarStartupTimer.qml"

BAR_CONTENT_SOURCE_PATH = INTERNAL_PATH / "WindowsBarContent.qml"

METRICS_PATH = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"

SCENE_URL = QUrl.fromLocalFile(
    str(INTERNAL_PATH / "windows-split-conventions.qml")
)

SPLIT_SCENE_SOURCE = b"""
import QtQuick
import PrismQML
import "." as Internal

Internal.WindowsSplit {
    objectName: "splitWindow"
    width: 760
    height: 540
    visible: true
    shadowMode: Enums.windowShadow.mode_none

    Item {
        objectName: "pageA"
    }

    Item {
        objectName: "pageB"
    }
}
"""

FILLED_SCENE_SOURCE = b"""
import QtQuick
import PrismQML
import "." as Internal

Internal.WindowsFilled {
    objectName: "filledWindow"
    width: 760
    height: 540
    visible: true
    shadowMode: Enums.windowShadow.mode_none
    navigationSmoothScroll: false
    navigationScrollDuration: Enums.duration.slower
    navigationScrollStep: Enums.spacing.xxl

    Item {
        objectName: "pageA"
    }

    Item {
        objectName: "pageB"
    }
}
"""

BAR_SCENE_SOURCE = b"""
import QtQuick
import PrismQML
import "." as Internal

Internal.WindowsBar {
    objectName: "barWindow"
    width: 760
    height: 540
    visible: true
    shadowMode: Enums.windowShadow.mode_none
    navigationSmoothScroll: false
    navigationScrollDuration: Enums.duration.slower
    navigationScrollStep: Enums.spacing.xxl
    navigationItems: null
    bottomNavigationItems: null

    Item {
        objectName: "pageA"
    }

    Item {
        objectName: "pageB"
    }
}
"""

BAR_NON_ITEM_SCENE_SOURCE = b"""
import QtQuick
import PrismQML
import "." as Internal

Internal.WindowsBar {
    id: window
    objectName: "barWindowWithTimer"
    width: 760
    height: 540
    visible: true
    shadowMode: Enums.windowShadow.mode_none

    property QtObject splashProbe: QtObject {
        property int finishCount: 0
        function finish() { finishCount += 1 }
    }
    readonly property int splashFinishCount: splashProbe.finishCount

    splashEnabled: false
    _splashInstance: splashProbe

    Timer {
        objectName: "nonPageTimer"
        running: false
    }

    Item {
        objectName: "pageA"
    }

    Item {
        objectName: "pageB"
    }
}
"""

BAR_SOURCE_MODE_SCENE_SOURCE = b"""
import QtQuick
import PrismQML
import "." as Internal

Internal.WindowsBar {
    id: window
    objectName: "barWindowWithSourcePages"
    width: 760
    height: 540
    visible: true
    shadowMode: Enums.windowShadow.mode_none
    splashEnabled: false
    pageSources: [null]

    Timer {
        objectName: "nonPageTimer"
        running: false
    }

    Item {
        objectName: "auxiliaryItem"
    }
}
"""

class _FakeNativeWindow(QObject):
    @Slot(QObject, result=bool)
    def finalizeAttach(self, _window):
        return True

    @Slot(QObject, result=bool)
    def detach(self, _window):
        return True

class _UnavailableMicaManager(QObject):
    @Property(bool, constant=True)
    def isMicaSupported(self):
        return False

def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()

def _wait_for(predicate, timeout_ms: int = 2400) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()

def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]

def _create_scene(monkeypatch, scene_source, activate=True):
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
    mica_manager = _UnavailableMicaManager(engine)
    engine.rootContext().setContextProperty("MicaManager", mica_manager)
    component = QQmlComponent(engine)
    component.setData(scene_source, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    if activate:
        window.requestActivate()
        assert _wait_for(window.isActive)
    return engine, component, window, warnings

def _dispose_scene(engine, component, window) -> None:
    window.setVisible(False)
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()

def _assert_page_transfer(window):
    assert _wait_for(lambda: window.property("stackedWidget") is not None)
    stack = window.property("stackedWidget")
    navigation = window.property("navigationView")
    page_a = window.findChild(QQuickItem, "pageA")
    page_b = window.findChild(QQuickItem, "pageB")
    assert stack is not None and navigation is not None
    assert page_a is not None and page_b is not None
    assert _wait_for(lambda: stack.property("count") == 2)
    container = stack.property("containerItem")
    assert page_a.parentItem() is container
    assert page_b.parentItem() is container
    assert page_a.isVisible() and not page_b.isVisible()
    if navigation.metaObject().indexOfProperty("smoothScroll") >= 0:
        assert navigation.property("smoothScroll") == window.property(
            "navigationSmoothScroll"
        )
        assert navigation.property("scrollDuration") == window.property(
            "navigationScrollDuration"
        )
        assert navigation.property("scrollStep") == window.property("navigationScrollStep")

    window.setProperty("currentIndex", 1)
    assert _wait_for(lambda: stack.property("_displayIndex") == 1)
    assert stack.property("currentIndex") == 1
    assert not page_a.isVisible() and page_b.isVisible()

def _exercise_page_transfer(
    monkeypatch,
    scene_source,
    check_compact_margin=False,
    expected_warning="",
):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene(monkeypatch, scene_source)
    try:
        _assert_page_transfer(window)
        if check_compact_margin:
            assert window.property("titleBarLeftMargin") == window.property(
                "navCompactWidth"
            )
        if expected_warning:
            assert len(warnings) == 1
            assert expected_warning in warnings[0]
        else:
            assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []

def _exercise_loading_overlay_lifecycle(monkeypatch, scene_source):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene(monkeypatch, scene_source)
    try:
        assert _wait_for(lambda: window.property("stackedWidget") is not None)
        loader = window.findChild(QObject, "loadingOverlayLoader")
        assert loader is not None
        assert loader.property("active") is False
        assert loader.property("item") is None
        assert window.findChild(QQuickItem, "loadingOverlay") is None

        window.setProperty("_pythonPageMode", True)
        window.setProperty("lazyLoading", True)
        stack = window.property("stackedWidget")
        assert QMetaObject.invokeMethod(
            window, "_markPythonPageReady", Q_ARG("QVariant", 0)
        )
        window.setProperty("currentIndex", 1)

        page_transition = stack.findChild(QObject, "lazyPageCircleTransition")
        transition = stack.findChild(QObject, "qmlPageCircleTransition")
        assert page_transition is not None
        assert transition is not None
        animation_started = []
        animation_finished = []
        current_changes = []
        stack.animationStarted.connect(lambda: animation_started.append(True))
        stack.animationFinished.connect(lambda: animation_finished.append(True))
        stack.currentChanged.connect(current_changes.append)

        window.setProperty("loadingText", "Loading overlay probe")
        assert QMetaObject.invokeMethod(
            window, "_startPythonLoading", Q_ARG("QVariant", 1)
        )
        assert loader.property("item") is None
        assert _wait_for(
            lambda: transition.property("collapsing") is True
            and transition.property("running") is True
        )
        assert loader.property("item") is None
        assert _wait_for(lambda: loader.property("item") is not None)
        overlay = window.findChild(QQuickItem, "loadingOverlay")
        assert overlay is loader.property("item")
        assert overlay.property("loading") is True
        assert overlay.isVisible()
        assert overlay.property("backgroundColor").alpha() == 0
        assert overlay.property("text") == "Loading overlay probe"
        rings = [
            child
            for child in overlay.findChildren(QObject)
            if child.metaObject().className().startswith("ProgressRing_")
        ]
        assert len(rings) == 1
        assert rings[0].property("indeterminate") is True
        assert rings[0].findChild(QQuickItem, "progressRingSpinningArc") is not None

        window.setProperty("loadingText", "Updated loading overlay probe")
        assert _wait_for(
            lambda: overlay.property("text") == "Updated loading overlay probe"
        )
        circle_frame = overlay.findChild(QObject, "qmlPageCircleFrame")
        assert circle_frame is None
        assert page_transition.property("collapsed") is True
        assert transition.property("running") is False

        target_page = window.findChild(QQuickItem, "pageB")
        assert target_page is not None
        target_page.setX(0)
        target_page.setY(0)
        target_page.setOpacity(1)
        target_page.setScale(1)

        assert QMetaObject.invokeMethod(
            window, "_markPythonPageReady", Q_ARG("QVariant", 1)
        )
        assert QMetaObject.invokeMethod(window, "_finishPythonLoading")
        assert page_transition.property("active") is True
        assert window.property("_pythonRevealScheduled") is False
        assert _wait_for(
            lambda: transition.property("collapsing") is False
            and transition.property("running") is True
        )
        assert target_page.isVisible()
        assert target_page.x() == 0
        assert 0 <= target_page.y() <= stack.property("popUpOffset")
        assert 0 <= target_page.opacity() < 1
        assert target_page.scale() == 1
        assert animation_started == [True]
        assert overlay.property("loading") is True
        assert _wait_for(lambda: overlay.property("finishing") is True)
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        assert _wait_for(lambda: loader.property("item") is None)
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        assert _wait_for(
            lambda: window.findChild(QQuickItem, "loadingOverlay") is None
        )
        assert _wait_for(lambda: animation_finished == [True])
        assert current_changes == [1]
        assert not [
            child
            for child in loader.findChildren(QObject)
            if child.metaObject().className().startswith("ProgressRing_")
        ]

        quick_switch_phases = []
        transition.collapsingChanged.connect(
            lambda: quick_switch_phases.append(
                bool(transition.property("collapsing"))
            )
        )
        window.setProperty("loadingText", "Recreated loading overlay probe")
        assert QMetaObject.invokeMethod(
            window, "_startPythonLoading", Q_ARG("QVariant", 1)
        )
        assert loader.property("item") is None
        assert QMetaObject.invokeMethod(window, "_finishPythonLoading")
        assert _wait_for(lambda: loader.property("item") is not None)
        recreated = window.findChild(QQuickItem, "loadingOverlay")
        assert recreated is loader.property("item")
        assert recreated.property("text") == "Recreated loading overlay probe"

        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        assert _wait_for(lambda: loader.property("item") is None)
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        assert _wait_for(
            lambda: window.findChild(QQuickItem, "loadingOverlay") is None
        )
        assert _wait_for(lambda: page_transition.property("active") is False)
        assert True in quick_switch_phases
        assert False in quick_switch_phases
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []
