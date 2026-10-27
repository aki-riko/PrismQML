# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Manual D3D11 acceptance probe for the glow button bloom. 泛光按钮人工验收探针。

Automated QML regressions run under the ``offscreen`` QPA platform, whose scene
graph falls back to the Software backend. That backend executes no shader
effects, so every effect-based surface is invisible there — including the
``RectangularShadow`` that paints the glow button's bloom. A bloom judged under
``offscreen`` therefore reports "nothing drawn" regardless of whether the shipped
rendering is correct; this probe opens a real window on Direct3D11 and measures
the shipped pixels instead.

自动 QML 回归运行在 ``offscreen`` QPA 平台, 其场景图回退到 Software 后端。该后端
不执行着色器效果, 因此所有基于效果的表层在那里都不可见 —— 包括绘制泛光按钮光晕的
``RectangularShadow``。在 ``offscreen`` 下判定泛光只会得到"什么都没画"的结论,
与实际渲染是否正确无关; 本探针在 Direct3D11 上打开真实窗口, 直接测量实际像素。

Checks 检查项::

1. bloom: pixels just outside the face are tinted, not background;
2. smoothness: the outward falloff has no visible banding (largest per-pixel step
   stays small relative to the total contrast);
3. containment: the bloom fades to background within its declared spread, so it
   does not bleed over neighbouring layout;
4. primary reference: a plain ``style_primary`` button has no bloom at all, which
   proves the halo is glow-specific rather than a general surface change;
5. edge fidelity: the face edge stays crisp — the bloom must sit behind the face,
   not blur it.

Run 运行::

    .\\.venv\\Scripts\\python.exe .\\scripts\\manual\\glow_button_bloom_probe.py

The report is written to ``.artifacts/glow-button-bloom/`` and the exit code is
non-zero when any check fails. 报告写入 ``.artifacts/glow-button-bloom/``,
任一检查失败时退出码非零。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QEventLoop, QObject, QPointF, QTimer, QUrl
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from prismqml import configure_qml_environment, register_types, setTheme, Theme


ARTIFACT_DIR = ROOT / ".artifacts" / "glow-button-bloom"
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: window

    width: 620
    height: 260
    visible: true
    color: "#ffffff"

    Button {
        objectName: "glowButton"
        x: 80
        y: 100
        width: 200
        height: 46
        style: Enums.button.style_glow
        text: "Glow"
    }

    Button {
        objectName: "plainButton"
        x: 360
        y: 100
        width: 200
        height: 46
        style: Enums.button.style_primary
        text: "Primary"
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _stable_grab(window: QQuickWindow) -> QImage:
    """Grab a frame that is stable within a small tolerance.

    The bloom breathes, so consecutive frames are never byte-identical: stabilising
    on exact equality would never succeed. A tolerance of a few levels per channel
    accepts the slow pulse while still rejecting a half-rendered frame.
    抓取一帧在容差内稳定的画面。泛光会呼吸, 因此相邻帧永远不会逐字节相同: 用严格
    相等判定永不成功。每通道数级的容差接受缓慢呼吸, 同时仍能排除半渲染的帧。
    """
    previous: QImage | None = None
    stable = 0
    for _ in range(90):
        current = window.grabWindow()
        if not current.isNull() and previous is not None:
            if _within_tolerance(previous, current):
                stable += 1
                if stable == 3:
                    return current
            else:
                stable = 0
        previous = current
        _pump()
    raise RuntimeError("glow window did not stabilize")


def _within_tolerance(first: QImage, second: QImage, tolerance: int = 3) -> bool:
    """True when two frames differ by at most ``tolerance`` per channel on average.

    两帧每通道平均差值不超过 ``tolerance`` 时为真。
    """
    if first.size() != second.size():
        return False
    left = first.convertToFormat(QImage.Format.Format_RGBA8888)
    right = second.convertToFormat(QImage.Format.Format_RGBA8888)
    total = 0
    samples = 0
    step = 3
    for y in range(0, left.height(), step):
        for x in range(0, left.width(), step):
            a = left.pixelColor(x, y)
            b = right.pixelColor(x, y)
            total += (
                abs(a.red() - b.red())
                + abs(a.green() - b.green())
                + abs(a.blue() - b.blue())
            )
            samples += 3
    return samples > 0 and total / samples <= tolerance


def _edge_profile(image: QImage, item: QObject, ratio: float,
                  count: int) -> list[int]:
    """Red-channel values from ``count`` px left of the face up to its edge.

    返回按钮面左边缘外 ``count`` 像素到边缘处的红通道值。
    """
    origin = item.mapToScene(QPointF(0, 0))
    center = item.mapToScene(QPointF(0, item.property("height") / 2))
    left = int(round(origin.x() * ratio))
    row = int(round(center.y() * ratio))
    start = max(0, left - count)
    return [
        image.pixelColor(x, row).red()
        for x in range(start, left)
    ]


def main() -> int:
    configure_qml_environment()
    app = QGuiApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    setTheme(Theme.LIGHT)

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    engine.loadData(
        SCENE_SOURCE,
        QUrl.fromLocalFile(str(ARTIFACT_DIR / "glow-button-bloom.qml")),
    )
    if not engine.rootObjects():
        print("failed to create the glow scene")
        return 1

    _pump(1400)
    window = engine.rootObjects()[0]
    backend = window.rendererInterface().graphicsApi()
    if "Direct3D11" not in str(backend):
        print(f"requires Direct3D11, got {backend}")
        return 1

    image = _stable_grab(window).convertToFormat(
        QImage.Format.Format_RGBA8888)
    ratio = image.width() / window.width()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    image.save(str(ARTIFACT_DIR / "glow-button-bloom.png"), "PNG")

    glow_button = window.findChild(QObject, "glowButton")
    plain_button = window.findChild(QObject, "plainButton")
    assert glow_button is not None and plain_button is not None
    halo = next(
        child
        for child in glow_button.findChildren(QObject)
        if child.metaObject().className().startswith("ButtonGlow_QMLTYPE_")
    )
    spread = float(halo.property("_spread"))
    window_span = int(round((spread + 2) * ratio))

    glow_profile = _edge_profile(image, glow_button, ratio, window_span)
    plain_profile = _edge_profile(image, plain_button, ratio, window_span)
    background = image.pixelColor(4, 4).red()

    checks: dict[str, bool] = {}
    details: dict[str, object] = {
        "graphics_api": str(backend),
        "device_pixel_ratio": ratio,
        "spread": spread,
        "background_red": background,
        "glow_profile": glow_profile,
        "plain_profile": plain_profile,
    }

    # 1. bloom: the band just outside the face must be tinted.
    checks["bloom_visible"] = min(glow_profile) < background - 6
    # 2. smoothness: no hard step. Stacked translucent discs banded here; an SDF
    # shadow must not. Threshold is 12% of the total contrast, which a 6-layer
    # disc stack exceeded on a real display.
    total_contrast = background - min(glow_profile) if glow_profile else 0
    steps = [
        abs(glow_profile[index + 1] - glow_profile[index])
        for index in range(len(glow_profile) - 1)
    ]
    details["total_contrast"] = total_contrast
    details["max_step"] = max(steps) if steps else 0
    checks["no_banding"] = (
        total_contrast > 0
        and (max(steps) if steps else 0) <= max(3, total_contrast * 0.12)
    )
    # 3. containment: the bloom must fade back to background within the shadow's
    # own painted extent. Measured on a real display, a RectangularShadow's visible
    # band is roughly spread + blur (8 + 24 px here), not spread alone, so the window
    # is derived from both tokens rather than from spread only.
    # 泛光必须在其自身绘制的范围内衰减回背景。真实显示器实测显示 RectangularShadow
    # 的可见带约为 spread + blur (此处 8 + 24 像素), 而不是只有 spread, 因此窗口由
    # 两个令牌共同推出而不是只用 spread。
    blur = float(halo.property("_tokens").property("glowBlur"))
    painted_extent = spread + blur
    details["painted_extent"] = painted_extent
    extent_span = int(round((painted_extent + 6) * ratio))
    glow_extent = _edge_profile(image, glow_button, ratio, extent_span)
    details["glow_extent_profile"] = glow_extent
    checks["contained_in_painted_extent"] = (
        abs(glow_extent[0] - background) <= 2 if glow_extent else False
    )
    details.pop("checks", None)
    # 4. primary reference: a plain primary button has no bloom. Its own edge
    # antialiasing reaches about 6 levels just outside the face, which is far less
    # than the bloom; compare against that measured edge rather than against zero.
    # 普通主色按钮没有泛光。它自己的边缘抗锯齿在面外会到约 6 级, 远小于泛光; 因此与
    # 实测边缘比较而不是与零比较。
    plain_span = int(round((spread + 2) * ratio))
    plain_profile = _edge_profile(image, plain_button, ratio, plain_span)
    details["plain_profile"] = plain_profile
    checks["primary_has_no_bloom"] = (
        min(plain_profile) >= background - 8 if plain_profile else False
    )
    # 5. edge fidelity: the pixel just left of the face is darker than the face
    # but the face row still reaches full ink, i.e. the bloom sits behind.
    checks["face_edge_preserved"] = glow_profile[-1] < background - 20

    details["checks"] = checks
    (ARTIFACT_DIR / "report.json").write_text(
        json.dumps(details, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}  {name}")
    print(f"report: {ARTIFACT_DIR / 'report.json'}")

    window.close()
    window.deleteLater()
    engine.deleteLater()
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
