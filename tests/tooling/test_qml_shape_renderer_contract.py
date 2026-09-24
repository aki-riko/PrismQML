# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Shape geometry renderer contract. Shape 几何渲染器合同。

实测 (Qt 6.11, 真实像素抓帧): `Shape` 走默认几何渲染器时圆弧与斜边**没有抗锯齿**
(边缘无覆盖率中间值), 只有显式选择曲线渲染器才会像 Canvas 一样平滑:

    Shape {
        preferredRendererType: Shape.CurveRenderer
    }

默认值既不平滑也不报错, 新写的 Shape 很容易静默变成锯齿边缘 (本项目已发生过一次),
因此每个 Shape 都必须显式声明渲染器。
"""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QML_ROOT = ROOT / "prismqml" / "PrismQML"
SHAPE_PATTERN = re.compile(r"\bShape\s*\{")
RENDERER_PATTERN = re.compile(r"preferredRendererType\s*:")


def test_every_shape_declares_its_renderer():
    offenders = []
    for path in sorted(QML_ROOT.rglob("*.qml")):
        source = path.read_text(encoding="utf-8")
        shapes = len(SHAPE_PATTERN.findall(source))
        if not shapes:
            continue
        declared = len(RENDERER_PATTERN.findall(source))
        if declared < shapes:
            offenders.append(
                f"{path.relative_to(ROOT).as_posix()} "
                f"(Shape={shapes}, preferredRendererType={declared})"
            )

    assert offenders == [], (
        "Every Shape must declare preferredRendererType explicitly: Qt's default "
        "geometry renderer draws stepped curves without warning (measured on Qt 6.11). "
        "Use preferredRendererType: Shape.CurveRenderer for antialiased curves. "
        "Offenders 违规文件: " + ", ".join(offenders)
    )


def test_tour_spotlight_corners_stay_antialiased():
    """The spotlight hole corners are curved geometry and must stay smooth.

    聚光孔圆角是曲线几何, 必须保持平滑。
    """
    source = (
        QML_ROOT / "controls" / "feedback" / "Overlay" / "_internal"
        / "TeachingTourMaskSurface.qml"
    ).read_text(encoding="utf-8")

    assert "preferredRendererType: Shape.CurveRenderer" in source
