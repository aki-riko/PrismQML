# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Domain bucket 1/1 of the former test_root_navigation_conventions.py."""
import pytest  # noqa: F401
from root_navigation_conventions_shared import *
from root_navigation_conventions_shared import (
    _pump,
    _wait_for,
    _descendants,
    _component_items,
    _indicator_visual,
    _item_with_text,
    _toggle_item,
    _direct_text_item,
    _marquee_item,
    _object_named,
    _click_item,
    _send_wheel,
    _new_visible_windows,
    _create_scene,
    _create_hidden_items_scene,
    _create_scroll_fade_scene,
    _top_flickable,
    _viewport_items,
    _viewport_opacities,
    _scroll_rail,
    _assert_rail_reveals_on_hover,
    _drag_viewport,
    _tap_second_item,
    _viewport_widths,
    _create_long_title_scene,
    _dispose_scene,
)

def test_navigation_view_routes_expand_and_real_click(navigation_scene):
    window, items, warnings, windows_before = navigation_scene
    view = items["navigationView"]
    clicked = []
    bottom_clicked = []
    expanded = []
    current_keys = []
    view.itemClicked.connect(lambda index: (clicked.append(index), view.setProperty("currentIndex", index)))
    view.bottomItemClicked.connect(bottom_clicked.append)
    view.aboutToExpand.connect(lambda: expanded.append(True))
    view.currentItemUpdated.connect(current_keys.append)

    assert window.property("viewCompact")
    assert not window.property("viewExpanded")
    assert QMetaObject.invokeMethod(window, "expandView")
    assert window.property("viewExpanded")
    assert expanded == [True]
    assert QMetaObject.invokeMethod(window, "expandView")
    assert expanded == [True]
    assert QMetaObject.invokeMethod(window, "collapseView")
    assert not window.property("viewExpanded")
    assert QMetaObject.invokeMethod(window, "toggleView")
    assert window.property("viewExpanded")
    assert expanded == [True, True]

    profile = _item_with_text(view, "NavigationViewItem", "Profile")
    _click_item(window, profile)
    assert _wait_for(lambda: clicked == [1])
    assert view.property("currentIndex") == 1
    assert window.property("viewCurrentKey") == "profile"
    assert current_keys[-1] == "profile"

    settings = _item_with_text(view, "NavigationViewItem", "Settings")
    _click_item(window, settings)
    assert _wait_for(lambda: bottom_clicked == [0])

    assert QMetaObject.invokeMethod(window, "addViewDynamic")
    assert window.property("viewModelCount") == 4
    assert view.widget("dynamic") is not None
    assert QMetaObject.invokeMethod(window, "selectViewProfile")
    assert view.property("currentIndex") == 1
    assert QMetaObject.invokeMethod(window, "removeViewDynamic")
    assert window.property("viewModelCount") == 3
    assert view.widget("dynamic") is None
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []

def test_navigation_bar_and_toggle_indicator_geometry(navigation_scene):
    window, items, warnings, windows_before = navigation_scene
    bar = items["navigationBar"]
    toggle = items["toggleNavigationBar"]
    bar_clicked = []
    toggle_clicked = []
    bar.itemClicked.connect(lambda index: (bar_clicked.append(index), bar.setProperty("currentIndex", index)))
    toggle.itemClicked.connect(toggle_clicked.append)

    bar_indicator = _component_items(bar, "SlidingIndicator")[0]
    bar_visual = _indicator_visual(bar_indicator)
    initial_y = bar_visual.y()
    three = _item_with_text(bar, "NavigationBarItem", "Three")
    _click_item(window, three)
    assert _wait_for(lambda: bar_clicked == [2])
    assert _wait_for(lambda: bar_visual.y() != pytest.approx(initial_y))

    flickable = next(
        item
        for item in _descendants(bar)
        if "QQuickFlickable" in item.metaObject().className()
    )
    before_scroll_y = bar_visual.y()
    flickable.setProperty("contentY", 30.0)
    assert _wait_for(lambda: bar_visual.y() < before_scroll_y)

    beta = _toggle_item(toggle, "Beta")
    _click_item(window, beta)
    assert _wait_for(lambda: toggle_clicked == [1])
    assert toggle.property("currentIndex") == 1
    toggle_indicator = _component_items(toggle, "SlidingIndicator")[0]
    toggle_visual = _indicator_visual(toggle_indicator)
    assert toggle_visual.width() > 0
    assert toggle_visual.height() > 0
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []

def test_hidden_navigation_items_keep_indices_without_sidebar_artifacts(qapp):
    """隐藏项保留路由索引, 但不占呈现尺寸或选中指示器。"""
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, items, warnings = _create_hidden_items_scene()
    try:
        for host_name, delegate_name in (
            ("hiddenView", "NavigationViewItem"),
            ("hiddenBar", "NavigationBarItem"),
            ("hiddenToggle", "ToggleNavigationBarItem"),
        ):
            host = items[host_name]
            hidden_top = _item_with_text(host, delegate_name, host_name.replace("hidden", "").title() + " Hidden")
            assert hidden_top.property("itemVisible") is False
            assert hidden_top.isVisible() is False
            assert hidden_top.width() == 0
            assert hidden_top.height() <= 0
            visible_top = _item_with_text(host, delegate_name, host_name.replace("hidden", "").title() + " Settings")
            assert visible_top.isVisible() is True
            assert visible_top.y() == pytest.approx(hidden_top.y())

            model = host.property("model")
            model = model.toVariant() if hasattr(model, "toVariant") else model
            assert len(model) == 3

            indicator = _component_items(host, "SlidingIndicator")[0]
            if host_name == "hiddenToggle":
                host.updateIndicatorForBottomItem("toggle-account")
                _pump(60)
                assert indicator.isVisible() is True
            host.setProperty("currentIndex", 1)
            _pump(60)
            assert indicator.isVisible() is False

            host.setProperty("currentIndex", 4)
            _pump(60)
            hidden_bottom_text = host_name.replace("hidden", "").title() + " Hidden Bottom"
            hidden_bottom = _item_with_text(host, delegate_name, hidden_bottom_text)
            assert hidden_bottom.property("itemVisible") is False
            assert hidden_bottom.width() == 0
            assert hidden_bottom.height() <= 0
            assert indicator.isVisible() is False
            visible_bottom = _item_with_text(host, delegate_name, host_name.replace("hidden", "").title() + " About")
            assert visible_bottom.y() == pytest.approx(hidden_bottom.y())

            host.setProperty("currentIndex", 2)
            _pump(60)
            assert indicator.isVisible() is True

        tabs = items["hiddenTabs"]
        assert tabs.property("_visibleItemCount") == 2
        tab_items = sorted(
            _component_items(tabs, "NavigationBarItem"),
            key=lambda item: item.property("text"),
        )
        assert [item.property("text") for item in tab_items] == [
            "Tab About",
            "Tab Hidden",
            "Tab Home",
        ]
        assert [item.width() for item in tab_items] == [180, 0, 180]
        assert all(item.isVisible() for item in tab_items if item.property("text") != "Tab Hidden")
        assert not next(item for item in tab_items if item.property("text") == "Tab Hidden").isVisible()

        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before

def test_navigation_indicator_waits_until_lazy_page_is_ready(navigation_scene):
    window, items, warnings, windows_before = navigation_scene
    view = items["navigationView"]
    indicator = _component_items(view, "SlidingIndicator")[0]
    indicator_visual = _indicator_visual(indicator)
    initial_y = indicator_visual.y()

    assert QMetaObject.invokeMethod(window, "beginLazyIndicatorSwitch")
    _pump()

    assert view.property("_pendingIndicatorAnimation") is True
    assert view.property("_pendingTargetIndex") == 2
    assert indicator_visual.y() == pytest.approx(initial_y)

    assert QMetaObject.invokeMethod(window, "finishLazyIndicatorSwitch")
    assert _wait_for(lambda: not view.property("_pendingIndicatorAnimation"))
    assert view.property("_pendingTargetIndex") == -1
    assert _wait_for(lambda: indicator_visual.y() != pytest.approx(initial_y))
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []

def test_navigation_bars_use_smooth_scroll_helper(navigation_scene):
    window, items, warnings, windows_before = navigation_scene
    bar = items["navigationBar"]
    toggle = items["toggleNavigationBar"]
    bar_flickable = next(
        item
        for item in _descendants(bar)
        if "QQuickFlickable" in item.metaObject().className()
    )
    toggle_flickable = next(
        item
        for item in _descendants(toggle)
        if "QQuickFlickable" in item.metaObject().className()
    )
    bar_helper = bar.findChild(QQuickItem, "navigationBarSmoothScrollHelper")
    toggle_helper = toggle.findChild(QQuickItem, "toggleNavigationBarSmoothScrollHelper")
    assert bar_helper is not None
    assert toggle_helper is not None
    # 视口现在可交互以支持触摸/拖拽滚动; 滚轮仍必须走平滑滚动助手,
    # 下面的 targetPos 与 contentY 断言就是在锁这一点。
    # The viewports are interactive now so touch and drag can scroll. The wheel
    # must still go through the smooth-scroll helper, which the targetPos and
    # contentY assertions below pin down.
    assert bar_flickable.property("interactive")
    assert toggle_flickable.property("interactive")
    assert window.property("barSmoothScroll") is True
    assert window.property("toggleSmoothScroll") is True
    assert window.property("barScrollDuration") == window.property(
        "navigationScrollDuration"
    )
    assert window.property("toggleScrollDuration") == window.property(
        "navigationScrollDuration"
    )
    assert bar.property("scrollStep") == pytest.approx(window.property("defaultScrollStep"))
    assert toggle.property("scrollStep") == pytest.approx(window.property("defaultScrollStep"))
    assert bar_helper.property("handleWheel") is False
    assert toggle_helper.property("handleWheel") is False
    assert bar_helper.property("duration") == window.property(
        "navigationScrollDuration"
    )
    assert toggle_helper.property("duration") == window.property(
        "navigationScrollDuration"
    )
    assert bar_helper.property("targetPos") == pytest.approx(0)

    wheel_point = _item_with_text(bar, "NavigationBarItem", "Four").mapToScene(QPointF(20, 20)).toPoint()
    _send_wheel(window, wheel_point, -120)
    assert bar_helper.property("targetPos") == pytest.approx(
        window.property("defaultScrollStep")
    )
    assert _wait_for(lambda: bar_flickable.property("contentY") > 0)

    assert QMetaObject.invokeMethod(window, "smoothScrollToggleBar")
    expected_toggle_target = min(
        window.property("defaultScrollStep"),
        toggle_helper.property("maxScroll"),
    )
    assert toggle_helper.property("targetPos") == pytest.approx(
        expected_toggle_target
    )
    assert _wait_for(lambda: toggle_flickable.property("contentY") > 0)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []

def test_navigation_bar_item_long_title_elides_then_scrolls_on_hover(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_long_title_scene()
    engine, component, window, nav_item, warnings = scene
    try:
        source = (ROOT / "prismqml" / "PrismQML" / "navigation" / "NavigationBarItem.qml").read_text(encoding="utf-8")
        assert "elide: Text.ElideRight" in source
        assert "speed: Enums.motion.navigationTitleMarqueeSpeed" in source
        assert "_labelWidth: Math.max(0, width - Enums.spacing.xs * 2)" in source

        QTest.mouseMove(window, QPoint(window.width() - 1, window.height() - 1))
        assert _wait_for(lambda: nav_item.property("hovered") is False)

        label = _direct_text_item(nav_item, "Navigation Settings")
        marquee = _marquee_item(nav_item, "Navigation Settings")
        marquee_content = _object_named(marquee, "marqueeContent")
        marquee_text = _object_named(marquee, "marqueeText")
        marquee_text_copy = _object_named(marquee, "marqueeTextCopy")
        label_left = label.mapToItem(nav_item, 0, 0).x()
        label_right = label_left + label.width()

        assert label_left >= window.property("safeTextInset")
        assert label_right <= nav_item.width() - window.property("safeTextInset")
        assert label.implicitWidth() > label.width()
        assert nav_item.property("_labelOverflowing") is True
        assert label.property("clip") is True
        assert label.isVisible()
        assert not marquee.isVisible()
        assert marquee.property("running") is False
        assert marquee.property("pauseDuration") == window.property("noDelay")
        assert marquee.property("speed") == window.property("navTitleMarqueeSpeed")
        assert marquee.property("fontPixelSize") == window.property("captionCompact")
        assert marquee.property("scrollGap") == window.property("marqueeGap")
        assert marquee.property("_scrollDistance") == pytest.approx(
            marquee_text.implicitWidth() + marquee.property("scrollGap")
        )
        assert marquee_text_copy.x() == pytest.approx(marquee.property("_scrollDistance"))
        marquee_left = marquee.mapToItem(nav_item, 0, 0).x()
        marquee_right = marquee_left + marquee.width()
        assert marquee.width() == pytest.approx(label.width())
        assert marquee_left == pytest.approx(label_left)
        assert marquee_right == pytest.approx(label_right)

        point = nav_item.mapToScene(QPointF(nav_item.width() / 2, nav_item.height() / 2)).toPoint()
        QTest.mouseMove(window, point)
        assert _wait_for(lambda: nav_item.property("hovered") is True)
        assert _wait_for(lambda: marquee.isVisible() and marquee.property("running") is True)
        assert _wait_for(lambda: marquee_content.x() < 0)
        assert not label.isVisible()
        assert marquee.width() <= nav_item.width()
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before

def test_navigation_bar_item_creates_badge_only_for_positive_count(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_long_title_scene()
    engine, component, window, nav_item, warnings = scene
    badge_name = "navigationBadge_Navigation Settings"
    try:
        assert not any(
            item.objectName() == badge_name for item in _descendants(nav_item)
        )

        assert nav_item.setProperty("badgeCount", 7)
        assert _wait_for(
            lambda: any(
                item.objectName() == badge_name for item in _descendants(nav_item)
            )
        )
        badge = _object_named(nav_item, badge_name)
        assert badge.property("count") == 7
        assert badge.isVisible()

        assert nav_item.setProperty("badgeCount", 0)
        assert _wait_for(
            lambda: not any(
                item.objectName() == badge_name for item in _descendants(nav_item)
            )
        )
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before

def test_sidebars_hint_overflow_with_a_graded_edge_fade(qapp):
    """溢出端渐隐提示可滚动; 不溢出时不得渐隐。

    Every sidebar fades items near an overflowing edge and stays fully opaque
    when its content fits.
    """
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, items, warnings = _create_scroll_fade_scene()
    try:
        full = window.property("fullOpacity")
        # 渐隐带必须跨多项, 否则逐项斜坡退化为硬切。
        # The band must span several items or the per-item ramp is a hard cut.
        assert window.property("fadeBandItems") >= 2.0

        for overflow_name, fitting_name, delegate in SCROLL_FADE_HOSTS:
            overflow = items[overflow_name]
            fitting = items[fitting_name]
            flickable = _top_flickable(overflow)

            # 视口必须有高度且内容确实溢出, 否则本用例什么也没验证。
            # A sized viewport with real overflow, or this case proves nothing.
            assert flickable.property("height") > 0, overflow_name
            assert flickable.property("contentHeight") > flickable.property("height"), (
                overflow_name
            )
            assert len(_viewport_items(overflow, delegate)) == 8, overflow_name

            parked = _viewport_opacities(overflow, delegate)
            assert parked[0] == full, (overflow_name, parked)
            graded = {value for value in parked if 0.0 < value < full}
            assert len(graded) >= 2, (overflow_name, parked)

            fits = _viewport_opacities(fitting, delegate)
            assert fits and all(value == full for value in fits), (fitting_name, fits)

            # 滚离顶部后顶端项必须开始淡出, 提示上方还有内容。
            # Once scrolled off the top, leading items fade to hint at more above.
            overflow.setProperty("currentIndex", 0)
            flickable.setProperty("contentY", 120.0)
            assert _wait_for(lambda: flickable.property("contentY") > 0), overflow_name
            assert _viewport_opacities(overflow, delegate)[0] < full, overflow_name

            # 指示器在视口之外, 必须与选中项锁步, 否则会在渐隐项旁保持清晰。
            # The indicator sits outside the viewport and must track its item.
            selected = _viewport_opacities(overflow, delegate)[0]
            assert overflow.property("_selectedItemFade") == pytest.approx(selected), (
                overflow_name
            )

            overflow.setProperty("scrollFadeEnabled", False)
            _pump(60)
            disabled = _viewport_opacities(overflow, delegate)
            assert all(value == full for value in disabled), (overflow_name, disabled)
            overflow.setProperty("scrollFadeEnabled", True)

        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before

def test_scroll_rail_overlays_without_changing_nav_item_widths(qapp):
    """浮层滚动轨不得改变导航项宽度, 且只在悬停或滚动后显形。

    The rail is an overlay: enabling it must not cost the nav items a single
    pixel. It reveals on hover and retreats once idle.
    """
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, items, warnings = _create_scroll_fade_scene()
    try:
        # offscreen 平台有个幽灵光标停在 (10,10), 贴着原点的宿主会被真实悬停。
        # 先用真实 mouseMove 把光标停到远处, 否则空闲态断言会因场景而假失败。
        # The offscreen platform parks a phantom cursor at (10,10), so a host at
        # the origin genuinely is hovered. Park it away with a real mouseMove
        # first, or the idle assertions fail for a scene reason, not a code one.
        QTest.mouseMove(window, QPoint(1150, 250))
        _pump(120)

        for overflow_name, fitting_name, delegate in SCROLL_FADE_HOSTS:
            overflow = items[overflow_name]
            rail = _scroll_rail(overflow)
            flickable = _top_flickable(overflow)
            expected = PRE_RAIL_WIDTHS[overflow_name]

            # 用户的硬约束: 开轨道不许挤掉导航项一个像素。
            # The user's hard constraint: the rail must not cost one pixel.
            assert overflow.width() == expected["host"], overflow_name
            assert flickable.width() == expected["viewport"], (
                overflow_name,
                flickable.width(),
            )
            widths = set(_viewport_widths(overflow, delegate))
            assert widths == {expected["delegate"]}, (overflow_name, widths)
            assert flickable.property("contentWidth") <= flickable.width(), overflow_name

            # 轨道必须压在视口之上, 而不是占用视口右侧的沟槽。
            # The rail must sit over the viewport, not in a gutter beside it.
            rail_left = rail.mapToItem(flickable, QPointF(0, 0)).x()
            assert 0 <= rail_left < flickable.width(), (overflow_name, rail_left)
            assert rail_left + rail.width() <= flickable.width(), overflow_name

            _pump(60)
            _assert_rail_reveals_on_hover(window, overflow, rail, overflow_name)

            # 不溢出的宿主根本不该出现轨道。 No rail at all when content fits.
            fitting_rail = _scroll_rail(items[fitting_name])
            assert not fitting_rail.property("scrollable"), fitting_name
            assert not fitting_rail.isVisible(), fitting_name

            # 关闭后必须彻底隐形, 而非留一条零宽占位。
            # Disabled means gone, not a zero-width placeholder.
            overflow.setProperty("scrollRailEnabled", False)
            _pump(60)
            assert not rail.isVisible(), overflow_name
            assert set(_viewport_widths(overflow, delegate)) == {expected["delegate"]}, (
                overflow_name
            )

        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before

def test_sidebars_scroll_by_touch_and_drag_without_losing_taps(qapp):
    """拖拽能滚动列表, 且点击仍然照常选中。

    Enabling drag must not cost the delegates their taps, and the switch must
    still turn dragging off.
    """
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, items, warnings = _create_scroll_fade_scene()
    try:
        for overflow_name, _fitting_name, delegate in SCROLL_FADE_HOSTS:
            overflow = items[overflow_name]
            flickable = _top_flickable(overflow)
            assert flickable.property("interactive"), overflow_name

            # 拖拽必须真的滚起来, 否则触摸设备上这个列表根本没法用。
            # The drag must genuinely scroll, or the list is unusable by touch.
            dragged = _drag_viewport(window, overflow)
            assert dragged > 0, (overflow_name, dragged)

            # 开了拖拽以后点击不能丢: 委托仍须发出 itemClicked。
            # Enabling drag must not swallow taps; itemClicked must still fire.
            assert _tap_second_item(window, overflow, delegate) == [1], overflow_name

            # 开关必须真的能关掉拖拽。 The switch must really disable dragging.
            overflow.setProperty("dragScrollEnabled", False)
            _pump(60)
            assert not flickable.property("interactive"), overflow_name
            assert _drag_viewport(window, overflow) == 0.0, overflow_name
            # 关掉拖拽后点击依然要能用。 Taps keep working with drag off.
            assert _tap_second_item(window, overflow, delegate) == [1], overflow_name

            overflow.setProperty("dragScrollEnabled", True)
            _pump(60)

        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before

def test_root_navigation_sources_follow_conventions():
    violations = []
    for source_path in ROOT_NAV_SOURCE_PATHS:
        path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations.extend(
            violation
            for violation in scan_source_text(
                source_path.read_text(encoding="utf-8"), path
            )
            if violation.rule in {"QML008", "QML009"}
        )
    assert violations == []

    smooth_scroll = ROOT_NAV_SOURCE_PATHS[0].read_text(encoding="utf-8")
    assert 'import "../../controls/containers/ScrollBar"' not in smooth_scroll
    assert "SmoothScrollHelper {" not in smooth_scroll
    assert smooth_scroll.count("Timer {") == 1
    assert smooth_scroll.count("NumberAnimation {") == 1
    assert "MouseArea {" not in smooth_scroll
    for source_path in (
        ROOT / "prismqml" / "PrismQML" / "navigation" / "NavigationBar.qml",
        ROOT / "prismqml" / "PrismQML" / "navigation" / "ToggleNavigationBar.qml",
    ):
        source = source_path.read_text(encoding="utf-8")
        assert "NavigationSmoothScroll" in source
        assert "_handleTopWheel" not in source
