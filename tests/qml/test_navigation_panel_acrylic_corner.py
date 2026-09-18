# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Acrylic navigation panel corner regressions. 亚克力导航面板角落回归。

The acrylic layer clips to its bounding rect, so its own image already covers
the four corner quadrants. A square "corner fill" painted on top therefore only
re-samples the blurred image from the wrong side and shows up as a colour block
in the window corner. 亚克力层按外接矩形裁剪, 图像本身已覆盖四个角象限; 覆盖在上
面的方形"角填充"只会用模糊图另一侧的区域重绘角落, 在窗口角落露出色块。
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtGui import QColor, QImage
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem

from prismqml import Skin, Theme, register_types, setSkin, setTheme

ROOT = Path(__file__).resolve().parents[2]

PANEL_SCENE = """
import QtQuick
import PrismQML

Window {
    width: 360
    height: 820
    visible: true
    color: "#FFFFFF"

    NavigationView {
        objectName: "probeNavigationView"
        width: 320
        height: 800
        isExpanded: true
        showReturnButton: false
        model: [{ "key": "p1", "text": "P One" }]
        acrylicEnabled: true
        acrylicImageSource: "%SOURCE%"
    }
}
"""


def _pump(milliseconds: int = 50) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _write_probe_image(path: Path) -> None:
    """Top half red, bottom half green: a mis-sampled corner is measurable.

    上半红、下半绿: 角落采样错位可以用像素直接量出来。
    """
    image = QImage(320, 800, QImage.Format.Format_ARGB32)
    image.fill(QColor("#FF0000"))
    for y in range(400, 800):
        for x in range(320):
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
        QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "acrylic-corner-probe.qml")),
    )
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert window is not None, [error.toString() for error in component.errors()]
    return engine, component, window, warnings


def test_acrylic_panel_corner_keeps_the_panel_image_region(qapp, tmp_path):
    setTheme(Theme.LIGHT)
    setSkin(Skin.FLUENT)
    probe_image = tmp_path / "acrylic-probe.png"
    _write_probe_image(probe_image)
    source = PANEL_SCENE.replace(
        "%SOURCE%", QUrl.fromLocalFile(str(probe_image)).toString()
    )
    engine, component, window, warnings = _create_scene(source)
    try:
        _pump(400)
        view = window.findChild(QQuickItem, "probeNavigationView")
        assert view is not None
        assert view.property("acrylicEnabled") is True
        grabbed = window.grabWindow()
        assert not grabbed.isNull()
        corner = grabbed.pixelColor(3, 3)
        adjacent = grabbed.pixelColor(3, 12)
        middle = grabbed.pixelColor(3, 400)
        detail = (
            f"corner={corner.name()} adjacent={adjacent.name()}"
            f" middle={middle.name()}"
        )
        # The corner still belongs to the panel's top image region.
        # 角落仍然取面板顶部那块图像区域。
        assert corner.red() > corner.green(), detail
        assert adjacent.red() > adjacent.green(), detail
        # No square step at the corner radius boundary.
        # 圆角半径边界处不得出现方形跳变。
        assert abs(corner.red() - adjacent.red()) <= 4, detail
        assert abs(corner.green() - adjacent.green()) <= 4, detail
        # The far end of the panel keeps the bottom image region, so the probe
        # really does distinguish the two halves.
        # 面板远端仍取底部图像区域, 证明探针确实能区分上下两半。
        assert middle.green() > middle.red(), detail
        assert warnings == [], warnings
    finally:
        window.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump(30)
