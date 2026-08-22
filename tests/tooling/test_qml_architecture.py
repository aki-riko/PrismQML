# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QML architecture boundaries and size gates. QML 架构边界与大小门禁。"""

import re
from pathlib import Path, PurePosixPath

from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
QML_ROOT = ROOT / "prismqml" / "PrismQML"
OVERSIZED_QML_EXCEPTIONS = {
    "prismqml/PrismQML/PrismEnums/Metrics.qml",
}


def _source(relative_path: str) -> Path:
    return ROOT / relative_path


def _declaration_indent(source: str, declaration: str) -> int:
    """返回声明所在行的缩进宽度, 用于判断两个对象是否同级。

    Indentation width of the line declaring ``declaration``, so callers can tell
    a sibling from a nested child.
    """
    for line in source.splitlines():
        if line.strip() == declaration:
            return len(line) - len(line.lstrip())
    raise AssertionError(f"declaration not found: {declaration}")


def _assert_modularized(entry_path: str, helper_path: str, helper_type: str) -> None:
    entry = _source(entry_path)
    helper = _source(helper_path)

    assert entry.exists()
    assert helper.exists()
    assert len(entry.read_text(encoding="utf-8").splitlines()) <= 700
    assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
    assert f"{helper_type} {{" in entry.read_text(encoding="utf-8")


def test_qml_files_respect_hard_size_limit():
    violations = []
    for path in sorted(QML_ROOT.rglob("*.qml")):
        relative = path.relative_to(ROOT).as_posix()
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > 700 and relative not in OVERSIZED_QML_EXCEPTIONS:
            violations.append(f"{relative}: {line_count} lines")

    assert violations == []


def test_windows_core_keeps_frame_modularized():
    entry = _source("prismqml/PrismQML/WindowsCore.qml")
    helper = _source(
        "prismqml/PrismQML/_internal/WindowsCoreFrame.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 500
    assert "WindowsCoreFrame {" in source
    assert "required property var targetWindow" in helper_source
    assert "property alias contentData: contentContainer.data" in helper_source
    assert "property alias leftPanelData: leftPanelContainer.data" in helper_source
    assert "id: windowFrame\n" not in source
    assert "id: contentContainer" not in source
    assert "WindowDragHandle {" not in source


def test_windows_core_keeps_resize_timer_modularized():
    entry = _source("prismqml/PrismQML/WindowsCore.qml")
    helper = _source(
        "prismqml/PrismQML/_internal/WindowsResizeHandlesTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 80
    assert "WindowsResizeHandlesTimer {" in source
    assert "id: _resizeHandlesTimer" in source
    assert "host: window" in source
    assert "required property var host" in helper_source
    assert "interval: Enums.window.resizeHandlesDelayMs" in helper_source
    assert "host._resizeHandlesReady = true" in helper_source
    assert "\n    Timer {" not in source


def test_windows_split_keeps_startup_timer_modularized():
    entry = _source("prismqml/PrismQML/_internal/WindowsSplit.qml")
    helper = _source(
        "prismqml/PrismQML/_internal/WindowsSplitStartupTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 280
    assert helper.exists()
    assert len(helper_source.splitlines()) < 60
    assert "WindowsSplitStartupTimer {" in source
    assert "id: startupTimer" in source
    assert "targetLoader: coreLoader" in source
    assert 'objectName: "windowsSplitCoreLoader"' in source
    assert "\n Timer {" not in source
    assert "required property var targetLoader" in helper_source
    assert 'objectName: "windowsSplitStartupTimer"' in helper_source
    assert "interval: Enums.window.splitStartupDelayMs" in helper_source
    assert "running: true" in helper_source
    assert "onTriggered: targetLoader.active = true" in helper_source
    assert "coreLoader" not in helper_source


def test_windows_bar_keeps_startup_timer_modularized():
    entry = _source("prismqml/PrismQML/_internal/WindowsBar.qml")
    helper = _source(
        "prismqml/PrismQML/_internal/WindowsBarStartupTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 90
    assert helper.exists()
    assert len(helper_source.splitlines()) < 80
    assert "WindowsBarStartupTimer {" in source
    assert "id: startupTimer" in source
    assert "host: window" in source
    assert "targetLoader: mainLoader" in source
    assert 'objectName: "windowsBarMainLoader"' in source
    assert "\n        Timer {" not in source
    assert "required property var host" in helper_source
    assert "required property var targetLoader" in helper_source
    assert 'objectName: "windowsBarStartupTimer"' in helper_source
    assert "interval: Enums.duration.none" in helper_source
    assert "running: !host._startupContentStarted" in helper_source
    assert "targetLoader.setSource(Qt.resolvedUrl(\"WindowsBarContent.qml\")" in helper_source
    assert "targetLoader.active = true" in helper_source
    assert "host._startupContentStarted = true" in helper_source
    assert "profileTime(\"WindowsBar startupTimer triggered\")" in helper_source
    assert "profileTime(\"WindowsBar mainLoader.active=true\")" in helper_source
    assert "mainLoader.setSource" not in helper_source
    assert "id: mainLoader" not in helper_source


def test_windows_filled_keeps_startup_timer_modularized():
    entry = _source("prismqml/PrismQML/_internal/WindowsFilled.qml")
    helper = _source(
        "prismqml/PrismQML/_internal/WindowsFilledStartupTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 200
    assert helper.exists()
    assert len(helper_source.splitlines()) < 60
    assert "WindowsFilledStartupTimer {" in source
    assert "id: startupTimer" in source
    assert "targetLoader: mainLoader" in source
    assert 'objectName: "windowsFilledCoreLoader"' in source
    assert "\n        Timer {" not in source
    assert "required property var targetLoader" in helper_source
    assert 'objectName: "windowsFilledStartupTimer"' in helper_source
    assert "interval: Enums.window.splitStartupDelayMs" in helper_source
    assert "running: true" in helper_source
    assert "onTriggered: targetLoader.active = true" in helper_source
    assert "mainLoader" not in helper_source


def test_native_window_startup_keeps_delay_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/_internal/NativeWindowStartupHelper.qml"
    )
    helper = _source(
        "prismqml/PrismQML/_internal/NativeWindowStartupDelayTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 160
    assert helper.exists()
    assert len(helper_source.splitlines()) < 60
    assert "NativeWindowStartupDelayTimer {" in source
    assert "id: delayTimer" in source
    assert "host: root" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "nativeWindowStartupDelayTimer"' in helper_source
    assert "interval: Enums.duration.instant" in helper_source
    assert "onTriggered: host._attemptNativeHook()" in helper_source
    assert "onTriggered: root._attemptNativeHook()" not in source


def test_window_icon_keeps_deferred_load_timer_modularized():
    entry = _source("prismqml/PrismQML/_internal/WindowIcon.qml")
    helper = _source(
        "prismqml/PrismQML/_internal/WindowIconDeferredLoadTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 120
    assert helper.exists()
    assert len(helper_source.splitlines()) < 60
    assert "WindowIconDeferredLoadTimer {" in source
    assert "id: deferredLoadTimer" in source
    assert "host: root" in source
    assert "deferredLoadTimer.restart()" in source
    assert "\n    Timer {" not in source
    assert "onTriggered: {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "windowIconDeferredLoadTimer"' in helper_source
    assert "interval: Enums.window.iconDeferredLoadDelayMs" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: host._deferredLoadReady = true" in helper_source
    assert "root._deferredLoadReady = true" not in source


def test_matrix_rain_keeps_animation_timer_modularized():
    entry = _source("prismqml/PrismQML/effects/MatrixRain.qml")
    helper = _source(
        "prismqml/PrismQML/effects/_internal/MatrixRainAnimationTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 60
    assert 'import "_internal" as MatrixRainInternal' in source
    assert "MatrixRainInternal.MatrixRainAnimationTimer {" in source
    assert "id: animationTimer" in source
    assert "host: root" in source
    assert "targetCanvas: canvas" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert "required property var targetCanvas" in helper_source
    assert 'objectName: "matrixRainAnimationTimer"' in helper_source
    assert "FrameAnimation {" in helper_source
    assert "frameTime * 1000" in helper_source
    assert "function takeStepScale()" in helper_source
    assert "targetCanvas.requestPaint()" in helper_source
    assert "\nTimer {" not in helper_source


def test_matrix_rain_keeps_canvas_rendering_modularized():
    entry = _source("prismqml/PrismQML/effects/MatrixRain.qml")
    helper = _source(
        "prismqml/PrismQML/effects/_internal/MatrixRainCanvas.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 250
    assert helper.exists()
    assert len(helper_source.splitlines()) < 240
    assert "MatrixRainInternal.MatrixRainCanvas {" in source
    assert "required property var host" in helper_source
    assert "onPaint:" in helper_source
    assert "function initDrops()" in helper_source
    assert "function clearCanvas()" in helper_source
    assert "\n    Canvas {" not in source


def test_login_window_keeps_visual_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/auth/LoginWindow.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/auth/_internal/LoginWindowContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 300
    assert helper.exists()
    assert len(helper_source.splitlines()) < 500
    assert 'import "_internal"' in source
    assert "LoginWindowContent {" in source
    assert "required property var loginControl" in helper_source
    assert "property alias usernameInput: usernameInput" in helper_source
    assert "property alias passwordInput: passwordInput" in helper_source
    assert "MatrixRain {" not in source
    assert "ShadowedRectangle {" not in source
    assert 'objectName: "loginModeToggleArea"' not in source


def test_data_widget_core_keeps_visual_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/DataWidgetCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/_internal/DataWidgetContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 250
    assert helper.exists()
    assert len(helper_source.splitlines()) < 500
    assert 'import "_internal"' in source
    assert "DataWidgetContent {" in source
    assert "required property var dataControl" in helper_source
    assert "property alias listView: listView" in helper_source
    assert "property alias scrollViewportState: scrollViewportState" in helper_source
    assert "contentLayer.needsVerticalScrollBar" in source
    assert "function createHorizontalScrollMixin()" in helper_source
    assert "horizontalScrollMixinComponent.createObject(contentArea)" in helper_source
    assert "contentLayer.createHorizontalScrollMixin()" in source
    assert "RectangularShadow {" not in source
    assert "QtQ.ListView {" not in source
    assert "HorizontalScrollMixin {" not in source


def test_navigation_window_core_keeps_orchestration_modularized():
    entry = _source("prismqml/PrismQML/NavigationWindowCore.qml")
    loading = _source(
        "prismqml/PrismQML/_internal/NavigationWindowLoading.js"
    )
    routing = _source(
        "prismqml/PrismQML/_internal/NavigationWindowRouting.js"
    )
    source = entry.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    for helper in (loading, routing):
        assert helper.exists()
        helper_source = helper.read_text(encoding="utf-8")
        assert len(helper_source.splitlines()) < 500
        assert ".pragma library" in helper_source

    assert (
        'import "_internal/NavigationWindowLoading.js" '
        "as NavigationWindowLoading"
    ) in source
    assert (
        'import "_internal/NavigationWindowRouting.js" '
        "as NavigationWindowRouting"
    ) in source
    assert "NavigationWindowLoading.start(window, index)" in source
    assert "NavigationWindowLoading.completeVisual(window, index)" in source
    assert "NavigationWindowRouting.moveDefaultPages(window," in source
    assert "NavigationWindowRouting.syncSelection(window," in source
    assert "NavigationWindowRouting.handleBottomItemClicked(window," in source


def test_navigation_window_core_keeps_splash_timer_modularized():
    entry = _source("prismqml/PrismQML/NavigationWindowCore.qml")
    helper = _source(
        "prismqml/PrismQML/_internal/NavigationSplashTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 480
    assert helper.exists()
    assert len(helper_source.splitlines()) < 80
    assert 'import "_internal"' in source
    assert "NavigationSplashTimer {" in source
    assert "id: _splashTimer" in source
    assert "host: window" in source
    assert "Timer {" in helper_source
    assert "required property var host" in helper_source
    assert "property bool _minimumVisiblePhase: false" in helper_source
    assert "property int _minimumVisibleInterval:" in helper_source
    assert "property var _onTimeout: null" in helper_source
    assert "host._scheduleSplashDismiss()" in helper_source
    assert "Enums.duration.splashTimeout" in helper_source
    assert "property bool _minimumVisiblePhase: false" not in source
    assert "property var _onTimeout: null" not in source


def test_navigation_window_core_keeps_mica_timers_modularized():
    entry = _source("prismqml/PrismQML/NavigationWindowCore.qml")
    backdrop = _source(
        "prismqml/PrismQML/_internal/NavigationMicaBackdropCommitTimer.qml"
    )
    reapply = _source(
        "prismqml/PrismQML/_internal/NavigationMicaReapplyTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    backdrop_source = backdrop.read_text(encoding="utf-8")
    reapply_source = reapply.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 475
    for helper in (backdrop, reapply):
        assert helper.exists()
        assert len(helper.read_text(encoding="utf-8").splitlines()) < 80
    assert "NavigationMicaBackdropCommitTimer {" in source
    assert source.count("NavigationMicaReapplyTimer {") == 2
    assert "id: _micaBackdropCommitTimer" in source
    assert "id: _micaReapplyTimer" in source
    assert "id: _micaLateReapplyTimer" in source
    assert "required property var host" in backdrop_source
    assert "required property var host" in reapply_source
    assert "required property bool late" in reapply_source
    assert "host._micaBackdropReady = true" in backdrop_source
    assert "host._applyMicaEffect(" in reapply_source
    assert "Enums.window.micaReapplyDelayMs" in backdrop_source
    assert "Enums.window.micaLateReapplyDelayMs" in reapply_source
    assert "interval: Enums.window.micaReapplyDelayMs" not in source
    assert "interval: Enums.window.micaLateReapplyDelayMs" not in source
    assert "window._micaBackdropReady = true" not in source


def test_navigation_panel_keeps_background_layer_modularized():
    entry = _source("prismqml/PrismQML/navigation/NavigationPanelCore.qml")
    background = _source(
        "prismqml/PrismQML/navigation/_internal/NavigationPanelBackground.qml"
    )
    border = _source(
        "prismqml/PrismQML/navigation/_internal/NavigationPanelBorder.qml"
    )
    source = entry.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert 'import "_internal"' in source
    assert "NavigationPanelBackground {" in source
    assert "NavigationPanelBorder {" in source
    for helper in (background, border):
        assert helper.exists()
        helper_source = helper.read_text(encoding="utf-8")
        assert len(helper_source.splitlines()) < 300
        assert "required property var panel" in helper_source
        assert "readonly property var control: panel" in helper_source
    assert "z: -2" in background.read_text(encoding="utf-8")
    assert "property bool ticketPaperEnabled: true" in source
    assert (
        "visible: control.ticketPaperEnabled && Enums.isVintageTicket"
        in background.read_text(encoding="utf-8")
    )
    assert "id: bgCanvas" not in source
    assert "id: acrylicLayer" not in source
    assert "id: rightBorderCanvas" not in source
    assert "TicketPaper {" not in source


def test_navigation_panel_keeps_indicator_timers_modularized():
    entry = _source("prismqml/PrismQML/navigation/NavigationPanelCore.qml")
    tracker = _source(
        "prismqml/PrismQML/navigation/_internal/"
        "NavigationIndicatorTrackerTimer.qml"
    )
    scroll_stop = _source(
        "prismqml/PrismQML/navigation/_internal/"
        "NavigationIndicatorScrollStopTimer.qml"
    )
    init_timer = _source(
        "prismqml/PrismQML/navigation/_internal/"
        "NavigationIndicatorInitTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    tracker_source = tracker.read_text(encoding="utf-8")
    scroll_stop_source = scroll_stop.read_text(encoding="utf-8")
    init_source = init_timer.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    for helper in (tracker, scroll_stop, init_timer):
        assert helper.exists()
        assert len(helper.read_text(encoding="utf-8").splitlines()) < 80
    assert "NavigationIndicatorTrackerTimer {" in source
    assert "NavigationIndicatorScrollStopTimer {" in source
    assert "NavigationIndicatorInitTimer {" in source
    assert "id: indicatorTracker" in source
    assert "id: _scrollStopTimer" in source
    assert "id: _initTimer" in source
    assert source.count("host: control") == 2
    assert "indicator: navIndicator" in source
    assert "tracker: indicatorTracker" in source
    assert "required property var host" in tracker_source
    assert "required property var indicator" in tracker_source
    assert "required property var tracker" in scroll_stop_source
    assert "required property var host" in init_source
    assert "property bool _scrolling: false" in tracker_source
    assert "FrameAnimation {" in tracker_source
    assert "Enums.duration.tick" not in tracker_source
    assert "host._updateIndicatorPositionRealtime()" in tracker_source
    assert "tracker._scrolling = false" in scroll_stop_source
    assert "Enums.duration.fast" in scroll_stop_source
    assert "interval: 50" in init_source
    assert "host._initIndicatorPosition()" in init_source
    assert "\n    Timer {" not in source


def test_sidebars_share_one_scroll_fade_implementation():
    """三种侧边栏共用同一份渐隐实现, 且渐隐参数只来自 Enums。

    The fade must stay in NavigationScrollFade with tokens from Enums, so the
    hint cannot drift apart between the three sidebars.
    """
    fade = _source("prismqml/PrismQML/navigation/_internal/NavigationScrollFade.qml")
    assert fade.exists()
    fade_source = fade.read_text(encoding="utf-8")

    # 渐隐参数必须走 Enums, 不得硬编码。 Tokens only, no hardcoded numbers.
    assert "Enums.navigationFade.bandItems" in fade_source
    assert "Enums.navigationFade.minOpacity" in fade_source
    assert "Enums.navigationFade.maxOpacity" in fade_source
    # 用真实 opacity 而非遮罩着色器, 才能在 Mica/透明背景下可见。
    # Real opacity, not a mask shader, so the hint survives Mica backgrounds.
    assert "MultiEffect" not in fade_source
    assert "ShaderEffect" not in fade_source
    assert "layer.effect" not in fade_source
    # 依赖登记守卫必须留在共用实现里 The dependency guard stays shared here
    assert "fade.itemCount > 0 && fade.flickable.contentHeight > 0" in fade_source

    for relative in (
        "prismqml/PrismQML/navigation/NavigationBar.qml",
        "prismqml/PrismQML/navigation/ToggleNavigationBar.qml",
        "prismqml/PrismQML/navigation/NavigationView.qml",
    ):
        source = _source(relative).read_text(encoding="utf-8")
        assert "NavigationScrollFade {" in source, relative
        assert "property bool scrollFadeEnabled: true" in source, relative
        assert "active: control.scrollFadeEnabled" in source, relative
        # itemCount 必须绑定 Repeater, 否则绑定会锁死在 Repeater 尚空的首次求值。
        # Bind the Repeater or the binding latches on its empty first pass.
        assert "itemCount: topRep.count" in source, relative
        assert "opacity: scrollFade.opacityAt(y, height)" in source, relative
        # 指示器位于视口之外, 必须由选中项的渐隐驱动才能锁步。
        # The indicator is outside the viewport; drive it from the item's fade.
        assert "scrollFade.selectionOpacity(" in source, relative
        # 每个宿主都要有真实视口, 否则溢出项被裁且无法触达。
        # A real viewport per host, or overflow items are clipped and unreachable.
        assert "Flickable {" in source, relative
        # 视口可交互以支持触摸/拖拽, 但必须留一个可关的开关。
        # Interactive for touch and drag, but the switch must stay public.
        assert "interactive: control.dragScrollEnabled" in source, relative
        assert "property bool dragScrollEnabled: true" in source, relative
        # 实测委托的 MouseArea 不抢拖拽, 因此不得引入 pressDelay 白添点击延迟。
        # Measured: the delegates do not steal the drag, so no pressDelay may be
        # introduced — it would only cost every click a delay.
        # 只查真正的属性赋值 —— 整词匹配会连解释这条约定的注释一起命中。
        # Match the assignment only; a bare substring also hits the comment that
        # explains this very rule.
        assert not re.search(r"^\s*pressDelay\s*:", source, re.MULTILINE), relative
        assert "boundsBehavior: Flickable.StopAtBounds" in source, relative
        assert "clip: true" in source, relative
        assert "NavigationSmoothScroll {" in source, relative


def test_sidebars_share_one_scroll_rail_implementation():
    """三种侧边栏共用同一份浮层滚动轨, 且轨道绝不进入布局。

    The rail must stay an overlay: if it ever takes layout width it would
    squeeze the nav items, which is exactly what the user ruled out.
    """
    rail = _source("prismqml/PrismQML/navigation/_internal/NavigationScrollRail.qml")
    assert rail.exists()
    rail_source = rail.read_text(encoding="utf-8")

    # 轨道参数必须走 Enums, 不得硬编码。 Tokens only, no hardcoded numbers.
    assert "Enums.navigationRail.inset" in rail_source
    assert "Enums.navigationRail.thickness" in rail_source
    assert "Enums.navigationRail.idleOpacity" in rail_source
    assert "Enums.navigationRail.activeOpacity" in rail_source
    assert "Enums.navigationRail.revealDuration" in rail_source
    assert "Enums.navigationRail.hideDuration" in rail_source
    assert "Enums.navigationRail.idleDelay" in rail_source
    # 轨道复用既有 ScrollBar, 不另造一套滚动条。 Reuse ScrollBar, do not fork it.
    assert "ScrollBar {" in rail_source
    # 浮层锚在视口之上, 且不得声明 implicit 尺寸 —— 那会被父布局读取。
    # Anchored over the viewport, and no implicit size a parent layout could read.
    assert "anchors.right: rail.flickable.right" in rail_source
    assert "implicitWidth" not in rail_source
    assert "Layout." not in rail_source

    for relative in (
        "prismqml/PrismQML/navigation/NavigationBar.qml",
        "prismqml/PrismQML/navigation/ToggleNavigationBar.qml",
        "prismqml/PrismQML/navigation/NavigationView.qml",
    ):
        source = _source(relative).read_text(encoding="utf-8")
        assert "NavigationScrollRail {" in source, relative
        assert "property bool scrollRailEnabled: true" in source, relative
        assert "active: control.scrollRailEnabled" in source, relative
        assert "flickable: topFlickable" in source, relative
        # 悬停整个侧边栏才显形, 而非只悬停那条看不见的细线。
        # Reveal on hovering the sidebar, not the invisible hairline itself.
        assert "hostHovered: hostHover.hovered" in source, relative
        assert "HoverHandler {" in source, relative
        # 轨道必须与 Flickable 同级: 放进 Flickable 里会随内容滚走。同级即同缩进,
        # 嵌套会更深, 所以比对缩进能真正区分二者(仅比对文本先后则区分不了)。
        # Sibling of the Flickable; nested, the rail would scroll away with the
        # content. Siblings share indentation while a nested item is deeper, so
        # comparing indentation actually tells them apart — text order does not.
        rail_indent = _declaration_indent(source, "NavigationScrollRail {")
        flickable_indent = _declaration_indent(source, "Flickable {")
        assert rail_indent == flickable_indent, relative


def test_toggle_navigation_bar_keeps_indicator_timers_modularized():
    entry = _source("prismqml/PrismQML/navigation/ToggleNavigationBar.qml")
    tracker = _source(
        "prismqml/PrismQML/navigation/_internal/"
        "ToggleNavigationIndicatorTrackerTimer.qml"
    )
    scroll_stop = _source(
        "prismqml/PrismQML/navigation/_internal/"
        "NavigationIndicatorScrollStopTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    tracker_source = tracker.read_text(encoding="utf-8")
    scroll_stop_source = scroll_stop.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 370
    for helper in (tracker, scroll_stop):
        assert helper.exists()
        assert len(helper.read_text(encoding="utf-8").splitlines()) < 80
    assert "ToggleNavigationIndicatorTrackerTimer {" in source
    assert "NavigationIndicatorScrollStopTimer {" in source
    assert "id: _indicatorTracker" in source
    assert "id: _scrollStopTimer" in source
    assert "host: control" in source
    assert "tracker: _indicatorTracker" in source
    assert "required property var host" in tracker_source
    assert "property bool _scrolling: false" in tracker_source
    assert "FrameAnimation {" in tracker_source
    assert "Enums.duration.tick" not in tracker_source
    assert "host._updateIndicator(false)" in tracker_source
    assert "required property var tracker" in scroll_stop_source
    assert "Enums.duration.fast" in scroll_stop_source
    assert "tracker._scrolling = false" in scroll_stop_source
    assert "\n    Timer {" not in source


def test_button_core_keeps_behavior_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/buttons/Button/ButtonCore.qml"
    )
    logic = _source(
        "prismqml/PrismQML/controls/buttons/Button/_internal/ButtonLogic.js"
    )
    helper_paths = (
        (
            "prismqml/PrismQML/controls/buttons/Button/_internal/"
            "ButtonFeatureLoader.qml",
            "ButtonFeatureLoader",
        ),
        (
            "prismqml/PrismQML/controls/buttons/Button/_internal/"
            "ButtonInteraction.qml",
            "ButtonInteraction",
        ),
        (
            "prismqml/PrismQML/controls/buttons/Button/_internal/"
            "ButtonCountdown.qml",
            "ButtonCountdown",
        ),
        (
            "prismqml/PrismQML/controls/buttons/Button/_internal/"
            "ButtonSurface.qml",
            "ButtonSurface",
        ),
        (
            "prismqml/PrismQML/controls/buttons/Button/_internal/"
            "ButtonContentLayer.qml",
            "ButtonContentLayer",
        ),
    )
    source = entry.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert logic.exists()
    logic_source = logic.read_text(encoding="utf-8")
    assert len(logic_source.splitlines()) < 500
    assert ".pragma library" in logic_source
    assert "Enums" not in logic_source

    for relative_path, helper_type in helper_paths:
        helper = _source(relative_path)
        assert helper.exists()
        assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
        assert f"{helper_type} {{" in source

    assert 'import "_internal" as ButtonInternal' in source
    assert 'import "_internal/ButtonLogic.js" as ButtonLogic' in source
    assert "ButtonLogic.click(control, Enums)" in source
    assert "ButtonLogic.updateTargetColors(" in source
    assert "ButtonLogic.prewarmMenu(control, Enums," in source


def test_button_countdown_keeps_timer_component_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/buttons/Button/_internal/ButtonCountdown.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/buttons/Button/_internal/"
        "ButtonCountdownTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 80
    assert helper.exists()
    assert len(helper_source.splitlines()) < 80
    assert "Loader {" in source
    assert "sourceComponent: ButtonCountdownTimer {" in source
    assert "button: countdownLoader.button" in source
    assert "sourceComponent: Timer {" not in source
    assert "\n    Timer {" not in source
    assert helper_source.count("Timer {") == 1
    assert "\nTimer {" in helper_source
    assert "required property var button" in helper_source
    assert "interval: Enums.duration.countUp" in helper_source
    assert "repeat: true" in helper_source
    assert "running: button._countdownActive" in helper_source
    assert "button.countdownFinished()" in helper_source
    assert "countdownLoader" not in helper_source


def test_button_core_keeps_surface_visuals_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/buttons/Button/ButtonCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/buttons/Button/_internal/ButtonSurface.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 430
    assert helper.exists()
    assert len(helper_source.splitlines()) < 180
    assert 'import "_internal" as ButtonInternal' in source
    assert "ButtonInternal.ButtonSurface {" in source
    assert "required property var buttonControl" in helper_source
    for alias in (
        "background",
        "border",
        "bgColorAnimation",
        "borderColorAnimation",
    ):
        assert f"property alias {alias}:" in helper_source
    assert "readonly property real animatedPressShift:" in helper_source
    assert "readonly property var pressTransform:" in helper_source
    assert "RectangularShadow {" in helper_source
    assert "NeumorphicShadow {" in helper_source
    assert "sourceComponent: ButtonNeoShadow" in helper_source
    assert "ColorAnimation {" in helper_source
    assert "RectangularShadow {" not in source
    assert "NeumorphicShadow {" not in source
    assert "sourceComponent: ButtonNeoShadow" not in source
    assert "ColorAnimation {" not in source


def test_button_core_keeps_content_layer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/buttons/Button/ButtonCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/buttons/Button/_internal/ButtonContentLayer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 370
    assert helper.exists()
    assert len(helper_source.splitlines()) < 150
    assert "ButtonInternal.ButtonContentLayer {" in source
    assert "required property var buttonControl" in helper_source
    assert "required property var pressTransform" in helper_source
    assert "default property alias contentData: customContentContainer.data" in helper_source
    assert "property alias customContentContainer: customContentContainer" in helper_source
    assert "property alias contentLoader: contentLoader" in helper_source
    assert "ButtonContent {" in helper_source
    assert "Item {\n        id: customContentContainer" not in source
    assert "Loader {\n        id: contentLoader" not in source
    assert "ButtonContent {" not in source


def test_button_dropdown_keeps_surface_visuals_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/buttons/Button/ButtonDropdown.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/buttons/Button/_internal/"
        "ButtonDropdownSurface.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 350
    assert helper.exists()
    assert len(helper_source.splitlines()) < 160
    assert 'import "_internal" as ButtonInternal' in source
    assert "ButtonInternal.ButtonDropdownSurface {" in source
    assert "required property var dropdownControl" in helper_source
    for state in ("mainHovered", "mainPressed", "dropHovered", "dropPressed"):
        assert f"readonly property bool {state}:" in helper_source
        assert f"dropdownSurface.{state}" in source
    for marker in (
        "id: splitMainArea",
        "id: splitDropArea",
        "id: splitMainMouse",
        "id: splitDropMouse",
        "id: menuArrow",
    ):
        assert marker not in source


def test_button_dropdown_keeps_geometry_prewarm_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/buttons/Button/ButtonDropdown.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/buttons/Button/_internal/"
        "ButtonDropdownPrewarmTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 350
    assert helper.exists()
    assert len(helper_source.splitlines()) < 80
    assert helper_source.count("Timer {") == 1
    assert "\nTimer {" in helper_source
    assert "required property var dropdownControl" in helper_source
    assert "interval: 0" in helper_source
    assert "onTriggered: dropdownControl._prewarmMenuGeometry()" in helper_source
    assert "ButtonInternal.ButtonDropdownPrewarmTimer {" in source
    assert "id: geometryPrewarmTimer" in source
    assert "dropdownControl: dropdownFeature" in source
    assert "\n    Timer {" not in source
    assert "onTriggered: dropdownFeature._prewarmMenuGeometry()" not in source


def test_popup_window_core_keeps_animation_logic_modularized():
    _assert_modularized(
        "prismqml/PrismQML/controls/utils/PopupWindowCore.qml",
        "prismqml/PrismQML/controls/utils/_internal/PopupAnimations.qml",
        "PopupAnimations",
    )


def test_popup_window_core_keeps_positioning_and_prewarm_modularized():
    entry = _source("prismqml/PrismQML/controls/utils/PopupWindowCore.qml")
    helpers = (
        _source(
            "prismqml/PrismQML/controls/utils/_internal/PopupPositioning.js"
        ),
        _source(
            "prismqml/PrismQML/controls/utils/_internal/PopupPrewarm.js"
        ),
    )
    source = entry.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    for helper in helpers:
        assert helper.exists()
        helper_source = helper.read_text(encoding="utf-8")
        assert len(helper_source.splitlines()) < 500
        assert ".pragma library" in helper_source
        assert "Enums" not in helper_source

    assert (
        'import "_internal/PopupPositioning.js" as PopupPositioning'
        in source
    )
    assert 'import "_internal/PopupPrewarm.js" as PopupPrewarm' in source
    assert "PopupPositioning.calcControlsPopupPosition(" in source
    assert "PopupPositioning.applyTrackedPosition(" in source
    assert "PopupPrewarm.doPrewarm(" in source


def test_popup_window_core_keeps_lifecycle_timers_modularized():
    entry = _source("prismqml/PrismQML/controls/utils/PopupWindowCore.qml")
    prewarm = _source(
        "prismqml/PrismQML/controls/utils/_internal/PopupPrewarmTimer.qml"
    )
    lifecycle = _source(
        "prismqml/PrismQML/controls/utils/_internal/PopupLifecycleTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    prewarm_source = prewarm.read_text(encoding="utf-8")
    lifecycle_source = lifecycle.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    for helper in (prewarm, lifecycle):
        assert helper.exists()
        assert len(helper.read_text(encoding="utf-8").splitlines()) < 80
    assert "PopupPrewarmTimer {" in source
    assert "PopupLifecycleTimer {" in source
    assert "id: prewarmTimer" in source
    assert "id: lifecycleTimer" in source
    assert "host: control" in source
    assert "readonly property alias _lifecycleTimer: lifecycleTimer" in source
    assert "required property var host" in prewarm_source
    assert "required property var host" in lifecycle_source
    assert "interval: 0" in prewarm_source
    assert "host._doPrewarm()" in prewarm_source
    assert "Enums.popupMetrics.showAnimDelayMs" in lifecycle_source
    assert "PopupLifecycle.onTimer(host)" in lifecycle_source
    assert "\n    Timer {" not in source


def test_popup_position_tracker_keeps_update_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/utils/_internal/PopupPositionTracker.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/utils/_internal/PopupPositionUpdateTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 140
    assert helper.exists()
    assert len(helper_source.splitlines()) < 60
    assert 'import "." as PopupInternal' in source
    assert "PopupInternal.PopupPositionUpdateTimer {" in source
    assert "id: updateTimer" in source
    assert "host: tracker" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "popupPositionUpdateTimer"' in helper_source
    assert "interval: 0" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: host._updatePosition()" in helper_source
    assert "onTriggered: tracker._updatePosition()" not in source


def test_viewport_culling_keeps_evaluation_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/utils/ViewportCulling.qml")
    helper = _source(
        "prismqml/PrismQML/controls/utils/_internal/"
        "ViewportCullingEvaluationTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 120
    assert helper.exists()
    assert len(helper_source.splitlines()) < 60
    assert 'import "_internal" as UtilsInternal' in source
    assert "UtilsInternal.ViewportCullingEvaluationTimer {" in source
    assert "id: evaluationTimer" in source
    assert "host: root" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "viewportCullingTimer"' in helper_source
    assert "interval: 150" in helper_source
    assert "running: host._flickable !== null && host._hostWindowExposed" in helper_source
    assert "repeat: true" in helper_source
    assert "triggeredOnStart: true" in helper_source
    assert "onTriggered: host._updateVisibility()" in helper_source
    assert "onTriggered: root._updateVisibility()" not in source


def test_list_widget_keeps_data_and_selection_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/List/ListWidget.qml"
    )
    controller = _source(
        "prismqml/PrismQML/controls/data/List/_internal/ListDataController.js"
    )
    source = entry.read_text(encoding="utf-8")
    controller_source = controller.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert controller.exists()
    assert len(controller_source.splitlines()) < 500
    assert ".pragma library" in controller_source
    assert (
        'import "_internal/ListDataController.js" as ListDataController'
        in source
    )

    delegated_methods = (
        "addItem", "addItems", "insertItem", "insertItems", "takeItem",
        "item", "row", "currentItem", "setCurrentItem", "currentRow",
        "setCurrentRow", "selectedItems", "clearSelection", "selectAll",
        "setSelectionMode", "findItems", "sortItems", "clear",
        "setItemText", "setItemIcon", "setItemData", "itemData",
        "setItemCheckState", "itemCheckState", "setItemSelected",
        "handleItemClick", "updateSelectedRows",
    )
    for method in delegated_methods:
        assert f"function {method}(" in controller_source
        assert f"ListDataController.{method}(" in source


def test_stacked_widget_keeps_source_pages_modularized():
    _assert_modularized(
        "prismqml/PrismQML/controls/navigation/StackedWidget.qml",
        "prismqml/PrismQML/controls/navigation/_internal/StackedSourcePages.qml",
        "StackedSourcePages",
    )


def test_stacked_widget_keeps_switching_orchestration_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/StackedWidget.qml")
    source = entry.read_text(encoding="utf-8")
    assert len(source.splitlines()) < 500

    for relative_path, helper_type in (
        (
            "prismqml/PrismQML/controls/navigation/_internal/StackedLazyController.qml",
            "StackedLazyController",
        ),
        (
            "prismqml/PrismQML/controls/navigation/_internal/StackedVisibilityController.qml",
            "StackedVisibilityController",
        ),
    ):
        helper = _source(relative_path)
        assert helper.exists()
        assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
        assert f"{helper_type} {{" in source

    assert "lazyController.preloadLazyHelperWhenReady" in source
    assert "visibilityController.doAnimation" in source


def test_stacked_widget_keeps_direct_pages_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/navigation/StackedWidget.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/StackedDirectPages.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 480
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert "StackedDirectPages {" in source
    assert "property Item containerItem: directPages" in source
    assert "required property Item host" in helper_source
    assert 'objectName: "stackLayout"' in helper_source
    assert "host._displayIndex" in helper_source
    assert "child.width = Qt.binding" in helper_source
    assert "child.height = Qt.binding" in helper_source
    for marker in (
        "\n        id: stackLayout\n",
        "stackLayout.children",
        "child.width = Qt.binding",
        "child.height = Qt.binding",
    ):
        assert marker not in source


def test_stacked_widget_keeps_lazy_helper_loader_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/navigation/StackedWidget.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/"
        "StackedLazyHelperLoader.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 470
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert "StackedLazyHelperLoader {" in source
    assert helper_source.startswith("// Copyright 2026 aki-riko")
    assert "Loader {" in helper_source
    assert "required property Item host" in helper_source
    assert "host._asynchronousPageLoaderEnabled" in helper_source
    assert "host._configureLazyHelper(item)" in helper_source
    assert "host._flushPendingLazySwitch()" in helper_source
    for handler in ("onActiveChanged:", "onStatusChanged:", "onLoaded:"):
        assert helper_source.count(handler) == 1
        assert handler not in source
    assert "id: lazyHelperLoader" in source
    assert "host: control" in source
    assert "lazyHelperLoader.setSource(Qt.resolvedUrl" in source
    assert "lazyHelperLoader: lazyHelperLoader" in source
    assert "StackedLazyHelperLoader {\n        id: lazyHelperLoader\n        host: control\n" in source


def test_tab_widget_keeps_content_pages_modularized():
    _assert_modularized(
        "prismqml/PrismQML/controls/navigation/TabWidget.qml",
        "prismqml/PrismQML/controls/navigation/_internal/TabContentPages.qml",
        "TabContentPages",
    )


def test_tab_widget_keeps_tab_delegate_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/TabWidget.qml")
    helper = _source("prismqml/PrismQML/controls/navigation/_internal/TabItem.qml")

    assert len(entry.read_text(encoding="utf-8").splitlines()) < 500
    assert helper.exists()
    assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
    assert "TabItem {" in entry.read_text(encoding="utf-8")


def test_tab_widget_keeps_edge_auto_scroll_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/TabWidget.qml")
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/TabEdgeAutoScroll.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 450
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert "TabEdgeAutoScroll {" in source
    assert "FrameAnimation {" in helper_source
    assert "required property Item host" in helper_source
    assert "required property Flickable tabFlickable" in helper_source
    assert "host._dragging" in helper_source
    assert "host._dragPointerRowX" in helper_source
    assert "frameTime" in helper_source
    assert "onTriggered:" in helper_source
    assert "var edgeMargin = 40" not in source
    assert "var step = 480 * frameTime" not in source
    assert "id: _edgeAutoScrollTimer" in source
    assert "host: control" in source
    assert "tabFlickable: tabFlickable" in source


def test_tab_widget_keeps_indicator_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/TabWidget.qml")
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/TabIndicator.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 300
    assert helper.exists()
    assert len(helper_source.splitlines()) < 250
    assert "TabIndicator {" in source
    assert "Item {" in helper_source
    for required_property in (
        "required property Item host",
        "required property Item tabBar",
        "required property Flickable tabFlickable",
        "required property var tabRepeater",
        "required property Item tabRow",
    ):
        assert required_property in helper_source
    for binding in (
        "host: control",
        "tabBar: tabBarBg",
        "tabFlickable: tabFlickable",
        "tabRepeater: tabRepeater",
        "tabRow: tabRow",
    ):
        assert binding in source
    assert "function _scheduleSync(animate)" in helper_source
    assert "function syncIndicator(animate)" in helper_source
    assert "SlidingIndicatorAnimation {" in helper_source
    assert "RectangularShadow {" in helper_source
    assert "NeumorphicShadow {" in helper_source
    assert "NeoShadow {" in helper_source
    assert "id: slidingIndicator" in source
    for marker in (
        "property int _currentTabKey:",
        "function _scheduleSync(animate)",
        "SlidingIndicatorAnimation {",
        "id: indicatorBg",
    ):
        assert marker not in source


def test_bar_chart_keeps_single_series_delegate_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/BarChartContent.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/BarChartBar.qml"
    )

    assert len(entry.read_text(encoding="utf-8").splitlines()) < 500
    assert helper.exists()
    assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
    assert entry.read_text(encoding="utf-8").count("BarChartBar {") == 2


def test_notification_manager_keeps_overlay_lifecycle_internal():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Notification/NotificationManager.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Notification/_internal/NotificationOverlayLifecycle.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 430
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert "NotificationOverlayLifecycle {" in source
    assert "required property var stackManager" in helper_source
    for marker in (
        "overlayComponent.createObject(null",
        "notification.closed.connect(function() { overlay.hide() })",
        "notification.destroy()",
        "stackManager.addToDesktopStack(overlay, position)",
        "stackManager.addToOutsideStack(overlay, position)",
    ):
        assert marker in helper_source
        assert marker not in source


def test_notification_manager_keeps_item_lifecycle_internal():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Notification/NotificationManager.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Notification/_internal/NotificationItemLifecycle.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 410
    assert helper.exists()
    assert len(helper_source.splitlines()) < 80
    assert "NotificationItemLifecycle {" in source
    assert "required property var stackManager" in helper_source
    for marker in (
        "component.createObject(parentItem, properties)",
        "stackManager.addToStack(item, position)",
        "stackManager.setPosition(item, parentItem, position)",
        "stackManager.removeFromStack(item, position)",
        "item.destroy()",
    ):
        assert marker in helper_source
        assert marker not in source


def test_line_chart_content_keeps_canvas_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/LineChartContent.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/LineChartCanvas.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 300
    assert "LineChartCanvas {" in source
    assert "lineControl: root" in source
    assert "required property var lineControl" in helper_source
    assert "function paintSingleSeries(" in helper_source
    assert "function paintMultiSeries(" in helper_source
    assert "\n    Canvas {" not in source
    assert "function paintSingleSeries(" not in source
    assert "function paintMultiSeries(" not in source


def test_boxplot_chart_content_keeps_canvas_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/BoxplotChartContent.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/BoxplotChartCanvas.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 250
    assert helper.exists()
    assert len(helper_source.splitlines()) < 350
    assert "BoxplotChartCanvas {" in source
    assert "boxplotControl: root" in source
    assert "required property var boxplotControl" in helper_source
    assert "readonly property var control: boxplotControl" in helper_source
    assert "function paintVertical(" in helper_source
    assert "function paintHorizontal(" in helper_source
    assert "Geometry.paintRange(" in helper_source
    assert "\n    Canvas {" not in source
    assert "function paintVertical(" not in source
    assert "function paintHorizontal(" not in source


def test_drawer_keeps_outside_window_modularized():
    entry = _source("prismqml/PrismQML/controls/containers/Drawer/Drawer.qml")
    helper = _source(
        "prismqml/PrismQML/controls/containers/Drawer/_internal/"
        "DrawerOutsideWindow.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 150
    assert 'import "_internal" as DrawerInternal' in source
    assert "DrawerInternal.DrawerOutsideWindow {" in source
    assert "property var drawerControl: control" in source
    assert "drawerControl: outsideDrawerWindowLoader.drawerControl" in source
    assert "required property var drawerControl" in helper_source
    assert "readonly property alias panel: outsideDrawerPanel" in helper_source
    assert "readonly property var control: drawerControl" in helper_source
    assert 'objectName: "outsideDrawerWindow"' in helper_source
    for token in (
        'objectName: "outsideDrawerViewport"',
        'objectName: "outsideDrawerPanel"',
        "transientParent: null",
        "\n            Window {",
    ):
        assert token not in source

    surface = _source(
        "prismqml/PrismQML/controls/containers/Drawer/_internal/DrawerSurface.qml"
    )
    surface_source = surface.read_text(encoding="utf-8")
    assert len(source.splitlines()) < 370
    assert surface.exists()
    assert len(surface_source.splitlines()) < 220
    assert "DrawerInternal.DrawerSurface {" in source
    assert "required property var drawerControl" in surface_source
    assert "default property alias content: contentItem.data" in surface_source
    assert "readonly property alias panel: drawer" in surface_source
    for token in (
        "RectangularShadow {",
        "NeumorphicShadow {",
        "\n        id: drawer\n",
        "\n        id: contentItem\n",
    ):
        assert token not in source


def test_smooth_scroll_helper_keeps_wheel_input_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/SmoothScrollHelper.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/_internal/"
        "SmoothScrollWheelArea.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert 'import "_internal" as ScrollBarInternal' in source
    assert "ScrollBarInternal.SmoothScrollWheelArea {" in source
    assert "scrollHelper: helper" in source
    assert "required property var scrollHelper" in helper_source
    assert "parent: scrollHelper.target" in helper_source
    assert "anchors.fill: parent" in helper_source
    assert "onWheel:" in helper_source
    assert "MouseArea {" not in source
    assert "onWheel:" not in source


def test_smooth_scroll_helper_keeps_frame_driver_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/SmoothScrollHelper.qml"
    )
    driver = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/_internal/"
        "SmoothScrollFrameDriver.qml"
    )
    source = entry.read_text(encoding="utf-8")
    driver_source = driver.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert driver.exists()
    assert len(driver_source.splitlines()) < 120
    assert source.count("ScrollBarInternal.SmoothScrollFrameDriver {") == 2
    assert "Behavior on _smoothY" not in source
    assert "Behavior on _smoothX" not in source
    assert "NumberAnimation {" not in source
    assert "Connections {" in driver_source
    assert "required property var scrollHelper" in driver_source
    assert "required property bool verticalAxis" in driver_source
    assert "function onFrameSwapped()" in driver_source
    assert "target.update()" in driver_source
    assert "WindowHelper.easingValueForProgress" in driver_source
    assert "Easing.valueForProgress" not in driver_source
    assert "AnimationController {" not in driver_source
    assert "FrameAnimation {" not in driver_source
    assert "Timer {" not in driver_source


def test_smooth_scroll_helper_keeps_bounce_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/SmoothScrollHelper.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/_internal/"
        "SmoothScrollBounceTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 80
    assert "ScrollBarInternal.SmoothScrollBounceTimer {" in source
    assert "scrollHelper: helper" in source
    assert "required property var scrollHelper" in helper_source
    assert "required property bool verticalAxis" in helper_source
    assert "scrollHelper._releaseBounceTimer(verticalAxis, bounceTimer)" in helper_source
    assert "\n        Timer {\n            id: bounceTimer\n" not in source


def test_smooth_scroll_helper_keeps_bounds_reconcile_timers_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/SmoothScrollHelper.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/_internal/"
        "SmoothScrollBoundsReconcileTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 60
    assert "ScrollBarInternal.SmoothScrollBoundsReconcileTimer {" in source
    assert source.count("SmoothScrollBoundsReconcileTimer {") == 2
    assert "objectName: \"smoothScrollVerticalReconcileTimer\"" in source
    assert "objectName: \"smoothScrollHorizontalReconcileTimer\"" in source
    assert "scrollHelper: helper" in source
    assert "verticalAxis: true" in source
    assert "verticalAxis: false" in source
    assert "required property var scrollHelper" in helper_source
    assert "required property bool verticalAxis" in helper_source
    assert 'objectName: verticalAxis' in helper_source
    assert "interval: Enums.duration.instant" in helper_source
    assert "repeat: false" in helper_source
    assert "scrollHelper._reconcileVerticalBounds()" in helper_source
    assert "scrollHelper._reconcileHorizontalBounds()" in helper_source
    assert "\n    Timer {\n        id: verticalReconcileTimer" not in source
    assert "\n    Timer {\n        id: horizontalReconcileTimer" not in source


def test_flow_layout_keeps_append_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/containers/Layout/FlowLayout.qml")
    helper = _source(
        "prismqml/PrismQML/controls/containers/Layout/_internal/"
        "FlowLayoutAppendTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 400
    assert helper.exists()
    assert len(helper_source.splitlines()) < 50
    assert 'import "_internal" as LayoutInternal' in source
    assert "LayoutInternal.FlowLayoutAppendTimer {" in source
    assert "id: appendLayoutTimer" in source
    assert "host: control" in source
    assert "required property var host" in helper_source
    assert 'objectName: "flowLayoutAppendTimer"' in helper_source
    assert "interval: 0" in helper_source
    assert "repeat: false" in helper_source
    assert "host._appendLayoutPending = false" in helper_source
    assert "host._appendDefaultItems()" in helper_source
    assert "\n    Timer {\n        id: appendLayoutTimer" not in source


def test_flow_layout_keeps_layout_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/containers/Layout/FlowLayout.qml")
    helper = _source(
        "prismqml/PrismQML/controls/containers/Layout/_internal/"
        "FlowLayoutLayoutTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 400
    assert helper.exists()
    assert len(helper_source.splitlines()) < 40
    assert "LayoutInternal.FlowLayoutLayoutTimer {" in source
    assert "id: layoutTimer" in source
    assert "host: control" in source
    assert "required property var host" in helper_source
    assert 'objectName: "flowLayoutLayoutTimer"' in helper_source
    assert "interval: 0" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: host._performLayout()" in helper_source
    assert "\n    Timer {\n        id: layoutTimer" not in source


def test_constants_keeps_theme_colors_modularized():
    entry = _source("prismqml/PrismQML/PrismEnums/Constants.qml")
    helper = _source(
        "prismqml/PrismQML/PrismEnums/_internal/ConstantsThemeColors.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 120
    assert 'import "_internal" as ConstantsInternal' in source
    assert (
        "readonly property QtObject themeColors: "
        "ConstantsInternal.ConstantsThemeColors {}"
    ) in source
    assert "readonly property QtObject themeColors: QtObject {" not in source
    assert "readonly property color backgroundDark" in helper_source
    assert "readonly property color accentForeground" in helper_source
    assert "readonly property color tabSelectedLight" in helper_source
    assert "required property bool isDark" not in helper_source


def test_metrics_keeps_shadow_logic_modularized():
    entry = _source("prismqml/PrismQML/PrismEnums/Metrics.qml")
    helper = _source(
        "prismqml/PrismQML/PrismEnums/_internal/MetricsShadow.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 900
    assert helper.exists()
    assert len(helper_source.splitlines()) < 150
    assert 'import "_internal" as MetricsInternal' in source
    assert "readonly property QtObject shadow: MetricsInternal.MetricsShadow {" in source
    assert "isDark: root.isDark" in source
    assert "isTicket: root.isTicket" in source
    assert "readonly property QtObject shadow: QtObject {" not in source
    assert "required property bool isDark" in helper_source
    assert "required property bool isTicket" in helper_source
    for level in (2, 4, 8, 16, 28):
        assert f"readonly property QtObject level{level}: QtObject {{" in helper_source
        assert f"function applyLevel{level}(target)" in helper_source


def test_combo_box_core_keeps_visual_content_modularized():
    entry = _source("prismqml/PrismQML/controls/inputs/ComboBox/ComboBoxCore.qml")
    helper = _source(
        "prismqml/PrismQML/controls/inputs/ComboBox/_internal/ComboBoxCoreContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 300
    assert helper.exists()
    assert len(helper_source.splitlines()) < 350
    assert "ComboBoxCoreContent {" in source
    assert "required property var comboControl" in helper_source
    for alias in (
        "editableInput",
        "mouseArea",
        "editableClickArea",
        "comboTextMeasureLoader",
        "popup",
    ):
        assert f"property alias {alias}:" in helper_source
    assert "property alias _popup: comboContent.popup" in source
    assert "layer.enabled: true" in helper_source
    assert "PopupWindowCore {" in helper_source
    assert "RectangularShadow {" in helper_source
    assert "PopupWindowCore {" not in source
    assert "layer.enabled: true" not in source


def test_combo_box_multi_tree_keeps_visual_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/ComboBox/ComboBoxMultiTree.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/ComboBox/_internal/ComboBoxMultiTreeContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 400
    assert helper.exists()
    assert len(helper_source.splitlines()) < 220
    assert 'import "_internal"' in source
    assert "ComboBoxMultiTreeContent {" in source
    assert "required property var comboControl" in helper_source
    assert "property alias _flatListModel: multiTreeContent.flatListModel" in source
    assert "property alias tokenFlickable: multiTreeContent.tokenFlickable" in source
    assert "property alias flatListModel: internalFlatListModel" in helper_source
    assert "property alias tokenFlickable: tokenFlickable" in helper_source
    assert "property alias popupContent: treePopupContent" in helper_source
    for visual_type in ("PopupSearchBox", "TreeMenuDelegate", "MultiSelectToken"):
        assert f"{visual_type} {{" in helper_source
        assert f"{visual_type} {{" not in source
    assert "ListModel {" in helper_source
    assert "Flickable {" in helper_source
    assert "popupContent: multiTreeContent.popupContent" in source


def test_xy_chart_core_keeps_axes_visuals_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/XYChartCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/XYChartAxes.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 350
    assert helper.exists()
    assert len(helper_source.splitlines()) < 350
    assert "XYChartAxes {" in source
    assert "chartControl: root" in source
    assert "required property var chartControl" in helper_source
    assert "required property var axisFontMetrics" in helper_source
    assert "readonly property Item chartArea: axesLayer.chartArea" in source
    assert "readonly property Item chartArea: chartAreaItem" in helper_source
    assert "readonly property var control: chartControl" in helper_source
    for token in (
        "id: gridLines",
        "id: horizontalYAxisLabels",
        "id: xAxisLabels",
        "id: scatterXAxisLabels",
        "HoverBehavior on color",
        'objectName: "chartXAxisViewport"',
    ):
        assert token not in source


def test_chart_view_keeps_render_layer_modularized():
    entry = _source("prismqml/PrismQML/controls/data/Chart/ChartView.qml")
    helper = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/ChartRenderLayer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 500
    assert "ChartRenderLayer {" in source
    assert "required property var chartControl" in helper_source
    assert "renderLayer.chart" not in helper_source
    for loader_name in (
        "xyChartBaseLoader", "barContentLoader", "lineContentLoader",
        "scatterContentLoader",
    ):
        assert f"property alias {loader_name}: {loader_name}" in helper_source
        assert f'objectName: "{loader_name}"' in helper_source
    for property_name, loader_name in (
        ("_xyChartBase", "xyChartBaseLoader"),
        ("_barContent", "barContentLoader"),
        ("_lineContent", "lineContentLoader"),
        ("_scatterContent", "scatterContentLoader"),
    ):
        assert (
            f"readonly property var {property_name}: "
            f"renderLayer.{loader_name}.item"
        ) in source


def test_settings_card_keeps_render_layer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/settings/SettingsCard/SettingsCard.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/settings/SettingsCard/_internal/"
        "SettingsCardRenderLayer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 500
    assert 'import "_internal"' in source
    assert "SettingsCardRenderLayer {" in source
    assert "required property var cardControl" in helper_source
    assert "property alias cardLoader: cardLoader" in helper_source
    assert "readonly property var control: cardControl" in helper_source
    assert "Component {" not in source
    assert "FolderDialog {" not in source


def test_chat_message_list_keeps_slot_delegate_modularized():
    entry = _source("prismqml/PrismQML/controls/chat/ChatMessageList.qml")
    helper = _source(
        "prismqml/PrismQML/controls/chat/_internal/ChatMessageSlot.qml"
    )
    viewport = _source(
        "prismqml/PrismQML/controls/chat/_internal/ChatMessageViewport.qml"
    )

    assert len(entry.read_text(encoding="utf-8").splitlines()) < 500
    assert helper.exists()
    assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
    assert "ChatMessageSlot {" in viewport.read_text(encoding="utf-8")


def test_chat_message_slot_keeps_measurement_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/chat/_internal/ChatMessageSlot.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/chat/_internal/"
        "ChatMessageSlotMeasurementTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 130
    assert helper.exists()
    assert len(helper_source.splitlines()) < 70
    assert 'import "." as ChatInternal' in source
    assert "ChatInternal.ChatMessageSlotMeasurementTimer {" in source
    assert "id: slotMeasurementTimer" in source
    assert "targetSlot: slot" in source
    assert "host: slot.host" in source
    assert "\n    Timer {" not in source
    assert "required property var targetSlot" in helper_source
    assert "required property var host" in helper_source
    assert 'objectName: "chatMessageSlotMeasurementTimer"' in helper_source
    assert "interval: 0" in helper_source
    assert "repeat: false" in helper_source
    assert "host._cacheSlotHeight(targetSlot, targetSlot.item.implicitHeight)" in helper_source
    assert "host._cacheSlotHeight(slot, slot.item.implicitHeight)" not in source


def test_code_block_keeps_copy_feedback_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/chat/CodeBlock.qml")
    helper = _source(
        "prismqml/PrismQML/controls/chat/_internal/"
        "CodeBlockCopyFeedbackTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 180
    assert helper.exists()
    assert len(helper_source.splitlines()) < 60
    assert 'import "_internal" as ChatInternal' in source
    assert "ChatInternal.CodeBlockCopyFeedbackTimer {" in source
    assert "id: copiedTimer" in source
    assert "host: copyBtn" in source
    assert "required property var host" in helper_source
    assert 'objectName: "codeBlockCopyFeedbackTimer"' in helper_source
    assert "interval: Enums.duration.copyFeedback" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: host._copied = false" in helper_source
    assert "onTriggered: copyBtn._copied = false" not in source
    assert "\n            Timer {" not in source


def test_chat_message_list_keeps_scroll_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/chat/ChatMessageList.qml")
    helper = _source(
        "prismqml/PrismQML/controls/chat/_internal/"
        "ChatMessageListScrollToBottomTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 400
    assert helper.exists()
    assert len(helper_source.splitlines()) < 60
    assert 'import "_internal" as ChatInternal' in source
    assert "ChatInternal.ChatMessageListScrollToBottomTimer {" in source
    assert "id: scrollToBottomTimer" in source
    assert "host: control" in source
    assert source.count("\n    Timer {") == 0
    assert "required property var host" in helper_source
    assert 'objectName: "chatMessageListScrollToBottomTimer"' in helper_source
    assert "interval: 0" in helper_source
    assert "repeat: false" in helper_source
    assert "host._scrollPending = false" in helper_source
    assert "if (host._followBottom) host._scrollToBottom()" in helper_source
    assert "control._scrollPending = false" not in source
    assert "if (control._followBottom) control._scrollToBottom()" not in source


def test_chat_message_list_keeps_slot_layout_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/chat/ChatMessageList.qml")
    helper = _source(
        "prismqml/PrismQML/controls/chat/_internal/"
        "ChatMessageListSlotLayoutTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 350
    assert helper.exists()
    assert len(helper_source.splitlines()) < 90
    assert 'import "_internal" as ChatInternal' in source
    assert "ChatInternal.ChatMessageListSlotLayoutTimer {" in source
    assert "id: slotLayoutTimer" in source
    assert "host: control" in source
    assert source.count("\n    Timer {") == 0
    assert "required property var host" in helper_source
    assert 'objectName: "chatMessageListSlotLayoutTimer"' in helper_source
    assert "interval: 0" in helper_source
    assert "repeat: false" in helper_source
    for marker in (
        "host._layoutPending = false",
        "host.messageRepeater.itemAt",
        "host.messageColumn.height = nextY",
        "host._scheduleLoadRangeUpdate()",
        "host._scheduleScrollToBottom()",
        "host._setContentY(host.messageViewport.contentY + anchorDelta, false)",
    ):
        assert marker in helper_source
    assert "control._layoutPending = false" not in source
    assert "control.messageColumn.height = nextY" not in source


def test_chat_message_list_keeps_load_range_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/chat/ChatMessageList.qml")
    helper = _source(
        "prismqml/PrismQML/controls/chat/_internal/"
        "ChatMessageListLoadRangeTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 350
    assert helper.exists()
    assert len(helper_source.splitlines()) < 70
    assert 'import "_internal" as ChatInternal' in source
    assert "ChatInternal.ChatMessageListLoadRangeTimer {" in source
    assert "id: loadRangeTimer" in source
    assert "host: control" in source
    assert "required property var host" in helper_source
    assert 'objectName: "chatMessageListLoadRangeTimer"' in helper_source
    assert "interval: 0" in helper_source
    assert "repeat: false" in helper_source
    for marker in (
        "host._rangeUpdatePending = false",
        "host.messageRepeater.itemAt",
        "host._applyLoadRange(-1, -1)",
        "host._scheduleSlotLayout(0)",
        "host._findFirstLoadIndex(topY)",
        "host._findLastLoadIndex(bottomY)",
        "host._applyLoadRange(firstIndex, lastIndex)",
    ):
        assert marker in helper_source
    assert "control._rangeUpdatePending = false" not in source
    assert "control._applyLoadRange(firstIndex, lastIndex)" not in source


def test_chat_message_list_keeps_viewport_content_modularized():
    entry = _source("prismqml/PrismQML/controls/chat/ChatMessageList.qml")
    helper = _source(
        "prismqml/PrismQML/controls/chat/_internal/ChatMessageViewport.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 400
    assert helper.exists()
    assert len(helper_source.splitlines()) < 120
    assert 'import "_internal" as ChatInternal' in source
    assert "ChatInternal.ChatMessageViewport {" in source
    assert "required property var chatControl" in helper_source
    assert "required property var messageModel" in helper_source
    for alias in ("viewport", "contentColumn", "repeater"):
        assert f"property alias {alias}:" in helper_source
    for alias in ("messageViewport", "messageColumn", "messageRepeater"):
        assert f"property alias {alias}: messageContent." in source
    for marker in (
        "id: messageViewport",
        "id: messageColumn",
        "id: messageRepeater",
        "ChatMessageSlot {",
    ):
        assert marker not in source


def test_tip_popup_keeps_main_window_surface_modularized():
    entry = _source("prismqml/PrismQML/controls/feedback/Tooltip/TipPopup.qml")
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Tooltip/_internal/TipPopupWindow.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 370
    assert helper.exists()
    assert len(helper_source.splitlines()) < 180
    assert 'import "_internal" as TooltipInternal' in source
    assert "TooltipInternal.TipPopupWindow {" in source
    assert "required property var popupControl" in helper_source
    assert "required property var positionHelper" in helper_source
    assert 'objectName: "tipPopupSurface"' in helper_source
    assert "\n                id: popupWindow\n" not in source
    for marker in (
        'objectName: "tipPopupSurface"',
        'objectName: "tipPrimaryActionButton"',
        'objectName: "tipSecondaryActionButton"',
    ):
        assert marker not in source


def test_tip_popup_keeps_auto_close_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/feedback/Tooltip/TipPopup.qml")
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Tooltip/_internal/"
        "TipPopupAutoCloseTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 370
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "_internal" as TooltipInternal' in source
    assert "TooltipInternal.TipPopupAutoCloseTimer {" in source
    assert "id: autoCloseTimer" in source
    assert "host: control" in source
    assert "autoCloseTimer.stop()" in source
    assert "autoCloseTimer.start()" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "tipPopupAutoCloseTimer"' in helper_source
    assert "interval: host.duration" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: host.close()" in helper_source
    assert "onTriggered: control.close()" not in source


def test_tooltip_core_keeps_follow_anchor_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Tooltip/TooltipCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Tooltip/_internal/"
        "TooltipFollowAnchorTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 232
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "_internal" as TooltipInternal' in source
    assert "TooltipInternal.TooltipFollowAnchorTimer {" in source
    assert "id: followTimer" in source
    assert "host: control" in source
    assert "nativeHost: windowHost" in source
    assert "\n            Timer {" not in source
    assert "required property var host" in helper_source
    assert "required property var nativeHost" in helper_source
    assert 'objectName: "tooltipFollowAnchorTimer"' in helper_source
    assert "FrameAnimation {" in helper_source
    assert "interval:" not in helper_source
    assert "repeat:" not in helper_source
    assert "running: host.followAnchor && nativeHost.windowVisible" in helper_source
    assert "onTriggered: host._reposition()" in helper_source
    assert "running: control.followAnchor && windowHost.windowVisible" not in source


def test_action_keeps_tooltip_show_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/menus/Action.qml")
    helper = _source(
        "prismqml/PrismQML/controls/menus/_internal/ActionTooltipShowTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 220
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "_internal" as MenuInternal' in source
    assert "MenuInternal.ActionTooltipShowTimer {" in source
    assert "id: tooltipShowTimer" in source
    assert "actionControl: control" in source
    assert "hoverArea: itemArea" in source
    assert "tooltip: actionTooltip" in source
    assert "\n            Timer {" not in source
    assert "required property var actionControl" in helper_source
    assert "required property var hoverArea" in helper_source
    assert "required property var tooltip" in helper_source
    assert 'objectName: "actionTooltipShowTimer"' in helper_source
    assert "interval: 600" in helper_source
    assert "repeat: false" in helper_source
    assert 'running: actionControl.toolTip !== "" && hoverArea.containsMouse' in helper_source
    assert "onTriggered: tooltip.show()" in helper_source
    assert "onTriggered: actionTooltip.show()" not in source


def test_auto_updater_keeps_update_dialog_wiring_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/AutoUpdater.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/_internal/"
        "AutoUpdaterUpdateDialog.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 430
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert 'import "_internal" as FeedbackInternal' in source
    assert "FeedbackInternal.AutoUpdaterUpdateDialog {" in source
    assert "updateDialogComponent.createObject(root)" in source
    assert "UpdateDialog {" in helper_source
    assert "required property var updaterControl" in helper_source
    assert "updaterControl._awaitingDecision" in helper_source
    assert "updaterControl._beginDownload" in helper_source
    assert "updaterControl._clearPending()" in helper_source
    for marker in (
        "\n        UpdateDialog {",
        "onConfirmed:",
        "onCancelled:",
        "\n            id: updateDialog\n",
    ):
        assert marker not in source


def test_auto_updater_keeps_feedback_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/AutoUpdater.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/_internal/"
        "AutoUpdaterFeedbackTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 430
    assert helper.exists()
    assert len(helper_source.splitlines()) < 50
    assert 'import "_internal" as FeedbackInternal' in source
    assert "FeedbackInternal.AutoUpdaterFeedbackTimer {" in source
    assert "required property var host" in helper_source
    assert 'objectName: "autoUpdaterFeedbackTimer"' in helper_source
    assert "interval: host._feedbackDuration" in helper_source
    assert "running: host._feedbackActive" in helper_source
    assert "host._feedbackDuration > Enums.duration.none" in helper_source
    assert "onTriggered: host._dismissFeedback()" in helper_source
    assert "\n    Timer {" not in source


def test_auto_updater_keeps_signal_orchestration_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/AutoUpdater.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/_internal/"
        "AutoUpdaterSignalConnections.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 300
    assert helper.exists()
    assert len(helper_source.splitlines()) < 180
    assert "FeedbackInternal.AutoUpdaterSignalConnections {" in source
    assert "host: root" in source
    assert "required property var host" in helper_source
    assert "target: host.updater" in helper_source
    assert "ignoreUnknownSignals: true" in helper_source
    assert "function onUpdateAvailable(" in helper_source
    assert "function onDownloadFinished(" in helper_source
    assert "function onInstallPreparationFinished(" in helper_source
    assert "\n    Connections {" not in source
    assert "function onUpdateAvailable(" not in source

    violations = []
    for path, candidate in ((entry, source), (helper, helper_source)):
        violations.extend(
            violation
            for violation in scan_source_text(
                candidate, PurePosixPath(path.relative_to(ROOT).as_posix())
            )
            if violation.rule in {"QML008", "QML009"}
        )
    assert violations == []


def test_auto_updater_toast_presenter_keeps_sync_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/AutoUpdaterToastPresenter.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/_internal/"
        "AutoUpdaterToastSyncTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 120
    assert helper.exists()
    assert len(helper_source.splitlines()) < 40
    assert 'import "_internal" as FeedbackInternal' in source
    assert "FeedbackInternal.AutoUpdaterToastSyncTimer {" in source
    assert "id: syncTimer" in source
    assert "host: root" in source
    assert "syncTimer.restart()" in source
    assert source.count("syncTimer.stop()") == 2
    assert "required property var host" in helper_source
    assert 'objectName: "autoUpdaterToastSyncTimer"' in helper_source
    assert "interval: Enums.duration.none" in helper_source
    assert "onTriggered: host._sync()" in helper_source
    assert "\n    Timer {" not in source


def test_info_bar_keeps_shared_close_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/InfoBar/InfoBarCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/InfoBar/_internal/"
        "InfoBarCloseTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 180
    assert helper.exists()
    assert len(helper_source.splitlines()) < 40
    assert 'import "_internal" as InfoBarInternal' in source
    assert "InfoBarInternal.InfoBarCloseTimer {" in source
    assert "id: closeTimer" in source
    assert "host: control" in source
    assert helper_source.count("Timer {") == 1
    assert "required property var host" in helper_source
    assert "readonly property bool completeMode" in helper_source
    assert 'objectName: "infoBarCloseTimer"' in helper_source
    assert "running: host._autoCloseActive || host._completeCloseActive" in helper_source
    assert "interval: completeMode ? host.completeDuration : host.duration" in helper_source
    assert "restart()" in helper_source
    assert "onTriggered: host.hide()" in helper_source
    assert "readonly property bool completeMode" not in source
    assert "\n    Timer {" not in source


def test_toast_keeps_auto_close_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Notification/Toast.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Notification/_internal/"
        "ToastAutoCloseTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 160
    assert helper.exists()
    assert len(helper_source.splitlines()) < 35
    assert 'import "_internal" as NotificationInternal' in source
    assert "NotificationInternal.ToastAutoCloseTimer {" in source
    assert "id: hideTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "\n        interval: control.duration\n" not in source
    assert "\n        running: control.visible && control.duration > 0 && !_isProgressMode\n" not in source
    assert "onTriggered: control.hide()" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "toastHideTimer"' in helper_source
    assert "interval: host.duration" in helper_source
    assert "running: host.visible && host.duration > 0 && !host._isProgressMode" in helper_source
    assert "onTriggered: host.hide()" in helper_source


def test_toast_keeps_progress_complete_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Notification/Toast.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Notification/_internal/"
        "ToastProgressCompleteTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 155
    assert helper.exists()
    assert len(helper_source.splitlines()) < 35
    assert 'import "_internal" as NotificationInternal' in source
    assert "NotificationInternal.ToastProgressCompleteTimer {" in source
    assert "id: completeTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "toastCompleteTimer"' in helper_source
    assert "running: host._progressComplete && host.visible" in helper_source
    assert "interval: host.completeDuration" in helper_source
    assert "onTriggered: host.hide()" in helper_source


def test_desktop_notification_keeps_auto_close_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Notification/"
        "DesktopNotification.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Notification/_internal/"
        "DesktopNotificationAutoCloseTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 235
    assert helper.exists()
    assert len(helper_source.splitlines()) < 35
    assert 'import "_internal" as NotificationInternal' in source
    assert "NotificationInternal.DesktopNotificationAutoCloseTimer {" in source
    assert "id: autoCloseTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "interval: duration" not in source
    assert "onTriggered: control.hide()" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "desktopNotificationAutoCloseTimer"' in helper_source
    assert "interval: host.duration" in helper_source
    assert "onTriggered: host.hide()" in helper_source


def test_notification_animator_keeps_geometry_update_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Notification/"
        "NotificationAnimator.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Notification/_internal/"
        "NotificationAnimatorGeometryUpdateTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 270
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert helper_source.count("Timer {") == 1
    assert "\nTimer {" in helper_source
    assert 'import "_internal" as NotificationInternal' in source
    assert "property Timer _geometryUpdateTimer:" in source
    assert "NotificationInternal.NotificationAnimatorGeometryUpdateTimer {" in source
    assert "host: animator" in source
    assert "required property var host" in helper_source
    assert (
        'objectName: "notificationAnimatorGeometryUpdateTimer"'
        in helper_source
    )
    assert "interval: Enums.duration.none" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: host.updatePosition()" in helper_source
    assert "_geometryUpdateTimer.restart()" in source
    assert "_geometryUpdateTimer.stop()" in source
    assert "property Timer _geometryUpdateTimer: Timer {" not in source
    assert "onTriggered: animator.updatePosition()" not in source


def test_window_outside_notification_keeps_native_overlay_lifecycle_internal():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Notification/_internal/"
        "WindowOutsideOverlay.qml"
    )
    geometry = _source(
        "prismqml/PrismQML/controls/feedback/Notification/_internal/"
        "WindowOutsideGeometry.qml"
    )
    animator = _source(
        "prismqml/PrismQML/controls/feedback/Notification/NotificationAnimator.qml"
    )
    source = entry.read_text(encoding="utf-8")
    geometry_source = geometry.read_text(encoding="utf-8")
    animator_source = animator.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 210
    assert len(geometry_source.splitlines()) < 45
    assert len(animator_source.splitlines()) < 270
    assert "required property var hostWindow" in source
    assert "property alias animator: animator" in source
    assert "property alias content: container" in source
    assert "property bool _attached: false" in source
    assert "function _releaseAttachment()" in source
    assert "if (!_attached) return false" in source
    assert "NotificationInternal.WindowOutsideGeometry {" in source
    assert "parentItem: outsideGeometry" in source
    assert "reverseShowDirection: true" in source
    assert "NotificationAnimator {" in source
    assert "target: control" in source
    assert "property bool reverseShowDirection: false" in animator_source
    assert "WindowHelper.registerWindowAttachment(" in source
    assert "WindowHelper.unregisterWindowAttachment(control)" in source
    assert "target: control.hostWindow" in source
    assert "target: typeof WindowHelper !== \"undefined\" ? WindowHelper : null" in source
    assert "required property var hostWindow" in geometry_source
    assert "required property int position" in geometry_source
    assert "required property real targetWidth" in geometry_source
    assert "required property real targetHeight" in geometry_source
    assert "WindowHelper.windowAttachmentGeometry(" in geometry_source
    assert "parentItem && typeof parentItem.calculate === \"function\"" in animator_source
    assert "var attachedGeometry = parentItem" in animator_source
    assert "property var hostWindow" not in animator_source


def test_notification_manager_keeps_outside_mode_as_internal_component_wiring():
    manager = _source(
        "prismqml/PrismQML/controls/feedback/Notification/NotificationManager.qml"
    )
    qmldir = _source(
        "prismqml/PrismQML/controls/feedback/Notification/_internal/qmldir"
    )
    source = manager.read_text(encoding="utf-8")
    qmldir_source = qmldir.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert "property var _windowOutsideComponent: null" in source
    assert "Enums.notification.mode_window_outside" in source
    assert "function _createWindowOutside(" in source
    assert "_getWindowOutsideComponent()" in source
    assert "WindowHelper" not in source
    assert "WindowOutsideGeometry" not in source
    assert "WindowOutsideOverlay WindowOutsideOverlay.qml" in qmldir_source
    assert "WindowOutsideGeometry WindowOutsideGeometry.qml" in qmldir_source


def test_marquee_keeps_layout_start_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/data/Marquee.qml")
    helper = _source(
        "prismqml/PrismQML/controls/data/_internal/MarqueeStartTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 130
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "_internal" as DataInternal' in source
    assert "DataInternal.MarqueeStartTimer {" in source
    assert "id: startTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "marqueeStartTimer"' in helper_source
    assert "interval: 100" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: host._tryStartAnimation()" in helper_source


def test_paginator_keeps_page_settle_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/Paginator.qml")
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/"
        "PaginatorPageSettleTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 250
    assert helper.exists()
    assert len(helper_source.splitlines()) < 30
    assert 'import "_internal" as NavigationInternal' in source
    assert "NavigationInternal.PaginatorPageSettleTimer {" in source
    assert "id: pageSettleTimer" in source
    assert "host: root" in source
    assert "slideAnimation: pageSlideAnimation" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert "required property var slideAnimation" in helper_source
    assert 'objectName: "paginatorPageSettleTimer"' in helper_source
    assert "interval: 0" in helper_source
    assert "repeat: false" in helper_source
    assert "if (!slideAnimation.running) host._settleLoadedPages()" in helper_source
    assert "if (!pageSlideAnimation.running) root._settleLoadedPages()" not in source


def test_menu_bar_keeps_dynamic_close_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/MenuBar.qml")
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/MenuBarCloseTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 180
    assert helper.exists()
    assert len(helper_source.splitlines()) < 30
    assert helper_source.count("Timer {") == 1
    assert "\nTimer {" in helper_source
    assert 'import "_internal" as NavigationInternal' in source
    assert "id: closeTimerComponent" in source
    assert "NavigationInternal.MenuBarCloseTimer {" in source
    assert "menuBar: control" in source
    assert "closeTimerComponent.createObject(" in source
    assert '"menuButton": menuBtn' in source
    assert '"ownerItem": menuItemContainer' in source
    assert "required property Item menuBar" in helper_source
    assert "required property Item menuButton" in helper_source
    assert "required property Item ownerItem" in helper_source
    assert 'objectName: "menuBarCloseTimer"' in helper_source
    assert "interval: Enums.duration.fast" in helper_source
    assert "repeat: false" in helper_source
    assert "ownerItem._closeTimer = null" in helper_source
    assert "destroy()" in helper_source
    assert "\n        Timer {" not in source
    assert "if (!menuButton.hovered)" not in source


def test_breadcrumb_keeps_dynamic_stage_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/Breadcrumb.qml")
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/BreadcrumbStageTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 360
    assert helper.exists()
    assert len(helper_source.splitlines()) < 30
    assert helper_source.count("Timer {") == 1
    assert "\nTimer {" in helper_source
    assert 'import "_internal"' in source
    assert "id: stageTimerComponent" in source
    assert "BreadcrumbStageTimer {}" in source
    assert "stageTimerComponent.createObject(" in source
    assert '"timerInterval": timerInterval' in source
    assert '"triggerCallback": triggerCallback' in source
    assert '"releaseCallback": releaseCallback' in source
    assert "required property int timerInterval" in helper_source
    assert "required property var triggerCallback" in helper_source
    assert "required property var releaseCallback" in helper_source
    assert 'objectName: "breadcrumbStageTimer"' in helper_source
    assert "interval: timerInterval" in helper_source
    assert "repeat: false" in helper_source
    assert helper_source.index("triggerCallback()") < helper_source.index(
        "releaseCallback(stageTimer)"
    )
    assert helper_source.index("releaseCallback(stageTimer)") < helper_source.index(
        "destroy()"
    )
    assert "\n        Timer {" not in source
    assert "releaseCallback(stageTimer)" not in source


def test_scroll_viewport_state_keeps_phase_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/ScrollViewportState.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/_internal/"
        "ScrollViewportPhaseTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 320
    assert helper.exists()
    assert len(helper_source.splitlines()) < 30
    assert helper_source.count("Timer {") == 1
    assert "\nTimer {" in helper_source
    assert 'import "_internal" as ScrollBarInternal' in source
    assert "ScrollBarInternal.ScrollViewportPhaseTimer {" in source
    assert "id: phaseTimer" in source
    assert "host: control" in source
    assert "required property var host" in helper_source
    assert 'objectName: "scrollViewportPhaseTimer"' in helper_source
    assert "host._phase === host._phaseContentUpdate" in helper_source
    assert "host._phase === host._phaseSuppressionClear" in helper_source
    assert "Enums.duration.fast" in helper_source
    assert "Enums.duration.instant" in helper_source
    assert "Enums.duration.none" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: host._runPhase()" in helper_source
    assert "phaseTimer.restart()" in source
    assert "phaseTimer.stop()" in source
    assert "\n    Timer {" not in source
    assert "onTriggered: control._runPhase()" not in source


def test_hover_behavior_keeps_unmatched_target_timer_modularized():
    entry = _source("prismqml/PrismQML/effects/HoverBehavior.qml")
    helper = _source(
        "prismqml/PrismQML/effects/_internal/"
        "HoverBehaviorUnmatchedTargetTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 120
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert helper_source.count("Timer {") == 1
    assert "\nTimer {" in helper_source
    assert 'import "_internal" as EffectsInternal' in source
    assert "property QtObject _unmatchedTargetTimer:" in source
    assert "EffectsInternal.HoverBehaviorUnmatchedTargetTimer {" in source
    assert "host: root" in source
    assert "required property var host" in helper_source
    assert 'objectName: "hoverBehaviorUnmatchedTargetTimer"' in helper_source
    assert "interval: Enums.duration.none" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: host._awaitingActiveAfterTarget = false" in helper_source
    assert "_unmatchedTargetTimer.stop()" in source
    assert "_unmatchedTargetTimer.restart()" in source
    assert "property QtObject _unmatchedTargetTimer: Timer {" not in source
    assert "onTriggered: root._awaitingActiveAfterTarget = false" not in source


def test_viewport_mixin_keeps_init_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/utils/ViewportMixin.qml")
    helper = _source(
        "prismqml/PrismQML/controls/utils/_internal/ViewportInitTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 110
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert helper_source.count("Timer {") == 1
    assert "\nTimer {" in helper_source
    assert 'import "_internal" as UtilsInternal' in source
    assert "property Timer initTimer:" in source
    assert "UtilsInternal.ViewportInitTimer {" in source
    assert "host: mixin" in source
    assert "required property var host" in helper_source
    assert 'objectName: "viewportInitTimer"' in helper_source
    assert "interval: 50" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: host._init()" in helper_source
    assert "property Timer initTimer: Timer {" not in source
    assert "onTriggered: _init()" not in source

    # onCompleted must initialize synchronously AND arm the settle re-check.
    # Deferring to the timer alone let consumers read a stale default first.
    # onCompleted 必须同步初始化并同时挂上稳定后复算；只靠定时器会让消费者先读到过期默认值。
    assert "Component.onCompleted: {" in source
    assert "_init()" in source
    assert "initTimer.start()" in source

    # Ancestor and contentItem wiring must stay declarative so a destroyed
    # consumer leaves no stale callback. 祖先与 contentItem 连接必须保持声明式。
    assert "UtilsInternal.ViewportAncestorWatcher {" in source
    assert "UtilsInternal.ViewportContentWatcher {" in source
    assert ".contentYChanged.connect(" not in source
    assert ".heightChanged.connect(" not in source


def test_widget_keeps_center_children_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/containers/Widget.qml")
    helper = _source(
        "prismqml/PrismQML/controls/containers/_internal/"
        "WidgetCenterChildrenTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 160
    assert helper.exists()
    assert len(helper_source.splitlines()) < 40
    assert helper_source.count("Timer {") == 1
    assert "\nTimer {" in helper_source
    assert 'import "_internal" as ContainerInternal' in source
    assert "readonly property Loader _centerChildrenDelayed: Loader" in source
    assert "active: widget.centerContent" in source
    assert "onLoaded: widget._scheduleCenterChildren()" in source
    assert "sourceComponent: ContainerInternal.WidgetCenterChildrenTimer {" in source
    assert "host: widget" in source
    assert "required property Item host" in helper_source
    assert 'objectName: "widgetCenterChildrenTimer"' in helper_source
    assert "interval: Enums.duration.tick" in helper_source
    assert "repeat: false" in helper_source
    assert "for (var i = 0; i < host.children.length; i++)" in helper_source
    assert "if (host._isCenterableChild(child))" in helper_source
    assert "child.anchors.centerIn = host" in helper_source
    assert "sourceComponent: Timer {" not in source
    assert "for (var i = 0; i < widget.children.length; i++)" not in source


def test_menu_core_keeps_visual_content_modularized():
    entry = _source("prismqml/PrismQML/controls/menus/MenuCore.qml")
    helper = _source("prismqml/PrismQML/controls/menus/_internal/MenuContent.qml")

    assert len(entry.read_text(encoding="utf-8").splitlines()) < 500
    assert helper.exists()
    assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
    assert "MenuContent {" in entry.read_text(encoding="utf-8")


def test_menu_core_keeps_logical_item_registry_modularized():
    entry = _source("prismqml/PrismQML/controls/menus/MenuCore.qml")
    helper = _source(
        "prismqml/PrismQML/controls/menus/_internal/MenuItemRegistry.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 410
    assert helper.exists()
    assert len(helper_source.splitlines()) < 80
    assert "MenuItemRegistry {" in source
    for marker in ("property var items: []", "function liveItems()",
                   "function measuredWidth(", "function measuredHeight()"):
        assert marker in helper_source
        assert marker not in source


def test_menu_core_keeps_submenu_open_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/menus/MenuCore.qml")
    helper = _source(
        "prismqml/PrismQML/controls/menus/_internal/MenuSubmenuOpenTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 80
    assert helper_source.count("Timer {") == 1
    assert "\nTimer {" in helper_source
    assert "required property var host" in helper_source
    assert "interval: Enums.duration.fast" in helper_source
    assert "repeat: false" in helper_source
    assert (
        "host._pendingSubmenuAction.hovered" in helper_source
    )
    assert "host._openSubmenuForAction(" in helper_source
    assert "MenuSubmenuOpenTimer {" in source
    assert "id: submenuOpenTimer" in source
    assert "host: control" in source
    assert "\n Timer {" not in source
    assert "interval: Enums.duration.fast" not in source
    assert "_pendingSubmenuAction && _pendingSubmenuAction.hovered" not in source


def test_infobar_core_keeps_visual_content_modularized():
    entry = _source("prismqml/PrismQML/controls/feedback/InfoBar/InfoBarCore.qml")
    helper = _source(
        "prismqml/PrismQML/controls/feedback/InfoBar/_internal/InfoBarContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 250
    assert helper.exists()
    assert len(helper_source.splitlines()) < 400
    assert 'import "_internal" as InfoBarInternal' in source
    assert "InfoBarInternal.InfoBarContent {" in source
    assert "required property var infoBar" in helper_source
    assert "property alias customContent: customContentLoader.sourceComponent" in helper_source
    assert "readonly property real calculatedContentWidth" in helper_source
    assert "readonly property real horizontalContentHeight" in helper_source
    assert "readonly property real verticalContentHeight" in helper_source

    for marker in (
        "RectangularShadow {",
        "NeumorphicShadow {",
        "NeoShadow {",
        "CloseButton {",
        "ProgressBar {",
        "ProgressRing {",
        "\n    Loader {",
        "\n    Component {",
    ):
        assert marker not in source


def test_toast_keeps_visual_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Notification/Toast.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Notification/_internal/ToastContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 250
    assert helper.exists()
    assert len(helper_source.splitlines()) < 400
    assert 'import "_internal" as NotificationInternal' in source
    assert "NotificationInternal.ToastContent {" in source
    assert "required property var toast" in helper_source
    assert "property alias customContent: customContentLoader.sourceComponent" in helper_source
    assert "readonly property real calculatedContentWidth" in helper_source
    assert "readonly property real horizontalHeight" in helper_source
    assert "readonly property real verticalHeight" in helper_source

    for marker in (
        "RectangularShadow {",
        "NeumorphicShadow {",
        "NeoShadow {",
        "CloseButton {",
        "ProgressBar {",
        "ProgressRing {",
        "\n    Loader {",
        "\n    Component {",
    ):
        assert marker not in source


def test_calendar_picker_core_keeps_content_tree_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/DatePicker/CalendarPickerCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/DatePicker/_internal/"
        "CalendarPickerContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 200
    assert helper.exists()
    assert len(helper_source.splitlines()) < 450
    assert 'import "_internal" as DatePickerInternal' in source
    assert "DatePickerInternal.CalendarPickerContent {" in source
    assert "required property var calendarControl" in helper_source
    assert "property alias gridWrapperBehavior: gridWrapperBehavior" in helper_source
    assert "property alias dayGrid: dayGrid" in helper_source
    assert "property alias nextGrid: nextGrid" in helper_source
    assert "readonly property real gridContainerHeight" in helper_source

    for marker in (
        "\n    Column {",
        "\n    Timer {",
        "CalendarNavButton {",
        "Grid {",
        "Repeater {",
    ):
        assert marker not in source


def test_date_time_picker_keeps_display_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/Picker/DateTimePicker.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/Picker/_internal/"
        "DateTimePickerDisplay.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 380
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert 'import "./_internal" as PickerInternal' in source
    assert "PickerInternal.DateTimePickerDisplay {" in source
    assert "required property var pickerControl" in helper_source
    assert "Repeater {" in helper_source
    assert "parent ? parent.width /" in helper_source
    assert "parent ? parent.height : 0" in helper_source
    assert "Row {" not in source
    assert "Repeater {" not in source


def test_date_time_picker_keeps_init_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/Picker/DateTimePicker.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/Picker/_internal/"
        "DateTimePickerInitTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 376
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "./_internal" as PickerInternal' in source
    assert "PickerInternal.DateTimePickerInitTimer {" in source
    assert "id: initTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "dateTimePickerInitTimer"' in helper_source
    assert "interval: 50" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: host._initWheelPositions()" in helper_source
    assert "control._initWheelPositions()" not in source


def test_color_picker_keeps_content_and_popup_tree_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/ColorPicker/ColorPicker.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/ColorPicker/_internal/"
        "ColorPickerContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 220
    assert helper.exists()
    assert len(helper_source.splitlines()) < 350
    assert 'import "_internal" as ColorPickerInternal' in source
    assert "ColorPickerInternal.ColorPickerContent {" in source
    assert "required property var colorControl" in helper_source
    for alias in (
        "property alias circleLoader: circleLoader",
        "property alias popup: popup",
        "property alias paletteDialogLoader: paletteDialogLoader",
        "property alias dialogLoader: dialogLoader",
    ):
        assert alias in helper_source
    assert helper_source.count("parent: colorControl") == 6

    for marker in (
        "Loader {",
        "PopupWindowCore {",
        "ColorPickerTrigger {",
        "ColorPalette {",
        "ColorPickerDropdown {",
        "ColorPickerDialog {",
        "CustomButtonCore {",
        "Connections {",
    ):
        assert marker not in source


def test_filter_bar_core_keeps_visual_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/FilterBar/FilterBarCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/FilterBar/_internal/"
        "FilterBarContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 180
    assert helper.exists()
    assert len(helper_source.splitlines()) < 260
    assert 'import "_internal" as FilterBarInternal' in source
    assert "FilterBarInternal.FilterBarContent {" in source
    assert "required property var filterControl" in helper_source
    assert "property alias itemRepeater: itemRepeater" in helper_source
    assert "readonly property real contentWidth" in helper_source
    assert helper_source.count("parent: filterControl") == 2

    for marker in (
        "NeumorphicShadow {",
        "Repeater {",
        "MouseArea {",
        "Icon {",
        "Label {",
    ):
        assert marker not in source


def test_audio_waveform_keeps_visual_content_modularized():
    entry = _source("prismqml/PrismQML/controls/data/AudioWaveform.qml")
    helper = _source(
        "prismqml/PrismQML/controls/data/_internal/AudioWaveformContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 160
    assert helper.exists()
    assert len(helper_source.splitlines()) < 260
    assert 'import "_internal" as DataInternal' in source
    assert "DataInternal.AudioWaveformContent {" in source
    assert "required property var waveformControl" in helper_source
    assert "property alias waveformContainer: waveformContainer" in helper_source
    assert "property alias mouseArea: mouseArea" in helper_source
    assert helper_source.startswith(
        "// Copyright 2026 aki-riko\n"
        "// SPDX-License-Identifier: MIT\n"
        "// This file is part of PrismQML, licensed under MIT.\n\n"
        "import QtQuick\n"
        "import \"../../..\"\n"
        "import \"../../../effects\"\n\n"
        "// AudioWaveformContent"
    )
    assert "ShadowedRectangle {" in helper_source
    assert helper_source.count("parent: waveformControl") == 2

    for marker in (
        "ShadowedRectangle {",
        "Repeater {",
        "MouseArea {",
        "\n    Item {",
    ):
        assert marker not in source


def test_shortcut_editor_keeps_scrollable_content_modularized():
    entry = _source("prismqml/PrismQML/controls/inputs/ShortcutEditor.qml")
    helper = _source(
        "prismqml/PrismQML/controls/inputs/_internal/ShortcutEditorContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 230
    assert helper.exists()
    assert len(helper_source.splitlines()) < 150
    assert 'import "_internal" as InputInternal' in source
    assert "InputInternal.ShortcutEditorContent {" in source
    assert "required property var editorControl" in helper_source
    assert "required property var cancelButton" in helper_source
    assert "property alias contentRow: contentRow" in helper_source
    assert helper_source.startswith(
        "// Copyright 2026 aki-riko\n"
        "// SPDX-License-Identifier: MIT\n"
        "// This file is part of PrismQML, licensed under MIT.\n\n"
        "import QtQuick\n"
        "import \"../../..\"\n"
        "import \"../../buttons\"\n"
        "import \"../../data/Label\"\n\n"
        "// ShortcutEditorContent"
    )

    for marker in (
        "\n    Flickable {",
        "\n        Repeater {",
        "\n        Label {",
    ):
        assert marker not in source


def test_cycle_wheel_picker_keeps_scroll_buttons_modularized():
    entry = _source("prismqml/PrismQML/controls/inputs/CycleWheelPicker.qml")
    helper = _source(
        "prismqml/PrismQML/controls/inputs/_internal/"
        "CycleWheelPickerButtons.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 330
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert 'import "_internal" as InputInternal' in source
    assert "InputInternal.CycleWheelPickerButtons {" in source
    assert "required property var wheelControl" in helper_source
    assert "\nRectangle {\n" in helper_source
    assert helper_source.count("parent: wheelControl") == 1

    for marker in (
        "\n    Rectangle {",
        "\n        Icon {",
        "\n        MouseArea {",
    ):
        assert marker not in source


def test_cycle_wheel_picker_keeps_delegates_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/CycleWheelPicker.qml"
    )
    path_delegate = _source(
        "prismqml/PrismQML/controls/inputs/_internal/"
        "CycleWheelPickerPathDelegate.qml"
    )
    list_delegate = _source(
        "prismqml/PrismQML/controls/inputs/_internal/"
        "CycleWheelPickerListDelegate.qml"
    )
    source = entry.read_text(encoding="utf-8")
    path_source = path_delegate.read_text(encoding="utf-8")
    list_source = list_delegate.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 270
    assert path_delegate.exists()
    assert list_delegate.exists()
    assert len(path_source.splitlines()) < 100
    assert len(list_source.splitlines()) < 110
    assert 'import "_internal" as InputInternal' in source
    assert "InputInternal.CycleWheelPickerPathDelegate {" in source
    assert "InputInternal.CycleWheelPickerListDelegate {" in source
    for helper_source in (path_source, list_source):
        assert "required property var wheelControl" in helper_source
        assert "required property var modelData" in helper_source
        assert "wheelControl._distanceFromCenter" in helper_source
    assert "required property int index" in list_source
    assert "ListView.view.currentIndex" in list_source
    assert "PathView.isCurrentItem" in path_source

    for marker in (
        "\n        delegate: Item {",
        "property real distanceFromCenter:",
        "text: String(modelData)",
    ):
        assert marker not in source


def test_cycle_wheel_picker_keeps_repeat_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/inputs/CycleWheelPicker.qml")
    helper = _source(
        "prismqml/PrismQML/controls/inputs/_internal/"
        "CycleWheelPickerRepeatTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 255
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "_internal" as InputInternal' in source
    assert "InputInternal.CycleWheelPickerRepeatTimer {" in source
    assert "id: repeatTimer" in source
    assert "wheelControl: control" in source
    assert "\n    Timer {" not in source
    assert "required property var wheelControl" in helper_source
    assert 'objectName: "cycleWheelPickerRepeatTimer"' in helper_source
    assert "interval: wheelControl._repeatStarted" in helper_source
    assert "Enums.duration.wheelPickerRepeatInterval" in helper_source
    assert "Enums.duration.wheelPickerRepeatDelay" in helper_source
    assert "repeat: true" in helper_source
    assert "onTriggered: wheelControl._triggerRepeat()" in helper_source


def test_pips_pager_keeps_navigation_button_visuals_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/FlipView/PipsPagerCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/FlipView/_internal/"
        "PipsPagerNavButton.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 230
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert 'import "_internal" as FlipViewInternal' in source
    assert "FlipViewInternal.PipsPagerNavButton {" in source
    assert "required property var pagerControl" in helper_source
    assert "required property bool isNext" in helper_source
    assert "pagerControl.next()" in helper_source
    assert "pagerControl.previous()" in helper_source
    assert "navButtonComponent.createObject(control" in source
    assert "ButtonCore {" not in source


def test_pips_pager_keeps_pips_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/FlipView/PipsPagerCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/FlipView/_internal/"
        "PipsPagerContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 150
    assert helper.exists()
    assert len(helper_source.splitlines()) < 150
    assert 'import "_internal" as FlipViewInternal' in source
    assert "FlipViewInternal.PipsPagerContent {" in source
    assert "required property var pagerControl" in helper_source
    assert "Repeater {" in helper_source
    assert "Behavior on _animatedScrollOffset" in helper_source
    assert "Item {\n        id: pipsContainer" not in source
    assert "Repeater {" not in source
    assert "property real _scrollOffset" not in source


def test_carousel_keeps_dynamic_factories_modularized():
    entry = _source("prismqml/PrismQML/controls/data/Carousel/Carousel.qml")
    helper = _source(
        "prismqml/PrismQML/controls/data/Carousel/_internal/"
        "CarouselFactories.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 320
    assert helper.exists()
    assert len(helper_source.splitlines()) < 180
    assert 'import "_internal" as CarouselInternal' in source
    assert "CarouselInternal.CarouselFactories {" in source
    assert "required property var carouselControl" in helper_source
    for component_name in (
        "contentAreaComponent",
        "indicatorComponent",
        "navButtonComponent",
    ):
        assert f"property alias {component_name}:" in helper_source
        assert f"carouselFactories.{component_name}.createObject(control" in source
    for marker in (
        "CarouselContent {",
        "FlipViewControls.PipsPager {",
        "CarouselNavButton {",
    ):
        assert marker not in source


def test_carousel_keeps_auto_play_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/Carousel/Carousel.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/Carousel/_internal/"
        "CarouselAutoPlayTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 300
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert "CarouselInternal.CarouselAutoPlayTimer {" in source
    assert "id: autoPlayTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "carouselAutoPlayTimer"' in helper_source
    assert "running: host.autoPlay && host._modelCount > 1" in helper_source
    assert "host.pauseOnHover && host._isHovered" in helper_source
    assert "repeat: true" in helper_source
    assert "interval: host.interval" in helper_source
    assert "onTriggered: host.next()" in helper_source


def test_confirm_dialog_keeps_countdown_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/dialogs/ConfirmDialog.qml")
    helper = _source(
        "prismqml/PrismQML/controls/dialogs/_internal/"
        "ConfirmDialogCountdownTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 220
    assert helper.exists()
    assert len(helper_source.splitlines()) < 30
    assert 'import "_internal" as DialogInternal' in source
    assert "DialogInternal.ConfirmDialogCountdownTimer {" in source
    assert "id: countdownTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "confirmDialogCountdownTimer"' in helper_source
    assert "interval: 1000" in helper_source
    assert "repeat: true" in helper_source
    assert "host._countdownRemaining--" in helper_source
    assert "if (host._countdownRemaining === 0) running = false" in helper_source


def test_progress_dialog_keeps_timeout_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/dialogs/ProgressDialog.qml")
    helper = _source(
        "prismqml/PrismQML/controls/dialogs/_internal/"
        "ProgressDialogTimeoutTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 190
    assert helper.exists()
    assert len(helper_source.splitlines()) < 30
    assert 'import "_internal" as DialogInternal' in source
    assert "DialogInternal.ProgressDialogTimeoutTimer {" in source
    assert "id: timeoutTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "progressDialogTimeoutTimer"' in helper_source
    assert "interval: host.maxWaitingTime" in helper_source
    assert "running: host._isOpen && host.maxWaitingTime > 0" in helper_source
    assert "host.timeout()" in helper_source
    assert "host.close()" in helper_source


def test_overlay_dialog_keeps_restore_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/dialogs/OverlayDialogCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/dialogs/_internal/"
        "OverlayDialogRestoreParentTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 175
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "_internal" as DialogInternal' in source
    assert "DialogInternal.OverlayDialogRestoreParentTimer {" in source
    assert "id: _restoreParentTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "overlayDialogRestoreParentTimer"' in helper_source
    assert "interval: Enums.duration.medium + Enums.spacing.xl" in helper_source
    assert "onTriggered: host._restoreParent()" in helper_source


def test_line_edit_core_keeps_variant_factories_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/LineEdit/LineEditCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/LineEdit/_internal/"
        "LineEditVariants.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 190
    assert helper.exists()
    assert len(helper_source.splitlines()) < 180
    assert 'import "_internal" as LineEditInternal' in source
    assert "LineEditInternal.LineEditVariants {" in source
    assert "required property var lineEditControl" in helper_source
    for component_name in ("normalComponent", "labelComponent", "tagComponent"):
        assert f"property alias {component_name}:" in helper_source
    for marker in (
        "\n    Component {\n        id: normalComponent",
        "\n    Component {\n        id: labelComponent",
        "\n    Component {\n        id: tagComponent",
    ):
        assert marker not in source


def test_line_edit_normal_keeps_hide_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/LineEdit/LineEditNormal.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/LineEdit/_internal/"
        "LineEditNormalHideTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 210
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "_internal" as LineEditInternal' in source
    assert "LineEditInternal.LineEditNormalHideTimer {" in source
    assert "id: _hideTimer" in source
    assert "host: normalInput" in source
    assert "_hideTimer.restart()" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "lineEditNormalHideTimer"' in helper_source
    assert "interval: Enums.duration.medium" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: if (!host.expanded) host._textInputVisible = false" in helper_source
    assert "onTriggered: if (!normalInput.expanded)" not in source


def test_pivot_keeps_indicator_sync_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/Pivot.qml")
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/"
        "PivotIndicatorSyncTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 215
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "_internal"' in source
    assert "PivotIndicatorSyncTimer {" in source
    assert "id: indicatorSyncTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "pivotIndicatorSyncTimer"' in helper_source
    assert "interval: Enums.duration.tick" in helper_source
    assert "repeat: true" in helper_source
    assert "onTriggered: host._updateIndicatorWithAnimation()" in helper_source


def test_teaching_tour_keeps_state_reset_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Overlay/TeachingTour.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Overlay/_internal/"
        "TeachingTourStateResetTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 365
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "_internal" as OverlayInternal' in source
    assert "OverlayInternal.TeachingTourStateResetTimer {" in source
    assert "id: stateResetTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "teachingTourStateResetTimer"' in helper_source
    assert "interval: Enums.duration.tipHide" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: if (!host._active) host._currentIndex = -1" in helper_source


def test_chart_data_zoom_keeps_drag_end_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/Chart/ChartDataZoom.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/"
        "ChartDataZoomDragEndTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 230
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "_internal" as ChartInternal' in source
    assert "ChartInternal.ChartDataZoomDragEndTimer {" in source
    assert "id: _dragEndTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "chartDataZoomDragEndTimer"' in helper_source
    assert "interval: Enums.duration.slow" in helper_source
    assert "repeat: false" in helper_source
    assert "host._dragging = false" in helper_source
    assert "host.interactiveChanged(false)" in helper_source


def test_segmented_control_keeps_delegate_visuals_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/SegmentedControl.qml")
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/SegmentedItem.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 230
    assert helper.exists()
    assert len(helper_source.splitlines()) < 130
    assert 'import "_internal" as NavigationInternal' in source
    assert "NavigationInternal.SegmentedItem {" in source
    assert "required property var segmentedControl" in helper_source
    assert "required property int index" in helper_source
    assert "required property var modelData" in helper_source
    assert "\nItem {\n" in helper_source
    assert "segmentedControl._scheduleSlideSync(false)" in helper_source
    assert "function _scheduleSlideSync(shouldAnimate)" in source
    assert "repeater.itemAt" in source

    violations = []
    for path, candidate in ((entry, source), (helper, helper_source)):
        violations.extend(
            violation
            for violation in scan_source_text(
                candidate, PurePosixPath(path.relative_to(ROOT).as_posix())
            )
            if violation.rule in {"QML008", "QML009"}
        )
    assert violations == []

    for marker in (
        "\n            Item {",
        "\n                Rectangle {",
        "\n                Row {",
        "\n                HoverHandler {",
        "\n                TapHandler {",
    ):
        assert marker not in source


def test_segmented_control_keeps_slide_sync_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/SegmentedControl.qml")
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/"
        "SegmentedSlideSyncTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 175
    assert helper.exists()
    assert len(helper_source.splitlines()) < 70
    assert 'import "_internal" as NavigationInternal' in source
    assert "NavigationInternal.SegmentedSlideSyncTimer {" in source
    assert "id: slideSyncTimer" in source
    assert "host: control" in source
    assert "segmentRow: segmentRow" in source
    assert "itemRepeater: repeater" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert "required property Item segmentRow" in helper_source
    assert "required property var itemRepeater" in helper_source
    assert 'objectName: "segmentedControlSlideSyncTimer"' in helper_source
    assert "function schedule(shouldAnimate)" in helper_source
    assert "interval: Enums.duration.tick" in helper_source
    assert "itemRepeater.itemAt(host.currentIndex)" in helper_source
    assert "host._updateSlidePosition(false)" in helper_source


def test_confetti_keeps_lifecycle_timers_modularized():
    entry = _source("prismqml/PrismQML/controls/feedback/Confetti.qml")
    spawn_helper = _source(
        "prismqml/PrismQML/controls/feedback/_internal/ConfettiSpawnTimer.qml"
    )
    stop_helper = _source(
        "prismqml/PrismQML/controls/feedback/_internal/ConfettiStopTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    spawn_source = spawn_helper.read_text(encoding="utf-8")
    stop_source = stop_helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 225
    assert spawn_helper.exists() and stop_helper.exists()
    assert len(spawn_source.splitlines()) < 25
    assert len(stop_source.splitlines()) < 25
    assert 'import "_internal" as FeedbackInternal' in source
    assert "FeedbackInternal.ConfettiSpawnTimer {" in source
    assert "FeedbackInternal.ConfettiStopTimer {" in source
    assert "id: spawnTimer" in source
    assert "id: stopTimer" in source
    assert source.count("host: control") == 2
    assert "\n    Timer {" not in source
    for helper_source in (spawn_source, stop_source):
        assert "required property var host" in helper_source
    assert 'objectName: "confettiSpawnTimer"' in spawn_source
    assert "running: host.running && host._spawnIndex < host.particleCount" in spawn_source
    assert "onTriggered: host._spawnBatch(8)" in spawn_source
    assert 'objectName: "confettiStopTimer"' in stop_source
    assert "interval: host.duration + Enums.duration.dialog" in stop_source
    assert "onTriggered: host.running = false" in stop_source


def test_pin_input_keeps_cell_delegate_modularized():
    entry = _source("prismqml/PrismQML/controls/inputs/PinInput.qml")
    helper = _source(
        "prismqml/PrismQML/controls/inputs/_internal/PinInputCell.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 180
    assert helper.exists()
    assert len(helper_source.splitlines()) < 170
    assert 'import "_internal" as InputInternal' in source
    assert "InputInternal.PinInputCell {" in source
    assert "required property var pinControl" in helper_source
    assert "required property int index" in helper_source
    assert "\nItem {\n" in helper_source
    assert "pinControl._focusInput()" in helper_source
    assert "function _focusInput()" in source

    violations = []
    for path, candidate in ((entry, source), (helper, helper_source)):
        violations.extend(
            violation
            for violation in scan_source_text(
                candidate, PurePosixPath(path.relative_to(ROOT).as_posix())
            )
            if violation.rule in {"QML008", "QML009"}
        )
    assert violations == []

    for marker in (
        "\n            Item {",
        "\n                RectangularShadow {",
        "\n                NeumorphicShadow {",
        "\n                NeoShadow {",
        "\n                MouseArea {",
    ):
        assert marker not in source


def test_spin_box_keeps_dynamic_button_components_modularized():
    entry = _source("prismqml/PrismQML/controls/inputs/SpinBox/SpinBoxCore.qml")
    helper = _source(
        "prismqml/PrismQML/controls/inputs/SpinBox/_internal/"
        "SpinBoxButtonGroups.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 330
    assert helper.exists()
    assert len(helper_source.splitlines()) < 150
    assert 'import "_internal" as SpinBoxInternal' in source
    assert "SpinBoxInternal.SpinBoxButtonGroups {" in source
    assert "required property var spinControl" in helper_source
    assert "property alias inlineButtonsComponent: inlineButtonsComponent" in helper_source
    assert "property alias compactButtonsComponent: compactButtonsComponent" in helper_source
    assert "sourceComponent: control.compactMode" in source
    assert "buttonGroups.compactButtonsComponent" in source
    assert "buttonGroups.inlineButtonsComponent" in source
    assert "Loader {" in source
    assert "Loader {" not in helper_source
    assert "onItemChanged:" in source

    for marker in (
        "\n    Component {",
        "\n        SpinBoxButton {",
        "\n        MiniSpinButton {",
    ):
        assert marker not in source


def test_spin_box_keeps_feedback_timers_modularized():
    entry = _source("prismqml/PrismQML/controls/inputs/SpinBox/SpinBoxCore.qml")
    helper = _source(
        "prismqml/PrismQML/controls/inputs/SpinBox/_internal/"
        "SpinBoxFeedbackTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 330
    assert helper.exists()
    assert len(helper_source.splitlines()) < 60
    assert 'import "_internal" as SpinBoxInternal' in source
    assert source.count("SpinBoxInternal.SpinBoxFeedbackTimer {") == 2
    assert "id: upFeedbackTimer" in source
    assert "id: downFeedbackTimer" in source
    assert source.count("spinControl: control") == 4
    assert "increase: true" in source
    assert "increase: false" in source
    assert "required property var spinControl" in helper_source
    assert "required property bool increase" in helper_source
    assert 'objectName: increase' in helper_source
    assert "interval: Enums.duration.fast" in helper_source
    assert "repeat: false" in helper_source
    assert "spinControl._increaseButton" in helper_source
    assert "spinControl._decreaseButton" in helper_source
    assert "pseudoHovered = false" in helper_source
    assert "pseudoPressed = false" in helper_source
    assert "\n    Timer {\n        id: upFeedbackTimer" not in source
    assert "\n    Timer {\n        id: downFeedbackTimer" not in source


def test_spin_box_keeps_auto_repeat_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/inputs/SpinBox/SpinBoxCore.qml")
    helper = _source(
        "prismqml/PrismQML/controls/inputs/SpinBox/_internal/"
        "SpinBoxAutoRepeatTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 300
    assert helper.exists()
    assert len(helper_source.splitlines()) < 70
    assert "SpinBoxInternal.SpinBoxAutoRepeatTimer {" in source
    assert "id: autoRepeatTimer" in source
    assert "spinControl: control" in source
    assert "required property var spinControl" in helper_source
    assert 'objectName: "spinBoxAutoRepeatTimer"' in helper_source
    assert "property bool _inRepeatPhase: false" in helper_source
    assert "interval: _inRepeatPhase" in helper_source
    assert "repeat: _inRepeatPhase" in helper_source
    for marker in (
        "spinControl._repeatCurrentInterval = spinControl.autoRepeatInterval",
        "spinControl._repeatIsUp",
        "spinControl.increase()",
        "spinControl.decrease()",
        "spinControl.autoRepeatMinInterval",
        "Enums.input.spinBoxRepeatAcceleration",
    ):
        assert marker in helper_source
    assert "\n    Timer {\n        id: autoRepeatTimer" not in source


def test_expander_keeps_header_visuals_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/containers/Expander/ExpanderCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/containers/Expander/_internal/"
        "HeaderContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 240
    assert helper.exists()
    assert len(helper_source.splitlines()) < 180
    assert 'import "_internal" as ExpanderInternal' in source
    assert "ExpanderInternal.HeaderContent {" in source
    assert "required property var expanderControl" in helper_source
    assert "property alias titleLabel: titleLabel" in helper_source
    assert "property alias contentLabel: contentLabel" in helper_source
    assert "property alias headerContent: headerContentLoader.sourceComponent" in helper_source
    assert "property alias headerContentLoader: headerContentLoader" in helper_source
    assert "expanderControl.toggled(expanderControl.expanded)" in helper_source

    for marker in (
        "\n        Row {\n            id: headerRow",
        "\n            Column {\n                id: titleCol",
        "\n        Loader {\n            id: headerContentLoader",
        "\n        MouseArea {\n            id: headerArea",
        "\n            Icon {\n                icon: Enums.icon.chevron_down",
    ):
        assert marker not in source


def test_slider_keeps_default_visual_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/Slider/SliderCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/Slider/_internal/"
        "SliderDefaultContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 280
    assert helper.exists()
    assert len(helper_source.splitlines()) < 240
    assert 'import "_internal" as SliderInternal' in source
    assert "SliderInternal.SliderDefaultContent {" in source
    assert "required property var sliderControl" in helper_source
    assert "readonly property bool hovered" in helper_source
    assert "sourceComponent: defaultSliderComponent" in source
    assert "sourceComponent: rangeSliderComponent" in source

    for marker in (
        "\n            MouseArea {\n                id: wheelArea",
        "\n                NeumorphicShadow {\n                    target: track",
        "\n                MouseArea {\n                    id: handleArea",
        "text: control._tipText(control.value)",
    ):
        assert marker not in source


def test_slider_keeps_range_visual_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/Slider/SliderCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/Slider/_internal/"
        "SliderRangeContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 190
    assert helper.exists()
    assert len(helper_source.splitlines()) < 230
    assert 'import "_internal" as SliderInternal' in source
    assert "SliderInternal.SliderRangeContent {" in source
    assert "required property var sliderControl" in helper_source
    assert "readonly property real firstPos" in helper_source
    assert "readonly property real secondPos" in helper_source
    assert "component RangeHandle: Rectangle" in helper_source
    assert "sliderControl.sliderMoved(" in helper_source
    assert "sourceComponent: rangeSliderComponent" in source

    for marker in (
        "\n            RangeHandle {",
        "\n            component RangeHandle:",
        "id: rangeHandleArea",
        "property real firstPos:",
    ):
        assert marker not in source


def test_toggle_keeps_visual_assembly_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/Toggle/Toggle.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/Toggle/_internal/"
        "ToggleContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 210
    assert helper.exists()
    assert len(helper_source.splitlines()) < 180
    assert 'import "_internal" as ToggleInternal' in source
    assert "ToggleInternal.ToggleContent {" in source
    assert "required property var toggleControl" in helper_source
    assert "readonly property bool contentLoaded" in helper_source
    assert "sourceComponent: content.toggleControl._isSubtitle" in helper_source

    for marker in (
        "\n    Row {\n        id: mainRow",
        "\n    Component {\n        id: checkboxIndicator",
        "\n    Component {\n        id: radioIndicator",
        "\n    Component {\n        id: switchIndicator",
        "\n    Component {\n        id: defaultContent",
        "\n    Component {\n        id: subtitleContent",
    ):
        assert marker not in source


def test_stacked_animations_monolith_stays_deleted():
    """堆叠动画只允许经 StackedModeAnimations 按模式加载。

    StackedWidget switched to per-mode backends; the old StackedAnimations.qml
    monolith kept a second full copy of every transition with no consumer. This
    gate keeps it deleted and keeps the mode dispatcher as the only entry.
    """
    internal = _source("prismqml/PrismQML/controls/navigation/_internal")
    monolith = internal / "StackedAnimations.qml"
    dispatcher = internal / "StackedModeAnimations.qml"

    assert not monolith.exists()
    assert dispatcher.exists()

    entry_source = _source(
        "prismqml/PrismQML/controls/navigation/StackedWidget.qml"
    ).read_text(encoding="utf-8")
    assert "StackedModeAnimations {" in entry_source
    assert "StackedAnimations {" not in entry_source

    dispatcher_source = dispatcher.read_text(encoding="utf-8")
    for backend in (
        "StackedFadeAnimations.qml",
        "StackedPopAnimations.qml",
        "StackedSlideAnimations.qml",
        "StackedCardAnimations.qml",
        "StackedZoomAnimations.qml",
    ):
        assert backend in dispatcher_source
        assert (internal / backend).exists()

    assert dispatcher_source.count('"StackedPopAnimations.qml"') == 2
    pop_source = (internal / "StackedPopAnimations.qml").read_text(encoding="utf-8")
    assert "property bool isPopDown: false" in pop_source
    assert "function configure(popDown)" in pop_source
    assert "Easing.OutBounce" in pop_source
    assert "Easing.OutQuad" in pop_source
    assert "StackedPopUpAnimations.qml" not in dispatcher_source
    assert "StackedPopDownAnimations.qml" not in dispatcher_source

    for path in QML_ROOT.rglob("*.qml"):
        assert path.name != "StackedAnimations.qml"
        assert path.name not in {
            "StackedPopUpAnimations.qml",
            "StackedPopDownAnimations.qml",
        }


def test_viewport_detection_has_exactly_one_owner():
    """视口检测算法只允许 ViewportMixin 一处实现, 消费者只能委托。

    Skeleton, ProgressBarImpl and ProgressRingImpl each carried a line-for-line
    copy of the ancestor walk and the in-viewport arithmetic. They now delegate to
    ViewportMixin. This gate blocks a fourth copy from reappearing anywhere in the
    QML tree.
    """
    owner = "prismqml/PrismQML/controls/utils/ViewportMixin.qml"
    consumers = (
        "prismqml/PrismQML/controls/feedback/State/Skeleton.qml",
        "prismqml/PrismQML/controls/feedback/Progress/_internal/"
        "ProgressBarImpl.qml",
        "prismqml/PrismQML/controls/feedback/Progress/_internal/"
        "ProgressRingImpl.qml",
    )

    reimplementers = []
    for path in sorted(QML_ROOT.rglob("*.qml")):
        relative = path.relative_to(ROOT).as_posix()
        source = path.read_text(encoding="utf-8")
        if "function _updateViewport()" in source and relative != owner:
            reimplementers.append(relative)

    assert reimplementers == []

    owner_source = _source(owner).read_text(encoding="utf-8")
    assert "function _updateViewport()" in owner_source
    assert "function _findFlickable()" in owner_source

    for relative in consumers:
        source = _source(relative).read_text(encoding="utf-8")
        assert "ViewportMixin {" in source, relative
        assert "readonly property bool _isInViewport: viewport.isInViewport" in (
            source
        ), relative
        assert "function _findFlickable()" not in source, relative


def test_tree_traversal_has_exactly_one_owner():
    """树遍历算法只允许 ComboBoxTreeNodes.js 一处实现。

    ComboBoxTree and ComboBoxMultiTree each carried an identical node-id scheme,
    search-match rule and walk order, differing only in how a visible row is
    emitted. The walk now lives in one pure library that takes an emit callback.
    """
    owner_path = (
        QML_ROOT / "controls" / "inputs" / "ComboBox" / "_internal"
        / "ComboBoxTreeNodes.js"
    )
    assert owner_path.exists()
    owner_source = owner_path.read_text(encoding="utf-8")

    # Pure shared library, so it must not reach for QML objects.
    # 纯共享库，因此不得触碰 QML 对象。
    assert ".pragma library" in owner_source
    assert "function flatten(" in owner_source
    assert "function hasMatchingDescendants(" in owner_source
    assert "function collectExpandable(" in owner_source
    assert "function toggleExpanded(" in owner_source
    assert "control." not in owner_source
    assert "Qt." not in owner_source

    consumers = (
        "prismqml/PrismQML/controls/inputs/ComboBox/ComboBoxTree.qml",
        "prismqml/PrismQML/controls/inputs/ComboBox/ComboBoxMultiTree.qml",
    )
    for relative in consumers:
        source = _source(relative).read_text(encoding="utf-8")
        assert 'import "_internal/ComboBoxTreeNodes.js" as TreeNodes' in source, (
            relative
        )
        assert "TreeNodes.flatten(" in source, relative
        assert "function _flattenTree(" not in source, relative
        assert "function _hasMatchingDescendants(" not in source, relative

    # No third copy anywhere in the tree. 整棵树不得出现第三份副本。
    reimplementers = []
    for path in sorted(QML_ROOT.rglob("*.qml")):
        source = path.read_text(encoding="utf-8")
        if "function _hasMatchingDescendants(" in source:
            reimplementers.append(path.relative_to(ROOT).as_posix())

    assert reimplementers == []


def test_window_page_stack_has_exactly_one_owner():
    """页面栈与懒加载 overlay 只允许 WindowsPageStack.qml 一处实现。

    WindowsFilled, WindowsSplit and WindowsBarContent each carried the same
    StackedWidget bindings and overlay Loader lifecycle, differing only in the
    navigation id they read, whether the host may be null, and where the loading
    caption comes from. Those three are now parameters on one helper.
    """
    owner = QML_ROOT / "_internal" / "WindowsPageStack.qml"
    assert owner.exists()
    owner_source = owner.read_text(encoding="utf-8")

    for prop in (
        "required property var host",
        "required property bool navAnimationEnabled",
        "required property bool overlayActive",
        "required property string overlayText",
    ):
        assert prop in owner_source, prop
    assert "readonly property alias stackAlias: stack" in owner_source
    assert 'objectName: "loadingOverlayLoader"' in owner_source
    # The loading state machine stays in NavigationWindowLoading.js.
    # loading 状态机仍归 NavigationWindowLoading.js。
    assert "function start(" not in owner_source
    assert "function finish(" not in owner_source

    consumers = (
        "prismqml/PrismQML/_internal/WindowsFilled.qml",
        "prismqml/PrismQML/_internal/WindowsSplit.qml",
        "prismqml/PrismQML/_internal/WindowsBarContent.qml",
    )
    for relative in consumers:
        source = _source(relative).read_text(encoding="utf-8")
        assert "WindowsPageStack {" in source, relative
        assert "property alias stackAlias: pageStack.stackAlias" in source, relative
        # No third copy of the extracted view layer. 不得留下第三份视图层副本。
        assert 'objectName: "loadingOverlayLoader"' not in source, relative
        assert "StackedWidget {" not in source, relative

    # Nothing else in the tree may declare the overlay loader either.
    # 整棵树内不得有其他文件声明该 overlay loader。
    declarers = sorted(
        path.relative_to(ROOT).as_posix()
        for path in QML_ROOT.rglob("*.qml")
        if 'objectName: "loadingOverlayLoader"' in path.read_text(encoding="utf-8")
    )
    assert declarers == ["prismqml/PrismQML/_internal/WindowsPageStack.qml"]


# ==================== ChartMath single ownership 图表统计单一归属 ====================

_CHART_INTERNAL = QML_ROOT / "controls" / "data" / "Chart" / "_internal"
_CHART_MATH = _CHART_INTERNAL / "ChartMath.js"


def test_chart_math_owns_series_statistics():
    """average/findMinMaxIndices 只允许在 ChartMath.js 内实现一次。"""
    source = _CHART_MATH.read_text(encoding="utf-8")
    assert "function average(" in source
    assert "function findMinMaxIndices(" in source
    # Contract: pure maths only, no Canvas/QML/theme coupling. 契约: 只放纯算式。
    # Checked as code, not as prose — the comments above legitimately name these.
    # 按代码而非文字检查, 因为文件注释本身会提到这些词。
    for banned in ("ctx.", "import QtQuick", "Enums.colorPicker", "Enums.chart"):
        assert banned not in source, banned


def test_chart_series_statistics_have_no_second_implementation():
    """除 ChartMath.js 外, 任何 Chart 文件都不得自带这两个算法的循环实现。"""
    for path in sorted(_CHART_INTERNAL.rglob("*")):
        if not path.is_file() or path.suffix not in {".js", ".qml"}:
            continue
        if path == _CHART_MATH:
            continue
        source = path.read_text(encoding="utf-8")
        # The min/max scan and the series-sum loop are the two duplicated shapes.
        # Matched narrowly: XYMultiTooltip.qml legitimately sums one hovered point
        # across series, which is a different computation.
        # 精确匹配: XYMultiTooltip.qml 是对多系列同一悬停点求和, 属不同计算。
        assert "if (values[i] < values[minIdx])" not in source, path.name
        assert "if (values[index] < values[minIdx])" not in source, path.name
        assert "i < values.length; i++) sum += values[i]" not in source, path.name
        assert (
            "index < values.length; index++) sum += values[index]" not in source
        ), path.name


# ==================== ColorPickerHsv single ownership HSV 转换单一归属 ====================

_PICKER_INTERNAL = QML_ROOT / "controls" / "inputs" / "ColorPicker" / "_internal"
_PICKER_HSV = _PICKER_INTERNAL / "ColorPickerHsv.js"
_PICKER_DIALOG = _PICKER_INTERNAL / "ColorPickerDialog.qml"
_PICKER_DROPDOWN = _PICKER_INTERNAL / "ColorPickerDropdown.qml"


def test_color_picker_hsv_owns_conversion():
    """decompose/compose 只允许在 ColorPickerHsv.js 内实现一次, 且保持纯函数。"""
    source = _PICKER_HSV.read_text(encoding="utf-8")
    assert "function decompose(" in source
    assert "function compose(" in source
    # The hue floor must stay a caller-supplied parameter, never an Enums read
    # or a magic number here. 色相下限必须由调用方传入, 本文件不得读 Enums 或写魔数。
    assert "achromaticHue" in source
    assert "Enums." not in source
    for banned in ("import QtQuick", "signal ", "Component.onCompleted"):
        assert banned not in source, banned


def test_color_picker_consumers_delegate_hsv_conversion():
    """两处消费者都必须转发给 helper, 不得自带 HSV 读写。"""
    for path in (_PICKER_DIALOG, _PICKER_DROPDOWN):
        source = path.read_text(encoding="utf-8")
        assert 'import "ColorPickerHsv.js" as Hsv' in source, path.name
        assert "Hsv.decompose(" in source, path.name
        assert "Hsv.compose(" in source, path.name
        # No second copy of the state conversion. Presentation-only Qt.hsva calls
        # (spectrum GradientStop) are untouched on purpose.
        # 不得有第二份状态换算。呈现用的 Qt.hsva（色谱渐变）有意不动。
        assert "selectedColor = Qt.hsva(" not in source, path.name
        assert "selectedColor.hsvHue" not in source, path.name
        assert "selectedColor.hsvSaturation" not in source, path.name
        # The floor stays an Enums token at the call site, not a literal.
        assert "Enums.opacityLevel.invisible" in source, path.name


def test_color_picker_notification_and_alpha_asymmetry_preserved():
    """两处的通知契约与 alpha 回读差异是有意的, 门禁锁住不许被 helper 吞掉。"""
    dialog = _PICKER_DIALOG.read_text(encoding="utf-8")
    dropdown = _PICKER_DROPDOWN.read_text(encoding="utf-8")
    # Distinct signals. 各自的信号名。
    assert "colorUpdated(selectedColor)" in dialog
    assert "colorChanged(selectedColor)" in dropdown
    # Dialog reads alpha back into its own integer range; dropdown must not.
    # 对话框把 alpha 回读到自己的整数区间; 下拉不回读。
    assert "hsv.alpha" in dialog
    assert "hsv.alpha" not in dropdown
