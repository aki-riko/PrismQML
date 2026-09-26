# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Drawer geometry and scrim interaction contracts. Drawer 几何与遮罩交互合同。"""

from pathlib import Path

import pytest
import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPoint,
    QPointF,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types
ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "drawer-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property int insideMode: Enums.drawer.mode_inside
    readonly property int outsideMode: Enums.drawer.mode_outside
    readonly property int leftPosition: Enums.position.left
    readonly property int rightPosition: Enums.position.right
    readonly property int topPosition: Enums.position.top
    readonly property int bottomPosition: Enums.position.bottom
    readonly property int outsideRadius: Enums.radius.large
    readonly property int outsideCollapsedExtent: Enums.border.thin
    property int drawerClicks: 0

    x: 100
    y: 120
    width: 600
    height: 400
    visible: true

    Drawer {
        id: drawer
        objectName: "drawer"
        position: Enums.position.left
        drawerWidth: 180
        drawerHeight: 120
        animationDuration: 40
        modal: true

        Rectangle {
            objectName: "drawerContent"
            width: 80
            height: 40

            MouseArea {
                anchors.fill: parent
                onClicked: root.drawerClicks += 1
            }
        }
    }

    Item {
        id: nestedHost

        width: 360
        height: parent.height

        Drawer {
            id: reparentDrawer

            objectName: "reparentDrawer"
            position: Enums.position.right
            drawerWidth: 180
            animationDuration: 240
        }
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


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
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow)
    _pump()
    drawer = window.findChild(QQuickItem, "drawer")
    content_item = drawer.findChild(QQuickItem, "contentItem")
    panel = content_item.parentItem()
    return engine, component, window, drawer, content_item, panel, warnings


def _dispose_scene(engine, component, window) -> None:
    for candidate in QGuiApplication.topLevelWindows():
        if candidate.objectName() in {"outsideDrawerWindow", "window"}:
            if shiboken6.isValid(candidate):
                candidate.close()
                candidate.deleteLater()
    if shiboken6.isValid(window):
        window.close()
        window.deleteLater()
    component.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.fixture
def drawer_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    scene = _create_scene()
    try:
        yield (*scene[2:], windows_before)
    finally:
        _dispose_scene(scene[0], scene[1], scene[2])


def _open_at(drawer, panel, position, expected):
    drawer.setProperty("position", position)
    assert QMetaObject.invokeMethod(drawer, "open")
    assert _wait_for(lambda: drawer.property("opened"))
    assert _wait_for(
        lambda: (panel.x(), panel.y(), panel.width(), panel.height())
        == pytest.approx(expected)
    )


def _close(drawer):
    assert QMetaObject.invokeMethod(drawer, "close")
    assert _wait_for(lambda: not drawer.property("opened"))
    assert _wait_for(lambda: not drawer.property("_isClosing"))


def _drawer_window():
    candidates = [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.objectName() == "outsideDrawerWindow"
    ]
    return next((window for window in candidates if window.isVisible()), None) or (
        candidates[-1] if candidates else None
    )


def _outside_window_geometry(host_window, position, extent, spread):
    frame = host_window.frameGeometry()
    left = frame.left()
    top = frame.top()
    right = frame.right() + 1
    bottom = frame.bottom() + 1
    if position == host_window.property("leftPosition"):
        return (
            left - extent - spread,
            top - spread,
            extent + spread,
            frame.height() + 2 * spread,
        )
    if position == host_window.property("rightPosition"):
        return (
            right,
            top - spread,
            extent + spread,
            frame.height() + 2 * spread,
        )
    if position == host_window.property("topPosition"):
        return (
            left - spread,
            top - extent - spread,
            frame.width() + 2 * spread,
            extent + spread,
        )
    return (
        left - spread,
        bottom,
        frame.width() + 2 * spread,
        extent + spread,
    )


def _outside_viewport_origin(host_window, position, full_extent, extent, spread):
    if position == host_window.property("leftPosition"):
        return (full_extent + spread - extent, spread)
    if position == host_window.property("topPosition"):
        return (spread, full_extent + spread - extent)
    if position == host_window.property("rightPosition"):
        return (0, spread)
    return (spread, 0)


def _outside_panel_origin(host_window, position, spread):
    if position == host_window.property("leftPosition"):
        return (spread, spread)
    if position == host_window.property("rightPosition"):
        return (0, spread)
    if position == host_window.property("topPosition"):
        return (spread, spread)
    return (spread, 0)


def test_drawer_four_direction_geometry(drawer_scene):
    window, drawer, content_item, panel, warnings, windows_before = drawer_scene
    assert drawer.property("mode") == window.property("insideMode")
    assert window.property("insideMode") != window.property("outsideMode")
    assert _drawer_window() is None
    cases = [
        (window.property("leftPosition"), (0, 0, 180, 400)),
        (window.property("rightPosition"), (420, 0, 180, 400)),
        (window.property("topPosition"), (0, 0, 600, 120)),
        (window.property("bottomPosition"), (0, 280, 600, 120)),
    ]
    for position, geometry in cases:
        _open_at(drawer, panel, position, geometry)
        assert (content_item.width(), content_item.height()) == pytest.approx(
            (panel.width() - 32, panel.height() - 32)
        )
        _close(drawer)
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_drawer_first_inside_open_rebases_closed_edge_before_animation(
    drawer_scene,
):
    window, drawer, _content_item, _panel, warnings, windows_before = (
        drawer_scene
    )
    reparent_drawer = window.findChild(QQuickItem, "reparentDrawer")
    reparent_content = reparent_drawer.findChild(QQuickItem, "contentItem")
    reparent_panel = reparent_content.parentItem()
    final_x = window.width() - reparent_panel.width()

    assert reparent_panel.x() == pytest.approx(360)
    assert QMetaObject.invokeMethod(reparent_drawer, "open")
    _pump(30)

    assert reparent_drawer.parentItem() is window.contentItem()
    assert reparent_panel.x() > final_x
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_drawer_mode_switch_creates_and_releases_outside_window(drawer_scene):
    window, drawer, content_item, panel, warnings, windows_before = drawer_scene
    assert _drawer_window() is None
    assert content_item.parentItem() is panel

    drawer.setProperty("mode", window.property("outsideMode"))
    outside_window = _drawer_window()
    outside_panel = drawer.findChild(QQuickItem, "outsideDrawerPanel")
    assert isinstance(outside_window, QQuickWindow)
    assert isinstance(outside_panel, QQuickItem)
    assert content_item.parentItem() is outside_panel

    drawer.setProperty("mode", window.property("insideMode"))
    assert _wait_for(lambda: _drawer_window() is None)
    assert content_item.parentItem() is panel

    drawer.setProperty("mode", window.property("outsideMode"))
    assert isinstance(_drawer_window(), QQuickWindow)
    assert content_item.parentItem() is drawer.findChild(
        QQuickItem, "outsideDrawerPanel"
    )
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_drawer_modal_scrim_click_rejects(drawer_scene):
    window, drawer, _content_item, panel, warnings, windows_before = drawer_scene
    rejected = []
    drawer.rejected.connect(lambda: rejected.append(True))
    _open_at(drawer, panel, window.property("leftPosition"), (0, 0, 180, 400))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        pos=QPoint(500, 200),
    )
    assert _wait_for(lambda: rejected == [True])
    assert _wait_for(lambda: not drawer.property("_isClosing"))
    assert not drawer.property("opened")
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_drawer_outside_mode_tracks_host_in_four_directions(drawer_scene):
    window, drawer, content_item, _panel, warnings, windows_before = drawer_scene
    drawer.setProperty("mode", window.property("outsideMode"))
    drawer_window = _drawer_window()
    assert isinstance(drawer_window, QQuickWindow)
    outside_panel = drawer.findChild(QQuickItem, "outsideDrawerPanel")
    assert isinstance(outside_panel, QQuickItem)

    assert drawer.property("radius") == window.property("outsideRadius")
    cases = [
        window.property("leftPosition"),
        window.property("rightPosition"),
        window.property("topPosition"),
        window.property("bottomPosition"),
    ]

    for position in cases:
        drawer.setProperty("position", position)
        QCoreApplication.processEvents()
        window_geometry = _outside_window_geometry(
            window,
            position,
            180 if position in (
                window.property("leftPosition"),
                window.property("rightPosition"),
            ) else 120,
            drawer.property("_outsideShadowSpread"),
        )
        assert QMetaObject.invokeMethod(drawer, "open")
        assert _wait_for(lambda: drawer.property("opened"))
        assert _wait_for(drawer_window.isVisible)
        assert _wait_for(
            lambda: (
                drawer_window.x(),
                drawer_window.y(),
                drawer_window.width(),
                drawer_window.height(),
            )
            == pytest.approx(window_geometry)
        ), (
            drawer_window.x(),
            drawer_window.y(),
            drawer_window.width(),
            drawer_window.height(),
            drawer.property("_outsideExtent"),
        )
        assert _wait_for(
            lambda: (
                outside_panel.x(),
                outside_panel.y(),
                outside_panel.width(),
                outside_panel.height(),
            )
            == pytest.approx(
                (
                    0,
                    0,
                    drawer_window.property("panelWidth"),
                    drawer_window.property("panelHeight"),
                )
            )
        )
        assert _wait_for(
            lambda: drawer.property("_outsideExtent")
            == (180 if position in (
                window.property("leftPosition"),
                window.property("rightPosition"),
            ) else 120)
        )
        assert content_item.parentItem() is outside_panel
        assert drawer_window.transientParent() is window
        # The panel keeps all four corners rounded; only the shadow squares off the seam.
        effective_radius = drawer.property("_effectiveRadius")
        assert outside_panel.property("radius") == pytest.approx(effective_radius)
        assert tuple(
            outside_panel.property(name)
            for name in (
                "topLeftRadius",
                "topRightRadius",
                "bottomLeftRadius",
                "bottomRightRadius",
            )
        ) == (effective_radius,) * 4
        if position == window.property("rightPosition"):
            click_pos = outside_panel.mapToItem(
                drawer_window.contentItem(),
                QPointF(content_item.x() + 10, content_item.y() + 10),
            )
            QTest.mouseClick(
                drawer_window,
                Qt.MouseButton.LeftButton,
                pos=click_pos.toPoint(),
            )
            assert _wait_for(lambda: window.property("drawerClicks") == 1)
        _close(drawer)
        assert _wait_for(lambda: not drawer_window.isVisible())

    drawer.setProperty("position", window.property("rightPosition"))
    assert QMetaObject.invokeMethod(drawer, "open")
    assert _wait_for(drawer_window.isVisible)
    window.setX(240)
    window.setY(260)
    window.resize(640, 420)
    assert _wait_for(
        lambda: (
            drawer_window.x(),
            drawer_window.y(),
            drawer_window.width(),
            drawer_window.height(),
        )
        == pytest.approx(
            _outside_window_geometry(
                window,
                window.property("rightPosition"),
                180,
                drawer.property("_outsideShadowSpread"),
            )
        )
    )
    _close(drawer)
    assert _wait_for(lambda: not drawer_window.isVisible())
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_outside_drawer_reserves_the_whole_self_drawn_shadow_band(drawer_scene):
    """自绘阴影的像带必须整体落在抽屉 HWND 内(接缝侧除外)。

    The silhouette is the panel grown by one `blur`, and the measured band spans about
    1.5x blur past that silhouette, so the HWND reserve has to hold both. This reads the
    geometry the control really commits instead of only the source expressions, so a
    reserve that covers just one of the two fails here.
    轮廓是面板朝外各扩 1 倍 blur, 实测像带在轮廓之外再铺约 1.5 倍 blur, 因此 HWND 留白
    必须同时容下两者。这里读的是控件真实提交的几何, 只覆盖其中一项的留白会在此失败。
    """
    window, drawer, _content_item, _panel, warnings, windows_before = drawer_scene
    drawer.setProperty("mode", window.property("outsideMode"))
    drawer_window = _drawer_window()
    assert isinstance(drawer_window, QQuickWindow)
    shadow = drawer_window.findChild(QQuickItem, "outsideDrawerShadow")
    assert isinstance(shadow, QQuickItem)

    blur = shadow.property("blur")
    spread = drawer.property("_outsideShadowSpread")
    # Measured on the real effect 真实效果实测的像带铺开量
    band = blur * 1.5
    assert spread == pytest.approx(blur * 2.5)
    # What is left of the reserve once the silhouette used its `blur` must still hold the
    # whole measured band. 留白减去轮廓占用的 `blur` 之后仍须容下完整的实测像带。
    assert spread - blur >= band
    tolerance = 1.0
    horizontal = (
        window.property("leftPosition"),
        window.property("rightPosition"),
    )

    for position in (
        *horizontal,
        window.property("topPosition"),
        window.property("bottomPosition"),
    ):
        drawer.setProperty("position", position)
        assert QMetaObject.invokeMethod(drawer, "open")
        assert _wait_for(lambda: drawer.property("opened"))
        assert _wait_for(drawer_window.isVisible)
        assert _wait_for(lambda: shadow.width() > 0)
        _pump(60)

        left = shadow.x()
        top = shadow.y()
        right = left + shadow.width()
        bottom = top + shadow.height()
        width = drawer_window.width()
        height = drawer_window.height()
        if position in horizontal:
            # Only the seam side (the panel edge that meets the host) may run past the
            # HWND; every other side has to hold the whole band.
            # 只有接缝侧(与宿主相接的面板边)允许越出 HWND; 其余各面都必须容下整条像带。
            assert top - band >= -tolerance, (position, top, band)
            assert bottom + band <= height + tolerance, (position, bottom, band, height)
            if position == window.property("rightPosition"):
                assert right + band <= width + tolerance, (right, band, width)
            else:
                assert left - band >= -tolerance, (left, band)
        else:
            assert left - band >= -tolerance, (position, left, band)
            assert right + band <= width + tolerance, (position, right, band, width)
            if position == window.property("topPosition"):
                assert top - band >= -tolerance, (top, band)
            else:
                assert bottom + band <= height + tolerance, (bottom, band, height)
        _close(drawer)
        assert _wait_for(lambda: not drawer_window.isVisible())
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_drawer_outside_mode_clips_fixed_content_in_four_directions(
    drawer_scene,
):
    window, drawer, content_item, _panel, warnings, windows_before = drawer_scene
    drawer.setProperty("mode", window.property("outsideMode"))
    drawer.setProperty("animationDuration", 240)
    drawer_window = _drawer_window()
    outside_panel = drawer.findChild(QQuickItem, "outsideDrawerPanel")
    viewport = drawer.findChild(QQuickItem, "outsideDrawerViewport")
    assert isinstance(drawer_window, QQuickWindow)
    assert isinstance(outside_panel, QQuickItem)
    assert isinstance(viewport, QQuickItem)
    cases = [
        (window.property("leftPosition"), 180),
        (window.property("rightPosition"), 180),
        (window.property("topPosition"), 120),
        (window.property("bottomPosition"), 120),
    ]

    for position, full_extent in cases:
        drawer.setProperty("position", position)
        expected_window_geometry = _outside_window_geometry(
            window,
            position,
            full_extent,
            drawer.property("_outsideShadowSpread"),
        )

        assert QMetaObject.invokeMethod(drawer, "open")
        assert _wait_for(drawer_window.isVisible)
        assert _wait_for(
            lambda: 1 < drawer.property("_outsideExtent") < full_extent,
        )
        mid_open_geometry = (
            drawer_window.x(),
            drawer_window.y(),
            drawer_window.width(),
            drawer_window.height(),
        )
        panel_origin = outside_panel.mapToItem(
            drawer_window.contentItem(),
            QPointF(),
        )
        viewport_extent = (
            viewport.width()
            if position in (
                window.property("leftPosition"),
                window.property("rightPosition"),
            )
            else viewport.height()
        )
        assert mid_open_geometry == pytest.approx(expected_window_geometry)
        assert viewport_extent == pytest.approx(drawer.property("_outsideExtent"))
        assert (viewport.x(), viewport.y()) == pytest.approx(
            _outside_viewport_origin(
                window,
                position,
                full_extent,
                drawer.property("_outsideExtent"),
                drawer.property("_outsideShadowSpread"),
            )
        )
        assert (panel_origin.x(), panel_origin.y()) == pytest.approx(
            _outside_panel_origin(
                window,
                position,
                drawer.property("_outsideShadowSpread"),
            )
        )
        expected_content_size = (
            (full_extent - 32, outside_panel.height() - 32)
            if position in (
                window.property("leftPosition"),
                window.property("rightPosition"),
            )
            else (outside_panel.width() - 32, full_extent - 32)
        )
        assert (content_item.width(), content_item.height()) == pytest.approx(
            expected_content_size
        )

        assert _wait_for(
            lambda: drawer.property("_outsideExtent") == full_extent
        )
        assert (
            drawer_window.x(),
            drawer_window.y(),
            drawer_window.width(),
            drawer_window.height(),
        ) == pytest.approx(mid_open_geometry)

        assert QMetaObject.invokeMethod(drawer, "close")
        assert _wait_for(
            lambda: 1 < drawer.property("_outsideExtent") < full_extent,
        )
        mid_close_geometry = (
            drawer_window.x(),
            drawer_window.y(),
            drawer_window.width(),
            drawer_window.height(),
        )
        panel_origin = outside_panel.mapToItem(
            drawer_window.contentItem(),
            QPointF(),
        )
        viewport_extent = (
            viewport.width()
            if position in (
                window.property("leftPosition"),
                window.property("rightPosition"),
            )
            else viewport.height()
        )
        assert mid_close_geometry == pytest.approx(mid_open_geometry)
        assert viewport_extent == pytest.approx(drawer.property("_outsideExtent"))
        assert (viewport.x(), viewport.y()) == pytest.approx(
            _outside_viewport_origin(
                window,
                position,
                full_extent,
                drawer.property("_outsideExtent"),
                drawer.property("_outsideShadowSpread"),
            )
        )
        assert (panel_origin.x(), panel_origin.y()) == pytest.approx(
            _outside_panel_origin(
                window,
                position,
                drawer.property("_outsideShadowSpread"),
            )
        )
        assert _wait_for(lambda: not drawer_window.isVisible())

    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_drawer_outside_mode_closes_with_host_window(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, drawer, _content_item, _panel, warnings = (
        _create_scene()
    )
    try:
        drawer.setProperty("mode", window.property("outsideMode"))
        drawer_window = _drawer_window()
        assert isinstance(drawer_window, QQuickWindow)
        assert QMetaObject.invokeMethod(drawer, "open")
        assert _wait_for(drawer_window.isVisible)
        window.close()
        assert _wait_for(lambda: not drawer.property("opened"))
        assert _wait_for(lambda: not drawer_window.isVisible())
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
    assert tuple(
        candidate
        for candidate in QGuiApplication.topLevelWindows()
        if candidate.isVisible()
    ) == tuple(candidate for candidate in windows_before if candidate.isVisible())
