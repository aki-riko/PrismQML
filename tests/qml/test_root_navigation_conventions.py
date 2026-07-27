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
    for source_path in (
        ROOT / "prismqml" / "PrismQML" / "navigation" / "NavigationBar.qml",
        ROOT / "prismqml" / "PrismQML" / "navigation" / "ToggleNavigationBar.qml",
    ):
        source = source_path.read_text(encoding="utf-8")
        assert "NavigationSmoothScroll" in source
        assert "_handleTopWheel" not in source
