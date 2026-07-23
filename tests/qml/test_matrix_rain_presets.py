# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""MatrixRain theme preset runtime contracts. MatrixRain 主题预设运行时契约。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]


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


def _palette(instance) -> tuple[str, str, str]:
    return tuple(
        instance.property(name).name(QColor.NameFormat.HexRgb)
        for name in ("mainColor", "headColor", "backgroundColor")
    )


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
