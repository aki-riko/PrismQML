# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Hidden D3D11 acrylic navigation pixel probe. 隐藏式 D3D11 亚克力像素探针。"""

from __future__ import annotations

import argparse
import json
import logging
import os
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
from PySide6.QtGui import QColor, QImage, QPainter  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlEngine  # noqa: E402
from PySide6.QtQuick import (  # noqa: E402
    QQuickItem,
    QQuickWindow,
    QSGRendererInterface,
)
from PySide6.QtWidgets import QApplication  # noqa: E402

from prismqml import (  # noqa: E402
    Skin,
    Theme,
    configure_qml_environment,
    register_types,
    setSkin,
    setTheme,
)
from prismqml.python.runtime import get_svg_provider  # noqa: E402
from prismqml.python.runtime.window_services import get_acrylic_helper  # noqa: E402
from prismqml.python.window.mica_window import _gaussian_blur_image  # noqa: E402

from examples.resources import register_gallery_resources  # noqa: E402


LOGGER = logging.getLogger(__name__)
PANEL_WIDTH = 320
TITLE_HEIGHT = 48
INITIAL_HEIGHT = 800
RESIZED_HEIGHT = 640
SETTINGS_PAGE_INDEX = 13
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


def _window_dpr(window: QQuickWindow) -> float:
    """Frame scale factor of this window 该窗口的帧缩放系数。"""
    ratio = float(window.devicePixelRatio())
    if ratio > 0:
        return ratio
    screen = QGuiApplication.primaryScreen()
    if screen is not None and float(screen.devicePixelRatio()) > 0:
        return float(screen.devicePixelRatio())
    return 1.0


def _rgba(color: QColor) -> list[int]:
    return [color.red(), color.green(), color.blue(), color.alpha()]


def _composite_hidden_window(image: QImage) -> QImage:
    """Composite the transparent hidden window over its light system backdrop.

    将隐藏窗口的透明像素合成到浅色系统背景上。该画面来自真实 QML 壳，
    并非桌面 DWM 截图。
    """
    result = QImage(image.size(), QImage.Format.Format_ARGB32_Premultiplied)
    result.fill(QColor("#f3f3f3"))
    result.setDevicePixelRatio(image.devicePixelRatio())
    painter = QPainter(result)
    painter.drawImage(0, 0, image)
    painter.end()
    return result


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


def _write_gallery_config() -> Path:
    config_path = Path(os.environ["PRISMQML_CONFIG_FILE"])
    config_path.write_text(
        json.dumps(
            {
                "Window": {
                    "WindowType": 0,
                    "MicaEnabled": True,
                    "LazyLoading": False,
                    "DwmShadow": False,
                },
                "Appearance": {
                    "Theme": "light",
                    "Skin": "fluent",
                    "Language": "zh_CN",
                },
            }
        ),
        encoding="utf-8",
    )
    return config_path


def _wait_for_gallery_shell(window: QQuickWindow) -> QQuickItem:
    for _ in range(120):
        _grab_settled(window, 1)
        navigation = window.property("navigationView")
        if isinstance(navigation, QQuickItem):
            return navigation
    raise AssertionError("Gallery WindowsSplit navigation did not load")


def _find_visual_item(window: QQuickWindow, object_name: str) -> QQuickItem | None:
    pending = [window.contentItem()]
    while pending:
        item = pending.pop()
        if item.objectName() == object_name:
            return item
        pending.extend(item.childItems())
    return None


def _wait_for_settings_page(window: QQuickWindow) -> None:
    assert window.setProperty("currentIndex", SETTINGS_PAGE_INDEX)
    for _ in range(120):
        _grab_settled(window, 1)
        if _find_visual_item(window, "windowTypeSettingsCard") is not None:
            return
    raise AssertionError("Gallery SettingsPage did not load")


def _gallery_samples(
    image: QImage, window: QQuickWindow, pane_width: float
) -> dict[str, list[int]]:
    height = float(window.height())
    points = {
        "corner_top_inset": (pane_width - 1, 1),
        "corner_bottom_inset": (pane_width - 1, height - 2),
        "edge_top_outside": (pane_width + 1, 1),
        "edge_center_inside": (pane_width - 1, height / 2),
        "edge_center_outside": (pane_width + 1, height / 2),
        "edge_bottom_outside": (pane_width + 1, height - 2),
        "body_upper": (pane_width / 2, height / 3),
        "body_lower": (pane_width / 2, height * 2 / 3),
    }
    return {name: _rgba(_pixel(image, window, *point)) for name, point in points.items()}


def _gallery_capture(
    window: QQuickWindow, pane_width: float
) -> tuple[QImage, dict[str, list[int]]]:
    image = _composite_hidden_window(_grab_settled(window, 4))
    return image, _gallery_samples(image, window, pane_width)


def _create_gallery_runtime():
    configure_qml_environment()
    setTheme(Theme.LIGHT)
    setSkin(Skin.FLUENT)
    engine = QQmlApplicationEngine()
    register_types(engine)
    assert register_gallery_resources()
    engine.addImageProvider("svg", get_svg_provider())
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.load(QUrl.fromLocalFile(str(REPO_ROOT / "examples" / "main.qml")))
    roots = engine.rootObjects()
    assert roots
    root = roots[0]
    window = root.property("windowInstance")
    assert isinstance(window, QQuickWindow)
    window.create()
    navigation = _wait_for_gallery_shell(window)
    return engine, root, window, navigation, warnings


def _prepare_gallery_acrylic(
    window: QQuickWindow, navigation: QQuickItem
) -> float:
    _wait_for_settings_page(window)
    assert window.setProperty("_micaBackdropReady", True)
    assert window.setProperty("_animOpacity", 1.0)
    assert window.setProperty("_animScale", 1.0)
    assert navigation.setProperty("isExpanded", False)
    collapsed = _composite_hidden_window(_grab_settled(window, 8))
    ratio = collapsed.width() / window.width()
    pane_width = float(navigation.width())
    capture = collapsed.copy(
        0,
        0,
        round(pane_width * ratio),
        collapsed.height(),
    )
    helper = get_acrylic_helper()
    helper.imageProvider.setImage(_gaussian_blur_image(capture, helper.blurRadius))
    assert navigation.setProperty("_acrylicSource", helper.getImageUrl())
    assert navigation.setProperty("_acrylicImageReady", True)
    assert navigation.setProperty("isExpanded", True)
    _grab_settled(window, 20)
    return pane_width


def _find_acrylic_layer(navigation: QQuickItem) -> QQuickItem:
    background = next(
        item
        for item in navigation.childItems()
        if item.metaObject().className().startswith("NavigationPanelBackground")
    )
    return next(
        item
        for item in background.childItems()
        if item.metaObject().indexOfProperty("acrylicTintColor") >= 0
    )


def _capture_gallery_layers(
    window: QQuickWindow, navigation: QQuickItem, pane_width: float
) -> tuple[QImage, dict[str, object], dict[str, object]]:
    shadow = _find_visual_item(window, "navigationPanelShadow")
    assert shadow is not None
    shadow_on_image, shadow_on = _gallery_capture(window, pane_width)
    shadow.setVisible(False)
    shadow_off_image, shadow_off = _gallery_capture(window, pane_width)
    acrylic = _find_acrylic_layer(navigation)
    acrylic_on = _gallery_samples(shadow_off_image, window, pane_width)
    acrylic.setVisible(False)
    _acrylic_off_image, acrylic_off = _gallery_capture(window, pane_width)
    return (
        shadow_on_image,
        {"on": shadow_on, "off": shadow_off},
        {"on": acrylic_on, "off": acrylic_off},
    )


def _gallery_report(
    window: QQuickWindow,
    navigation: QQuickItem,
    warnings: list[str],
    pane_width: float,
    image: QImage,
    shadow: dict[str, object],
    acrylic: dict[str, object],
) -> dict[str, object]:
    backend = window.rendererInterface().graphicsApi()
    return {
        "backend": backend.name,
        # Reference values in docs/acrylic-panel-handover.md were tuned on a DPR 1.5
        # frame; publish the frame ratio so consumers can tell whether the sampled
        # pixels are comparable.
        # docs/acrylic-panel-handover.md 的参考值调定于 DPR 1.5 的帧; 发布帧比例, 便于
        # 消费方判断采样像素是否可比。
        "frame_dpr": _window_dpr(window),
        "warnings": warnings,
        "window_visible": window.isVisible(),
        "window_class": window.metaObject().className().split("_QMLTYPE_", 1)[0],
        "settings_page_loaded": (
            _find_visual_item(window, "windowTypeSettingsCard") is not None
        ),
        "expanded": bool(navigation.property("isExpanded")),
        "pane_width": pane_width,
        "size": [image.width(), image.height()],
        "acrylic_source": "collapsed_qml_composite_not_desktop_dwm",
        "shadow": shadow,
        "acrylic": acrylic,
    }


def _exercise_gallery_shell(app: QApplication) -> dict[str, object]:
    engine, root, window, navigation, warnings = _create_gallery_runtime()
    pane_width = _prepare_gallery_acrylic(window, navigation)
    image, shadow, acrylic = _capture_gallery_layers(
        window, navigation, pane_width
    )
    result = _gallery_report(
        window, navigation, warnings, pane_width, image, shadow, acrylic
    )
    window.destroy()
    root.deleteLater()
    engine.deleteLater()
    app.processEvents()
    return result


def _dispose(app, engine, component, window) -> None:
    window.destroy()
    component.deleteLater()
    engine.deleteLater()
    app.processEvents()


def main() -> int:
    args = _arguments()
    _write_gallery_config()
    app, engine, component, window, view, warnings = _create_runtime()
    report = _exercise_lifecycle(window, view)
    backend = window.rendererInterface().graphicsApi()
    assert backend == QSGRendererInterface.GraphicsApi.Direct3D11, backend
    report.update(
        backend=backend.name,
        warnings=warnings,
        window_visible=window.isVisible(),
    )
    _dispose(app, engine, component, window)
    report["gallery_shell"] = _exercise_gallery_shell(app)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    LOGGER.info("Native acrylic probe completed: %s", args.output)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    raise SystemExit(main())
