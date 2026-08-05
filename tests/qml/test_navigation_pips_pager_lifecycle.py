# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Navigation PipsPager delegate lifecycle regressions. 导航点页器委托生命周期回归。"""

from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QPoint,
    QPointF,
    QTimer,
    Qt,
    QUrl,
)
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "navigation-pips-pager-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    property int dynamicOrientation: Qt.Horizontal
    readonly property int animationDuration: Enums.duration.normal

    width: 260
    height: 260
    visible: true
    color: Enums.backgroundColor

    PipsPager {
        id: pager

        objectName: "pager"
        anchors.centerIn: parent
        pageCount: 5
        currentIndex: 2
        visiblePipCount: 5
        orientation: root.dynamicOrientation
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1_600) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _branch(pager: QQuickItem, class_name: str) -> QQuickItem:
    matches = [
        child
        for child in pager.childItems()
        if child.metaObject().className() == class_name
    ]
    assert len(matches) == 1, [
        child.metaObject().className() for child in pager.childItems()
    ]
    return matches[0]


def _pips(branch: QQuickItem) -> list[QQuickItem]:
    return [
        child
        for child in branch.childItems()
        if child.metaObject().className().startswith("QQuickRectangle_QML_")
    ]


def _stable_window_image(window: QQuickWindow) -> QImage:
    previous = QImage()
    stable_frames = 0
    for _ in range(40):
        current = window.grabWindow()
        assert not current.isNull()
        if current == previous:
            stable_frames += 1
            if stable_frames == 3:
                return current
        else:
            stable_frames = 0
        previous = current
        _pump()
    raise AssertionError("PipsPager frame did not stabilize within 800 ms")


def _point_for(window: QQuickWindow, item: QQuickItem) -> QPoint:
    point = item.mapToItem(
        window.contentItem(), QPointF(item.width() / 2, item.height() / 2)
    )
    return QPoint(round(point.x()), round(point.y()))


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
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
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    window.requestActivate()
    assert _wait_for(window.isActive)
    pager = window.findChild(QQuickItem, "pager")
    assert pager is not None
    return engine, component, window, pager, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def test_navigation_pips_pager_loads_only_active_direction_delegates(qapp):
    """Keep only active delegates while preserving clicks and restored pixels.

    仅保留当前方向委托，同时保持点击与方向恢复像素。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, pager, warnings = _create_scene()
    clicked = []
    pager.pageClicked.connect(clicked.append)
    try:
        row = _branch(pager, "QQuickRow")
        column = _branch(pager, "QQuickColumn")
        assert row.isVisible()
        assert not column.isVisible()
        assert len(_pips(row)) == 5
        assert _pips(column) == []
        QTest.mouseMove(window, QPoint(10, 250))
        _pump(int(window.property("animationDuration")) + 50)
        horizontal_image = _stable_window_image(window)

        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            _point_for(window, _pips(row)[4]),
        )
        assert _wait_for(lambda: pager.property("currentIndex") == 4)
        assert clicked == [4]

        pager.setProperty("currentIndex", 2)
        window.setProperty("dynamicOrientation", Qt.Orientation.Vertical)
        assert _wait_for(lambda: not row.isVisible() and column.isVisible())
        assert _pips(row) == []
        assert len(_pips(column)) == 5
        assert column.width() > 0 and column.height() > 0
        assert len({item.y() for item in _pips(column)}) == 5

        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            _point_for(window, _pips(column)[0]),
        )
        assert _wait_for(lambda: pager.property("currentIndex") == 0)
        assert clicked == [4, 0]

        pager.setProperty("currentIndex", 2)
        window.setProperty("dynamicOrientation", Qt.Orientation.Horizontal)
        assert _wait_for(lambda: row.isVisible() and not column.isVisible())
        assert len(_pips(row)) == 5
        assert _pips(column) == []
        assert row.width() > 0 and row.height() > 0
        assert len({item.x() for item in _pips(row)}) == 5
        QTest.mouseMove(window, QPoint(10, 250))
        _pump(int(window.property("animationDuration")) + 50)
        assert _stable_window_image(window) == horizontal_image
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []
