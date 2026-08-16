# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""MatrixRain public lifecycle characterization. MatrixRain 公开生命周期基线。"""

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import configure_qml_environment, register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE = b"""
import QtQuick
import PrismQML

MatrixRain {
    objectName: "matrixRain"
    width: 160
    height: 120
    running: false
    interactive: true
}
"""


def test_matrix_rain_public_controls_preserve_state(qapp):
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE, QUrl.fromLocalFile(str(ROOT / "tests/qml/matrix-rain.qml")))
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    rain = component.create(engine.rootContext())
    assert rain is not None
    qapp.processEvents()

    rain.start()
    assert rain.property("running") is True
    rain.pause()
    assert rain.property("paused") is True
    rain.resume()
    assert rain.property("paused") is False
    rain.setDirection("left")
    assert rain.property("direction") == "left"
    assert rain.property("isHorizontal") is True
    rain.setDirection("invalid")
    assert rain.property("direction") == "left"
    rain.setCharsetPreset("binary")
    assert rain.property("charsetPreset") == "binary"
    rain.reset()
    rain.stop()
    assert rain.property("running") is False
    rain.deleteLater()
    qapp.processEvents()
