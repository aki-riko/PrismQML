# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""PieChartContent paint performance regressions. 饼图绘制性能回归。"""

from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "data"
    / "Chart"
    / "_internal"
    / "PieChartContent.qml"
)
INTERNAL_URL = QUrl.fromLocalFile(str(SOURCE_PATH.parent)).toString()
SCENE_SOURCE = f'''import QtQuick
import QtQuick.Window
import PrismQML
import "{INTERNAL_URL}" as ChartInternal

Window {{
    id: host

    property string colorCalls: ""

    function recordColor(index) {{
        colorCalls += index.toString()
        return Enums.accentColor
    }}

    width: 320
    height: 320
    visible: true

    ChartInternal.PieChartContent {{
        objectName: "pieContent"
        anchors.fill: parent
        chartData: [
            {{ label: "Alpha", value: 50 }},
            {{ label: "Beta", value: 30 }},
            {{ label: "Gamma", value: 20 }}
        ]
        totalValue: 100
        animated: false
        showValues: true
        isDonut: false
        donutRatio: 0.5
        getColor: host.recordColor
        labelOutside: true
    }}
}}
'''.encode("utf-8")


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1_500) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        SCENE_SOURCE,
        QUrl.fromLocalFile(
            str(ROOT / "tests" / "qml" / "pie-chart-content-performance.qml")
        ),
    )
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    content = window.findChild(QQuickItem, "pieContent")
    assert content is not None
    canvases = [
        child
        for child in content.findChildren(QObject)
        if child.metaObject().indexOfProperty("animProgress") >= 0
    ]
    assert len(canvases) == 1
    assert _wait_for(lambda: canvases[0].property("available"))
    _pump(50)
    return engine, component, window, canvases[0], warnings


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def test_pie_chart_offscreen_paint_preserves_color_call_sequence(qapp):
    engine, component, window, canvas, warnings = _create_scene()
    try:
        window.setProperty("colorCalls", "")
        assert QMetaObject.invokeMethod(canvas, "requestPaint") is True
        assert _wait_for(lambda: len(window.property("colorCalls")) >= 6)
        assert window.property("colorCalls") == "001122"
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)


def test_pie_chart_hot_loop_uses_frame_snapshot():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    paint_section = source.split("onPaint: {", 1)[1].split(
        "Component.onCompleted:", 1
    )[0]
    loop_marker = "for (var i = 0; i < chartData.length; i++) {"
    assert loop_marker in paint_section
    frame_setup, hot_loop = paint_section.split(loop_marker, 1)
    for snapshot in (
        "var chartData = root.chartData",
        "var totalValue = root.totalValue",
        "var frameAnimProgress = animProgress",
        "var frameProgress = root.animated ? frameAnimProgress : 1",
        "var showValues = root.showValues",
        "var isDonut = root.isDonut",
        "var donutRatio = root.donutRatio",
        "var hoveredIndex = root.hoveredIndex",
        "var previousHoveredIndex = root.previousHoveredIndex",
        "var labelOutside = root.labelOutside",
        "var frameHoverOffset = hoverOffset",
        "var frameTransitionProgress = transitionProgress",
    ):
        assert snapshot in frame_setup
    assert hot_loop.count("root.getColor(i)") == 2
    assert hot_loop.count("root.") == 2
    assert "animProgress" not in hot_loop
    assert "hoverOffset" not in hot_loop
    assert "transitionProgress" not in hot_loop
