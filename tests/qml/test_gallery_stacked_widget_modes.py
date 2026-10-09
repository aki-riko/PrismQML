# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Gallery StackedWidget 动画类型展示合同测试。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QElapsedTimer,
    QEvent,
    QEventLoop,
    QObject,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from examples.resources import register_gallery_resources
from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
PAGE_PATH = ROOT / "examples" / "pages" / "NavigationPage.qml"
# (base animation, orientation) shown by the Gallery, in display order.
# Gallery 按顺序展示的 (基础动画, 轴向) 组合。
EXPECTED_TILES = (
    ("opacity", None),
    ("popup", None),
    ("popdown", None),
    ("slide", "horizontal"),
    ("slide", "vertical"),
    ("slide_fade", "horizontal"),
    ("slide_fade", "vertical"),
    ("card", "horizontal"),
    ("card", "vertical"),
    ("zoom", None),
)
_ENUM_PROPERTIES = {
    "opacity": "opacityMode",
    "popup": "popupMode",
    "popdown": "popdownMode",
    "slide": "slideMode",
    "slide_fade": "slideFadeMode",
    "card": "cardMode",
    "zoom": "zoomMode",
}
_ORIENTATION_PROPERTIES = {
    "horizontal": "horizontalOrientation",
    "vertical": "verticalOrientation",
}
_ENUM_SOURCE = b"""
import QtQuick
import PrismQML

QtObject {
    readonly property int opacityMode: Enums.animation.opacity
    readonly property int popupMode: Enums.animation.popup
    readonly property int popdownMode: Enums.animation.popdown
    readonly property int slideMode: Enums.animation.slide
    readonly property int slideFadeMode: Enums.animation.slide_fade
    readonly property int cardMode: Enums.animation.card
    readonly property int zoomMode: Enums.animation.zoom
    readonly property int horizontalOrientation: Qt.Horizontal
    readonly property int verticalOrientation: Qt.Vertical
}
"""


def _tile_label(mode: str, orientation) -> str:
    return mode if orientation is None else f"{mode} ({orientation})"


def _pump(milliseconds: int = 80) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _dispose(obj) -> None:
    if obj is None:
        return
    obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def _wait_ready(component: QQmlComponent, timeout_ms: int = 2_000) -> None:
    elapsed = QElapsedTimer()
    elapsed.start()
    while component.status() == QQmlComponent.Status.Loading and elapsed.elapsed() < timeout_ms:
        _pump(10)
    assert not component.isError(), [error.toString() for error in component.errors()]
    assert component.status() == QQmlComponent.Status.Ready


def _enum_modes(engine: QQmlApplicationEngine):
    component = QQmlComponent(engine)
    component.setData(_ENUM_SOURCE, QUrl("inline:gallery-stacked-widget-modes"))
    _wait_ready(component)
    modes = component.create(engine.rootContext())
    assert modes is not None, [error.toString() for error in component.errors()]
    # The component owns the object; keep both alive for the whole test.
    # 组件持有该对象的所有权；两者都要在整个用例期间存活。
    modes.setParent(engine)
    return component, modes


def _stacked_widget_tiles(page: QQuickItem):
    tiles = []
    for card in page.findChildren(QQuickItem):
        if "ComponentCard" not in card.metaObject().className():
            continue
        labels = card.findChildren(QObject, "componentCardLabel")
        stacks = [
            child
            for child in card.findChildren(QQuickItem)
            if "StackedWidget" in child.metaObject().className()
        ]
        if len(labels) != 1 or len(stacks) != 1:
            continue
        tiles.append((labels[0].property("text"), stacks[0]))
    return tiles


def test_gallery_shows_base_animations_with_orientation(qapp):
    """Gallery 必须展示"基础动画 + 轴向"的组合，且不再枚举 *_horizontal/*_vertical。"""
    register_gallery_resources()
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    host = QQuickWindow()
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(PAGE_PATH)))
    _wait_ready(component)
    page = component.create(engine.rootContext())
    modes_component, modes = _enum_modes(engine)

    try:
        assert page is not None, [error.toString() for error in component.errors()]
        assert isinstance(page, QQuickItem)
        page.setParentItem(host.contentItem())
        page.setWidth(1000)
        page.setHeight(760)
        _pump(200)

        tiles = _stacked_widget_tiles(page)
        assert [label for label, _stack in tiles] == [
            _tile_label(mode, orientation) for mode, orientation in EXPECTED_TILES
        ]
        for (label, stack), (mode, orientation) in zip(tiles, EXPECTED_TILES):
            assert stack.property("animationType") == modes.property(
                _ENUM_PROPERTIES[mode]
            ), label
            if orientation is None:
                continue
            assert stack.property("animationOrientation") == modes.property(
                _ORIENTATION_PROPERTIES[orientation]
            ), label

        assert warnings == []
    finally:
        _dispose(page)
        _dispose(component)
        _dispose(modes)
        _dispose(modes_component)
        _dispose(host)
        engine.collectGarbage()
        engine.clearComponentCache()
        _dispose(engine)
