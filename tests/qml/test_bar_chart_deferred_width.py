# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Horizontal bar deferred width regressions. 横向柱子延迟宽度回归。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickWindow

from prismqml import register_types

ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "bar-chart-deferred-width.qml"))
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 600
    height: 400
    visible: true

    ChartView {
        width: 420
        height: 220
        chartType: Enums.chart.type_bar
        barOrientation: Enums.chart.orientation_horizontal
        chartData: [{label: "a", value: 3}, {label: "b", value: 5}, {label: "c", value: 2}]
    }
}
"""


def test_horizontal_bars_destroyed_before_deferred_width_stay_silent(qapp):
    """Bars destroyed before their deferred width call must not throw.

    柱子在延迟宽度调用执行前被销毁时不得抛错。
    """
    engine = QQmlApplicationEngine()
    warnings: list[str] = []
    engine.warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [e.toString() for e in component.errors()]
    try:
        # Destroy before the event loop runs Qt.callLater 在事件循环执行 Qt.callLater 前销毁
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        for _ in range(20):
            QCoreApplication.processEvents()
        assert [w for w in warnings if "BarChartBar" in w] == []
    finally:
        component.deleteLater()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()
