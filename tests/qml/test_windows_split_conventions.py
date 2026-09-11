# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Domain bucket 1/1 of the former test_windows_split_conventions.py."""
import pytest  # noqa: F401
from windows_split_conventions_shared import *
from windows_split_conventions_shared import (
    _FakeNativeWindow,
    _UnavailableMicaManager,
    _pump,
    _wait_for,
    _new_visible_windows,
    _create_scene,
    _dispose_scene,
    _assert_page_transfer,
    _exercise_page_transfer,
    _exercise_loading_overlay_lifecycle,
)

def test_windows_split_loads_core_and_transfers_default_pages(monkeypatch, qapp):
    _exercise_page_transfer(monkeypatch, SPLIT_SCENE_SOURCE, True)

def test_windows_split_startup_timer_preserves_delayed_loader_activation(
    monkeypatch, qapp
):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene(
        monkeypatch, SPLIT_SCENE_SOURCE, activate=False
    )
    try:
        timer = window.findChild(QObject, "windowsSplitStartupTimer")
        loader = window.findChild(QObject, "windowsSplitCoreLoader")
        assert timer is not None and loader is not None
        assert timer.parent() is loader.parent()
        assert timer.property("running") is True
        assert timer.property("interval") > 0
        assert loader.property("active") is False
        assert window.property("stackedWidget") is None

        window.requestActivate()
        assert _wait_for(window.isActive)
        assert _wait_for(lambda: loader.property("active") is True)
        assert _wait_for(lambda: window.property("stackedWidget") is not None)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []

def test_windows_filled_loads_core_and_transfers_default_pages(monkeypatch, qapp):
    _exercise_page_transfer(monkeypatch, FILLED_SCENE_SOURCE)

def test_windows_filled_startup_timer_preserves_delayed_loader_activation(
    monkeypatch, qapp
):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene(
        monkeypatch, FILLED_SCENE_SOURCE, activate=False
    )
    try:
        timer = window.findChild(QObject, "windowsFilledStartupTimer")
        loader = window.findChild(QObject, "windowsFilledCoreLoader")
        assert timer is not None and loader is not None
        assert timer.parent() is loader.parent()
        assert timer.property("targetLoader") is loader
        assert timer.property("running") is True
        assert timer.property("interval") > 0
        assert loader.property("active") is False
        assert window.property("stackedWidget") is None

        window.requestActivate()
        assert _wait_for(window.isActive)
        assert _wait_for(lambda: loader.property("active") is True)
        assert _wait_for(lambda: window.property("stackedWidget") is not None)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []

def test_windows_bar_loads_core_and_transfers_default_pages(monkeypatch, qapp):
    _exercise_page_transfer(monkeypatch, BAR_SCENE_SOURCE)

def test_windows_bar_startup_timer_preserves_gate_and_loader_setup(
    monkeypatch, qapp
):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene(
        monkeypatch, BAR_SCENE_SOURCE, activate=False
    )
    try:
        timer = window.findChild(QObject, "windowsBarStartupTimer")
        loader = window.findChild(QObject, "windowsBarMainLoader")
        assert timer is not None and loader is not None
        assert timer.parent() is loader.parent()
        assert timer.property("host") is window
        assert timer.property("targetLoader") is loader
        assert timer.property("interval") == 0
        assert timer.property("running") is False
        assert window.property("_startupContentStarted") is False
        assert loader.property("active") is False
        assert window.property("stackedWidget") is None

        window.requestActivate()
        assert _wait_for(window.isActive)
        assert _wait_for(lambda: timer.property("running") is False)
        assert _wait_for(lambda: loader.property("active") is True)
        assert _wait_for(lambda: window.property("stackedWidget") is not None)
        assert window.property("_startupContentStarted") is True
        assert loader.property("source").toString().endswith(
            "WindowsBarContent.qml"
        )
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []

def test_windows_split_creates_loading_overlay_only_while_needed(monkeypatch, qapp):
    _exercise_loading_overlay_lifecycle(monkeypatch, SPLIT_SCENE_SOURCE)

def test_windows_filled_creates_loading_overlay_only_while_needed(monkeypatch, qapp):
    _exercise_loading_overlay_lifecycle(monkeypatch, FILLED_SCENE_SOURCE)

def test_windows_bar_creates_loading_overlay_only_while_needed(monkeypatch, qapp):
    _exercise_loading_overlay_lifecycle(monkeypatch, BAR_SCENE_SOURCE)

def test_windows_bar_skips_non_item_default_child_and_dismisses_splash(
    monkeypatch, qapp
):
    marker = "[WindowsBar] Skipping non-Item default child"
    messages = []
    previous_handler = None

    def message_handler(message_type, context, message):
        if marker in message:
            messages.append(message)
            return
        if previous_handler is not None:
            previous_handler(message_type, context, message)

    previous_handler = qInstallMessageHandler(message_handler)
    windows_before = tuple(QGuiApplication.topLevelWindows())
    try:
        engine, component, window, warnings = _create_scene(
            monkeypatch, BAR_NON_ITEM_SCENE_SOURCE
        )
        try:
            _assert_page_transfer(window)
            assert _wait_for(lambda: window.property("_splashDismissed"))
            assert window.property("splashFinishCount") == 1
            assert messages == [
                marker + " / 跳过非 Item 默认子对象: sourceIndex=0"
            ]
            assert not any(
                "Cannot assign to read-only property \"parent\"" in warning
                for warning in warnings
            )
            assert _new_visible_windows(windows_before, window) == []
        finally:
            _dispose_scene(engine, component, window)
            assert _new_visible_windows(windows_before) == []
    finally:
        qInstallMessageHandler(previous_handler)

def test_windows_bar_source_pages_do_not_migrate_default_children(
    monkeypatch, qapp
):
    marker = "[WindowsBar] Skipping non-Item default child"
    messages = []
    previous_handler = None

    def message_handler(message_type, context, message):
        if marker in message:
            messages.append(message)
            return
        if previous_handler is not None:
            previous_handler(message_type, context, message)

    previous_handler = qInstallMessageHandler(message_handler)
    windows_before = tuple(QGuiApplication.topLevelWindows())
    try:
        engine, component, window, warnings = _create_scene(
            monkeypatch, BAR_SOURCE_MODE_SCENE_SOURCE
        )
        try:
            assert _wait_for(lambda: window.property("stackedWidget") is not None)
            stack = window.property("stackedWidget")
            assert stack.property("count") == 1
            auxiliary = window.findChild(QQuickItem, "auxiliaryItem")
            assert auxiliary is not None
            assert auxiliary.parentItem() is not stack.property("containerItem")
            assert messages == []
            assert not any(marker in warning for warning in warnings)
            assert _new_visible_windows(windows_before, window) == []
        finally:
            _dispose_scene(engine, component, window)
            assert _new_visible_windows(windows_before) == []
    finally:
        qInstallMessageHandler(previous_handler)

def test_windows_split_source_conventions_and_startup_delay_token():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    helper_source = STARTUP_TIMER_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    helper_path = PurePosixPath(STARTUP_TIMER_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path) + scan_source_text(
        helper_source, helper_path
    )
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    assert "WindowsSplitStartupTimer {" in source
    assert "targetLoader: coreLoader" in source
    assert "\n Timer {" not in source
    assert "onTriggered: coreLoader.active = true" not in source
    assert "required property var targetLoader" in helper_source
    assert "interval: Enums.window.splitStartupDelayMs" in helper_source
    assert "running: true" in helper_source
    assert "onTriggered: targetLoader.active = true" in helper_source
    assert "default property list<QtObject> pages" in source
    assert "id: _hiddenStack" not in source
    assert "interval: 50" not in helper_source
    assert "paperOriginX: window.navCompactWidth" in source
    assert "paperOriginY: window.titleBarHeight" in source
    assert "pageStack.stackAlias, window.pageSources" in source
    assert "navInterface, stack," not in source
    metrics = METRICS_PATH.read_text(encoding="utf-8")
    assert "readonly property int splitStartupDelayMs: 50" in metrics

def test_windows_filled_source_conventions_and_stack_binding():
    source = FILLED_SOURCE_PATH.read_text(encoding="utf-8")
    helper_source = FILLED_STARTUP_TIMER_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(FILLED_SOURCE_PATH.relative_to(ROOT).as_posix())
    helper_path = PurePosixPath(FILLED_STARTUP_TIMER_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path) + scan_source_text(
        helper_source, helper_path
    )
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    assert "WindowsFilledStartupTimer {" in source
    assert "targetLoader: mainLoader" in source
    assert "\n        Timer {" not in source
    assert "onTriggered: mainLoader.active = true" not in source
    assert "required property var targetLoader" in helper_source
    assert 'objectName: "windowsFilledStartupTimer"' in helper_source
    assert "interval: Enums.window.splitStartupDelayMs" in helper_source
    assert "running: true" in helper_source
    assert "onTriggered: targetLoader.active = true" in helper_source
    assert "stackedWidget: stack" not in source
    assert "default property list<QtObject> pages" in source
    assert "id: _hiddenStack" not in source
    assert "window.stackedWidget = item.stackAlias" in source
    assert "smoothScroll: window.navigationSmoothScroll" in source
    assert "scrollDuration: window.navigationScrollDuration" in source

def test_windows_bar_source_conventions_and_startup_gate():
    source = BAR_SOURCE_PATH.read_text(encoding="utf-8")
    helper_source = BAR_STARTUP_TIMER_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(BAR_SOURCE_PATH.relative_to(ROOT).as_posix())
    helper_path = PurePosixPath(BAR_STARTUP_TIMER_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path) + scan_source_text(
        helper_source, helper_path
    )
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    assert "WindowsBarStartupTimer {" in source
    assert "host: window" in source
    assert "targetLoader: mainLoader" in source
    assert "\n        Timer {" not in source
    assert "window._startupContentStarted = true" not in source
    assert "mainLoader.setSource" not in source
    assert "required property var host" in helper_source
    assert "required property var targetLoader" in helper_source
    assert "interval: Enums.duration.none" in helper_source
    assert "interval: 0" not in source
    assert (
        "running: !window._startupContentStarted &&\n"
        "        (window.lazyLoading || window._startupPresentationReady)"
        not in source
    )
    assert (
        "running: !host._startupContentStarted &&\n"
        "        (host.lazyLoading || host._startupPresentationReady)"
        in helper_source
    )
    assert "host._startupContentStarted = true" in helper_source
    assert "targetLoader.setSource(Qt.resolvedUrl(\"WindowsBarContent.qml\")" in helper_source
    assert "targetLoader.active = true" in helper_source
    assert "host.profileTime(\"WindowsBar startupTimer triggered\")" in helper_source
    assert "host.profileTime(\"WindowsBar mainLoader.active=true\")" in helper_source
    assert "window._moveDefaultPages(" in source
    assert "default property list<QtObject> pages" in source
    assert "id: _hiddenStack" not in source
    assert "finally {" in source
    content_source = BAR_CONTENT_SOURCE_PATH.read_text(encoding="utf-8")
    assert (
        "smoothScroll: root.hostWindow ? root.hostWindow.navigationSmoothScroll : true"
        in content_source
    )
    assert (
        "scrollDuration: root.hostWindow ? "
        "root.hostWindow.navigationScrollDuration : Enums.duration.navigationScroll"
        in content_source
    )
    assert "pageStack.stackAlias, root.hostWindow.pageSources" in content_source
    assert "navigationBar, stack," not in content_source
    assert (
        "scrollStep: root.hostWindow ? "
        "root.hostWindow.navigationScrollStep : Enums.spacing.navigationScrollStep"
        in content_source
    )
    assert "paperOriginX: root._compactNav ? 0 : navigationBar.width" in content_source
    assert "typeof hostWindow.titleBarHeight === \"number\"" in content_source
    assert "paperOriginY: root._windowPaperOriginY" in content_source
    assert "!!hostWindow && Enums.isVintageTicket && !root._compactNav" in content_source
    assert content_source.count(
        "backgroundColor: root._usesWindowTicketPaper"
    ) == 2
    assert content_source.count(
        "ticketPaperEnabled: !root._usesWindowTicketPaper"
    ) == 2
    assert 'objectName: "ticketTitleDivider"' in content_source
    assert "width: navigationBar.width" in content_source
    assert "visible: Enums.isVintageTicket && !root._compactNav" in content_source
    assert (
        "model: root.hostWindow && !root._compactNav\n"
        "            ? root.hostWindow.navigationItems : []"
        in content_source
    )
    assert (
        "bottomItems: root.hostWindow && !root._compactNav\n"
        "            ? root.hostWindow.bottomNavigationItems : []"
        in content_source
    )
