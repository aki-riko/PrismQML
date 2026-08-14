# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Shared hover exit motion policy regressions. 共享悬浮退出运动策略回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
QML_ROOT = ROOT / "prismqml" / "PrismQML"
METRICS_SOURCE = QML_ROOT / "PrismEnums" / "Metrics.qml"
BUTTON_CORE_SOURCE = (
    QML_ROOT / "controls" / "buttons" / "Button" / "ButtonCore.qml"
)

HOVER_POLICY_COUNTS = {
    "navigation/NavigationBarItem.qml": 3,
    "controls/buttons/CloseButton.qml": 2,
    "controls/buttons/Button/CustomButtonCore.qml": 1,
    "controls/buttons/Button/ButtonDropdown.qml": 2,
    "controls/navigation/Paginator.qml": 1,
    "controls/navigation/NavigationProfileCard.qml": 1,
    "controls/navigation/TabWidget.qml": 1,
    "controls/data/AudioWaveform.qml": 3,
    "controls/data/Avatar/AvatarSelector.qml": 1,
    "controls/inputs/Chip.qml": 1,
    "controls/data/Table/_internal/TableRowDelegate.qml": 1,
    "controls/data/Table/_internal/TableHeader.qml": 1,
    "controls/data/Table/TableView.qml": 1,
    "controls/data/Chart/_internal/XYChartCore.qml": 2,
    "controls/inputs/ComboBox/ComboBoxCore.qml": 1,
    "controls/inputs/ColorPicker/_internal/ColorCircles.qml": 1,
    "controls/inputs/PinInput.qml": 2,
    "controls/data/List/TreeWidget/_internal/TreeWidgetDelegate.qml": 1,
    "controls/data/List/TreeWidget/TreeView.qml": 1,
    "controls/data/List/ListWidgetItem.qml": 2,
    "controls/inputs/FilterBar/FilterBarCore.qml": 1,
    "controls/containers/Card/Card.qml": 5,
    "controls/data/Chart/_internal/ChartBottomLegend.qml": 3,
    "controls/data/Chart/_internal/PieChartContent.qml": 1,
    "controls/containers/ScrollBar/ScrollBarEntry.qml": 2,
    "controls/containers/ScrollBar/ScrollBar.qml": 1,
    "controls/data/Chart/_internal/PieChartArea.qml": 3,
    "controls/containers/Layout/SplitPane.qml": 4,
    "controls/inputs/Search/_internal/SearchResultItem.qml": 1,
    "controls/data/Chart/_internal/BoxplotChartArea.qml": 1,
    "controls/inputs/Rating/RatingCore.qml": 2,
    "controls/inputs/Slider/SliderCore.qml": 2,
    "controls/inputs/Slider/BeforeAfterSlider.qml": 1,
    "controls/data/FlipView/PipsPagerCore.qml": 2,
    "controls/data/Chart/_internal/BarChartContent.qml": 2,
    "controls/inputs/Toggle/ToggleCheckIndicator.qml": 2,
    "controls/data/DataWidgetCore.qml": 2,
    "controls/inputs/Toggle/ToggleRadioIndicator.qml": 2,
}

PROBE_QML = b"""
import QtQuick
import PrismQML

Window {
    id: root

    property bool hovered: false
    readonly property int enterDuration: Enums.duration.fast
    readonly property color surfaceColor: surface.color
    readonly property real hoverScale: scaleProbe.hoverScale

    width: 120
    height: 80
    visible: true

    Rectangle {
        id: surface
        anchors.fill: parent
        color: root.hovered ? "#000000" : "#ffffff"

        HoverBehavior on color {
            active: root.hovered
            enterDuration: root.enterDuration
        }
    }

    Item {
        id: scaleProbe
        property real hoverScale: root.hovered ? 1.2 : 1.0

        HoverBehavior on hoverScale {
            active: root.hovered
            enterDuration: root.enterDuration
        }
    }
}
"""


def _pump(milliseconds: int) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def test_hover_motion_policy_disables_exit_animation():
    source = METRICS_SOURCE.read_text(encoding="utf-8")
    assert "readonly property int hoverExitDuration: root.duration.none" in source
    behavior_source = (
        QML_ROOT / "effects" / "HoverBehavior.qml"
    ).read_text(encoding="utf-8")
    assert "required property bool active" in behavior_source
    assert "property bool _previousActive: false" in behavior_source
    assert "Qt.callLater(root._commitActive)" in behavior_source
    assert "Component.onCompleted" not in behavior_source
    assert "? Enums.motion.hoverExitDuration : root.enterDuration" in behavior_source


def test_hover_visuals_route_through_shared_motion_policy():
    for relative_path, expected_count in HOVER_POLICY_COUNTS.items():
        source = (QML_ROOT / relative_path).read_text(encoding="utf-8")
        assert source.count("HoverBehavior on ") == expected_count, relative_path
        assert "active: parent." not in source, relative_path


def test_hover_behavior_animates_entry_and_resets_exit_immediately(qapp):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(PROBE_QML, QUrl("inline:hover-exit-motion-policy.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(10)
    window = component.create(engine.rootContext())
    assert window is not None, [error.toString() for error in component.errors()]
    try:
        _pump(20)
        window.setProperty("hovered", True)
        _pump(30)
        entering_color = window.property("surfaceColor")
        assert QColor("#000000") != entering_color != QColor("#ffffff")
        assert 1.0 < window.property("hoverScale") < 1.2

        _pump(window.property("enterDuration"))
        assert window.property("surfaceColor") == QColor("#000000")
        assert window.property("hoverScale") == pytest.approx(1.2)

        window.setProperty("hovered", False)
        _pump(1)
        assert window.property("surfaceColor") == QColor("#ffffff")
        assert window.property("hoverScale") == pytest.approx(1.0)
    finally:
        window.close()
        window.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump(1)


def test_hover_behavior_created_active_still_resets_exit_immediately(qapp):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        PROBE_QML.replace(
            b"property bool hovered: false",
            b"property bool hovered: true",
        ),
        QUrl("inline:hover-exit-initially-active.qml"),
    )
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(10)
    window = component.create(engine.rootContext())
    assert window is not None, [error.toString() for error in component.errors()]
    try:
        _pump(20)
        assert window.property("surfaceColor") == QColor("#000000")
        assert window.property("hoverScale") == pytest.approx(1.2)

        window.setProperty("hovered", False)
        _pump(1)
        assert window.property("surfaceColor") == QColor("#ffffff")
        assert window.property("hoverScale") == pytest.approx(1.0)
    finally:
        window.close()
        window.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump(1)


def test_button_manual_color_animation_cannot_restart_hover_exit():
    source = BUTTON_CORE_SOURCE.read_text(encoding="utf-8")
    assert "property bool _hoverExitPending: false" in source
    assert "_updateTargetColors(hovered)" in source
    assert "Qt.callLater(control._completeHoverExit)" in source
    assert source.count("_updateTargetColors(!_hoverExitPending)") == 2
