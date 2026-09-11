# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Domain bucket 1/7 of the former test_qml_architecture.py."""
import pytest  # noqa: F401
from qml_architecture_shared import *
from qml_architecture_shared import (
    _source,
    _declaration_indent,
    _assert_modularized,
    _CHART_INTERNAL,
    _CHART_MATH,
    _PICKER_INTERNAL,
    _PICKER_HSV,
    _PICKER_DIALOG,
    _PICKER_DROPDOWN,
)

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

    assert len(source.splitlines()) < 500
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

    assert len(source.splitlines()) <= 500
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
