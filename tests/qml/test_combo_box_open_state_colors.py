# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""ComboBox expanded-state colour regressions. 下拉框展开态颜色回归。

Expanding the dropdown must not overlay any colour on the control: the open state
keeps the resting fill of its style and outranks hover/press.
展开下拉不得给控件叠加任何颜色: 展开态锁定该样式的静止底色, 并优先于 hover/press。
"""

from __future__ import annotations

import os
from pathlib import Path

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QColor, QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import Skin, Theme, register_types, setSkin, setTheme


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "combo-box-open-state-colors.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    readonly property color restingFill: Enums.stateColor.controlBg
    readonly property color pressedFill: Enums.stateColor.controlBgPressed
    readonly property color accentFill: Enums.accentColor

    width: 260
    height: 260
    visible: true
    color: Enums.backgroundColor

    ComboBoxCore {
        objectName: "plain"
        x: 30
        y: 40
        width: 200
        model: ["Alpha", "Beta"]
        currentIndex: 0
    }

    ComboBoxCore {
        objectName: "primary"
        x: 30
        y: 110
        width: 200
        model: ["Primary1", "Primary2"]
        currentIndex: 0
        style: Enums.comboBox.style_primary
    }

    ComboBoxCore {
        objectName: "transparent"
        x: 30
        y: 180
        width: 200
        model: ["Ghost1", "Ghost2"]
        currentIndex: 0
        style: Enums.comboBox.style_transparent
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _stable_window_image(window: QQuickWindow) -> QImage:
    previous = QImage()
    stable_frames = 0
    for _ in range(30):
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
    raise AssertionError("ComboBox frame did not stabilize within 600 ms")


def _sample(image: QImage, scale: float, point) -> tuple[int, int, int, int]:
    # grabWindow returns device pixels, so a scaled display needs the ratio applied.
    # grabWindow 返回设备像素, 缩放显示下采样点需按比例换算。
    color = image.pixelColor(
        int(round(point[0] * scale)), int(round(point[1] * scale))
    )
    return (color.red(), color.green(), color.blue(), color.alpha())


def _fill_rgba(color: QColor) -> tuple[int, int, int, int]:
    return (color.red(), color.green(), color.blue(), color.alpha())


def _interior_point(combo: QQuickItem) -> tuple[float, float]:
    # Sit just below the top border at half width: the label is vertically centred
    # with padding above it, so the probe clears the glyphs whatever font the
    # platform resolves (headless runs draw fallback boxes), and it stays far left
    # of the chevron that rotates while the list is open.
    # 取上边框下方、水平居中位置: 文本垂直居中且上方留白, 因此无论平台解析到什么
    # 字体采样点都不会落到字形上 (无头环境会画缺字方框); 同时远离展开时旋转的箭头。
    return (combo.x() + combo.width() * 0.5, combo.y() + 3)


# Chevron column kept out of the comparison 箭头所在列不参与比较
ARROW_ZONE = 44


def _control_band(image: QImage, scale: float, combo: QQuickItem) -> QImage:
    # The control surface left of the chevron, inside the 1 px border: exactly what
    # the open state must leave untouched.
    # 控件表面去掉箭头列并排除 1px 边框: 这正是展开态必须原样保留的区域。
    left = int(round((combo.x() + 1) * scale))
    top = int(round((combo.y() + 1) * scale))
    width = int(round((combo.width() - ARROW_ZONE - 2) * scale))
    height = int(round((combo.height() - 2) * scale))
    assert width > 0 and height > 0
    return image.copy(left, top, width, height)


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
    register_types(engine)
    engine.addImportPath(str(ROOT / "prismqml"))
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
    assert _wait_for(window.isExposed)
    return engine, component, window, warnings


def _dispose_scene(qapp, engine, component, window) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def test_combo_box_expanded_state_overlays_no_colour(qapp):
    """展开下拉后控件像素必须与静止态完全一致。"""
    setTheme(Theme.LIGHT)
    setSkin(Skin.FLUENT)
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, warnings = _create_scene()
    try:
        resting = _fill_rgba(window.property("restingFill"))
        pressed = _fill_rgba(window.property("pressedFill"))
        # Without this the regression could pass on a theme where both fills agree.
        # 否则在两者恰好相同的主题下该回归会失去意义。
        assert resting != pressed

        baseline = _stable_window_image(window)
        scale = baseline.width() / float(window.width())
        canvas = _sample(baseline, scale, (window.width() - 10, 10))
        cases = (
            ("plain", resting),
            ("primary", _fill_rgba(window.property("accentFill"))),
            # The transparent style keeps alpha 0, so the window colour shows through.
            # 透明样式保持 alpha 0, 因此呈现窗口底色。
            ("transparent", canvas),
        )

        for name, expected in cases:
            combo = window.findChild(QQuickItem, name)
            assert combo is not None, name
            point = _interior_point(combo)
            closed = _stable_window_image(window)
            assert _sample(closed, scale, point) == expected, name

            combo.showPopup()
            assert _wait_for(lambda: combo.property("isOpen")), name
            assert combo.property("popupVisible") is True
            opened = _stable_window_image(window)
            assert _sample(opened, scale, point) == expected, name
            assert _sample(opened, scale, point) != pressed, name
            # The expanded control must not merely match the resting fill, it must be
            # the very same surface: the chevron is the only part allowed to move.
            # 展开后的控件不能只是底色相同, 而必须是同一个表面: 只允许箭头变化。
            assert _control_band(closed, scale, combo) == _control_band(
                opened, scale, combo
            ), name

            combo.closePopup()
            assert _wait_for(lambda: not combo.property("isOpen")), name
            assert _wait_for(lambda: not combo.property("popupVisible")), name

        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)
        setSkin(Skin.FLUENT)
        setTheme(Theme.LIGHT)
        assert _new_visible_windows(windows_before) == []
