# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
from root_navigation_conventions_scenes import (
    SCENE_SOURCE,
    HIDDEN_ITEMS_SOURCE,
)

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

def _create_hidden_items_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(HIDDEN_ITEMS_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [error.toString() for error in component.errors()]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    names = ("hiddenView", "hiddenBar", "hiddenToggle", "hiddenTabs")
    items = {name: window.findChild(QQuickItem, name) for name in names}
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

def _drag_viewport(window, host: QQuickItem, steps: int = 12, dy: int = 12) -> float:
    """拖拽视口并返回落点。 Drag the viewport upward and report where it settled.

    小步移动是必需的: 单次跳跃不会被识别为拖拽手势。
    Small steps are required; one jump is not read as a drag gesture.
    """
    flickable = _top_flickable(host)
    flickable.setProperty("contentY", 0.0)
    _pump(60)
    pos = QPoint(
        int(host.x() + host.width() / 2),
        int(host.y() + host.height() * 0.7),
    )
    QTest.mousePress(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pos
    )
    for _ in range(steps):
        pos = QPoint(pos.x(), pos.y() - dy)
        QTest.mouseMove(window, pos)
        _pump(16)
    QTest.mouseRelease(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pos
    )
    _pump(220)
    return round(flickable.property("contentY"), 1)

def _tap_second_item(window, host: QQuickItem, delegate_name: str) -> list:
    """点击第二项并返回 itemClicked 收到的下标。 Tap and report itemClicked.

    currentIndex 由上层 window 接收 itemClicked 后回绑, 场景里没有那层接线,
    所以点击契约要测信号而不是 currentIndex。
    _onItemClicked deliberately does not set currentIndex; an upper-layer window
    binds it back from itemClicked. So the tap contract is the signal.
    """
    fired = []
    host.itemClicked.connect(fired.append)
    try:
        flickable = _top_flickable(host)
        flickable.setProperty("contentY", 0.0)
        _pump(80)
        target = sorted(
            _component_items(flickable, delegate_name), key=lambda item: item.y()
        )[1]
        centre = target.mapToItem(None, target.width() / 2, target.height() / 2)
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(int(centre.x()), int(centre.y())),
        )
        _pump(220)
    finally:
        host.itemClicked.disconnect(fired.append)
    return fired

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

SCROLL_FADE_HOSTS = (
    ("overflowView", "fittingView", "NavigationViewItem"),
    ("overflowBar", "fittingBar", "NavigationBarItem"),
    ("overflowToggle", "fittingToggle", "ToggleNavigationBarItem"),
)

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
