# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QML SVG icon migration regressions. QML SVG 图标迁移回归测试。"""

import pytest

from PySide6.QtCore import QEventLoop, QObject, QPoint, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


QML = b"""import QtQuick
import QtQuick.Window
import PrismQML

Window {
    visible: true
    width: 760
    height: 560
    color: "white"

    Timeline {
        objectName: "timeline"
        width: 300
        virtualized: false
        items: [{
            "title": "Info group",
            "status": "info",
            "cards": [{"text": "Info card", "status": "info"}]
        }]
    }

    Timeline {
        objectName: "virtualTimeline"
        y: 300
        width: 300
        height: 180
        virtualized: true
        items: [{
            "title": "Virtual info group",
            "status": "info",
            "cards": [{"text": "Virtual info card", "status": "info"}]
        }]
    }

    CycleWheelPicker {
        objectName: "wheel"
        x: 340
        width: 80
        visibleItems: 3
        items: ["One", "Two", "Three"]
        _hovered: true
    }

    Rating {
        objectName: "rating"
        x: 340
        y: 180
        value: 2
        maxValue: 3
    }
}
"""


def _pump(milliseconds: int = 50) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_window(engine: QQmlApplicationEngine) -> tuple[QQmlComponent, QQuickWindow]:
    component = QQmlComponent(engine)
    component.setData(QML, QUrl("inline:p6c2b-svg-icons.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    _pump(150)
    return component, window


def _walk_visual_tree(parent: QQuickItem):
    for child in parent.childItems():
        yield child
        yield from _walk_visual_tree(child)


def _icons(parent: QObject) -> list[QQuickItem]:
    assert isinstance(parent, QQuickItem)
    return [
        child
        for child in _walk_visual_tree(parent)
        if child.metaObject().indexOfProperty("isSvgIcon") >= 0
    ]


def _icons_named(parent: QObject, name: str) -> list[QQuickItem]:
    return [icon for icon in _icons(parent) if icon.property("icon") == name]


def _is_effectively_visible(item: QQuickItem) -> bool:
    current = item
    while current is not None:
        if not current.isVisible():
            return False
        current = current.parentItem()
    return True


def _visible_icons_named(parent: QObject, name: str) -> list[QQuickItem]:
    return [
        icon for icon in _icons_named(parent, name) if _is_effectively_visible(icon)
    ]


def _svg_image(icon: QQuickItem) -> QQuickItem:
    resolved_source = str(icon.property("_resolvedSource"))
    for child in icon.childItems():
        source = child.property("source")
        if isinstance(source, QUrl) and source.toString() == resolved_source:
            assert child.isVisible()
            assert child.property("progress") == 1.0
            return child
    raise AssertionError(f"No loaded SVG image for {icon.property('icon')}")


def _grab_svg_image(icon: QQuickItem) -> QImage:
    size = int(icon.property("iconSize"))
    grab_pointer = _svg_image(icon).grabToImage(QSize(size * 2, size * 2))
    grab_result = grab_pointer.data()
    assert grab_result is not None

    loop = QEventLoop()
    grab_result.ready.connect(loop.quit)
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(loop.quit)
    timeout.start(2000)
    if grab_result.image().isNull():
        loop.exec()
    assert timeout.isActive(), "Timed out while rendering migrated SVG icon"
    timeout.stop()

    image = grab_result.image()
    assert not image.isNull()
    return image


def _has_visible_pixel(image: QImage) -> bool:
    converted = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return any(
        converted.pixelColor(x, y).alpha() > 0
        for y in range(converted.height())
        for x in range(converted.width())
    )


@pytest.fixture
def icon_window(qapp):
    engine = QQmlApplicationEngine()
    register_types(engine)
    component, window = _create_window(engine)
    try:
        yield window
    finally:
        window.close()
        window.deleteLater()
        del component
        engine.deleteLater()


def _timeline_icons(window: QQuickWindow) -> list[QQuickItem]:
    timeline = window.findChild(QObject, "timeline")
    virtual_timeline = window.findChild(QObject, "virtualTimeline")
    assert timeline is not None
    assert virtual_timeline is not None
    timeline_info = _icons_named(timeline, "Info")
    assert sorted(icon.property("iconSize") for icon in timeline_info) == [8, 10]
    virtual_info = _visible_icons_named(virtual_timeline, "Info")
    assert [icon.property("iconSize") for icon in virtual_info] == [10]
    return timeline_info + virtual_info


def _wheel_icons(window: QQuickWindow) -> list[QQuickItem]:
    wheel = window.findChild(QObject, "wheel")
    assert wheel is not None
    up_icons = _icons_named(wheel, "ChevronUp")
    down_icons = _icons_named(wheel, "ChevronDown")
    assert len(up_icons) == len(down_icons) == 1
    assert up_icons[0].property("iconSize") == 14
    assert down_icons[0].property("iconSize") == 14
    return up_icons + down_icons


def _rating_icons(window: QQuickWindow) -> list[QQuickItem]:
    rating = window.findChild(QObject, "rating")
    assert rating is not None
    filled_stars = _icons_named(rating, "StarFilled")
    outline_stars = _icons_named(rating, "StarOutline")
    assert len(filled_stars) == 2
    assert len(outline_stars) == 1
    assert all(icon.property("iconSize") == 24 for icon in filled_stars + outline_stars)
    return filled_stars + outline_stars


def _assert_svg_icons_render(icons: list[QQuickItem]) -> None:
    for icon in icons:
        assert icon.property("isSvgIcon") is True
        assert str(icon.property("_resolvedSource")).endswith(
            f"/{icon.property('icon')}.svg"
        )
        assert _has_visible_pixel(_grab_svg_image(icon))


def _assert_wheel_press(window: QQuickWindow) -> None:
    wheel = window.findChild(QObject, "wheel")
    assert wheel is not None
    up_icon = _icons_named(wheel, "ChevronUp")[0]
    point = QPoint(380, 16)
    QTest.mouseMove(window, point)
    QTest.mousePress(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point
    )
    _pump(10)
    assert up_icon.property("iconSize") == 12
    QTest.mouseRelease(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point
    )
    _pump(10)
    assert up_icon.property("iconSize") == 14


def _click(window: QQuickWindow, point: QPoint) -> None:
    QTest.mousePress(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point
    )
    QTest.mouseRelease(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point
    )
    _pump(10)


def _assert_rating_interaction(window: QQuickWindow) -> None:
    rating = window.findChild(QObject, "rating")
    assert rating is not None
    first_star = _icons_named(rating, "StarFilled")[0]
    QTest.mouseMove(window, QPoint(352, 192))
    _pump(150)
    assert first_star.scale() == pytest.approx(1.15)
    _click(window, QPoint(404, 192))
    assert rating.property("value") == 3
    assert len(_icons_named(rating, "StarFilled")) == 3


def test_migrated_font_icons_use_svg_assets_and_render(icon_window):
    icons = _timeline_icons(icon_window)
    icons += _wheel_icons(icon_window)
    icons += _rating_icons(icon_window)
    _assert_svg_icons_render(icons)


def test_migrated_icons_preserve_pressed_hover_and_click_behavior(icon_window):
    _assert_wheel_press(icon_window)
    _assert_rating_interaction(icon_window)
