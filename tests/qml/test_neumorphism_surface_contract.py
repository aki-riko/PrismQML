# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Neumorphic radius, border, and elevation contract regressions. 新拟态表面合同回归。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import Skin, Theme, getSkin, getTheme, register_types, setSkin, setTheme


ROOT = Path(__file__).resolve().parents[2]
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property int expectedSurfaceRadius: Enums.neumorphism.radius
    readonly property real expectedSurfaceBorderWidth: Enums.neumorphism.borderWidth
    readonly property real shadowedRadius: shadowed.radius
    readonly property real chartRadius: chart.radius
    readonly property real chartBorderWidth: chart.border.width
    readonly property real textEditRadius: textEdit.radius
    readonly property real spinBoxRadius: spinBox.radius
    readonly property real calendarRadius: calendar.radius
    readonly property real calendarBorderWidth: calendar.border.width
    readonly property real dateTimeRadius: dateTime.radius
    readonly property real dateTimeBorderWidth: dateTime.border.width
    readonly property real filterRadius: filter.radius
    readonly property Item waveformBackground: waveform.children.length > 0
                                               ? waveform.children[0] : null
    readonly property real waveformRadius: waveformBackground ? waveformBackground.radius : -1
    readonly property real waveformBorderWidth: waveformBackground
                                                  ? waveformBackground.border.width : -1
    readonly property real dropZoneRadius: dropZone.radius

    width: 1200
    height: 900

    ShadowedRectangle {
        id: shadowed
        objectName: "shadowed"
        width: 180
        height: 80
    }

    ChartView {
        id: chart
        objectName: "chart"
        x: 220
        width: 320
        height: 200
        chartData: [{"label": "A", "value": 1}]
    }

    TextEdit {
        id: textEdit
        objectName: "textEdit"
        y: 240
        width: 240
        height: 120
    }

    SpinBoxCore {
        id: spinBox
        objectName: "spinBox"
        x: 280
        y: 240
    }

    CalendarPicker {
        id: calendar
        objectName: "calendar"
        y: 400
    }

    DateTimePicker {
        id: dateTime
        objectName: "dateTime"
        x: 280
        y: 400
    }

    FilterBarCore {
        id: filter
        objectName: "filter"
        y: 480
        items: ["All", "Open"]
    }

    AudioWaveform {
        id: waveform
        objectName: "waveform"
        y: 560
        width: 360
        height: 100
        waveformData: [0.2, 0.8, 0.4]
    }

    DropZone {
        id: dropZone
        objectName: "dropZone"
        x: 420
        y: 560
    }
}
"""


def _pump(milliseconds=0):
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, QUrl("inline:neumorphism-surface-contract.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(10)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _pump()
    return engine, component, root, warnings


def _neumorphic_shadows(owner):
    return [
        child
        for child in owner.findChildren(QObject)
        if "NeumorphicShadow" in child.metaObject().className()
        and child.metaObject().indexOfProperty("target") >= 0
        and child.property("target") == owner
    ]


def test_neumorphic_surfaces_share_radius_border_and_elevation(qapp):
    previous_skin = getSkin()
    previous_theme = getTheme()
    setTheme(Theme.LIGHT)
    setSkin(Skin.NEUMORPHISM)
    engine, component, root, warnings = _create_scene()
    try:
        radius = root.property("expectedSurfaceRadius")
        border_width = root.property("expectedSurfaceBorderWidth")
        assert radius == 14
        assert border_width == 0

        for property_name in (
            "shadowedRadius",
            "chartRadius",
            "textEditRadius",
            "spinBoxRadius",
            "calendarRadius",
            "dateTimeRadius",
            "filterRadius",
            "waveformRadius",
            "dropZoneRadius",
        ):
            assert root.property(property_name) == radius, property_name

        for property_name in (
            "chartBorderWidth",
            "calendarBorderWidth",
            "dateTimeBorderWidth",
            "waveformBorderWidth",
        ):
            assert root.property(property_name) == border_width, property_name

        for object_name in ("calendar", "dateTime", "filter"):
            surface = root.findChild(QObject, object_name)
            assert surface is not None
            assert len(_neumorphic_shadows(surface)) == 1

        assert warnings == []
    finally:
        setTheme(previous_theme)
        setSkin(previous_skin)
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump()
