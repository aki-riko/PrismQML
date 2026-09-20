# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Hidden D3D11 acrylic navigation pixel probe. 隐藏式 D3D11 亚克力像素探针。"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import runpy
import sys


ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ROOT
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_PROCESS = runpy.run_path(str(REPO_ROOT / "scripts" / "test_process.py"))
prepare_automated_test_process = TEST_PROCESS["prepare_automated_test_process"]
prepare_automated_test_process(None)

from PySide6.QtCore import QEventLoop, QTimer, QUrl  # noqa: E402
from PySide6.QtGui import QColor, QImage  # noqa: E402
from PySide6.QtQml import QQmlComponent, QQmlEngine  # noqa: E402
from PySide6.QtQuick import (  # noqa: E402
    QQuickItem,
    QQuickWindow,
    QSGRendererInterface,
)
from PySide6.QtWidgets import QApplication  # noqa: E402

from prismqml import Skin, Theme, register_types, setSkin, setTheme  # noqa: E402
from prismqml.python.runtime.window_services import get_acrylic_helper  # noqa: E402


LOGGER = logging.getLogger(__name__)
PANEL_WIDTH = 320
TITLE_HEIGHT = 48
INITIAL_HEIGHT = 800
RESIZED_HEIGHT = 640
SCENE_SOURCE = f"""
import QtQuick
import PrismQML

Window {{
    id: root
    property bool acrylicOn: true

    width: 360
    height: {INITIAL_HEIGHT}
    visible: false
    color: "transparent"

    Item {{
        x: 0
        y: -{TITLE_HEIGHT}
        width: {PANEL_WIDTH}
        height: root.height + {TITLE_HEIGHT}
        clip: true

        NavigationView {{
            objectName: "probeNavigationView"
            anchors.fill: parent
            isExpanded: true
            showReturnButton: false
            model: [{{ "key": "p1", "text": "P One" }}]
            backgroundColor: "transparent"
            acrylicEnabled: root.acrylicOn && isExpanded
        }}
    }}
}}
"""


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _source_image(height: int, top: str, bottom: str) -> QImage:
    image = QImage(PANEL_WIDTH, height, QImage.Format.Format_ARGB32)
    image.fill(QColor(top))
    bottom_color = QColor(bottom)
    for y in range(height // 2, height):
        for x in range(PANEL_WIDTH):
            image.setPixelColor(x, y, bottom_color)
    return image


def _publish_source(view: QQuickItem, image: QImage) -> str:
    helper = get_acrylic_helper()
    helper.imageProvider.setImage(image)
    source = helper.getImageUrl()
    assert view.setProperty("acrylicImageSource", source)
    return source


def _grab_settled(window: QQuickWindow, frames: int = 8) -> QImage:
    grabbed = QImage()
    for _ in range(frames):
        grabbed = window.grabWindow()
        _pump()
    assert not grabbed.isNull()
    return grabbed


def _pixel(image: QImage, window: QQuickWindow, x: float, y: float) -> QColor:
    ratio = image.width() / window.width()
    px = min(image.width() - 1, max(0, round(x * ratio)))
    py = min(image.height() - 1, max(0, round(y * ratio)))
    return image.pixelColor(px, py)


def _rgba(color: QColor) -> list[int]:
    return [color.red(), color.green(), color.blue(), color.alpha()]


def _samples(image: QImage, window: QQuickWindow) -> dict[str, list[int]]:
    height = float(window.height())
    points = {
        "top_outside": (PANEL_WIDTH - 1.5, 1.5),
        "bottom_outside": (PANEL_WIDTH - 1.5, height - 1.5),
        "top_inside": (PANEL_WIDTH - 8.0, 8.0),
        "bottom_inside": (PANEL_WIDTH - 8.0, height - 8.0),
        "upper_center": (PANEL_WIDTH / 2, height / 2 - 12),
        "lower_center": (PANEL_WIDTH / 2, height / 2 + 12),
    }
    return {name: _rgba(_pixel(image, window, *point)) for name, point in points.items()}


def _capture_pair(window: QQuickWindow, view: QQuickItem) -> dict[str, object]:
    on_image = _grab_settled(window)
    assert window.setProperty("acrylicOn", False)
    off_image = _grab_settled(window, 4)
    assert window.setProperty("acrylicOn", True)
    _grab_settled(window, 4)
    return {
        "on": _samples(on_image, window),
        "off": _samples(off_image, window),
        "size": [on_image.width(), on_image.height()],
        "expanded": bool(view.property("isExpanded")),
    }


def _create_scene(engine: QQmlEngine):
    component = QQmlComponent(engine)
    url = QUrl.fromLocalFile(str(Path(__file__).with_suffix(".qml")))
    component.setData(SCENE_SOURCE.encode("utf-8"), url)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    return component, window


def _exercise_lifecycle(window: QQuickWindow, view: QQuickItem) -> dict[str, object]:
    _publish_source(view, _source_image(INITIAL_HEIGHT, "#ff0000", "#00ff00"))
    initial = _capture_pair(window, view)
    _publish_source(view, _source_image(INITIAL_HEIGHT, "#0000ff", "#ff0000"))
    updated = _capture_pair(window, view)
    window.setHeight(RESIZED_HEIGHT)
    _publish_source(view, _source_image(RESIZED_HEIGHT, "#ff0000", "#00ff00"))
    resized = _capture_pair(window, view)
    setTheme(Theme.DARK)
    dark = _capture_pair(window, view)
    assert view.setProperty("isExpanded", False)
    _grab_settled(window, 4)
    assert view.setProperty("isExpanded", True)
    reexpanded = _capture_pair(window, view)
    return {
        "initial": initial,
        "updated": updated,
        "resized": resized,
        "dark": dark,
        "reexpanded": reexpanded,
    }


def _create_runtime():
    QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.Direct3D11)
    app = QApplication.instance() or QApplication([])
    setTheme(Theme.LIGHT)
    setSkin(Skin.FLUENT)
    engine = QQmlEngine()
    register_types(engine)
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    component, window = _create_scene(engine)
    window.create()
    view = window.findChild(QQuickItem, "probeNavigationView")
    assert view is not None
    return app, engine, component, window, view, warnings


def _dispose(app, engine, component, window) -> None:
    window.destroy()
    component.deleteLater()
    engine.deleteLater()
    app.processEvents()


def main() -> int:
    args = _arguments()
    app, engine, component, window, view, warnings = _create_runtime()
    report = _exercise_lifecycle(window, view)
    backend = window.rendererInterface().graphicsApi()
    assert backend == QSGRendererInterface.GraphicsApi.Direct3D11, backend
    report.update(
        backend=backend.name,
        warnings=warnings,
        window_visible=window.isVisible(),
    )
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    LOGGER.info("Native acrylic probe completed: %s", args.output)
    _dispose(app, engine, component, window)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    raise SystemExit(main())
