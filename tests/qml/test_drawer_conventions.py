# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Drawer geometry and scrim interaction contracts. Drawer 几何与遮罩交互合同。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QPoint,
    QTimer,
    QUrl,
    Qt,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "containers"
    / "Drawer"
    / "Drawer.qml"
)
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
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
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
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before


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
    return next(
        (
            window
            for window in QGuiApplication.topLevelWindows()
            if window.objectName() == "outsideDrawerWindow"
        ),
        None,
    )


def test_drawer_four_direction_geometry(drawer_scene):
    window, drawer, content_item, panel, warnings, windows_before = drawer_scene
    assert drawer.property("mode") == window.property("insideMode")
    assert window.property("insideMode") != window.property("outsideMode")
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

    extent = drawer.property("_outsideShadowExtent")
    cases = [
        (
            window.property("leftPosition"),
            (100 - 180 - extent, 120 - extent, 180 + extent, 400 + extent * 2),
            (extent, extent, 180, 400),
        ),
        (
            window.property("rightPosition"),
            (700, 120 - extent, 180 + extent, 400 + extent * 2),
            (0, extent, 180, 400),
        ),
        (
            window.property("topPosition"),
            (100 - extent, 120 - 120 - extent, 600 + extent * 2, 120 + extent),
            (extent, extent, 600, 120),
        ),
        (
            window.property("bottomPosition"),
            (100 - extent, 520, 600 + extent * 2, 120 + extent),
            (extent, 0, 600, 120),
        ),
    ]

    for position, window_geometry, panel_geometry in cases:
        drawer.setProperty("position", position)
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
        )
        assert _wait_for(
            lambda: (
                outside_panel.x(),
                outside_panel.y(),
                outside_panel.width(),
                outside_panel.height(),
            )
            == pytest.approx(panel_geometry)
        )
        assert content_item.parentItem() is outside_panel
        if position == window.property("rightPosition"):
            QTest.mouseClick(
                drawer_window,
                Qt.MouseButton.LeftButton,
                pos=QPoint(
                    round(outside_panel.x() + content_item.x() + 10),
                    round(outside_panel.y() + content_item.y() + 10),
                ),
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
        == pytest.approx((880, 260 - extent, 180 + extent, 420 + extent * 2))
    )
    _close(drawer)
    assert _wait_for(lambda: not drawer_window.isVisible())
    assert warnings == []
    assert _new_visible_windows(windows_before, window) == []


def test_drawer_outside_mode_closes_with_host_window(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, drawer, _content_item, _panel, warnings = (
        _create_scene()
    )
    drawer_window = _drawer_window()
    try:
        drawer.setProperty("mode", window.property("outsideMode"))
        assert QMetaObject.invokeMethod(drawer, "open")
        assert _wait_for(drawer_window.isVisible)
        window.close()
        assert _wait_for(lambda: not drawer.property("opened"))
        assert _wait_for(lambda: not drawer_window.isVisible())
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
    assert tuple(QGuiApplication.topLevelWindows()) == windows_before


def test_drawer_source_follows_conventions():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    path = PurePosixPath(SOURCE_PATH.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)
    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009"}
    ] == []
