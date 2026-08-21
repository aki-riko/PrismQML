# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""EffectsPage MatrixRain control regressions. 特效页数字雨控制回归。"""

from __future__ import annotations

import math
from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QPoint,
    QPointF,
    QTimer,
    Qt,
    QUrl,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from examples.resources import register_gallery_resources
from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
PAGE_PATH = ROOT / "examples" / "pages" / "EffectsPage.qml"


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1600) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def _matrix_sliders(page: QQuickItem) -> dict[tuple[float, float], QQuickItem]:
    sliders = {}
    for obj in page.findChildren(QObject):
        meta = obj.metaObject()
        if not isinstance(obj, QQuickItem):
            continue
        if (
            meta.indexOfProperty("snapMode") < 0
            or meta.indexOfProperty("_dragging") < 0
        ):
            continue
        key = (float(obj.property("from")), float(obj.property("to")))
        sliders[key] = obj
    return sliders


def _matrix_rain(page: QQuickItem) -> QQuickItem:
    matches = []
    for obj in page.findChildren(QObject):
        meta = obj.metaObject()
        if not isinstance(obj, QQuickItem):
            continue
        if meta.indexOfProperty("density") < 0 or meta.indexOfProperty("cols") < 0:
            continue
        if meta.indexOfProperty("cellSize") >= 0:
            matches.append(obj)
    assert len(matches) == 1
    return matches[0]


def _default_handle(slider: QQuickItem) -> QQuickItem:
    matches = [
        item
        for item in _visual_descendants(slider)
        if item.metaObject().indexOfProperty("_ratio") >= 0
    ]
    assert len(matches) == 1
    return matches[0]


def _window_point(
    window: QQuickWindow, item: QQuickItem, x: float, y: float
) -> QPoint:
    point = item.mapToItem(window.contentItem(), QPointF(x, y))
    return QPoint(round(point.x()), round(point.y()))


def _create_scene():
    register_gallery_resources()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(PAGE_PATH)))
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    page = component.create(engine.rootContext())
    assert isinstance(page, QQuickItem)
    window = QQuickWindow()
    window.resize(1260, 900)
    page.setParentItem(window.contentItem())
    page.setWidth(window.width())
    page.setHeight(window.height())
    window.show()
    window.requestActivate()
    assert _wait_for(window.isActive)
    assert _wait_for(lambda: len(_matrix_sliders(page)) == 4)
    return windows_before, engine, component, window, page, warnings


def _dispose_scene(windows_before, engine, component, window, page) -> None:
    window.close()
    page.setParentItem(None)
    page.deleteLater()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()
    assert tuple(QGuiApplication.topLevelWindows()) == windows_before


@pytest.fixture
def effects_page_scene(qapp):
    scene = _create_scene()
    try:
        yield scene[3], scene[4], scene[5]
    finally:
        _dispose_scene(*scene[:5])


def test_matrix_control_steps_match_fractional_ranges(effects_page_scene):
    _, page, warnings = effects_page_scene
    sliders = _matrix_sliders(page)

    assert sliders[(0.2, 4.0)].property("stepSize") == pytest.approx(0.1)
    assert sliders[(8.0, 28.0)].property("stepSize") == pytest.approx(1.0)
    assert sliders[(0.5, 2.0)].property("stepSize") == pytest.approx(0.1)
    assert sliders[(0.02, 0.15)].property("stepSize") == pytest.approx(0.01)
    assert sliders[(0.5, 2.0)].property("value") == pytest.approx(0.7)
    rain = _matrix_rain(page)
    expected_columns = math.ceil(rain.width() / rain.property("cellSize") * 0.7)
    assert _wait_for(lambda: rain.property("cols") == expected_columns)
    assert warnings == []


def test_effects_page_does_not_expose_matrix_rain_api(effects_page_scene):
    _, _, warnings = effects_page_scene
    source = PAGE_PATH.read_text(encoding="utf-8")

    assert "MatrixRain API" not in source
    assert "API说明 API documentation" not in source
    assert warnings == []


def test_lower_density_value_produces_fewer_columns(effects_page_scene):
    _, page, warnings = effects_page_scene
    density_slider = _matrix_sliders(page)[(0.5, 2.0)]
    rain = _matrix_rain(page)

    density_slider.setProperty("value", 0.5)
    expected_low = math.ceil(rain.width() / rain.property("cellSize") * 0.5)
    assert _wait_for(lambda: rain.property("cols") == expected_low)

    density_slider.setProperty("value", 1.5)
    expected_high = math.ceil(rain.width() / rain.property("cellSize") * 1.5)
    assert _wait_for(lambda: rain.property("cols") == expected_high)
    assert expected_low < expected_high
    assert warnings == []


def test_font_size_change_rebuilds_column_geometry(effects_page_scene):
    _, page, warnings = effects_page_scene
    font_size_slider = _matrix_sliders(page)[(8.0, 28.0)]
    rain = _matrix_rain(page)

    font_size_slider.setProperty("value", 28)
    assert _wait_for(lambda: rain.property("cellSize") == 30)
    expected_columns = math.ceil(
        rain.width() / rain.property("cellSize") * rain.property("_safeDensity")
    )

    assert _wait_for(lambda: rain.property("cols") == expected_columns)
    assert warnings == []


def test_fade_slider_drag_keeps_a_fractional_value(effects_page_scene):
    window, page, warnings = effects_page_scene
    fade_slider = _matrix_sliders(page)[(0.02, 0.15)]
    handle = _default_handle(fade_slider)
    start = _window_point(window, handle, handle.width() / 2, handle.height() / 2)
    target = _window_point(
        window,
        fade_slider,
        fade_slider.width() * 0.75,
        fade_slider.height() / 2,
    )

    QTest.mouseMove(window, start)
    QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseMove(window, target, 20)
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=target)
    QTest.mouseMove(window, QPoint(window.width() - 10, window.height() - 10))

    assert _wait_for(lambda: fade_slider.property("value") > 0.05)
    assert fade_slider.property("value") == pytest.approx(0.12, abs=0.01)
    assert _matrix_rain(page).property("fadeSpeed") == pytest.approx(
        fade_slider.property("value")
    )
    assert warnings == []
