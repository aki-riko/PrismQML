# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Manual D3D11 acceptance probe for the Avatar circle mask. 头像圆形遮罩人工验收探针。

Automated QML regressions run under the ``offscreen`` QPA platform, whose scene
graph falls back to the Software backend; that backend executes no shader
effects, so the avatar layer mask cannot be judged there (see
``tests/qml/test_avatar_bitmap_paint_reliability.py`` and
``tests/qml/test_color_overlay_contract.py``). This probe opens a real window on
Direct3D11 and measures the shipped rendering instead:

1. circle: the bitmap is masked to a circle, so the box corners stay background;
2. centre: the bitmap content reaches the centre pixel;
3. antialiasing: the circle rim blends instead of stair-stepping;
4. device resolution: a one-device-pixel checkerboard source survives at a
   fractional device pixel ratio, while the retired Canvas/FBO path blurs it
   (both are measured side by side in the same frame);
5. border: the parent border ring outside the masked child is not clipped away.

自动 QML 回归运行在 ``offscreen`` QPA 平台, 其场景图回退到 Software 后端, 该后端
不执行着色器效果, 因此无法在自动门禁中判定头像层遮罩(见
``tests/qml/test_avatar_bitmap_paint_reliability.py`` 与
``tests/qml/test_color_overlay_contract.py``)。本探针在 Direct3D11 上打开真实窗口,
直接测量实际渲染: 圆形裁剪、中心位图内容、边缘抗锯齿、分数设备像素比下的设备分辨率
清晰度(与已退役的 Canvas/FBO 路径同帧并排对比), 以及父级描边不被遮罩裁掉。

Run 运行::

    .\\.venv\\Scripts\\python.exe .\\scripts\\manual\\avatar_circle_mask_probe.py

A fractional device pixel ratio is required for check 4; on a 100% display pass
``QT_SCALE_FACTOR`` (it multiplies the native scale factor, so use e.g. ``1.5``
there and ``1`` on an already scaled display). The report is written to
``.artifacts/avatar-circle-mask/`` and the exit code is non-zero when any check
fails. 第 4 项检查需要分数设备像素比; 在 100% 显示上请传 ``QT_SCALE_FACTOR``
(它按倍数作用于系统缩放, 100% 显示用 ``1.5``, 已缩放显示用 ``1``)。报告写入
``.artifacts/avatar-circle-mask/``, 任一检查失败时退出码非零。
"""

from __future__ import annotations

import base64
import json
import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Keep bytecode under the shared artifact root before importing the package.
# 导入项目包前把字节码缓存集中到统一产物根目录。
_CACHE_PATH = Path(
    os.environ.get("PRISM_ARTIFACT_ROOT", str(ROOT / ".artifacts"))
) / "python" / "pycache"
os.environ["PYTHONPYCACHEPREFIX"] = str(_CACHE_PATH)
sys.pycache_prefix = str(_CACHE_PATH)

REPORT_DIR = ROOT / ".artifacts" / "avatar-circle-mask"
AVATAR_SIZE = 80.0
BITMAP_RGB = (255, 0, 255)
CHECKER_RGB = (0, 255, 0)
BACKGROUND_RGB = (255, 255, 255)
BORDER_RGB = (255, 0, 0)
MIN_RIM_BLEND_RATIO = 0.2
MIN_CRISP_RATIO = 0.75
MAX_LEGACY_CRISP_RATIO = 0.35
MIN_CRISP_GAIN = 0.3

from PySide6.QtCore import (  # noqa: E402
    QBuffer,
    QEventLoop,
    QIODevice,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QColor, QImage  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent  # noqa: E402
from PySide6.QtQuick import (  # noqa: E402
    QQuickItem,
    QQuickWindow,
    QSGRendererInterface,
)
from PySide6.QtWidgets import QApplication  # noqa: E402

from prismqml import configure_qml_environment, register_types  # noqa: E402

SCENE = """
import QtQuick
import QtQuick.Window
import QtQuick.Effects
import PrismQML

Window {
    id: window

    property string solidUri: ""
    property string checkerUri: ""

    width: 460
    height: 140
    visible: true
    color: "#ffffff"

    // Shipped Avatar 正式 Avatar
    Avatar {
        objectName: "avatar"
        x: 10
        y: 20
        size: 80
        source: window.solidUri
    }

    // Inset masked child inside a bordered parent: the parent ring lies outside
    // the child circle, so it must stay visible. 带描边父级内的内缩遮罩子项。
    Rectangle {
        objectName: "borderHost"
        x: 110
        y: 20
        width: 80
        height: 80
        radius: 40
        color: "transparent"
        antialiasing: true
        border.width: 4
        border.color: "#ff0000"

        Image {
            id: borderImage
            objectName: "borderImage"
            anchors.fill: parent
            anchors.margins: 12
            source: window.solidUri
            fillMode: Image.PreserveAspectCrop
            asynchronous: false
            layer.enabled: status === Image.Ready
            layer.smooth: true
            layer.effect: MultiEffect {
                maskEnabled: true
                maskThresholdMin: Enums.mask.thresholdMin
                maskSpreadAtMin: Enums.mask.spreadFull
                maskSource: ShaderEffectSource {
                    sourceItem: Rectangle {
                        width: borderImage.width
                        height: borderImage.height
                        radius: borderImage.width / 2
                        antialiasing: true
                    }
                    smooth: true
                }
            }
        }
    }

    // Retired Canvas/FBO reference 已退役 Canvas/FBO 参照
    Item {
        objectName: "legacy"
        x: 210
        y: 20
        width: 80
        height: 80

        Image {
            id: legacySource
            source: window.checkerUri
            visible: false
            asynchronous: false
        }

        Canvas {
            id: legacyCanvas
            anchors.fill: parent
            antialiasing: true
            renderStrategy: Canvas.Threaded
            renderTarget: Canvas.FramebufferObject

            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                if (legacySource.status !== Image.Ready) return
                var w = width, h = height, r = Math.min(w, h) / 2
                ctx.beginPath()
                ctx.arc(w / 2, h / 2, r, 0, Math.PI * 2)
                ctx.closePath()
                ctx.clip()
                var imgW = legacySource.sourceSize.width
                var imgH = legacySource.sourceSize.height
                var scale = Math.max(w / imgW, h / imgH)
                ctx.drawImage(legacySource, (w - imgW * scale) / 2,
                              (h - imgH * scale) / 2, imgW * scale, imgH * scale)
            }

            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()
            onVisibleChanged: requestPaint()
        }
    }

    // Shipped path with the same checkerboard source 同一棋盘格的正式路径
    Avatar {
        objectName: "crispAvatar"
        x: 310
        y: 20
        size: 80
        source: window.checkerUri
    }
}
"""


def _png_data_uri(image: QImage) -> str:
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer, "PNG")
    return "data:image/png;base64," + base64.b64encode(bytes(buffer.data())).decode()


def _checkerboard(size: int) -> QImage:
    """One-device-pixel checkerboard. 单设备像素棋盘格。"""
    image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    for y in range(size):
        for x in range(size):
            colour = (
                QColor(*BITMAP_RGB) if (x + y) % 2 == 0 else QColor(*CHECKER_RGB)
            )
            image.setPixelColor(x, y, colour)
    return image


def _solid(size: int) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(QColor(*BITMAP_RGB))
    return image


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 5_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _stable_frame(window: QQuickWindow) -> QImage:
    previous = QImage()
    stable_frames = 0
    for _ in range(80):
        current = window.grabWindow()
        assert not current.isNull(), "D3D11 grabWindow returned an empty image"
        if current == previous:
            stable_frames += 1
            if stable_frames == 3:
                return current
        else:
            stable_frames = 0
        previous = current
        _pump()
    raise RuntimeError("frame did not stabilize within 1.6 s")


def _rgb(image: QImage, ratio: float, x: float, y: float) -> tuple:
    colour = image.pixelColor(int(round(x * ratio)), int(round(y * ratio)))
    return (colour.red(), colour.green(), colour.blue())


def _rim_blend_ratio(
    image: QImage, ratio: float, left: float, top: float, size: float
) -> float:
    """Share of rim pixels that blend instead of stair-stepping. 边缘混合像素比例。"""
    centre_x = (left + size / 2) * ratio
    centre_y = (top + size / 2) * ratio
    radius = size / 2 * ratio
    blended = 0
    total = 0
    for y in range(int(round(top * ratio)), int(round((top + size) * ratio))):
        for x in range(int(round(left * ratio)), int(round((left + size) * ratio))):
            distance = math.hypot(x + 0.5 - centre_x, y + 0.5 - centre_y)
            if abs(distance - radius) > 1.5:
                continue
            total += 1
            if image.pixelColor(x, y).getRgb()[:3] not in (
                BITMAP_RGB,
                BACKGROUND_RGB,
            ):
                blended += 1
    return blended / max(total, 1)


def _crisp_ratio(
    image: QImage, ratio: float, left: float, top: float, size: float
) -> float:
    """Share of interior pixels that keep an exact source colour. 源色保真像素比例。"""
    exact = 0
    total = 0
    for y in range(
        int(round((top + 8) * ratio)), int(round((top + size - 8) * ratio))
    ):
        for x in range(
            int(round((left + 8) * ratio)), int(round((left + size - 8) * ratio))
        ):
            total += 1
            if image.pixelColor(x, y).getRgb()[:3] in (BITMAP_RGB, CHECKER_RGB):
                exact += 1
    return exact / max(total, 1)


def main() -> int:
    QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.Direct3D11)
    configure_qml_environment()
    app = QApplication([])
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE.encode("utf-8"), QUrl.fromLocalFile(str(ROOT / "probe.qml")))
    if not _wait_for(lambda: component.status() != QQmlComponent.Status.Loading):
        raise RuntimeError("probe scene did not finish loading")
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]

    graphics_api = window.rendererInterface().graphicsApi().name
    assert _wait_for(window.isExposed)
    _pump(300)

    # The source bitmap must match the item's device pixels for check 4.
    # 第 4 项检查要求源位图与 item 的设备像素一致。
    ratio = window.grabWindow().width() / 460.0
    device_size = max(int(round(AVATAR_SIZE * ratio)), 16)
    window.setProperty("solidUri", _png_data_uri(_solid(device_size)))
    window.setProperty("checkerUri", _png_data_uri(_checkerboard(device_size)))
    _pump(700)

    frame = _stable_frame(window)
    ratio = frame.width() / 460.0
    avatar = window.findChild(QQuickItem, "avatar")
    border_host = window.findChild(QQuickItem, "borderHost")
    legacy = window.findChild(QQuickItem, "legacy")
    crisp = window.findChild(QQuickItem, "crispAvatar")
    assert None not in (avatar, border_host, legacy, crisp)

    checks = {
        "graphics_api": graphics_api,
        "device_pixel_ratio": ratio,
        "source_device_size": device_size,
        "avatar_centre": _rgb(frame, ratio, 50, 60),
        "avatar_corner": _rgb(frame, ratio, 13, 23),
        "rim_blend_ratio": _rim_blend_ratio(frame, ratio, 10, 20, AVATAR_SIZE),
        "border_rim": _rgb(frame, ratio, 112, 60),
        "shipped_crisp_ratio": _crisp_ratio(frame, ratio, 310, 20, AVATAR_SIZE),
        "legacy_crisp_ratio": _crisp_ratio(frame, ratio, 210, 20, AVATAR_SIZE),
    }
    failures = []
    if graphics_api != "Direct3D11":
        failures.append(f"graphics api is {graphics_api}, not Direct3D11")
    if float(ratio).is_integer():
        failures.append(
            f"device pixel ratio is {ratio}, an integer; checks 4 needs a "
            "fractional ratio (set QT_SCALE_FACTOR)"
        )
    if checks["avatar_centre"] != BITMAP_RGB:
        failures.append(
            f"bitmap content missing at the avatar centre: {checks['avatar_centre']}"
        )
    if checks["avatar_corner"] != BACKGROUND_RGB:
        failures.append(
            f"circle mask did not clip the box corner: {checks['avatar_corner']}"
        )
    if checks["rim_blend_ratio"] < MIN_RIM_BLEND_RATIO:
        failures.append(
            f"circle rim is not antialiased: blend ratio {checks['rim_blend_ratio']:.3f}"
        )
    if checks["border_rim"] != BORDER_RGB:
        failures.append(
            f"parent border was clipped away by the child mask: {checks['border_rim']}"
        )
    if checks["shipped_crisp_ratio"] < MIN_CRISP_RATIO:
        failures.append(
            "shipped avatar is not rendered at device resolution: "
            f"crisp ratio {checks['shipped_crisp_ratio']:.3f}"
        )
    if checks["legacy_crisp_ratio"] > MAX_LEGACY_CRISP_RATIO:
        failures.append(
            "retired Canvas reference is unexpectedly crisp: "
            f"{checks['legacy_crisp_ratio']:.3f}"
        )
    if (
        checks["shipped_crisp_ratio"] - checks["legacy_crisp_ratio"]
        < MIN_CRISP_GAIN
    ):
        failures.append(
            "shipped avatar does not improve on the retired Canvas path: "
            f"{checks['shipped_crisp_ratio']:.3f} vs "
            f"{checks['legacy_crisp_ratio']:.3f}"
        )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "probe": "avatar_circle_mask_probe",
        "requested_graphics_api": "Direct3D11",
        "checks": {
            key: (list(value) if isinstance(value, tuple) else value)
            for key, value in checks.items()
        },
        "thresholds": {
            "min_rim_blend_ratio": MIN_RIM_BLEND_RATIO,
            "min_crisp_ratio": MIN_CRISP_RATIO,
            "max_legacy_crisp_ratio": MAX_LEGACY_CRISP_RATIO,
            "min_crisp_gain": MIN_CRISP_GAIN,
        },
        "failures": failures,
    }
    report_path = REPORT_DIR / "avatar_circle_mask_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("AVATAR_CIRCLE_MASK_PROBE", json.dumps(report["checks"], ensure_ascii=False))
    print("REPORT", report_path)
    for failure in failures:
        print("FAILURE", failure)
    window.close()
    component.deleteLater()
    engine.deleteLater()
    app.processEvents()
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
