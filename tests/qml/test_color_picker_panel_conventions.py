# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Color picker panel runtime regressions. 颜色选择面板运行时回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QPoint,
    QTimer,
    Qt,
    QUrl,
)
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlProperty
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "color-picker-panel-runtime.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/inputs/ColorPicker/_internal"

Window {
    width: 360
    height: 280
    visible: true
    color: Enums.transparent

    ColorPickerPanel {
        objectName: "panel"
        x: 40
        y: 30
    }
}
"""
ANIMATION_SETTLE_MS = 150


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1200) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump(10)
        elapsed += 10
    return predicate()


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
    window.requestActivate()
    assert _wait_for(window.isActive)
    _pump(50)
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump(20)


def _visual_descendants(root: QQuickItem) -> list[QQuickItem]:
    result = []
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def _panel_parts(window: QQuickWindow):
    panel = window.findChild(QQuickItem, "panel")
    assert panel is not None
    descendants = _visual_descendants(panel)
    canvases = [
        item for item in descendants
        if item.metaObject().className() == "QQuickCanvasItem"
    ]
    selectors = [
        item for item in descendants
        if item.metaObject().className().startswith("QQuickRectangle")
        and item.width() == pytest.approx(16)
        and item.height() == pytest.approx(16)
    ]
    assert len(canvases) == 1
    assert len(selectors) == 1
    return panel, canvases[0], selectors[0]


def _read(item: QQuickItem, name: str):
    prop = QQmlProperty(item, name)
    assert prop.isValid(), (item.metaObject().className(), name)
    return prop.read()


def _new_visible_windows(windows_before, root_window):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and window is not root_window
        and not any(window is existing for existing in windows_before)
    ]


def _assert_color(actual: QColor, expected: QColor) -> None:
    assert actual.getRgbF() == pytest.approx(expected.getRgbF(), abs=1 / 65535)


def test_color_picker_panel_preserves_defaults_selector_and_clamp(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene()
    try:
        panel, canvas, selector = _panel_parts(window)
        assert panel.property("implicitWidth") == pytest.approx(260)
        assert panel.property("implicitHeight") == pytest.approx(200)
        assert panel.property("hue") == pytest.approx(0.5)
        assert panel.property("saturation") == pytest.approx(1.0)
        assert panel.property("brightness") == pytest.approx(1.0)
        assert (canvas.width(), canvas.height()) == pytest.approx((260, 200))
        assert (selector.x(), selector.y()) == pytest.approx((122, 0))

        panel.setProperty("saturation", 0.5)
        _pump(ANIMATION_SETTLE_MS)
        assert (selector.x(), selector.y()) == pytest.approx((122, 92))

        panel.setProperty("hue", -1.0)
        panel.setProperty("saturation", 2.0)
        _pump(ANIMATION_SETTLE_MS)
        assert (selector.x(), selector.y()) == pytest.approx((0, 0))

        panel.setProperty("hue", 2.0)
        panel.setProperty("saturation", -1.0)
        _pump(ANIMATION_SETTLE_MS)
        assert (selector.x(), selector.y()) == pytest.approx((244, 184))

        panel.setProperty("brightness", 1.0)
        panel.setProperty("saturation", 0.0)
        _assert_color(_read(selector, "border.color"), QColor("black"))
        panel.setProperty("brightness", 0.0)
        panel.setProperty("saturation", 1.0)
        _assert_color(_read(selector, "border.color"), QColor("white"))
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)


def test_color_picker_panel_maps_real_mouse_clicks_and_emits(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene()
    try:
        panel, _canvas, selector = _panel_parts(window)
        changed = []
        panel.colorChanged.connect(lambda hue, saturation: changed.append((hue, saturation)))

        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(105, 180),
        )
        _pump(ANIMATION_SETTLE_MS)
        assert (panel.property("hue"), panel.property("saturation")) == pytest.approx(
            (0.25, 0.25)
        )
        assert (selector.x(), selector.y()) == pytest.approx((57, 142))

        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(235, 80),
        )
        _pump(ANIMATION_SETTLE_MS)
        assert (panel.property("hue"), panel.property("saturation")) == pytest.approx(
            (0.75, 0.75)
        )
        assert (selector.x(), selector.y()) == pytest.approx((187, 42))
        assert changed == pytest.approx([(0.25, 0.25), (0.75, 0.75)])
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)


def test_color_picker_panel_repaints_rendered_canvas_on_brightness(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene()
    try:
        panel, canvas, _selector = _panel_parts(window)
        painted = []
        canvas.painted.connect(lambda: painted.append(True))

        before = window.grabWindow().pixelColor(170, 130)
        panel.setProperty("brightness", 0.25)
        _pump(100)
        after = window.grabWindow().pixelColor(170, 130)

        assert painted
        assert before.getRgb() == pytest.approx((128, 255, 255, 255), abs=1)
        assert after.getRgb() == pytest.approx((32, 64, 64, 255), abs=1)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
