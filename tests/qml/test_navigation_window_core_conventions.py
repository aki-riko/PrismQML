# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""NavigationWindowCore API and state contracts. 导航窗口核心 API 与状态合同。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QMetaObject,
    QObject,
    Property,
    QUrl,
    Slot,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickWindow

import prismqml.python.window as window_module
from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "prismqml" / "PrismQML" / "NavigationWindowCore.qml"
MICA_BACKDROP_TIMER_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "_internal"
    / "NavigationMicaBackdropCommitTimer.qml"
)
MICA_REAPPLY_TIMER_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "_internal"
    / "NavigationMicaReapplyTimer.qml"
)
METRICS_PATH = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "navigation-window-core-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

NavigationWindowCore {
    objectName: "window"
    property int topCount: -1
    property int bottomCount: -1
    property int foundIndex: -1
    property int remainingCount: -1
    property bool loadingAfterStart: false
    property bool loadingAfterFinish: true
    property int bottomPageResult: -99
    property int bottomActionResult: -99
    property int nullableTopCount: -1
    property int nullableBottomCount: -1
    property int nullableFoundIndex: -1
    property int nullPageSourceResult: -99
    property string indicatorKey: ""
    readonly property string bottomCurrentKey: navStub._currentKey
    readonly property int bottomMappedIndex: navStub._bottomPageIndexMap["page_1"] === undefined
        ? -1 : navStub._bottomPageIndexMap["page_1"]
    property var readyEvents: []
    property var bottomEvents: []
    property var pageEvents: []
    property bool smoothScrollDefault: navigationSmoothScroll
    property int scrollDurationDefault: navigationScrollDuration
    property real scrollStepDefault: navigationScrollStep
    property int expectedNavigationScrollDuration: Enums.duration.navigationScroll
    property real defaultScrollStep: Enums.spacing.navigationScrollStep

    width: 640
    height: 480
    visible: false
    shadowMode: Enums.windowShadow.mode_none
    navigationItems: [{"key": "first", "text": "First"}]
    bottomNavigationItems: [
        {"key": "page_1", "text": "Bottom", "selectable": true},
        {"text": "Action", "selectable": false}
    ]

    function exercisePublicApi() {
        addPage(null, "home", "Home", "", "top", "", false)
        addPage(null, "settings", "Settings", "", "bottom", "", false)
        topCount = navigationItems.length
        bottomCount = bottomNavigationItems.length
        foundIndex = findKeyIndex("Home")
        navigateTo("Home")
        removePage("Home")
        remainingCount = navigationItems.length
    }

    function exercisePythonLoading() {
        _startPythonLoading(7)
        loadingAfterStart = _pythonLoading
        _finishPythonLoading()
        loadingAfterFinish = _pythonLoading
    }

    function exerciseBottomItems() {
        bottomPageResult = _handleBottomItemClicked(0, navStub, null, [])
        bottomActionResult = _handleBottomItemClicked(1, navStub, null, [])
        indicatorKey = navStub.lastKey
    }

    function exerciseNullableCollections() {
        navigationItems = null
        bottomNavigationItems = null
        addPage(null, "home", "Recovered", "", "top", "", false)
        addPage(null, "settings", "RecoveredBottom", "", "bottom", "", false)
        nullableTopCount = navigationItems.length
        nullableBottomCount = bottomNavigationItems.length
        navigationItems = [null, {"key": "safe", "text": "Safe"}]
        nullableFoundIndex = findKeyIndex("safe")
        bottomNavigationItems = [{"key": "null-source", "selectable": true}]
        nullPageSourceResult = _handleBottomItemClicked(0, navStub, null, [null])
    }

    onPythonPageReady: (index) => readyEvents = readyEvents.concat(index)
    onBottomItemClicked: (index) => bottomEvents = bottomEvents.concat(index)
    onCurrentPageChanged: (index) => pageEvents = pageEvents.concat(index)

    QtObject {
        id: navStub
        property var _bottomPageIndexMap: ({})
        property bool _skipIndicatorAnimation: false
        property string _currentKey: ""
        property string lastKey: ""
        function updateIndicatorForBottomItem(key) { lastKey = key }
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


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _new_visible_windows(windows_before):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
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
    mica_manager = _UnavailableMicaManager(engine)
    engine.rootContext().setContextProperty("MicaManager", mica_manager)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_navigation_window_core_public_and_internal_contracts(monkeypatch, qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene(monkeypatch)
    try:
        assert QMetaObject.invokeMethod(window, "exercisePublicApi")
        assert window.property("topCount") == 2
        assert window.property("bottomCount") == 3
        assert window.property("foundIndex") == 1
        assert window.property("currentIndex") == 1
        assert window.property("remainingCount") == 1

        assert QMetaObject.invokeMethod(window, "exercisePythonLoading")
        assert window.property("loadingAfterStart")
        assert not window.property("loadingAfterFinish")
        assert _variant(window.property("readyEvents")) == [7]

        assert QMetaObject.invokeMethod(window, "exerciseBottomItems")
        assert window.property("bottomPageResult") == 1
        assert window.property("bottomActionResult") == -1
        assert window.property("indicatorKey") == "page_1"
        assert window.property("bottomCurrentKey") == "page_1"
        assert window.property("bottomMappedIndex") == 1
        assert _variant(window.property("bottomEvents")) == [0, 1]
        assert _variant(window.property("pageEvents")) == [1]
        assert QMetaObject.invokeMethod(window, "exerciseNullableCollections")
        assert window.property("nullableTopCount") == 1
        assert window.property("nullableBottomCount") == 1
        assert window.property("nullableFoundIndex") == 1
        assert window.property("nullPageSourceResult") == -1
        assert window.property("smoothScrollDefault") is True
        assert window.property("scrollDurationDefault") == window.property(
            "expectedNavigationScrollDuration"
        )
        assert window.property("scrollStepDefault") == window.property("defaultScrollStep")
        assert warnings == []
        assert _new_visible_windows(windows_before) == []
    finally:
        _dispose_scene(engine, component, window)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_navigation_window_core_source_conventions_and_mica_tokens():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    backdrop_timer = MICA_BACKDROP_TIMER_PATH.read_text(encoding="utf-8")
    reapply_timer = MICA_REAPPLY_TIMER_PATH.read_text(encoding="utf-8")
    metrics = METRICS_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    assert 'import "navigation"' not in source
    assert 'import "controls/navigation"' not in source
    assert "NavigationMicaBackdropCommitTimer {" in source
    assert "NavigationMicaReapplyTimer {" in source
    assert "id: _micaBackdropCommitTimer" in source
    assert "id: _micaReapplyTimer" in source
    assert "id: _micaLateReapplyTimer" in source
    assert "host: window" in source
    assert "host._micaBackdropReady = true" in backdrop_timer
    assert "interval: Enums.window.micaReapplyDelayMs" in backdrop_timer
    assert "Enums.window.micaLateReapplyDelayMs" in reapply_timer
    assert '"restore:"' in reapply_timer
    assert '"late-restore:"' in reapply_timer
    assert "property bool navigationSmoothScroll: true" in source
    assert "property int navigationScrollDuration: Enums.duration.navigationScroll" in source
    assert "property real navigationScrollStep: Enums.spacing.navigationScrollStep" in source
    assert "readonly property int navigationScroll: 250" in metrics
    assert "readonly property int navigationScrollStep: 72" in metrics
    assert "interval: 16" not in source
    assert "interval: 180" not in source
    assert "readonly property int micaReapplyDelayMs: 16" in metrics
    assert "readonly property int micaLateReapplyDelayMs: 180" in metrics
