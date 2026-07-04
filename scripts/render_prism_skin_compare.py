# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Render real QML screenshots for Prism Design three-skin comparison."""

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "windows" if sys.platform.startswith("win") else "offscreen")
os.environ.setdefault("QML_XHR_ALLOW_FILE_READ", "1")
os.environ.setdefault("QT_LOGGING_RULES", "qt.text.font.db=false")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import Qt, QTimer, QUrl  # noqa: E402
from PySide6.QtQuick import QQuickWindow, QSGRendererInterface  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from prismqml import Skin, Theme, register_types, setSkin, setTheme  # noqa: E402
from prismqml.python.core.logger import error, info, warning  # noqa: E402


OUTPUT_DIR = PROJECT_ROOT / "examples" / "resources" / "image" / "prism-design"
SHOT_SIZE = (520, 360)

QML_SCENE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: win

    visible: true
    width: 520
    height: 360
    color: Enums.backgroundColor

    readonly property string skinLabel: Enums.isPrismDesign ? "Prism Design"
                                      : (Enums.isNeobrutalism ? "Neobrutalism" : "Fluent")
    readonly property string themeLabel: Enums.isDark ? "Dark" : "Light"

    Card {
        anchors.fill: parent
        anchors.margins: Enums.spacing.xl
        autoHeight: false
        cardType: Enums.card.type_default

        Column {
            anchors.fill: parent
            anchors.margins: Enums.spacing.xl
            spacing: Enums.spacing.l

            Row {
                width: parent.width
                spacing: Enums.spacing.l

                Column {
                    width: parent.width - badge.width - parent.spacing
                    spacing: Enums.spacing.xxs

                    Text {
                        text: win.skinLabel
                        font.family: Enums.fontFamily
                        font.pixelSize: Enums.typography.titleLarge
                        font.bold: true
                        color: Enums.textColor.primary
                    }

                    Text {
                        text: win.themeLabel + " / shared scene"
                        font.family: Enums.fontFamily
                        font.pixelSize: Enums.typography.caption
                        color: Enums.textColor.secondary
                    }
                }

                Tag {
                    id: badge
                    text: Enums.skin
                }
            }

            Row {
                spacing: Enums.spacing.m
                Button { style: Enums.button.style_primary; text: "Deploy" }
                Button { text: "Preview" }
                LineEdit { width: 170; placeholderText: "Filter runs" }
            }

            Row {
                spacing: Enums.spacing.l

                Column {
                    width: 220
                    spacing: Enums.spacing.m

                    ComboBox {
                        width: parent.width
                        model: ["All states", "Success", "Warning"]
                        currentIndex: 0
                    }

                    Progress {
                        width: parent.width
                        type: Enums.progress.type_bar_filled
                        value: 68
                        text: "68%"
                    }

                    InfoBar {
                        width: parent.width
                        title: "Build ready"
                        content: "Token-driven UI"
                        severity: "success"
                        duration: 0
                    }
                }

                ChartView {
                    width: 220
                    height: 150
                    title: "Signals"
                    chartData: [
                        { "label": "UI", "value": 42 },
                        { "label": "QML", "value": 68 },
                        { "label": "Docs", "value": 34 }
                    ]
                }
            }

            Row {
                spacing: Enums.spacing.s
                Skeleton { width: 140; height: 12 }
                Skeleton { width: 84; height: 12 }
                Skeleton { shape: Enums.skeleton.shape_circle; width: 30; height: 30 }
            }
        }
    }
}
"""


def _render(
    engine: QQmlApplicationEngine,
    keep_alive: list[tuple[QQmlComponent, object]],
    scene_name: str,
    skin: Skin,
    theme: Theme,
    output_path: Path,
) -> None:
    setTheme(theme)
    setSkin(skin)

    component = QQmlComponent(engine)
    component.setData(QML_SCENE.encode("utf-8"), QUrl("inline"))
    if component.isError():
        raise RuntimeError("; ".join(error.toString() for error in component.errors()))

    window = component.create(engine.rootContext())
    if window is None:
        raise RuntimeError("; ".join(error.toString() for error in component.errors()))

    app = QApplication.instance()
    for _ in range(80):
        app.processEvents()
        time.sleep(0.005)

    image = window.grabWindow()
    if image.isNull() or image.width() < SHOT_SIZE[0] or image.height() < SHOT_SIZE[1]:
        raise RuntimeError(f"{scene_name}: invalid image {image.width()}x{image.height()}")
    if image.width() != SHOT_SIZE[0] or image.height() != SHOT_SIZE[1]:
        image = image.scaled(
            SHOT_SIZE[0],
            SHOT_SIZE[1],
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    _assert_nonblank(scene_name, image)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(output_path)):
        raise RuntimeError(f"{scene_name}: failed to save {output_path}")

    window.setVisible(False)
    window.close()
    keep_alive.append((component, window))
    info(f"rendered {scene_name}: {output_path}", tag="PrismCompare")


def _assert_nonblank(scene_name: str, image) -> None:
    colors = set()
    for x in range(0, image.width(), max(1, image.width() // 12)):
        for y in range(0, image.height(), max(1, image.height() // 8)):
            color = image.pixelColor(x, y)
            colors.add((color.red(), color.green(), color.blue(), color.alpha()))
    if len(colors) < 8:
        raise RuntimeError(f"{scene_name}: screenshot looks blank ({len(colors)} colors)")


def main() -> int:
    try:
        QQuickWindow.setGraphicsApi(QSGRendererInterface.OpenGL)
    except RuntimeError as exc:
        warning(f"OpenGL renderer selection skipped: {exc}", tag="PrismCompare")

    app = QApplication.instance() or QApplication(sys.argv)
    keep_app = app
    _ = keep_app
    engine = QQmlApplicationEngine()
    register_types(engine)
    keep_alive: list[tuple[QQmlComponent, object]] = []

    cases = [
        ("fluent", Skin.FLUENT),
        ("neobrutalism", Skin.NEOBRUTALISM),
        ("prism-design", Skin.PRISM_DESIGN),
    ]
    themes = [
        ("light", Theme.LIGHT),
        ("dark", Theme.DARK),
    ]

    try:
        for theme_name, theme in themes:
            for skin_name, skin in cases:
                scene_name = f"{skin_name}-{theme_name}"
                output_path = OUTPUT_DIR / f"skin-compare-{scene_name}.png"
                _render(engine, keep_alive, scene_name, skin, theme, output_path)
    except Exception as exc:
        error(f"Prism skin compare render failed: {exc}", tag="PrismCompare", exc_info=True)
        return 1
    finally:
        setTheme(Theme.LIGHT)
        setSkin(Skin.FLUENT)

    for _, window in reversed(keep_alive):
        window.setVisible(False)
        window.close()
        window.deleteLater()

    QTimer.singleShot(0, app.quit)
    app.exec()
    keep_alive.clear()
    engine.collectGarbage()

    return 0


if __name__ == "__main__":
    sys.exit(main())
