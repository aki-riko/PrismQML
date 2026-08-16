# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""MatrixRain theme preset runtime contracts. MatrixRain 主题预设运行时契约。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QMetaObject, QObject, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import (
    QQmlApplicationEngine,
    QQmlComponent,
    QQmlEngine,
    QQmlExpression,
)

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
MATRIX_RAIN_SOURCE = ROOT / "prismqml" / "PrismQML" / "effects" / "MatrixRain.qml"
MATRIX_RAIN_CANVAS_SOURCE = (
    MATRIX_RAIN_SOURCE.parent / "_internal" / "MatrixRainCanvas.qml"
)


EXPECTED_PALETTES = {
    "classic": ("#00ff00", "#aaffaa", "#000000"),
    "cyan": ("#00ffff", "#aaffff", "#000011"),
    "amber": ("#ffaa00", "#ffff00", "#0a0500"),
    "red": ("#ff0040", "#ff8888", "#0a0000"),
    "purple": ("#aa00ff", "#ffaaff", "#050005"),
    "blue": ("#0088ff", "#88ccff", "#000510"),
    "white": ("#ffffff", "#ffffff", "#111111"),
    "pink": ("#ff69b4", "#ffb6c1", "#0a0008"),
    "gold": ("#ffd700", "#ffec8b", "#0a0800"),
    "lime": ("#32cd32", "#90ee90", "#000a00"),
    "orange": ("#ff6600", "#ffaa66", "#0a0300"),
    "teal": ("#008080", "#40e0d0", "#000505"),
    "neon": ("#39ff14", "#7fff00", "#000000"),
    "sunset": ("#ff4500", "#ff8c00", "#1a0a00"),
    "ocean": ("#006994", "#00ced1", "#001015"),
    "forest": ("#228b22", "#98fb98", "#000800"),
    "midnight": ("#191970", "#6495ed", "#000008"),
}

WINDOW_SOURCE = b"""import QtQuick
import QtQuick.Window
import PrismQML

Window {
    visible: true
    width: 64
    height: 64

    MatrixRain {
        objectName: "rain"
        anchors.fill: parent
        running: false
    }
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_matrix_rain(engine: QQmlApplicationEngine):
    engine.addImportPath(str(ROOT / "prismqml"))
    component = QQmlComponent(engine)
    component.setData(
        b"""import PrismQML
MatrixRain {
    width: 64
    height: 64
    running: false
}
""",
        QUrl("inline:p6c-matrix-rain-presets.qml"),
    )
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    instance = component.create(engine.rootContext())
    assert instance is not None, [error.toString() for error in component.errors()]
    return component, instance


def _create_matrix_rain_window(engine: QQmlApplicationEngine):
    engine.addImportPath(str(ROOT / "prismqml"))
    component = QQmlComponent(engine)
    component.setData(WINDOW_SOURCE, QUrl("inline:p6c-matrix-rain-frame.qml"))
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
    rain = window.findChild(QObject, "rain")
    assert rain is not None
    canvases = [
        child
        for child in rain.findChildren(QObject)
        if "Canvas" in child.metaObject().className()
    ]
    assert len(canvases) == 1
    for _ in range(50):
        if canvases[0].property("available"):
            break
        _pump(20)
    assert canvases[0].property("available") is True
    return component, window, rain, canvases[0]


def _palette(instance) -> tuple[str, str, str]:
    return tuple(
        instance.property(name).name(QColor.NameFormat.HexRgb)
        for name in ("mainColor", "headColor", "backgroundColor")
    )


def _evaluate(instance, source: str):
    expression = QQmlExpression(QQmlEngine.contextForObject(instance), instance, source)
    result = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    if isinstance(result, tuple):
        result, is_undefined = result
        assert not is_undefined
    return result


def test_matrix_rain_theme_presets_preserve_runtime_contract(qapp):
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = instance = None
    try:
        component, instance = _create_matrix_rain(engine)
        emitted: list[str] = []
        instance.themeApplied.connect(emitted.append)

        assert instance.property("running") is False
        assert _palette(instance) == EXPECTED_PALETTES["classic"]
        assert instance.getAvailableThemes().toVariant() == list(EXPECTED_PALETTES)

        for theme_name, expected_palette in EXPECTED_PALETTES.items():
            emitted.clear()
            instance.setTheme(theme_name)
            assert _palette(instance) == expected_palette
            assert emitted == [theme_name]

        emitted.clear()
        palette_before_unknown = _palette(instance)
        instance.setTheme("missing-theme")
        assert _palette(instance) == palette_before_unknown
        assert emitted == []
    finally:
        if instance is not None:
            instance.deleteLater()
        del component
        engine.deleteLater()
        _pump()


def test_matrix_rain_invalid_runtime_limits_stay_finite(qapp):
    engine = QQmlApplicationEngine()
    component = instance = None
    try:
        component, instance = _create_matrix_rain(engine)
        instance.setProperty("density", 0)
        instance.setProperty("speed", 0)
        instance.setProperty("interactionRadius", 0)
        _pump(20)
        assert instance.property("_safeDensity") == 0.5
        assert instance.property("_safeSpeed") == 0.1
        assert instance.property("_safeInteractionRadius") == 0
    finally:
        if instance is not None:
            instance.deleteLater()
        del component
        engine.deleteLater()
        _pump()


def test_matrix_rain_animation_timer_preserves_runtime_contract(qapp):
    engine = QQmlApplicationEngine()
    component = instance = None
    try:
        component, instance = _create_matrix_rain(engine)
        timer = instance.findChild(QObject, "matrixRainAnimationTimer")
        assert timer is not None
        assert timer.parent() is instance
        assert timer.property("host") is instance
        target_canvas = timer.property("targetCanvas")
        assert target_canvas is not None
        assert timer.metaObject().indexOfProperty("frameTime") >= 0
        assert timer.property("running") is False

        instance.setProperty("running", True)
        _pump(10)
        assert timer.property("running") is True

        instance.setProperty("speed", 0)
        assert instance.property("_safeSpeed") == 0.1
        assert timer.property("legacyIntervalMilliseconds") == 500
        instance.setProperty("speed", 5)
        assert timer.property("legacyIntervalMilliseconds") == 16

        assert _evaluate(timer, "_pendingStepScale = 0.5; takeStepScale()") == 0.5
        assert _evaluate(timer, "takeStepScale()") == 1

        instance.setProperty("paused", True)
        _pump(10)
        assert timer.property("running") is False
    finally:
        if instance is not None:
            instance.deleteLater()
        del component
        engine.deleteLater()
        _pump()


def test_matrix_rain_frame_updates_reuse_drop_array_without_property_change(qapp):
    engine = QQmlApplicationEngine()
    component = instance = None
    try:
        component, instance = _create_matrix_rain(engine)
        emitted: list[None] = []
        instance.dropsChanged.connect(lambda: emitted.append(None))

        _evaluate(instance, "drops = [1]")
        emitted.clear()
        _evaluate(instance, "drops = drops")
        assert emitted == []

        emitted.clear()
        assert _evaluate(instance, "drops[0] += 1; drops[0]") == 2
        assert emitted == []

        source = MATRIX_RAIN_SOURCE.read_text(encoding="utf-8")
        canvas_source = MATRIX_RAIN_CANVAS_SOURCE.read_text(encoding="utf-8")
        assert "MatrixRainInternal.MatrixRainCanvas" in source
        assert "animationDriver: animationTimer" in source
        assert "required property var animationDriver" in canvas_source
        assert "animationDriver.takeStepScale()" in canvas_source
        assert "_scaledProbability(host.fadeSpeed, stepScale)" in canvas_source
        assert "characterUpdateProbability = Math.min(1, stepScale)" in canvas_source
        assert "localCharacterSeeds[i] = Math.random()" in canvas_source
        assert "* stepScale" in canvas_source
        assert "root.drops = localDrops" not in canvas_source
        hot_loop = canvas_source.split("for (var i = 0; i < count; i++) {", 1)[1].split(
            "// Update rainbow offset", 1
        )[0]
        assert "root." not in hot_loop
    finally:
        if instance is not None:
            instance.deleteLater()
        del component
        engine.deleteLater()
        _pump()


def test_matrix_rain_offscreen_frame_advances_drop_without_property_change(qapp):
    engine = QQmlApplicationEngine()
    component = window = None
    try:
        component, window, rain, canvas = _create_matrix_rain_window(engine)
        _evaluate(rain, "direction = 'down'; cols = 1; drops = [0]")
        frame_driver = rain.findChild(QObject, "matrixRainAnimationTimer")
        assert frame_driver is not None
        _evaluate(frame_driver, "_pendingStepScale = 0.25")
        emitted: list[None] = []
        rain.dropsChanged.connect(lambda: emitted.append(None))

        assert QMetaObject.invokeMethod(canvas, "requestPaint") is True
        for _ in range(50):
            if _evaluate(rain, "drops[0]") > 0:
                break
            _pump(20)

        drop = _evaluate(rain, "drops[0]")
        assert 0.125 <= drop < 0.25
        assert emitted == []
    finally:
        if window is not None:
            window.close()
            window.deleteLater()
        del component
        engine.deleteLater()
        _pump()
