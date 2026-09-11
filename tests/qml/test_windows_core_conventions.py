# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Domain bucket 1/2 of the former test_windows_core_conventions.py."""
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

def test_windows_core_top_left_and_qml_shadow_geometry(monkeypatch, qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    (
        engine,
        component,
        window,
        content,
        left_probe,
        warnings,
        startup_events,
    ) = _create_scene(monkeypatch)
    try:
        icon_event = "icon"
        assert _wait_for(lambda: startup_events.count(icon_event) == 2)
        first_icon_index = startup_events.index(icon_event)
        native_index = startup_events.index("native-finalized")
        second_icon_index = len(startup_events) - 1 - startup_events[::-1].index(
            icon_event
        )
        assert first_icon_index < native_index < second_icon_index
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
    (
        engine,
        component,
        window,
        content,
        left_probe,
        warnings,
        _startup_events,
    ) = _create_scene(monkeypatch)
    try:
        assert not window.property("_resizeHandlesReady")
        assert _wait_for(lambda: bool(window.property("_resizeHandlesReady")))
        assert _wait_for(lambda: len(_resize_areas(window)) == 8)
        resize_areas = _resize_areas(window)
        assert len(resize_areas) == 8
        # Edges plus the four corners so diagonal resize works.
        # 四条边加四个角落，保证对角线缩放可用。
        expected_edges = sorted(
            int(edge.value)
            for edge in (
                Qt.Edge.LeftEdge,
                Qt.Edge.RightEdge,
                Qt.Edge.TopEdge,
                Qt.Edge.BottomEdge,
                Qt.Edge.LeftEdge | Qt.Edge.TopEdge,
                Qt.Edge.RightEdge | Qt.Edge.TopEdge,
                Qt.Edge.LeftEdge | Qt.Edge.BottomEdge,
                Qt.Edge.RightEdge | Qt.Edge.BottomEdge,
            )
        )
        edge_values = sorted(int(area.property("edge")) for area in resize_areas)
        assert edge_values == expected_edges
        corners = {
            int(Qt.Edge.LeftEdge.value | Qt.Edge.TopEdge.value),
            int(Qt.Edge.RightEdge.value | Qt.Edge.TopEdge.value),
            int(Qt.Edge.LeftEdge.value | Qt.Edge.BottomEdge.value),
            int(Qt.Edge.RightEdge.value | Qt.Edge.BottomEdge.value),
        }
        assert corners.issubset(set(edge_values))
        _pump(window.property("resizeDelay") // 4)
        assert len(_resize_areas(window)) == 8
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []

def test_windows_core_right_title_chrome_is_layout_scoped(monkeypatch, qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    (
        engine,
        component,
        window,
        _content,
        _left_probe,
        warnings,
        _startup_events,
    ) = _create_scene(monkeypatch)
    try:
        loader = window.findChild(QObject, "rightTitleChromeLoader")
        assert loader is not None
        assert not loader.property("active")
        assert window.findChild(QObject, "rightTitleChrome") is None

        window.setProperty("titleBarPosition", window.property("leftLayout"))
        chrome = window.findChild(QQuickItem, "rightTitleChrome")
        buttons = window.findChild(QQuickItem, "captionButtonsRight")
        drag_area = window.findChild(QQuickItem, "rightTitleBarDragArea")
        assert chrome is not None and buttons is not None and drag_area is not None
        assert buttons.x() == pytest.approx(
            window.width() - window.property("captionButtonWidth") * 3
        )
        assert drag_area.x() == pytest.approx(
            max(
                window.property("leftPanelWidth"),
                window.property("navPanelMinWidth"),
            )
            + window.property("dividerWidth")
        )
        assert drag_area.width() == pytest.approx(buttons.x() - drag_area.x())

        maximize_center = buttons.mapToItem(
            window.contentItem(),
            QPointF(
                window.property("captionButtonWidth") * 1.5,
                window.property("captionButtonHeight") / 2,
            ),
        )
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(maximize_center.x()), round(maximize_center.y())),
        )
        assert _wait_for(
            lambda: window.visibility() == QWindow.Visibility.Maximized
        )
        window.showNormal()
        assert _wait_for(lambda: window.visibility() == QWindow.Visibility.Windowed)

        window.setProperty("titleBarPosition", window.property("topLayout"))
        assert _wait_for(
            lambda: window.findChild(QObject, "rightTitleChrome") is None
        )
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []

@pytest.mark.parametrize("initial_left_layout", [False, True])
def test_windows_core_generic_caption_action_uses_system_button_slot(
    monkeypatch, qapp, initial_left_layout
):
    """The host-defined action stays immediately before system buttons.

    宿主定义的通用动作必须固定在系统按钮之前,且点击只发通用信号。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    (
        engine,
        component,
        window,
        _content,
        _left_probe,
        warnings,
        _startup_events,
    ) = _create_scene(monkeypatch, initial_left_layout=initial_left_layout)
    try:
        window.setProperty("captionActionIcon", "Bot")
        window.setProperty("captionActionToolTip", "AI")
        window.setProperty("captionActionVisible", True)
        window.setProperty("captionActionEnabled", True)
        _pump()

        row_name = "captionButtonsRight" if initial_left_layout else "captionButtonsTop"
        row = window.findChild(QQuickItem, row_name)
        action = window.findChild(QQuickItem, "captionActionButton")
        assert row is not None and action is not None
        assert action.property("icon") == "Bot"
        assert action.property("toolTipText") == "AI"
        assert action.property("actionEnabled") is True
        assert action.isVisible()
        assert action.width() == pytest.approx(window.property("captionButtonWidth"))
        assert action.x() == pytest.approx(0)
        assert row.width() == pytest.approx(window.property("_captionControlsWidth"))

        trigger_count = []
        window.captionActionTriggered.connect(lambda: trigger_count.append(True))
        center = action.mapToItem(
            window.contentItem(),
            QPointF(action.width() / 2, action.height() / 2),
        )
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(center.x()), round(center.y())),
        )
        assert _wait_for(lambda: len(trigger_count) == 1)

        window.setProperty("captionActionEnabled", False)
        _pump()
        assert action.property("actionEnabled") is False
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(center.x()), round(center.y())),
        )
        _pump()
        assert len(trigger_count) == 1

        window.setProperty("captionActionVisible", False)
        _pump()
        assert not action.isVisible()
        assert row.width() == pytest.approx(
            window.property("captionButtonWidth") * 3
        )
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []

def test_windows_core_initial_left_title_chrome_is_ready(monkeypatch, qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    (
        engine,
        component,
        window,
        _content,
        _left_probe,
        warnings,
        _startup_events,
    ) = _create_scene(monkeypatch, initial_left_layout=True)
    try:
        loader = window.findChild(QObject, "rightTitleChromeLoader")
        assert loader is not None and loader.property("active")
        assert window.findChild(QObject, "rightTitleChrome") is not None
        assert window.findChild(QObject, "captionButtonsRight") is not None
        assert window.findChild(QObject, "rightTitleBarDragArea") is not None
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []

@pytest.mark.parametrize(
    ("initial_left_layout", "drag_area_name"),
    (
        (False, "topTitleBarDragArea"),
        (True, "leftTitleBarDragArea"),
        (True, "rightTitleBarDragArea"),
    ),
)
def test_windows_core_titlebar_double_click_routes_native_transition(
    monkeypatch, qapp, initial_left_layout, drag_area_name
):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    (
        engine,
        component,
        window,
        _content,
        _left_probe,
        warnings,
        startup_events,
    ) = _create_scene(
        monkeypatch, initial_left_layout=initial_left_layout
    )
    try:
        drag_area = window.findChild(QQuickItem, drag_area_name)
        assert drag_area is not None, drag_area_name

        def double_click_drag_area():
            center = drag_area.mapToItem(
                window.contentItem(),
                QPointF(drag_area.width() / 2, drag_area.height() / 2),
            )
            QTest.mouseDClick(
                window,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                QPoint(round(center.x()), round(center.y())),
            )

        double_click_drag_area()
        assert _wait_for(
            lambda: window.visibility() == QWindow.Visibility.Maximized
        )
        double_click_drag_area()
        assert _wait_for(
            lambda: window.visibility() == QWindow.Visibility.Windowed
        )
        assert startup_events.count("native-maximize") == 1
        assert startup_events.count("native-restore") == 1
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []

def test_windows_core_native_close_reuses_lazy_circle_exit_animation(monkeypatch, qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    (
        engine,
        component,
        window,
        _content,
        _left_probe,
        warnings,
        _startup_events,
    ) = _create_scene(monkeypatch)
    try:
        assert _wait_for(
            lambda: window.opacity() == pytest.approx(1)
            and window.property("_animOpacity") == pytest.approx(1)
            and window.property("_animScale") == pytest.approx(1)
        )

        transition = window.findChild(QObject, "windowClosePageTransition")
        assert transition is not None
        assert transition.property("animationType") == 7

        # The first native/QWindow close leaves the current onClosing delivery,
        # then reuses PageTransition before the accepted close.
        # 首次原生/QWindow 关闭退出当前 onClosing 分发, 再复用 PageTransition 后真实关闭。
        assert window.close() is False
        assert window.property("_closeInProgress") is True
        assert window.property("nativeCloseAcceptedCount") == 0

        assert _wait_for(
            lambda: window.property("nativeCloseAcceptedCount") == 1
            and not window.isVisible(),
            timeout_ms=500,
        )
        assert window.opacity() == pytest.approx(1)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []

def test_windows_core_close_collapse_reaches_zero_radius_before_teardown(
    monkeypatch, qapp
):
    """退场必须收紧到零半径才移除窗口，且中途不得跳步。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    (
        engine,
        component,
        window,
        _content,
        _left_probe,
        warnings,
        _startup_events,
    ) = _create_scene(monkeypatch)
    try:
        transition = window.findChild(QObject, "windowClosePageTransition")
        assert transition is not None

        # The exit must not inherit the page-switch collapse pacing.
        # 退场不得沿用页面切换的收紧节奏。
        page_cover_duration = 300
        assert transition.property("coverDuration") > page_cover_duration
        assert transition.property("coverEasing") == int(
            QEasingCurve.Type.InOutQuad.value
        )

        # Offscreen presents almost no frames during the collapse, so the
        # per-frame trajectory is not observable here; assert the ordering
        # invariant instead and leave pacing to the visible D3D11 probe
        # (scripts/manual/window_close_collapse_probe.py). offscreen 在收紧
        # 期间几乎不上屏, 逐帧轨迹在此不可观测; 这里只断言时序不变量, 节奏交给
        # 可见 D3D11 探针验收。
        collapse_endpoints = []
        transition.collapseFinished.connect(
            lambda: collapse_endpoints.append(
                (
                    float(transition.property("progress")),
                    float(transition.property("revealRadiusPixels")),
                    bool(window.isVisible()),
                )
            )
        )
        visibility_progress = []
        window.visibleChanged.connect(
            lambda: visibility_progress.append(
                (
                    bool(window.isVisible()),
                    float(transition.property("progress")),
                )
            )
        )

        assert window.close() is False
        assert _wait_for(
            lambda: window.property("nativeCloseAcceptedCount") == 1
            and not window.isVisible(),
            timeout_ms=2000,
        )

        # The collapse must finish at the zero endpoint, and it must finish
        # while the window is still on screen. 收紧必须走到零终点, 且必须在窗口
        # 仍在屏上时完成。
        assert collapse_endpoints
        end_progress, end_radius, visible_at_end = collapse_endpoints[-1]
        assert end_progress == pytest.approx(0, abs=1e-6)
        assert end_radius == pytest.approx(0, abs=1e-6)
        assert visible_at_end is True
        # Teardown may only happen after the collapse reached zero.
        # 只有收紧到零之后才允许移除窗口。
        hide_events = [
            progress for visible, progress in visibility_progress if not visible
        ]
        assert hide_events
        assert hide_events[-1] == pytest.approx(0, abs=1e-6)
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []

def test_windows_core_close_collapse_clips_unmasked_shadow_layer(monkeypatch, qapp):
    """收紧期间必须撤掉未被遮罩的阴影层，否则圆外残留矩形留白。"""
    windows_before = tuple(QGuiApplication.topLevelWindows())
    (
        engine,
        component,
        window,
        _content,
        _left_probe,
        warnings,
        _startup_events,
    ) = _create_scene(monkeypatch)
    try:
        # The QML shadow host is a sibling of the masked frame layer, so the
        # close circle's layer effect never clips it. It fills the window with
        # an opaque windowColor rect, which shows through as a rectangular
        # blank once the circle shrinks past it.
        # QML 阴影宿主是被遮罩帧层的兄弟节点, 关闭圆环的 layer effect 裁不到它。它
        # 以不透明 windowColor 矩形铺满窗口, 圆收过去后就露成矩形留白。
        shadow_host = window.findChild(QObject, "windowQmlShadowHost")
        assert shadow_host is not None
        # The scene defaults to the native shadow, which leaves this host
        # inactive and would make the assertion below vacuous. Force the QML
        # shadow so the unmasked layer really exists.
        # 场景默认走原生阴影, 该宿主不激活, 下面的断言会变成空断言。强制 QML 阴影,
        # 让未遮罩层真实存在。
        window.setProperty("shadowMode", _WINDOW_SHADOW_MODE_QML)
        assert _wait_for(lambda: shadow_host.property("active") is True)

        transition = window.findChild(QObject, "windowClosePageTransition")
        assert transition is not None

        samples = []

        def _sample():
            samples.append(
                (
                    float(transition.property("progress")),
                    bool(shadow_host.property("active")),
                )
            )

        sampler = QTimer()
        sampler.setInterval(8)
        sampler.timeout.connect(_sample)
        sampler.start()

        assert window.close() is False
        assert _wait_for(
            lambda: window.property("nativeCloseAcceptedCount") == 1
            and not window.isVisible(),
            timeout_ms=2000,
        )
        sampler.stop()

        # Every sample taken while the circle was still open must show the
        # unmasked layer already gone. The close-state rewind reactivates the
        # host once the collapse reaches zero so the window can close again
        # later; those post-zero samples are expected and excluded by progress.
        # 圆尚未收完时的每个采样都必须显示未遮罩层已经撤掉。关闭状态复位会在收紧
        # 归零之后重新激活宿主, 使窗口之后仍可再次关闭; 这些归零后的采样属预期,
        # 用 progress 排除。
        assert samples
        during_collapse = [
            (progress, active) for progress, active in samples if progress > 0.0
        ]
        assert during_collapse
        still_active = [
            progress for progress, active in during_collapse if active
        ]
        assert still_active == []
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []

def test_windows_core_close_collapse_easing_spreads_motion_evenly():
    """收紧缓动必须把运动均匀分布，不得把大半距离压到末尾几帧。"""
    frame_count = 12
    # The curve replaced everywhere, kept here as the contrast case.
    # 已被全面替换掉的曲线, 保留作对照。
    rejected = QEasingCurve(QEasingCurve.Type.InCubic)
    shared = QEasingCurve(QEasingCurve.Type.InOutQuad)

    def _radius_series(curve):
        # progress runs 1 -> 0, radius scales with progress.
        # progress 由 1 走到 0, 半径随 progress 线性缩放。
        return [
            1.0 - curve.valueForProgress(index / (frame_count - 1))
            for index in range(frame_count)
        ]

    def _max_step(series):
        return max(
            earlier - later for earlier, later in zip(series, series[1:])
        )

    def _half_at(series):
        return next(
            index / (frame_count - 1)
            for index, radius in enumerate(series)
            if radius <= 0.5
        )

    rejected_series = _radius_series(rejected)
    shared_series = _radius_series(shared)

    # The rejected curve reaches half radius only near the very end, leaving the
    # whole second half to the last frames. 被弃用的曲线直到接近末尾才收到半径
    # 一半, 把后半程全部压给最后几帧。
    assert _half_at(rejected_series) > 0.7
    assert _half_at(shared_series) == pytest.approx(0.5, abs=0.1)
    assert _max_step(shared_series) < _max_step(rejected_series)
    assert _max_step(shared_series) < 0.2

def test_windows_core_close_accepts_custom_page_transition(monkeypatch, qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    (
        engine,
        component,
        window,
        _content,
        _left_probe,
        warnings,
        _startup_events,
    ) = _create_scene(monkeypatch, custom_close=True)
    try:
        transition = window.findChild(QObject, "windowClosePageTransition")
        assert transition is not None
        assert transition.property("animationType") == 8
        assert window.property("customCollapseCount") == 0

        assert window.close() is False
        assert _wait_for(
            lambda: window.property("customCollapseCount") == 1
            and window.property("nativeCloseAcceptedCount") == 1
            and not window.isVisible(),
            timeout_ms=500,
        )
        # PageTransition stops any previous operation before starting collapse.
        # PageTransition 会先停止已有操作, 再开始本次收紧。
        assert window.property("customStopCount") == 1
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []

def test_windows_core_close_accepts_none_transition(monkeypatch, qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    (
        engine,
        component,
        window,
        _content,
        _left_probe,
        warnings,
        _startup_events,
    ) = _create_scene(monkeypatch, none_close=True)
    try:
        transition = window.findChild(QObject, "windowClosePageTransition")
        assert transition is not None
        assert transition.property("animationType") == window.property(
            "noneAnimationType"
        )

        assert window.close() is False
        assert window.property("nativeCloseAcceptedCount") == 0
        assert _wait_for(
            lambda: window.property("nativeCloseAcceptedCount") == 1
            and not window.isVisible(),
            timeout_ms=500,
        )
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []
