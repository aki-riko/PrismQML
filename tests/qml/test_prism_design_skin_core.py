# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Light Prism Design tokens, core controls, and navigation coverage."""

from test_prism_design_skin_support import rgb


def _build_light_tokens(context):
    return context.build(b"""
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
""")


def _assert_light_tokens(tokens):
    assert tokens.property("skinValue") == "prism_design"
    assert tokens.property("prismDesign") is True
    assert tokens.property("neobrutalism") is False
    assert rgb(tokens.property("accent")) == (11, 127, 137)
    assert rgb(tokens.property("background")) == (238, 245, 247)
    assert rgb(tokens.property("surface")) == (248, 251, 252)
    assert rgb(tokens.property("controlBg")) == (252, 254, 255)
    assert rgb(tokens.property("segmentedSelected")) == (221, 244, 247)
    assert rgb(tokens.property("treeItemHover")) == (237, 245, 247)
    assert rgb(tokens.property("chartFirst")) == (11, 127, 137)
    assert rgb(tokens.property("chartGrid")) == (214, 227, 230)
    assert tokens.property("radiusControl") == 10
    assert tokens.property("radiusCard") == 14
    assert tokens.property("radiusPopup") == 18


def _verify_button(context):
    button = context.build(b"""
import PrismQML
Button {
    text: "OK"
    style: Enums.button.style_primary
    width: 120
    height: 36
}
""")
    assert button.property("radius") == 10
    assert button.property("_neoPressShift") == 0
    assert rgb(button.property("color")) == (11, 127, 137)


def _verify_card(context):
    card = context.build(b"""
import PrismQML
Card {
    width: 200
    height: 120
}
""")
    assert card.property("borderRadius") == 14
    assert rgb(card.property("color")) == (252, 254, 255)


def _verify_input_core(context):
    input_core = context.build(b"""
import PrismQML
InputCore {
    width: 200
    height: 32
}
""")
    assert input_core.property("radius") == 10
    assert rgb(input_core.property("color")) == (252, 254, 255)
    assert rgb(input_core.property("inputTextColor")) == (18, 34, 38)


def _verify_segmented_control(context):
    segmented = context.build(b"""
import PrismQML
SegmentedControl {
    items: ["Token", "State", "Surface"]
    currentIndex: 1
}
""")
    assert segmented.property("radius") == 10
    assert rgb(segmented.property("color")) == (248, 251, 252)


def _verify_info_bar(context):
    info_bar = context.build(b"""
import PrismQML
InfoBar {
    title: "Info"
    content: "Prism overlay"
    duration: Enums.duration.persistent
}
""")
    assert info_bar.property("radius") == 18
    assert rgb(info_bar.property("borderColor")) == (185, 204, 209)


def _verify_action(context):
    action = context.build(b"""
import PrismQML
Action {
    text: "Cut"
}
""")
    assert action.property("radius") == 10


def _verify_list_widget(context):
    list_widget = context.build(b"""
import PrismQML
ListWidget {
    width: 220
    height: 120
}
""")
    assert list_widget.property("radius") == 14
    assert list_widget.property("borderRadius") == 14


def _verify_data_widget(context):
    data_widget = context.build(b"""
import PrismQML
DataWidgetCore {
    width: 240
    height: 140
}
""")
    assert data_widget.property("borderRadius") == 14


def _verify_table_widget(context):
    table_widget = context.build(b"""
import PrismQML
TableWidget {
    width: 260
    height: 160
    tableData: [{ "name": "Alpha" }]
    columns: [{ "text": "Name", "role": "name" }]
}
""")
    assert table_widget.property("borderRadius") == 14


def _verify_tree_widget(context):
    tree_widget = context.build(b"""
import PrismQML
TreeWidget {
    width: 260
    height: 160
    model: [{ "text": "Root", "children": [{ "text": "Child" }] }]
}
""")
    assert tree_widget.property("borderRadius") == 14


def _verify_chart_view(context):
    chart_view = context.build(b"""
import PrismQML
ChartView {
    width: 260
    height: 180
    chartData: [{ "label": "Alpha", "value": 12 }]
}
""")
    assert chart_view.property("radius") == 14


def _verify_tag(context):
    tag = context.build(b"""
import PrismQML
Tag {
    text: "Stable"
}
""")
    assert tag.property("radius") == 10


def _build_navigation_basics(context):
    context.build(b"""
import PrismQML
NavigationViewItem {
    text: "Dashboard"
    icon: "Home"
    selected: true
}
""")
    context.build(b"""
import PrismQML
PipsPager {
    pageCount: 4
    currentIndex: 1
}
""")


def _build_navigation_paging(context):
    context.build(b"""
import PrismQML
ToggleNavigationBar {
    width: 220
    height: 160
    model: [{ "text": "Files", "icon": "Home" }, { "text": "Settings", "icon": "Settings" }]
    currentIndex: 1
}
""")
    context.build(b"""
import PrismQML
Paginator {
    currentPage: 2
    totalPages: 6
    visiblePages: 5
}
""")


def _build_navigation_tabs(context):
    context.build(b"""
import PrismQML
Pivot {
    items: [{ "key": "overview", "text": "Overview" }, { "key": "details", "text": "Details" }]
    currentIndex: 1
}
""")
    context.build(b"""
import PrismQML
TabWidget {
    width: 320
    height: 220
    tabs: [{ "title": "Overview", "icon": "Home" }, { "title": "Details", "icon": "Settings" }]
    currentIndex: 1
    showAddButton: true
}
""")


def _build_navigation_profile(context):
    context.build(b"""
import PrismQML
NavigationProfileCard {
    title: "Prism"
    subtitle: "Design Skin"
    isCompacted: false
}
""")


def verify_light_core(context):
    _assert_light_tokens(_build_light_tokens(context))
    _verify_button(context)
    _verify_card(context)
    _verify_input_core(context)
    _verify_segmented_control(context)
    _verify_info_bar(context)
    _verify_action(context)
    _verify_list_widget(context)
    _verify_data_widget(context)
    _verify_table_widget(context)
    _verify_tree_widget(context)
    _verify_chart_view(context)
    _verify_tag(context)
    _build_navigation_basics(context)
    _build_navigation_paging(context)
    _build_navigation_tabs(context)
    _build_navigation_profile(context)
