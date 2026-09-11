# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Domain bucket 2/2 of the former test_windows_core_conventions.py."""
import pytest  # noqa: F401
from windows_core_conventions_shared import *
from windows_core_conventions_shared import (
    _WINDOW_SHADOW_MODE_QML,
    _FakeNativeWindow,
    _FakeWindowHelper,
    _pump,
    _wait_for,
    _visual_descendants,
    _resize_areas,
    _new_visible_windows,
    _create_scene,
    _dispose_scene,
)

def test_windows_core_source_conventions_and_timing_tokens():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    frame_source = WINDOW_FRAME_PATH.read_text(encoding="utf-8")
    resize_timer_source = RESIZE_HANDLES_TIMER_PATH.read_text(encoding="utf-8")
    drag_handle_source = WINDOW_DRAG_HANDLE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    assert "WindowsResizeHandlesTimer {" in source
    assert "id: _resizeHandlesTimer" in source
    assert "host: window" in source
    assert "\n    Timer {" not in source
    assert "Timer {" in resize_timer_source
    assert "required property var host" in resize_timer_source
    assert "interval: Enums.window.resizeHandlesDelayMs" in resize_timer_source
    assert "host._resizeHandlesReady = true" in resize_timer_source
    assert "_animationStartTimer" not in source
    assert "interval: 100" not in source
    assert "interval: 1200" not in source
    assert "window.showMaximized()" not in source
    assert "window.showNormal()" not in source
    assert "WindowsCoreFrame {" in source
    assert "WindowDragHandle {" not in source
    window_frame_index = frame_source.index("id: windowFrame")
    window_ticket_paper_index = frame_source.index(
        'objectName: "windowTicketPaper"'
    )
    title_bar_index = frame_source.index("id: titleBar")
    assert window_frame_index < window_ticket_paper_index < title_bar_index
    assert "TicketPaper {" in frame_source[
        window_frame_index:title_bar_index
    ]
    assert frame_source.count("WindowDragHandle {") == 3
    assert "window.startSystemMove()" not in source
    assert "property bool enableDrag: true" in drag_handle_source
    assert "property bool _doubleClickPending: false" in drag_handle_source
    assert "onDoubleClicked:" in drag_handle_source
    assert "onReleased: root._applyPendingDoubleClick()" in drag_handle_source
    assert "NativeWindow.requestMaximize(win)" in drag_handle_source
    assert "NativeWindow.requestRestore(win)" in drag_handle_source
    profile_start = source.index("function profileTime(msg)")
    profile_end = source.index("function profileDetail(msg)", profile_start)
    assert "if (!_startupProfilingVerboseActive) return" in source[
        profile_start:profile_end
    ]
    metrics = METRICS_PATH.read_text(encoding="utf-8")
    assert "readonly property int resizeHandlesDelayMs: 1200" in metrics

def test_leaf_startup_diagnostics_do_not_attach_to_default_object_tree():
    windows_core = SOURCE_PATH.read_text(encoding="utf-8")
    assert "function profileDetail(msg)" in windows_core
    assert "Component.onCompleted: window.profileDetail" not in windows_core
    assert "profileTarget" not in windows_core

    for source_path in STARTUP_DIAGNOSTIC_PATHS:
        source = source_path.read_text(encoding="utf-8")
        assert "profileDetail" not in source, source_path
        assert "profileTarget" not in source, source_path

    builder = WINDOW_BUILDER_PATH.read_text(encoding="utf-8")
    assert "profileDetail" not in builder

def test_window_animation_helper_source_conventions_and_dead_paths():
    source = ANIMATION_HELPER_PATH.read_text(encoding="utf-8")
    close_frame_waiter_source = WINDOW_CLOSE_FRAME_WAITER_PATH.read_text(
        encoding="utf-8"
    )
    path = PurePosixPath(ANIMATION_HELPER_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    assert "animatedMinimizeWithForward" not in source
    assert "handleVisibilityChange" not in source
    assert "WindowCloseDissolve" not in source
    assert "closeEffectLoader" not in source
    assert "prewarmCloseAnimation" not in source
    assert "animatedClose" not in source
    assert "animHelper.handleVisibilityChange" not in SOURCE_PATH.read_text(
        encoding="utf-8"
    )
    windows_core_source = SOURCE_PATH.read_text(encoding="utf-8")
    assert 'import "./controls/navigation"' in windows_core_source
    assert "property int closeAnimationType: Enums.lazyAnimation.lazy_circle" in windows_core_source
    assert "property Component closeAnimation: null" in windows_core_source
    assert "property bool _closeSourceWasVisible: true" in windows_core_source
    assert "property bool _closeCompletionPending: false" in windows_core_source
    assert "PageTransition {" in windows_core_source
    assert 'objectName: "windowClosePageTransition"' in windows_core_source
    assert "animationType: window.closeAnimationType" in windows_core_source
    assert "customAnimation: window.closeAnimation" in windows_core_source
    # The aperture closes to the center unconditionally now, so the exit must not
    # pin an opt-in for it. 光圈现在无条件收紧到中心, 因此退场不得再钉死开关。
    assert "collapseToCenter" not in windows_core_source
    # The collapse pacing is shared with page switch, so the exit must inherit
    # the facade default rather than pin its own duration or easing. Measured on
    # a real display, both sites produce identical pacing.
    # 收紧节奏与页面切换共用, 因此退场应继承门面默认值, 不得自己钉死时长或缓动。
    # 真机实测两处节奏完全相同。
    assert "coverDuration:" not in windows_core_source
    assert "coverEasing:" not in windows_core_source
    assert "closeTransition.collapse(windowFrameLayer)" in windows_core_source
    assert "windowFrameLayer.visible = _closeSourceWasVisible" in windows_core_source
    assert "Qt.callLater(window._armAcceptedClose)" in windows_core_source
    assert "function _handleCloseFrameEnd()" in windows_core_source
    assert "closeFrameWaiter.arm()" in windows_core_source
    waiter_path = PurePosixPath(
        WINDOW_CLOSE_FRAME_WAITER_PATH.relative_to(ROOT).as_posix()
    )
    waiter_violations = scan_source_text(close_frame_waiter_source, waiter_path)
    assert [
        violation
        for violation in waiter_violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    assert "function onAfterFrameEnd()" in close_frame_waiter_source
    assert "Timer {" not in close_frame_waiter_source
    assert "interval:" not in close_frame_waiter_source
    assert "animHelper.animatedClose()" not in windows_core_source

def test_window_close_dissolve_artifacts_and_api_are_removed():
    assert [path for path in REMOVED_CLOSE_EFFECT_PATHS if path.exists()] == []
    windows_core_source = SOURCE_PATH.read_text(encoding="utf-8")
    caption_source = CAPTION_BUTTON_PATH.read_text(encoding="utf-8")
    metrics_source = METRICS_PATH.read_text(encoding="utf-8")
    enums_source = ENUMS_PATH.read_text(encoding="utf-8")
    assert "prewarmCloseAnimation" not in windows_core_source
    assert "prewarmCloseAnimation" not in caption_source
    assert "windowCloseMetrics" not in enums_source
    assert "readonly property QtObject windowClose" not in metrics_source

def test_window_leaf_source_conventions_and_icon_delay_token():
    for source_path in WINDOW_LEAF_PATHS:
        source = source_path.read_text(encoding="utf-8")
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations = scan_source_text(source, path)
        assert [
            violation
            for violation in violations
            if violation.rule in {"QML008", "QML009"}
        ] == []
    window_icon = (
        ROOT / "prismqml" / "PrismQML" / "_internal" / "WindowIcon.qml"
    ).read_text(encoding="utf-8")
    icon_timer = WINDOW_ICON_DEFERRED_TIMER_PATH.read_text(encoding="utf-8")
    icon_timer_path = PurePosixPath(
        WINDOW_ICON_DEFERRED_TIMER_PATH.relative_to(ROOT).as_posix()
    )
    icon_timer_violations = scan_source_text(icon_timer, icon_timer_path)
    assert [
        violation
        for violation in icon_timer_violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
    assert "WindowIconDeferredLoadTimer {" in window_icon
    assert "host: root" in window_icon
    assert "\n    Timer {" not in window_icon
    assert "onTriggered: {" not in window_icon
    assert "required property var host" in icon_timer
    assert 'objectName: "windowIconDeferredLoadTimer"' in icon_timer
    assert "interval: Enums.window.iconDeferredLoadDelayMs" in icon_timer
    assert "repeat: false" in icon_timer
    assert "onTriggered: host._deferredLoadReady = true" in icon_timer
    assert "interval: 1" not in window_icon
    metrics = METRICS_PATH.read_text(encoding="utf-8")
    assert "readonly property int iconDeferredLoadDelayMs: 1" in metrics

def test_windows_core_close_animates_in_overlay_window_not_by_dropping_dwm_effects():
    """关闭收紧必须在覆盖窗口里跑, 且禁止为此撤掉 hwnd 级 DWM 效果。

    真机 A/B 隔离过: --drop=mica 会闪一帧, --drop=none/host/shadow 都不闪。写
    DWMWA_SYSTEMBACKDROP_TYPE 让 DWM 在 QML 重绘之前可见地重新合成, QML 侧无论怎么
    排序都盖不住 —— 所以"撤掉 Mica 好让遮罩裁到外围"这条路本身就是闪烁的来源。

    正解是根本不在主窗口里遮罩: 收紧改在覆盖窗口(无 Mica、Qt.NoFluentShadowWindowHint)
    里跑, 主窗口在遮罩帧上屏后以 opacity 藏掉。这条门禁锁住那个开关, 并挡住撤除方案
    以任何形式回来 —— 它在 offscreen 测试里不会复现, 只在真机上闪。
    """
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "preferOverlayWindow: true" in source

    # The drop-based approach and its scaffolding must stay gone.
    # 撤除方案及其脚手架必须保持删除状态。
    for banned in (
        "closeCollapseStateChanged",
        "_setNativeShadowForClose",
        "NavigationMicaCloseBackdrop",
    ):
        assert banned not in source, f"WindowsCore.qml 又出现撤除方案残留: {banned}"

    # Shadow mode switching and the dwmShadow config handler legitimately toggle the native
    # shadow; only the close path must not. Scope the check to the close functions.
    # 阴影模式切换与 dwmShadow 配置响应本就该切原生阴影, 只有关闭路径不许。把检查限定在
    # 关闭相关函数内。
    for function_name in ("_startAcceptedClose", "_cancelCloseRequest"):
        body = source.split(f"function {function_name}")[1].split("\n    function ")[0]
        assert "ShadowManager" not in body, (
            f"{function_name} 又在动原生阴影: 那是真机实测过的闪烁源"
        )
        assert "MicaManager" not in body, f"{function_name} 又在动 Mica"

    navigation = (ROOT / "prismqml" / "PrismQML" / "NavigationWindowCore.qml").read_text(
        encoding="utf-8"
    )
    for banned in ("closeCollapseStateChanged", "NavigationMicaCloseBackdrop"):
        assert banned not in navigation, f"NavigationWindowCore.qml 残留: {banned}"
    assert not (
        ROOT / "prismqml" / "PrismQML" / "_internal" / "NavigationMicaCloseBackdrop.js"
    ).exists()

def test_overlay_window_path_hides_host_and_restores_it_only_after_close():
    """覆盖窗口那条路必须藏住宿主窗口, 且只在关闭成功后才还原。

    只藏源项不够: 宿主窗口仍带着 hwnd 级 Mica 和原生阴影, 它们画在覆盖窗遮罩之外,
    搬到覆盖窗这件事就白做了。两个顺序坑:

    1. 用 opacity 而非 visible=false —— 后者拆掉场景图, 而那个场景图还在驱动覆盖窗动画
    2. 还原必须等 window.close() 成功之后 —— 早一点就露出一帧完整的、没收紧的窗口
    """
    backend = (
        ROOT
        / "prismqml"
        / "PrismQML"
        / "controls"
        / "navigation"
        / "_internal"
        / "LazyPageCircleTransition.qml"
    ).read_text(encoding="utf-8")

    # The switch must gate the in-window branch, or _hostWindow being always set for a
    # window-hosted transition means the overlay branch is unreachable.
    # 开关必须门控窗口内分支, 否则窗口内过渡的 _hostWindow 恒有值, 覆盖窗分支不可达。
    assert "if (transition._hostWindow && !transition.preferOverlayWindow) {" in backend
    assert "host.opacity = Enums.opacityLevel.invisible" in backend
    assert "visible = false" not in backend.split("_hideHostWindowForOverlay")[1].split(
        "function _restoreHostWindowAfterOverlay"
    )[0]

    source = SOURCE_PATH.read_text(encoding="utf-8")
    completed = source.split("function _completeAcceptedClose")[1].split("function ")[0]
    close_index = completed.index("window.close()")
    restore_index = completed.index("closeTransition.restoreHostWindow()")
    assert close_index < restore_index, (
        "还原必须在 window.close() 之后, 否则会露出一帧完整的未收紧窗口"
    )
