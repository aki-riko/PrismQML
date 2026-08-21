# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Root navigation runtime contracts. 顶层导航组件运行时合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QMetaObject, QPoint, QPointF, QTimer, QUrl, Qt
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
ROOT_NAV_SOURCE_PATHS = tuple(
    ROOT / "prismqml" / "PrismQML" / "navigation" / name
    for name in (
        "_internal/NavigationSmoothScroll.qml",
        "_internal/NavigationPanelBackground.qml",
        "_internal/NavigationPanelBorder.qml",
        "NavigationBar.qml",
        "NavigationBarItem.qml",
        "NavigationPanelCore.qml",
        "NavigationView.qml",
        "NavigationViewItem.qml",
        "ToggleNavigationBar.qml",
    )
)
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "root-navigation-conventions.qml"))
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property int viewModelCount: navigationView.model.length
    readonly property string viewCurrentKey: navigationView.currentKey
    readonly property bool viewExpanded: navigationView.isExpanded
    readonly property bool viewCompact: navigationView.isCompact
    readonly property int navigationScrollDuration: Enums.duration.navigationScroll
    readonly property real defaultScrollStep: Enums.spacing.navigationScrollStep
    readonly property bool barSmoothScroll: navigationBar.smoothScroll
    readonly property bool toggleSmoothScroll: toggleBar.smoothScroll
    readonly property int barScrollDuration: navigationBar.scrollDuration
    readonly property int toggleScrollDuration: toggleBar.scrollDuration

    function expandView() { navigationView.expand() }
    function collapseView() { navigationView.collapse() }
    function toggleView() { navigationView.toggle() }
    function selectViewProfile() { navigationView.setCurrentItem("profile") }
    function addViewDynamic() {
        navigationView.addItem("dynamic", "", "Dynamic", null, true, "", "top")
    }
    function removeViewDynamic() { navigationView.removeWidget("dynamic") }
    function smoothScrollNavigationBar() { navigationBar.smoothScrollBy(120) }
    function beginLazyIndicatorSwitch() {
        navigationView.delayIndicatorAnimation = true
        navigationView._isPageLoading = true
        navigationView.currentIndex = 2
    }
    function finishLazyIndicatorSwitch() {
        navigationView._isPageLoading = false
        navigationView.playPendingIndicatorAnimation()
    }
    function smoothScrollToggleBar() { toggleBar.smoothScrollBy(toggleBar.scrollStep) }

    width: 900
    height: 420
    visible: true

    NavigationView {
        id: navigationView
        objectName: "navigationView"
        width: isExpanded ? implicitWidth : Enums.controlSize.navPanelCompactWidth
        height: parent.height
        showReturnButton: false
        indicatorAnimationEnabled: false
        model: [
            { "key": "home", "text": "Home" },
            { "key": "profile", "text": "Profile" },
            { "key": "reports", "text": "Reports" }
        ]
        bottomItems: [
            { "key": "settings", "text": "Settings", "selectable": true },
            { "text": "Help", "selectable": false }
        ]
        _bottomPageIndexMap: ({ "settings": 3 })
    }

    NavigationBar {
        id: navigationBar
        objectName: "navigationBar"
        x: 300
        width: implicitWidth
        height: parent.height
        indicatorAnimationEnabled: false
        model: [
            { "key": "one", "text": "One" },
            { "key": "two", "text": "Two" },
            { "key": "three", "text": "Three" },
            { "key": "four", "text": "Four" },
            { "key": "five", "text": "Five" },
            { "key": "six", "text": "Six" },
            { "key": "seven", "text": "Seven" },
            { "key": "eight", "text": "Eight" },
            { "key": "nine", "text": "Nine" }
        ]
        bottomItems: [{ "key": "bar-settings", "text": "Settings", "selectable": true }]
        _bottomPageIndexMap: ({ "bar-settings": 6 })
    }

    ToggleNavigationBar {
        id: toggleBar
        objectName: "toggleNavigationBar"
        x: 430
        y: 20
        width: 260
        height: 300
        model: [
            { "key": "alpha", "text": "Alpha" },
            { "key": "beta", "text": "Beta" },
            { "key": "gamma", "text": "Gamma" },
            { "key": "delta", "text": "Delta" },
            { "key": "epsilon", "text": "Epsilon" },
            { "key": "zeta", "text": "Zeta" },
            { "key": "eta", "text": "Eta" },
            { "key": "theta", "text": "Theta" }
        ]
        bottomItems: [{ "key": "toggle-settings", "text": "Settings", "selectable": true }]
        _bottomPageIndexMap: ({ "toggle-settings": 3 })
    }
}
"""
SCROLL_FADE_SOURCE = """
import QtQuick
import QtQuick.Window
import PrismQML

// 三种侧边栏各给一个溢出模型与一个不溢出模型, 用于验证边缘渐隐提示。
// An overflowing and a fitting model for each sidebar, to check the edge fade.
Window {
    readonly property real fullOpacity: Enums.navigationFade.maxOpacity
    readonly property real fadeBandItems: Enums.navigationFade.bandItems

    width: 1200
    height: 260
    visible: true

    NavigationView {
        id: overflowView
        objectName: "overflowView"
        width: 300
        height: parent.height
        isExpanded: true
        showReturnButton: false
        smoothScroll: false
        indicatorAnimationEnabled: false
        model: [
            { "key": "v1", "text": "V One" },
            { "key": "v2", "text": "V Two" },
            { "key": "v3", "text": "V Three" },
            { "key": "v4", "text": "V Four" },
            { "key": "v5", "text": "V Five" },
            { "key": "v6", "text": "V Six" },
            { "key": "v7", "text": "V Seven" },
            { "key": "v8", "text": "V Eight" }
        ]
        bottomItems: [{ "key": "v-settings", "text": "Settings", "selectable": true }]
        _bottomPageIndexMap: ({ "v-settings": 8 })
    }

    NavigationBar {
        id: overflowBar
        objectName: "overflowBar"
        x: 320
        width: implicitWidth
        height: parent.height
        smoothScroll: false
        indicatorAnimationEnabled: false
        model: [
            { "key": "b1", "text": "B One" },
            { "key": "b2", "text": "B Two" },
            { "key": "b3", "text": "B Three" },
            { "key": "b4", "text": "B Four" },
            { "key": "b5", "text": "B Five" },
            { "key": "b6", "text": "B Six" },
            { "key": "b7", "text": "B Seven" },
            { "key": "b8", "text": "B Eight" }
        ]
        bottomItems: [{ "key": "b-settings", "text": "Settings", "selectable": true }]
        _bottomPageIndexMap: ({ "b-settings": 8 })
    }

    ToggleNavigationBar {
        id: overflowToggle
        objectName: "overflowToggle"
        x: 420
        width: 240
        height: parent.height
        smoothScroll: false
        model: [
            { "key": "t1", "text": "T One" },
            { "key": "t2", "text": "T Two" },
            { "key": "t3", "text": "T Three" },
            { "key": "t4", "text": "T Four" },
            { "key": "t5", "text": "T Five" },
            { "key": "t6", "text": "T Six" },
            { "key": "t7", "text": "T Seven" },
            { "key": "t8", "text": "T Eight" }
        ]
        bottomItems: [{ "key": "t-settings", "text": "Settings", "selectable": true }]
        _bottomPageIndexMap: ({ "t-settings": 8 })
    }

    NavigationView {
        id: fittingView
        objectName: "fittingView"
        x: 680
        width: 300
        height: parent.height
        isExpanded: true
        showReturnButton: false
        indicatorAnimationEnabled: false
        model: [{ "key": "f1", "text": "F One" }]
        bottomItems: [{ "key": "f-settings", "text": "Settings", "selectable": true }]
        _bottomPageIndexMap: ({ "f-settings": 1 })
    }

    NavigationBar {
        id: fittingBar
        objectName: "fittingBar"
        x: 1000
        width: implicitWidth
        height: parent.height
        indicatorAnimationEnabled: false
        model: [{ "key": "g1", "text": "G One" }]
        bottomItems: [{ "key": "g-settings", "text": "Settings", "selectable": true }]
        _bottomPageIndexMap: ({ "g-settings": 1 })
    }

    ToggleNavigationBar {
        id: fittingToggle
        objectName: "fittingToggle"
        x: 1090
        width: 100
        height: parent.height
        model: [{ "key": "h1", "text": "H One" }]
        bottomItems: [{ "key": "h-settings", "text": "Settings", "selectable": true }]
        _bottomPageIndexMap: ({ "h-settings": 1 })
    }
}
""".encode("utf-8")
LONG_TITLE_SOURCE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property int captionCompact: Enums.typography.captionCompact
    readonly property int noDelay: Enums.duration.none
    readonly property int navTitleMarqueeSpeed: Enums.motion.navigationTitleMarqueeSpeed
    readonly property int marqueeGap: Enums.spacing.l
    readonly property int safeTextInset: Enums.spacing.xs

    width: 120
    height: 100
    visible: true

    NavigationBarItem {
        id: navItem
        objectName: "navItem"
        width: implicitWidth
        height: implicitHeight
        text: "Navigation Settings"
        icon: "Home"
    }

}
""".encode("utf-8")


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1500) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


def _descendants(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _descendants(child)


def _component_items(root: QQuickItem, component_name: str):
    return [
        item
        for item in _descendants(root)
        if component_name in item.metaObject().className()
    ]


def _indicator_visual(indicator: QQuickItem):
    return next(
        item
        for item in indicator.childItems()
        if item.isVisible() and item.width() > 0 and item.height() > 0
    )


def _item_with_text(root: QQuickItem, component_name: str, text: str):
    return next(
        item
        for item in _component_items(root, component_name)
        if item.property("text") == text
    )


def _toggle_item(root: QQuickItem, text: str):
    return next(
        item
        for item in _descendants(root)
        if item.metaObject().indexOfProperty("itemText") >= 0
        and item.property("itemText") == text
    )


def _direct_text_item(root: QQuickItem, text: str):
    return next(
        item
        for item in root.childItems()
        if item.metaObject().indexOfProperty("paintedWidth") >= 0
        and item.property("text") == text
    )


def _marquee_item(root: QQuickItem, text: str):
    return next(
        item
        for item in _descendants(root)
        if item.metaObject().indexOfProperty("forceScroll") >= 0
        and item.property("text") == text
    )


def _object_named(root: QQuickItem, object_name: str):
    return next(
        item
        for item in _descendants(root)
        if item.objectName() == object_name
    )


def _click_item(window: QQuickWindow, item: QQuickItem) -> None:
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=point)


def _send_wheel(window: QQuickWindow, point: QPoint, delta: int) -> None:
    event = QWheelEvent(
        QPointF(point),
        QPointF(window.mapToGlobal(point)),
        QPoint(),
        QPoint(0, delta),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    QCoreApplication.sendEvent(window, event)
    _pump()


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is accepted for accepted in allowed)
    ]


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [error.toString() for error in component.errors()]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    items = {
        name: window.findChild(QQuickItem, name)
        for name in ("navigationView", "navigationBar", "toggleNavigationBar")
    }
    assert all(items.values())
    _pump(100)
    return engine, component, window, items, warnings


def _create_scroll_fade_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCROLL_FADE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    names = (
        "overflowView",
        "overflowBar",
        "overflowToggle",
        "fittingView",
        "fittingBar",
        "fittingToggle",
    )
    items = {name: window.findChild(QQuickItem, name) for name in names}
    for name, item in items.items():
        assert item is not None, name
    _pump(150)
    return engine, component, window, items, warnings


def _top_flickable(host: QQuickItem):
    """The scrollable viewport of a sidebar. 侧边栏的可滚动视口。"""
    return next(
        item
        for item in _descendants(host)
        if "QQuickFlickable" in item.metaObject().className()
    )


def _viewport_items(host: QQuickItem, delegate_name: str):
    """Delegates inside the viewport, top to bottom. 视口内的委托, 自上而下。

    Matching on the delegate type avoids catching the nested Labels, which also
    carry a text property. 按委托类型匹配, 避免误取同样带 text 的内层 Label。
    """
    items = _component_items(_top_flickable(host), delegate_name)
    return sorted(items, key=lambda item: item.y())


def _viewport_opacities(host: QQuickItem, delegate_name: str):
    return [
        round(item.property("opacity"), 3)
        for item in _viewport_items(host, delegate_name)
    ]


def _scroll_rail(host: QQuickItem):
    """The overlay rail of a sidebar. 侧边栏的浮层滚动轨。"""
    return next(
        item
        for item in _descendants(host)
        if "NavigationScrollRail" in item.metaObject().className()
    )


def _assert_rail_reveals_on_hover(window, host: QQuickItem, rail, label: str) -> None:
    """空闲退隐, 悬停显形, 滚动后短暂显形。 Idle hides, hover and scroll reveal."""
    assert rail.property("opacity") == pytest.approx(0.0), (
        label,
        rail.property("opacity"),
    )
    assert not rail.property("shown"), label

    centre = QPoint(
        int(host.x() + host.width() / 2),
        int(host.y() + host.height() / 2),
    )
    QTest.mouseMove(window, centre)
    assert _wait_for(lambda: rail.property("shown")), label
    assert _wait_for(lambda: rail.property("opacity") > 0.9), label

    QTest.mouseMove(window, QPoint(1150, 250))
    assert _wait_for(lambda: not rail.property("shown")), label

    # 纯滚轮操作也要有位置反馈: 内容一动就短暂显形。
    # Wheel-only use still gets feedback: any content move reveals it.
    _top_flickable(host).setProperty("contentY", 90.0)
    assert _wait_for(lambda: rail.property("shown")), label


def _viewport_widths(host: QQuickItem, delegate_name: str):
    return [item.width() for item in _viewport_items(host, delegate_name)]


def _create_long_title_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(LONG_TITLE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [error.toString() for error in component.errors()]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    nav_item = window.findChild(QQuickItem, "navItem")
    assert nav_item is not None
    _pump(100)
    return engine, component, window, nav_item, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.fixture
def navigation_scene(qapp):
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    try:
        yield (*scene[2:], windows_before)
    finally:
        _dispose_scene(scene[0], scene[1], scene[2])
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


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
    assert not bar_flickable.property("interactive")
    assert not toggle_flickable.property("interactive")
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


SCROLL_FADE_HOSTS = (
    ("overflowView", "fittingView", "NavigationViewItem"),
    ("overflowBar", "fittingBar", "NavigationBarItem"),
    ("overflowToggle", "fittingToggle", "ToggleNavigationBarItem"),
)


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


# 轨道引入前(73e1a017d)在同一场景实测的基准宽度, 连测两次逐字节一致。
# 只比对"轨道开 vs 关"抓不到常驻沟槽 —— 那会让两个测量值等量缩小而依然相等,
# 所以这里钉住引入前的绝对值。
# Widths measured in this same scene before the rail existed (73e1a017d), stable
# across two runs. Comparing rail-on against rail-off cannot catch a permanently
# reserved gutter, because both measurements would shrink equally and still
# match, so pin the pre-rail absolute values instead.
PRE_RAIL_WIDTHS = {
    "overflowView": {"host": 300.0, "viewport": 292.0, "delegate": 292.0},
    "overflowBar": {"host": 68.0, "viewport": 68.0, "delegate": 64.0},
    "overflowToggle": {"host": 240.0, "viewport": 232.0, "delegate": 232.0},
}

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
