# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Progress and gauge range robustness regressions. 进度与仪表盘范围健壮性回归。"""

import math

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


SCENE = b"""
import QtQuick
import PrismQML

Item {
    width: 320
    height: 160

    ProgressBar {
        objectName: "bar"
        from: 5
        to: 5
        value: 5
    }

    ProgressRing {
        objectName: "ring"
        from: 5
        to: 5
        value: 5
    }

    CircularGauge {
        objectName: "gauge"
        minValue: 5
        maxValue: 5
        value: 5
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def test_degenerate_progress_ranges_have_zero_finite_position(qapp):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE, QUrl("inline:progress-range-robustness.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    try:
        _pump()
        bar = root.findChild(type(root), "bar")
        ring = root.findChild(type(root), "ring")
        gauge = root.findChild(type(root), "gauge")
        assert bar is not None and ring is not None and gauge is not None
        assert bar.property("position") == 0
        assert ring.property("position") == 0
        assert gauge.property("progress") == 0
        assert all(
            math.isfinite(float(value))
            for value in (
                bar.property("position"),
                ring.property("position"),
                gauge.property("progress"),
            )
        )
        assert warnings == []
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()
