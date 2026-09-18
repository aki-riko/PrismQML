# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Acrylic navigation panel regressions. 亚克力导航面板回归。

Two defects are locked here, both about the acrylic layer showing the wrong part
of its blurred capture:

1. A square "corner fill" on top of the layer re-sampled the image from its
   bottom-right region and surfaced as a colour block in the window corner.
2. The layer starts one title bar above the window while the capture covers the
   panel inside the window, so filling the whole layer stretched the blur and
   lifted it by one title bar — a second, offset copy of the panel behind the
   real content.

这里锁定两个缺陷, 都与亚克力层取错了模糊图区域有关: 覆盖在层上的方形"角填充"
用图像右下角重绘角落, 在窗口角落露出色块; 层比窗口高出一个标题栏而截图只覆盖
窗口内的面板, 铺满整层会把模糊图拉伸并整体上移, 在真实内容后多出一层错位重影。
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtGui import QColor, QImage
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem

from prismqml import Skin, Theme, register_types, setSkin, setTheme

ROOT = Path(__file__).resolve().parents[2]

PANEL_WIDTH = 320
WINDOW_HEIGHT = 800

PANEL_SCENE = """
import QtQuick
import PrismQML

Window {
    width: 360
    height: 800
    visible: true
    color: "#FFFFFF"

    // Mirrors WindowsSplit: the panel container rises one title bar above the
    // window, so the panel's own rect is taller than the captured region.
    // 复刻 WindowsSplit: 面板容器比窗口高出一个标题栏, 面板自身矩形因而高于截图区域。
    Item {
        objectName: "probeNavigationContainer"
        x: 0
        y: -48
        width: 320
        height: 848
        clip: true

        NavigationView {
            objectName: "probeNavigationView"
            anchors.fill: parent
            isExpanded: true
            showReturnButton: false
            model: [{ "key": "p1", "text": "P One" }]
            acrylicEnabled: true
            acrylicImageSource: "%SOURCE%"
        }
    }
}
"""


def _pump(milliseconds: int = 50) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _write_probe_image(path: Path) -> None:
    """Top half red, bottom half green: a mis-sampled panel is measurable.

    上半红、下半绿: 面板取错图像区域可以用像素直接量出来。
    """
    image = QImage(PANEL_WIDTH, WINDOW_HEIGHT, QImage.Format.Format_ARGB32)
    image.fill(QColor("#FF0000"))
    for y in range(WINDOW_HEIGHT // 2, WINDOW_HEIGHT):
        for x in range(PANEL_WIDTH):
            image.setPixelColor(x, y, QColor("#00FF00"))
    assert image.save(str(path))


def _create_scene(source: str):
    engine = QQmlEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    component = QQmlComponent(engine)
    component.setData(
        source.encode("utf-8"),
        QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "acrylic-panel-probe.qml")),
    )
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert window is not None, [error.toString() for error in component.errors()]
    return engine, component, window, warnings


def _windowed_probe(qapp, tmp_path):
    setTheme(Theme.LIGHT)
    setSkin(Skin.FLUENT)
    probe_image = tmp_path / "acrylic-probe.png"
    _write_probe_image(probe_image)
    source = PANEL_SCENE.replace(
        "%SOURCE%", QUrl.fromLocalFile(str(probe_image)).toString()
    )
    engine, component, window, warnings = _create_scene(source)
    _pump(400)
    view = window.findChild(QQuickItem, "probeNavigationView")
    assert view is not None
    assert view.property("acrylicEnabled") is True
    return engine, component, window, warnings


def _dispose(engine, component, window) -> None:
    window.deleteLater()
    component.deleteLater()
    engine.deleteLater()
    _pump(30)


def test_acrylic_panel_corner_keeps_the_panel_image_region(qapp, tmp_path):
    engine, component, window, warnings = _windowed_probe(qapp, tmp_path)
    try:
        grabbed = window.grabWindow()
        assert not grabbed.isNull()
        corner = grabbed.pixelColor(3, 3)
        adjacent = grabbed.pixelColor(3, 12)
        detail = f"corner={corner.name()} adjacent={adjacent.name()}"
        # The corner still belongs to the panel's top image region.
        # 角落仍然取面板顶部那块图像区域。
        assert corner.red() > corner.green(), detail
        assert adjacent.red() > adjacent.green(), detail
        # No square step at the corner radius boundary.
        # 圆角半径边界处不得出现方形跳变。
        assert abs(corner.red() - adjacent.red()) <= 4, detail
        assert abs(corner.green() - adjacent.green()) <= 4, detail
        assert warnings == [], warnings
    finally:
        _dispose(engine, component, window)


def test_acrylic_panel_image_aligns_with_the_visible_panel(qapp, tmp_path):
    engine, component, window, warnings = _windowed_probe(qapp, tmp_path)
    try:
        grabbed = window.grabWindow()
        assert not grabbed.isNull()
        # The capture's mid line must land on the window's mid line: filling the
        # whole taller layer instead stretches the blur by 848/800 and pulls the
        # boundary up to about y=386.
        # 截图的中线必须落在窗口的中线: 若铺满更高的整层, 模糊图会被拉伸 848/800,
        # 分界线会被上拉到 y≈386。
        above = grabbed.pixelColor(3, WINDOW_HEIGHT // 2 - 10)
        below = grabbed.pixelColor(3, WINDOW_HEIGHT // 2 + 10)
        detail = f"above={above.name()} below={below.name()}"
        assert above.red() > above.green(), detail
        assert below.green() > below.red(), detail
        # The lifted copy must not leave the capture's top strip uncovered.
        # 被上移的副本也不得在截图上缘留出未覆盖的条带。
        top = grabbed.pixelColor(3, 2)
        assert top.red() > top.green(), f"top={top.name()}"
        assert warnings == [], warnings
    finally:
        _dispose(engine, component, window)


def test_acrylic_stays_inside_the_rounded_panel_silhouette(qapp, tmp_path):
    engine, component, window, warnings = _windowed_probe(qapp, tmp_path)
    try:
        grabbed = window.grabWindow()
        assert not grabbed.isNull()
        # The panel is rounded on its right side, so the acrylic must not paint
        # into the two corner quadrants outside that silhouette: a rectangle
        # clip keeps the blur's square corners there and they read as a second,
        # square-cornered layer sticking out of the panel.
        # 面板右侧是圆角, 亚克力不得画进圆角之外的角象限: 矩形裁剪会让模糊图在那里
        # 留下方角, 看起来就是面板外多出一层"没有圆角"的层。
        top_right = grabbed.pixelColor(PANEL_WIDTH - 2, 2)
        bottom_right = grabbed.pixelColor(PANEL_WIDTH - 2, WINDOW_HEIGHT - 2)
        for label, pixel in (
            ("top-right", top_right),
            ("bottom-right", bottom_right),
        ):
            detail = f"{label}={pixel.name()}"
            # The window behind is white; acrylic would be red/green there.
            # 背后的窗口是白色; 若亚克力画到这里, 会是红/绿。
            assert pixel.green() <= pixel.red() + 4, detail
            assert pixel.blue() <= pixel.red() + 4, detail
        # The silhouette's rounded edge must not cut the panel itself either.
        # 轮廓的圆角也不得裁掉面板本身。
        inside = grabbed.pixelColor(PANEL_WIDTH - 2, WINDOW_HEIGHT // 2)
        assert inside.green() > inside.red(), f"inside={inside.name()}"
        assert warnings == [], warnings
    finally:
        _dispose(engine, component, window)
