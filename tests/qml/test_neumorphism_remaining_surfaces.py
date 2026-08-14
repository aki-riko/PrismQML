# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Remaining neumorphic surface contracts. 新拟态残余表面合同。"""

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
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlProperty
from PySide6.QtQuick import QQuickItem

from prismqml import Skin, Theme, getSkin, getTheme, register_types, setSkin, setTheme


ROOT = Path(__file__).resolve().parents[2]
CHART_INTERNAL_URL = QUrl.fromLocalFile(
    str(ROOT / "prismqml" / "PrismQML" / "controls" / "data" / "Chart" / "_internal")
).toString()
SCENE_SOURCE = f"""
import QtQuick
import QtQuick.Window
import PrismQML
import "{CHART_INTERNAL_URL}" as ChartInternal

Window {{
    id: host
    width: 960
    height: 640
    visible: true

    readonly property int expectedRadius: Enums.neumorphism.radius
    readonly property real expectedBorderWidth: Enums.neumorphism.borderWidth
    readonly property color expectedPrimaryText: Enums.textColor.primary
    readonly property color expectedSecondaryText: Enums.textColor.secondary
    readonly property color expectedSurfaceColor: Enums.cardColor
    readonly property color chartTooltipText: Enums.stateColor.chartTooltipText
    readonly property color chartStrongText: Enums.chartColors.strongText

    LoginWindow {{
        id: login
        objectName: "remainingLogin"
        width: 520
        height: 500
        matrixEnabled: false
    }}

    ChartInternal.ChartTooltip {{
        id: chartTooltip
        objectName: "remainingChartTooltip"
        label: "Series"
        value: 42
        visible: true
    }}

    ChartInternal.ChartMultiTooltip {{
        id: chartMultiTooltip
        objectName: "remainingChartMultiTooltip"
        xLabel: "Monday"
        seriesData: [{{"name": "Series", "value": 42, "color": "#3867D6"}}]
        visible: true
    }}

    Item {{
        id: anchor
        objectName: "tipAnchor"
        x: 700
        y: 80
        width: 80
        height: 32
    }}

    TipPopup {{
        id: tip
        objectName: "remainingTipPopup"
        target: anchor
        closable: false
    }}

    FilterBarCore {{
        id: filter
        objectName: "remainingFilter"
        x: 20
        y: 560
        items: ["all", "open", "closed"]
    }}

    SpinBoxButton {{
        id: spinButton
        objectName: "remainingSpinButton"
        x: 860
        y: 560
        width: 28
        height: 28
        preferredHeight: 24
        preferredWidth: 24
    }}
}}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _dispose_scene(engine, component, window) -> None:
    window.close()
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _pump()


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        SCENE_SOURCE.encode("utf-8"),
        QUrl("inline:neumorphism-remaining-surfaces.qml"),
    )
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump()
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert window is not None, [error.toString() for error in component.errors()]
    _pump()
    return engine, component, window, warnings


def _visual_descendants(root: QQuickItem):
    result = []
    pending = list(root.childItems())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.childItems())
    return result


def _border_width(item: QObject, engine) -> float:
    return float(QQmlProperty(item, "border.width", engine).read())


def test_remaining_surfaces_follow_neumorphic_tokens(qapp):
    previous_skin = getSkin()
    previous_theme = getTheme()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    setTheme(Theme.LIGHT)
    setSkin(Skin.NEUMORPHISM)
    engine, component, window, warnings = _create_scene()
    try:
        expected_radius = window.property("expectedRadius")
        expected_border = window.property("expectedBorderWidth")

        login = window.findChild(QObject, "remainingLogin")
        chart = window.findChild(QObject, "remainingChartTooltip")
        multi = window.findChild(QObject, "remainingChartMultiTooltip")
        tip = window.findChild(QObject, "remainingTipPopup")
        filter_bar = window.findChild(QObject, "remainingFilter")
        spin_button = window.findChild(QObject, "remainingSpinButton")
        assert all(item is not None for item in (login, chart, multi, tip, filter_bar, spin_button))

        assert login.property("_cardRadius") == expected_radius
        assert login.property("_cardBorderWidth") == expected_border
        assert login.property("_errorRadius") == expected_radius
        assert chart.property("_tooltipRadius") == expected_radius
        assert chart.property("_tooltipBorderColor").alpha() == 0
        assert multi.property("_tooltipRadius") == expected_radius
        assert _border_width(multi, engine) == expected_border
        assert tip.property("_tipRadius") == expected_radius
        assert tip.property("_tipBorderWidth") == expected_border
        assert tip.property("_tipBackground") == window.property("expectedSurfaceColor")

        descendants = _visual_descendants(filter_bar)
        indicators = [
            child for child in descendants
            if child.metaObject().indexOfProperty("targetIndex") >= 0
            and child.metaObject().indexOfProperty("refreshTrigger") >= 0
        ]
        items = [
            child for child in descendants
            if child.metaObject().indexOfProperty("parsedData") >= 0
            and child.metaObject().indexOfProperty("selected") >= 0
            and child.metaObject().indexOfProperty("index") >= 0
        ]
        assert len(indicators) == 1
        assert len(items) == 3
        assert indicators[0].property("radius") == expected_radius
        assert all(item.property("radius") == expected_radius for item in items)
        assert spin_button.property("radius") == expected_radius

        assert window.property("chartTooltipText") == window.property("expectedSecondaryText")
        assert window.property("chartStrongText") == window.property("expectedPrimaryText")
        assert warnings == []
        assert [
            item for item in QGuiApplication.topLevelWindows()
            if item.isVisible() and item not in windows_before and item is not window
        ] == []
    finally:
        _dispose_scene(engine, component, window)
        setTheme(previous_theme)
        setSkin(previous_skin)


def test_tip_popup_arrow_reuses_surface_border_contract(qapp):
    previous_skin = getSkin()
    previous_theme = getTheme()
    setTheme(Theme.LIGHT)
    setSkin(Skin.NEUMORPHISM)
    engine, component, window, warnings = _create_scene()
    try:
        tip = window.findChild(QObject, "remainingTipPopup")
        assert tip is not None
        assert QMetaObject.invokeMethod(tip, "prewarm")
        _pump(20)
        surface = tip.findChild(QObject, "tipPopupSurface")
        assert surface is not None
        assert surface.property("radius") == window.property("expectedRadius")
        assert _border_width(surface, engine) == window.property("expectedBorderWidth")
        assert warnings == []
    finally:
        _dispose_scene(engine, component, window)
        setTheme(previous_theme)
        setSkin(previous_skin)
