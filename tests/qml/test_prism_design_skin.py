# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design skin token and component smoke tests."""

from pathlib import Path

from PySide6.QtCore import QFile, QResource, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import Skin, Theme, register_types, setSkin, setTheme


def _build(engine, qml: bytes):
    component = QQmlComponent(engine)
    component.setData(qml, QUrl("inline"))
    assert not component.isError(), [error.toString() for error in component.errors()]

    item = component.create(engine.rootContext())
    assert item is not None, [error.toString() for error in component.errors()]
    return component, item


def _rgb(qcolor):
    return (
        round(qcolor.redF() * 255),
        round(qcolor.greenF() * 255),
        round(qcolor.blueF() * 255),
    )


def test_prism_design_skin_tokens_and_controls(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build(engine, b"""
import QtQuick
import PrismQML
Item {
    property string skinValue: Enums.skin
    property bool prismDesign: Enums.isPrismDesign
    property bool neobrutalism: Enums.isNeobrutalism
    property color accent: Enums.accentColor
    property color background: Enums.backgroundColor
    property color surface: Enums.surfaceColor
    property color controlBg: Enums.stateColor.controlBg
    property color segmentedSelected: Enums.stateColor.segmentedSelected
    property color treeItemHover: Enums.stateColor.treeItemHover
    property color chartFirst: Enums.chartColors.palette[0]
    property color chartGrid: Enums.chartColors.gridLine
    property int radiusControl: Enums.prismDesign.radiusControl
    property int radiusCard: Enums.prismDesign.radiusCard
    property int radiusPopup: Enums.prismDesign.radiusPopup
}
"""))
        tokens = keep[-1][1]
        assert tokens.property("skinValue") == "prism_design"
        assert tokens.property("prismDesign") is True
        assert tokens.property("neobrutalism") is False
        assert _rgb(tokens.property("accent")) == (11, 127, 137)
        assert _rgb(tokens.property("background")) == (238, 245, 247)
        assert _rgb(tokens.property("surface")) == (248, 251, 252)
        assert _rgb(tokens.property("controlBg")) == (252, 254, 255)
        assert _rgb(tokens.property("segmentedSelected")) == (221, 244, 247)
        assert _rgb(tokens.property("treeItemHover")) == (237, 245, 247)
        assert _rgb(tokens.property("chartFirst")) == (11, 127, 137)
        assert _rgb(tokens.property("chartGrid")) == (214, 227, 230)
        assert tokens.property("radiusControl") == 10
        assert tokens.property("radiusCard") == 14
        assert tokens.property("radiusPopup") == 18

        keep.append(_build(engine, b"""
import PrismQML
Button {
    text: "OK"
    style: Enums.button.style_primary
    width: 120
    height: 36
}
"""))
        button = keep[-1][1]
        assert button.property("radius") == 10
        assert button.property("_neoPressShift") == 0
        assert _rgb(button.property("color")) == (11, 127, 137)

        keep.append(_build(engine, b"""
import PrismQML
Card {
    width: 200
    height: 120
}
"""))
        card = keep[-1][1]
        assert card.property("borderRadius") == 14
        assert _rgb(card.property("color")) == (252, 254, 255)

        keep.append(_build(engine, b"""
import PrismQML
InputCore {
    width: 200
    height: 32
}
"""))
        input_core = keep[-1][1]
        assert input_core.property("radius") == 10
        assert _rgb(input_core.property("color")) == (252, 254, 255)
        assert _rgb(input_core.property("inputTextColor")) == (18, 34, 38)

        keep.append(_build(engine, b"""
import PrismQML
SegmentedControl {
    items: ["Token", "State", "Surface"]
    currentIndex: 1
}
"""))
        segmented = keep[-1][1]
        assert segmented.property("radius") == 10
        assert _rgb(segmented.property("color")) == (248, 251, 252)

        keep.append(_build(engine, b"""
import PrismQML
InfoBar {
    title: "Info"
    content: "Prism overlay"
    duration: 0
}
"""))
        info_bar = keep[-1][1]
        assert info_bar.property("radius") == 18
        assert _rgb(info_bar.property("borderColor")) == (185, 204, 209)

        keep.append(_build(engine, b"""
import PrismQML
Action {
    text: "Cut"
}
"""))
        action = keep[-1][1]
        assert action.property("radius") == 10

        keep.append(_build(engine, b"""
import PrismQML
ListWidget {
    width: 220
    height: 120
}
"""))
        list_widget = keep[-1][1]
        assert list_widget.property("radius") == 14
        assert list_widget.property("borderRadius") == 14

        keep.append(_build(engine, b"""
import PrismQML
DataWidgetCore {
    width: 240
    height: 140
}
"""))
        data_widget = keep[-1][1]
        assert data_widget.property("borderRadius") == 14

        keep.append(_build(engine, b"""
import PrismQML
TableWidget {
    width: 260
    height: 160
    tableData: [{ "name": "Alpha" }]
    columns: [{ "text": "Name", "role": "name" }]
}
"""))
        table_widget = keep[-1][1]
        assert table_widget.property("borderRadius") == 14

        keep.append(_build(engine, b"""
import PrismQML
TreeWidget {
    width: 260
    height: 160
    model: [{ "text": "Root", "children": [{ "text": "Child" }] }]
}
"""))
        tree_widget = keep[-1][1]
        assert tree_widget.property("borderRadius") == 14

        keep.append(_build(engine, b"""
import PrismQML
ChartView {
    width: 260
    height: 180
    chartData: [{ "label": "Alpha", "value": 12 }]
}
"""))
        chart_view = keep[-1][1]
        assert chart_view.property("radius") == 14

        keep.append(_build(engine, b"""
import PrismQML
Tag {
    text: "Stable"
}
"""))
        tag = keep[-1][1]
        assert tag.property("radius") == 10

        keep.append(_build(engine, b"""
import PrismQML
NavigationViewItem {
    text: "Dashboard"
    icon: "Home"
    selected: true
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
PipsPager {
    pageCount: 4
    currentIndex: 1
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
ToggleNavigationBar {
    width: 220
    height: 160
    model: [{ "text": "Files", "icon": "Home" }, { "text": "Settings", "icon": "Settings" }]
    currentIndex: 1
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
Paginator {
    currentPage: 2
    totalPages: 6
    visiblePages: 5
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
Pivot {
    items: [{ "key": "overview", "text": "Overview" }, { "key": "details", "text": "Details" }]
    currentIndex: 1
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
TabWidget {
    width: 320
    height: 220
    tabs: [{ "title": "Overview", "icon": "Home" }, { "title": "Details", "icon": "Settings" }]
    currentIndex: 1
    showAddButton: true
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
NavigationProfileCard {
    title: "Prism"
    subtitle: "Design Skin"
    isCompacted: false
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
DateTimePicker {
}
"""))
        picker = keep[-1][1]
        assert picker.property("radius") == 10

        keep.append(_build(engine, b"""
import PrismQML
FilterBarCore {
    items: ["All", "Open", "Closed"]
    currentIndex: 1
}
"""))
        filter_bar = keep[-1][1]
        assert filter_bar.property("radius") == 10

        keep.append(_build(engine, b"""
import PrismQML
SpinBoxCore {
    value: 3
    minimum: 0
    maximum: 10
}
"""))
        spin_box = keep[-1][1]
        assert spin_box.property("radius") == 10

        keep.append(_build(engine, b"""
import PrismQML
CalendarPicker {
}
"""))
        calendar_picker = keep[-1][1]
        assert calendar_picker.property("radius") == 10

        keep.append(_build(engine, b"""
import PrismQML
TextEdit {
    placeholderText: "Notes"
}
"""))
        text_edit = keep[-1][1]
        assert text_edit.property("radius") == 10

        keep.append(_build(engine, b"""
import PrismQML
Chip {
    text: "Prism"
    checked: true
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
PinInput {
    length: 4
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
CheckIndicator {
    checkState: 0
}
"""))
        check_indicator = keep[-1][1]
        assert check_indicator.property("_indicatorRadius") == 10
        assert check_indicator.property("_indicatorBorderWidth") == 1
        assert _rgb(check_indicator.property("_indicatorColor")) == (252, 254, 255)
        assert _rgb(check_indicator.property("_indicatorBorderColor")) == (120, 173, 184)

        keep.append(_build(engine, b"""
import PrismQML
CheckIndicator {
    checkState: 2
}
"""))
        checked_indicator = keep[-1][1]
        assert checked_indicator.property("_indicatorBorderWidth") == 1
        assert _rgb(checked_indicator.property("_indicatorColor")) == (11, 127, 137)
        assert _rgb(checked_indicator.property("_indicatorBorderColor")) == (7, 95, 104)
        assert _rgb(checked_indicator.property("_checkIconColor")) == (255, 255, 255)

        toggle_internal_dir = (
            Path(__file__).resolve().parents[2]
            / "prismqml"
            / "PrismQML"
            / "controls"
            / "inputs"
            / "Toggle"
        )
        radio_indicator_component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(toggle_internal_dir / "ToggleRadioIndicator.qml")),
        )
        assert not radio_indicator_component.isError(), [
            error.toString() for error in radio_indicator_component.errors()
        ]
        radio_indicator = radio_indicator_component.create(engine.rootContext())
        assert radio_indicator is not None, [
            error.toString() for error in radio_indicator_component.errors()
        ]
        keep.append((radio_indicator_component, radio_indicator))
        radio_indicator.setProperty("checked", True)
        assert radio_indicator.property("_indicatorBorderWidth") == 1
        assert _rgb(radio_indicator.property("_indicatorColor")) == (11, 127, 137)
        assert _rgb(radio_indicator.property("_borderColor")) == (7, 95, 104)
        assert _rgb(radio_indicator.property("_innerDotColor")) == (255, 255, 255)

        switch_indicator_component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(toggle_internal_dir / "ToggleSwitchIndicator.qml")),
        )
        assert not switch_indicator_component.isError(), [
            error.toString() for error in switch_indicator_component.errors()
        ]
        switch_indicator = switch_indicator_component.create(engine.rootContext())
        assert switch_indicator is not None, [
            error.toString() for error in switch_indicator_component.errors()
        ]
        keep.append((switch_indicator_component, switch_indicator))
        assert switch_indicator.property("_trackBorderWidth") == 1
        assert _rgb(switch_indicator.property("_trackColor")) == (252, 254, 255)
        assert _rgb(switch_indicator.property("_trackBorderColor")) == (120, 173, 184)
        assert _rgb(switch_indicator.property("_handleColor")) == (252, 254, 255)
        switch_indicator.setProperty("checked", True)
        assert _rgb(switch_indicator.property("_trackColor")) == (11, 127, 137)
        assert _rgb(switch_indicator.property("_trackBorderColor")) == (7, 95, 104)
        assert _rgb(switch_indicator.property("_handleColor")) == (255, 255, 255)

        keep.append(_build(engine, b"""
import PrismQML
Slider {
    width: 220
    value: 55
}
"""))
        slider = keep[-1][1]
        assert _rgb(slider.property("handleColor")) == (252, 254, 255)
        assert _rgb(slider.property("_trackColor")) == (221, 233, 237)
        assert _rgb(slider.property("_progressColor")) == (11, 127, 137)
        assert slider.property("_handleBorderWidth") == 1
        assert _rgb(slider.property("_handleBorderColor")) == (120, 173, 184)

        keep.append(_build(engine, b"""
import PrismQML
Rating {
    value: 3
}
"""))
        rating = keep[-1][1]
        assert _rgb(rating.property("_effectiveFillColor")) == (255, 220, 6)
        assert _rgb(rating.property("_effectiveOutlineColor")) == (118, 138, 145)

        keep.append(_build(engine, b"""
import PrismQML
DropZone {
    preferredWidth: 260
    preferredHeight: 140
}
"""))
        drop_zone = keep[-1][1]
        assert drop_zone.property("radius") == 14

        keep.append(_build(engine, b"""
import PrismQML
Progress {
    type: Enums.progress.type_bar_filled
    value: 45
    text: "45%"
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
EmptyState {
    actionText: "Create"
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
ResultState {
    state: "success"
    actionText: "Done"
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
StateWidget {
    stateType: Enums.state.type_result
    severity: "success"
    actionText: "OK"
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
OfflineState {
    retryText: "Retry"
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
Expander {
    title: "More"
    content: "Details"
    expanded: true
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
GroupBox {
    title: "Options"
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
CommandBar {
    type: Enums.commandBar.type_view
    primaryCommands: [{ "text": "Open", "icon": "FolderOpen" }]
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
Widget {
    preferredWidth: 220
    preferredHeight: 80
    toolTipText: "Prism tooltip"
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
ProgressDialog {
    title: "Loading"
    content: "Please wait"
    progress: 45
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
UpdateDialog {
    version: "1.2.3"
    currentVersion: "1.2.2"
    notes: "Prism skin update"
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
DesktopNotification {
    title: "Prism"
    message: "Container feedback"
    severity: "success"
    duration: 0
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
Skeleton {
    shape: Enums.skeleton.shape_rect
    width: 80
    height: 24
}
"""))
        skeleton = keep[-1][1]
        assert skeleton.property("_radius") == 10

        keep.append(_build(engine, b"""
import PrismQML
CodeBlock {
    code: "print('prism')"
    language: "python"
}
"""))
        code_block = keep[-1][1]
        assert code_block.property("_radius") == 14
        assert _rgb(code_block.property("_blockBackground")) == (247, 252, 254)

        keep.append(_build(engine, b"""
import PrismQML
ChatBubble {
    width: 420
    role: "assistant"
    content: "Hello Prism"
}
"""))
        chat_bubble = keep[-1][1]
        assert chat_bubble.property("_bubbleRadius") == 18
        assert chat_bubble.property("_bubbleTailRadius") == 10

        keep.append(_build(engine, b"""
import PrismQML
ColorPicker {
    type: Enums.colorPicker.type_picker
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
GradientSlider {
    width: 180
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
ColorPickerDialog {
    title: "Pick"
}
"""))

        keep.append(_build(engine, b"""
import PrismQML
LoginWindow {
    width: 640
    height: 520
    matrixEnabled: false
    errorMessage: "Invalid credentials"
}
"""))
        login_window = keep[-1][1]
        assert login_window.property("_cardRadius") == 24
        assert login_window.property("_errorRadius") == 10

        chart_tooltip_path = (
            Path(__file__).resolve().parents[2]
            / "prismqml"
            / "PrismQML"
            / "controls"
            / "data"
            / "Chart"
            / "_internal"
            / "ChartTooltip.qml"
        )
        chart_tooltip_component = QQmlComponent(engine, QUrl.fromLocalFile(str(chart_tooltip_path)))
        assert not chart_tooltip_component.isError(), [
            error.toString() for error in chart_tooltip_component.errors()
        ]
        chart_tooltip = chart_tooltip_component.create(engine.rootContext())
        assert chart_tooltip is not None, [
            error.toString() for error in chart_tooltip_component.errors()
        ]
        keep.append((chart_tooltip_component, chart_tooltip))
        assert _rgb(chart_tooltip.property("_tooltipBackground")) == (247, 252, 254)
        assert chart_tooltip.property("_tooltipRadius") == 18
        assert _rgb(chart_tooltip.property("_tooltipBorderColor")) == (185, 204, 209)

        chart_internal_dir = chart_tooltip_path.parent
        chart_multi_tooltip_component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(chart_internal_dir / "ChartMultiTooltip.qml")),
        )
        assert not chart_multi_tooltip_component.isError(), [
            error.toString() for error in chart_multi_tooltip_component.errors()
        ]
        chart_multi_tooltip = chart_multi_tooltip_component.create(engine.rootContext())
        assert chart_multi_tooltip is not None, [
            error.toString() for error in chart_multi_tooltip_component.errors()
        ]
        keep.append((chart_multi_tooltip_component, chart_multi_tooltip))
        assert chart_multi_tooltip.property("_tooltipRadius") == 18
        assert _rgb(chart_multi_tooltip.property("_tooltipBackground")) == (247, 252, 254)
        assert _rgb(chart_multi_tooltip.property("_tooltipBorderColor")) == (185, 204, 209)

        chart_legend_component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(chart_internal_dir / "ChartBottomLegend.qml")),
        )
        assert not chart_legend_component.isError(), [
            error.toString() for error in chart_legend_component.errors()
        ]
        chart_legend = chart_legend_component.create(engine.rootContext())
        assert chart_legend is not None, [
            error.toString() for error in chart_legend_component.errors()
        ]
        keep.append((chart_legend_component, chart_legend))
        assert chart_legend.property("_itemRadius") == 10
        assert _rgb(chart_legend.property("_itemHoverColor")) == (234, 244, 247)
        assert _rgb(chart_legend.property("_itemBorderColor")) == (220, 233, 237)

        chart_data_zoom_path = chart_internal_dir.parent / "ChartDataZoom.qml"
        chart_data_zoom_component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(chart_data_zoom_path)),
        )
        assert not chart_data_zoom_component.isError(), [
            error.toString() for error in chart_data_zoom_component.errors()
        ]
        chart_data_zoom = chart_data_zoom_component.create(engine.rootContext())
        assert chart_data_zoom is not None, [
            error.toString() for error in chart_data_zoom_component.errors()
        ]
        keep.append((chart_data_zoom_component, chart_data_zoom))
        assert chart_data_zoom.property("_panelRadius") == 14
        assert _rgb(chart_data_zoom.property("_panelColor")) == (248, 251, 252)
        assert _rgb(chart_data_zoom.property("_panelBorderColor")) == (220, 233, 237)
        assert chart_data_zoom.property("_thumbnailFillAlpha") == 0.3
        assert chart_data_zoom.property("_thumbnailStrokeAlpha") == 0.6

        page_path = Path(__file__).resolve().parents[2] / "examples" / "pages" / "PrismDesignPage.qml"
        page_component = QQmlComponent(engine, QUrl.fromLocalFile(str(page_path)))
        assert not page_component.isError(), [error.toString() for error in page_component.errors()]
        page = page_component.create(engine.rootContext())
        assert page is not None, [error.toString() for error in page_component.errors()]
        keep.append((page_component, page))
        assert page.property("galleryEvidenceViewKeys").split("|") == [
            "Token Board",
            "State Wall",
            "Component Matrix",
            "Three Skin Compare",
            "Real App Surface",
            "Dark Audit",
        ]
        assert page.property("stateWallEvidenceKeys").split("|") == [
            "normal",
            "hover",
            "pressed",
            "focused",
            "disabled",
            "selected",
            "error",
            "success",
            "loading",
        ]
        assert page.property("darkAuditEvidenceKeys").split("|") == [
            "input",
            "table",
            "overlay",
            "semantic",
            "focus",
            "selection",
        ]

        resource_dir = Path(__file__).resolve().parents[2] / "examples" / "resources"
        qrc_text = (resource_dir / "gallery.qrc").read_text(encoding="utf-8")
        rcc_path = resource_dir / "gallery.rcc"
        registered_gallery_resources = QResource.registerResource(str(rcc_path))
        assert registered_gallery_resources
        try:
            for theme_name in ("light", "dark"):
                for skin_name in ("fluent", "neobrutalism", "prism-design"):
                    asset_name = f"image/prism-design/skin-compare-{skin_name}-{theme_name}.png"
                    assert (resource_dir / asset_name).is_file()
                    assert f"<file>{asset_name}</file>" in qrc_text
                    assert QFile.exists(f":/{asset_name}")
        finally:
            QResource.unregisterResource(str(rcc_path))

        setTheme(Theme.DARK)
        keep.append(_build(engine, b"""
import QtQuick
import PrismQML
Item {
    property string skinValue: Enums.skin
    property bool prismDesign: Enums.isPrismDesign
    property color accent: Enums.accentColor
    property color background: Enums.backgroundColor
    property color surface: Enums.surfaceColor
    property color chartFirst: Enums.chartColors.palette[0]
}
"""))
        dark_tokens = keep[-1][1]
        assert dark_tokens.property("skinValue") == "prism_design"
        assert dark_tokens.property("prismDesign") is True
        assert _rgb(dark_tokens.property("accent")) == (109, 235, 242)
        assert _rgb(dark_tokens.property("background")) == (9, 14, 16)
        assert _rgb(dark_tokens.property("surface")) == (16, 24, 27)
        assert _rgb(dark_tokens.property("chartFirst")) == (109, 235, 242)

        keep.append(_build(engine, b"""
import PrismQML
CheckIndicator {
    checkState: 0
}
"""))
        dark_check_indicator = keep[-1][1]
        assert _rgb(dark_check_indicator.property("_indicatorColor")) == (26, 37, 41)
        assert _rgb(dark_check_indicator.property("_indicatorBorderColor")) == (106, 169, 181)

        keep.append(_build(engine, b"""
import PrismQML
Slider {
    width: 220
    value: 55
}
"""))
        dark_slider = keep[-1][1]
        assert _rgb(dark_slider.property("handleColor")) == (26, 37, 41)
        assert _rgb(dark_slider.property("_trackColor")) == (12, 21, 24)
        assert _rgb(dark_slider.property("_progressColor")) == (109, 235, 242)
        assert _rgb(dark_slider.property("_handleBorderColor")) == (106, 169, 181)

        keep.append(_build(engine, b"""
import PrismQML
Rating {
    value: 3
}
"""))
        dark_rating = keep[-1][1]
        assert _rgb(dark_rating.property("_effectiveOutlineColor")) == (115, 138, 145)

        dark_chart_tooltip_component = QQmlComponent(engine, QUrl.fromLocalFile(str(chart_tooltip_path)))
        assert not dark_chart_tooltip_component.isError(), [
            error.toString() for error in dark_chart_tooltip_component.errors()
        ]
        dark_chart_tooltip = dark_chart_tooltip_component.create(engine.rootContext())
        assert dark_chart_tooltip is not None, [
            error.toString() for error in dark_chart_tooltip_component.errors()
        ]
        keep.append((dark_chart_tooltip_component, dark_chart_tooltip))
        assert _rgb(dark_chart_tooltip.property("_tooltipBackground")) == (34, 48, 54)
        assert _rgb(dark_chart_tooltip.property("_tooltipBorderColor")) == (50, 72, 79)

        dark_chart_data_zoom_component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(chart_data_zoom_path)),
        )
        assert not dark_chart_data_zoom_component.isError(), [
            error.toString() for error in dark_chart_data_zoom_component.errors()
        ]
        dark_chart_data_zoom = dark_chart_data_zoom_component.create(engine.rootContext())
        assert dark_chart_data_zoom is not None, [
            error.toString() for error in dark_chart_data_zoom_component.errors()
        ]
        keep.append((dark_chart_data_zoom_component, dark_chart_data_zoom))
        assert _rgb(dark_chart_data_zoom.property("_panelColor")) == (16, 24, 27)
        assert _rgb(dark_chart_data_zoom.property("_panelBorderColor")) == (38, 58, 65)
        assert dark_chart_data_zoom.property("_thumbnailFillAlpha") == 0.3
        assert dark_chart_data_zoom.property("_thumbnailStrokeAlpha") == 0.6

        dark_page_component = QQmlComponent(engine, QUrl.fromLocalFile(str(page_path)))
        assert not dark_page_component.isError(), [
            error.toString() for error in dark_page_component.errors()
        ]
        dark_page = dark_page_component.create(engine.rootContext())
        assert dark_page is not None, [error.toString() for error in dark_page_component.errors()]
        keep.append((dark_page_component, dark_page))
    finally:
        setTheme(Theme.LIGHT)
        setSkin(Skin.FLUENT)
