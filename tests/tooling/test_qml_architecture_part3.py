# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Domain bucket 3/7 of the former test_qml_architecture.py."""
import pytest  # noqa: F401
from qml_architecture_shared import *
from qml_architecture_shared import (
    _source,
    _declaration_indent,
    _assert_modularized,
    _CHART_INTERNAL,
    _CHART_MATH,
    _PICKER_INTERNAL,
    _PICKER_HSV,
    _PICKER_DIALOG,
    _PICKER_DROPDOWN,
)

def test_boxplot_chart_content_keeps_canvas_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/BoxplotChartContent.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/BoxplotChartCanvas.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 250
    assert helper.exists()
    assert len(helper_source.splitlines()) < 350
    assert "BoxplotChartCanvas {" in source
    assert "boxplotControl: root" in source
    assert "required property var boxplotControl" in helper_source
    assert "readonly property var control: boxplotControl" in helper_source
    assert "function paintVertical(" in helper_source
    assert "function paintHorizontal(" in helper_source
    assert "Geometry.paintRange(" in helper_source
    assert "\n    Canvas {" not in source
    assert "function paintVertical(" not in source
    assert "function paintHorizontal(" not in source

def test_drawer_keeps_outside_window_modularized():
    entry = _source("prismqml/PrismQML/controls/containers/Drawer/Drawer.qml")
    helper = _source(
        "prismqml/PrismQML/controls/containers/Drawer/_internal/"
        "DrawerOutsideWindow.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 150
    assert 'import "_internal" as DrawerInternal' in source
    assert "DrawerInternal.DrawerOutsideWindow {" in source
    assert "property var drawerControl: control" in source
    assert "drawerControl: outsideDrawerWindowLoader.drawerControl" in source
    assert "required property var drawerControl" in helper_source
    assert "readonly property alias panel: outsideDrawerPanel" in helper_source
    assert "readonly property var control: drawerControl" in helper_source
    assert 'objectName: "outsideDrawerWindow"' in helper_source
    for token in (
        'objectName: "outsideDrawerViewport"',
        'objectName: "outsideDrawerPanel"',
        "transientParent: null",
        "\n            Window {",
    ):
        assert token not in source

    surface = _source(
        "prismqml/PrismQML/controls/containers/Drawer/_internal/DrawerSurface.qml"
    )
    surface_source = surface.read_text(encoding="utf-8")
    assert len(source.splitlines()) < 370
    assert surface.exists()
    assert len(surface_source.splitlines()) < 220
    assert "DrawerInternal.DrawerSurface {" in source
    assert "required property var drawerControl" in surface_source
    assert "default property alias content: contentItem.data" in surface_source
    assert "readonly property alias panel: drawer" in surface_source
    for token in (
        "RectangularShadow {",
        "NeumorphicShadow {",
        "\n        id: drawer\n",
        "\n        id: contentItem\n",
    ):
        assert token not in source

def test_smooth_scroll_helper_keeps_wheel_input_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/SmoothScrollHelper.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/_internal/"
        "SmoothScrollWheelArea.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert 'import "_internal" as ScrollBarInternal' in source
    assert "ScrollBarInternal.SmoothScrollWheelArea {" in source
    assert "scrollHelper: helper" in source
    assert "required property var scrollHelper" in helper_source
    assert "parent: scrollHelper.target" in helper_source
    assert "anchors.fill: parent" in helper_source
    assert "onWheel:" in helper_source
    assert "MouseArea {" not in source
    assert "onWheel:" not in source

def test_smooth_scroll_helper_keeps_frame_driver_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/SmoothScrollHelper.qml"
    )
    driver = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/_internal/"
        "SmoothScrollFrameDriver.qml"
    )
    source = entry.read_text(encoding="utf-8")
    driver_source = driver.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert driver.exists()
    assert len(driver_source.splitlines()) < 120
    assert source.count("ScrollBarInternal.SmoothScrollFrameDriver {") == 2
    assert "Behavior on _smoothY" not in source
    assert "Behavior on _smoothX" not in source
    assert "NumberAnimation {" not in source
    assert "Connections {" in driver_source
    assert "required property var scrollHelper" in driver_source
    assert "required property bool verticalAxis" in driver_source
    assert "function onFrameSwapped()" in driver_source
    assert "target.update()" in driver_source
    assert "WindowHelper.easingValueForProgress" in driver_source
    assert "Easing.valueForProgress" not in driver_source
    assert "AnimationController {" not in driver_source
    assert "FrameAnimation {" not in driver_source
    assert "Timer {" not in driver_source

def test_smooth_scroll_helper_keeps_bounce_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/SmoothScrollHelper.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/_internal/"
        "SmoothScrollBounceTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 80
    assert "ScrollBarInternal.SmoothScrollBounceTimer {" in source
    assert "scrollHelper: helper" in source
    assert "required property var scrollHelper" in helper_source
    assert "required property bool verticalAxis" in helper_source
    assert "scrollHelper._releaseBounceTimer(verticalAxis, bounceTimer)" in helper_source
    assert "\n        Timer {\n            id: bounceTimer\n" not in source

def test_smooth_scroll_helper_keeps_bounds_reconcile_timers_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/SmoothScrollHelper.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/containers/ScrollBar/_internal/"
        "SmoothScrollBoundsReconcileTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 60
    assert "ScrollBarInternal.SmoothScrollBoundsReconcileTimer {" in source
    assert source.count("SmoothScrollBoundsReconcileTimer {") == 2
    assert "objectName: \"smoothScrollVerticalReconcileTimer\"" in source
    assert "objectName: \"smoothScrollHorizontalReconcileTimer\"" in source
    assert "scrollHelper: helper" in source
    assert "verticalAxis: true" in source
    assert "verticalAxis: false" in source
    assert "required property var scrollHelper" in helper_source
    assert "required property bool verticalAxis" in helper_source
    assert 'objectName: verticalAxis' in helper_source
    assert "interval: Enums.duration.instant" in helper_source
    assert "repeat: false" in helper_source
    assert "scrollHelper._reconcileVerticalBounds()" in helper_source
    assert "scrollHelper._reconcileHorizontalBounds()" in helper_source
    assert "\n    Timer {\n        id: verticalReconcileTimer" not in source
    assert "\n    Timer {\n        id: horizontalReconcileTimer" not in source

def test_flow_layout_keeps_append_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/containers/Layout/FlowLayout.qml")
    helper = _source(
        "prismqml/PrismQML/controls/containers/Layout/_internal/"
        "FlowLayoutAppendTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 400
    assert helper.exists()
    assert len(helper_source.splitlines()) < 50
    assert 'import "_internal" as LayoutInternal' in source
    assert "LayoutInternal.FlowLayoutAppendTimer {" in source
    assert "id: appendLayoutTimer" in source
    assert "host: control" in source
    assert "required property var host" in helper_source
    assert 'objectName: "flowLayoutAppendTimer"' in helper_source
    assert "interval: 0" in helper_source
    assert "repeat: false" in helper_source
    assert "host._appendLayoutPending = false" in helper_source
    assert "host._appendDefaultItems()" in helper_source
    assert "\n    Timer {\n        id: appendLayoutTimer" not in source

def test_flow_layout_keeps_layout_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/containers/Layout/FlowLayout.qml")
    helper = _source(
        "prismqml/PrismQML/controls/containers/Layout/_internal/"
        "FlowLayoutLayoutTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 400
    assert helper.exists()
    assert len(helper_source.splitlines()) < 40
    assert "LayoutInternal.FlowLayoutLayoutTimer {" in source
    assert "id: layoutTimer" in source
    assert "host: control" in source
    assert "required property var host" in helper_source
    assert 'objectName: "flowLayoutLayoutTimer"' in helper_source
    assert "interval: 0" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: host._performLayout()" in helper_source
    assert "\n    Timer {\n        id: layoutTimer" not in source

def test_constants_keeps_theme_colors_modularized():
    entry = _source("prismqml/PrismQML/PrismEnums/Constants.qml")
    helper = _source(
        "prismqml/PrismQML/PrismEnums/_internal/ConstantsThemeColors.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 120
    assert 'import "_internal" as ConstantsInternal' in source
    assert (
        "readonly property QtObject themeColors: "
        "ConstantsInternal.ConstantsThemeColors {}"
    ) in source
    assert "readonly property QtObject themeColors: QtObject {" not in source
    assert "readonly property color backgroundDark" in helper_source
    assert "readonly property color accentForeground" in helper_source
    assert "readonly property color tabSelectedLight" in helper_source
    assert "required property bool isDark" not in helper_source

def test_metrics_keeps_shadow_logic_modularized():
    entry = _source("prismqml/PrismQML/PrismEnums/Metrics.qml")
    helper = _source(
        "prismqml/PrismQML/PrismEnums/_internal/MetricsShadow.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 900
    assert helper.exists()
    assert len(helper_source.splitlines()) < 150
    assert 'import "_internal" as MetricsInternal' in source
    assert "readonly property QtObject shadow: MetricsInternal.MetricsShadow {" in source
    assert "isDark: root.isDark" in source
    assert "isTicket: root.isTicket" in source
    assert "readonly property QtObject shadow: QtObject {" not in source
    assert "required property bool isDark" in helper_source
    assert "required property bool isTicket" in helper_source
    for level in (2, 4, 8, 16, 28):
        assert f"readonly property QtObject level{level}: QtObject {{" in helper_source
        assert f"function applyLevel{level}(target)" in helper_source

def test_combo_box_core_keeps_visual_content_modularized():
    entry = _source("prismqml/PrismQML/controls/inputs/ComboBox/ComboBoxCore.qml")
    helper = _source(
        "prismqml/PrismQML/controls/inputs/ComboBox/_internal/ComboBoxCoreContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 300
    assert helper.exists()
    assert len(helper_source.splitlines()) < 350
    assert "ComboBoxCoreContent {" in source
    assert "required property var comboControl" in helper_source
    for alias in (
        "editableInput",
        "mouseArea",
        "editableClickArea",
        "comboTextMeasureLoader",
        "popup",
    ):
        assert f"property alias {alias}:" in helper_source
    assert "property alias _popup: comboContent.popup" in source
    assert "layer.enabled: true" in helper_source
    assert "PopupWindowCore {" in helper_source
    assert "RectangularShadow {" in helper_source
    assert "PopupWindowCore {" not in source
    assert "layer.enabled: true" not in source

def test_combo_box_multi_tree_keeps_visual_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/ComboBox/ComboBoxMultiTree.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/ComboBox/_internal/ComboBoxMultiTreeContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 400
    assert helper.exists()
    assert len(helper_source.splitlines()) < 220
    assert 'import "_internal"' in source
    assert "ComboBoxMultiTreeContent {" in source
    assert "required property var comboControl" in helper_source
    assert "property alias _flatListModel: multiTreeContent.flatListModel" in source
    assert "property alias tokenFlickable: multiTreeContent.tokenFlickable" in source
    assert "property alias flatListModel: internalFlatListModel" in helper_source
    assert "property alias tokenFlickable: tokenFlickable" in helper_source
    assert "property alias popupContent: treePopupContent" in helper_source
    for visual_type in ("PopupSearchBox", "TreeMenuDelegate", "MultiSelectToken"):
        assert f"{visual_type} {{" in helper_source
        assert f"{visual_type} {{" not in source
    assert "ListModel {" in helper_source
    assert "Flickable {" in helper_source
    assert "popupContent: multiTreeContent.popupContent" in source

def test_xy_chart_core_keeps_axes_visuals_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/XYChartCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/XYChartAxes.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 350
    assert helper.exists()
    assert len(helper_source.splitlines()) < 350
    assert "XYChartAxes {" in source
    assert "chartControl: root" in source
    assert "required property var chartControl" in helper_source
    assert "required property var axisFontMetrics" in helper_source
    assert "readonly property Item chartArea: axesLayer.chartArea" in source
    assert "readonly property Item chartArea: chartAreaItem" in helper_source
    assert "readonly property var control: chartControl" in helper_source
    for token in (
        "id: gridLines",
        "id: horizontalYAxisLabels",
        "id: xAxisLabels",
        "id: scatterXAxisLabels",
        "HoverBehavior on color",
        'objectName: "chartXAxisViewport"',
    ):
        assert token not in source

def test_chart_view_keeps_render_layer_modularized():
    entry = _source("prismqml/PrismQML/controls/data/Chart/ChartView.qml")
    helper = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/ChartRenderLayer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 500
    assert "ChartRenderLayer {" in source
    assert "required property var chartControl" in helper_source
    assert "renderLayer.chart" not in helper_source
    for loader_name in (
        "xyChartBaseLoader", "barContentLoader", "lineContentLoader",
        "scatterContentLoader",
    ):
        assert f"property alias {loader_name}: {loader_name}" in helper_source
        assert f'objectName: "{loader_name}"' in helper_source
    for property_name, loader_name in (
        ("_xyChartBase", "xyChartBaseLoader"),
        ("_barContent", "barContentLoader"),
        ("_lineContent", "lineContentLoader"),
        ("_scatterContent", "scatterContentLoader"),
    ):
        assert (
            f"readonly property var {property_name}: "
            f"renderLayer.{loader_name}.item"
        ) in source

def test_settings_card_keeps_render_layer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/settings/SettingsCard/SettingsCard.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/settings/SettingsCard/_internal/"
        "SettingsCardRenderLayer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 500
    assert 'import "_internal"' in source
    assert "SettingsCardRenderLayer {" in source
    assert "required property var cardControl" in helper_source
    assert "property alias cardLoader: cardLoader" in helper_source
    assert "readonly property var control: cardControl" in helper_source
    assert "Component {" not in source
    assert "FolderDialog {" not in source

def test_chat_message_list_keeps_slot_delegate_modularized():
    entry = _source("prismqml/PrismQML/controls/chat/ChatMessageList.qml")
    helper = _source(
        "prismqml/PrismQML/controls/chat/_internal/ChatMessageSlot.qml"
    )
    viewport = _source(
        "prismqml/PrismQML/controls/chat/_internal/ChatMessageViewport.qml"
    )

    assert len(entry.read_text(encoding="utf-8").splitlines()) < 500
    assert helper.exists()
    assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
    assert "ChatMessageSlot {" in viewport.read_text(encoding="utf-8")

def test_chat_message_slot_keeps_measurement_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/chat/_internal/ChatMessageSlot.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/chat/_internal/"
        "ChatMessageSlotMeasurementTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 130
    assert helper.exists()
    assert len(helper_source.splitlines()) < 70
    assert 'import "." as ChatInternal' in source
    assert "ChatInternal.ChatMessageSlotMeasurementTimer {" in source
    assert "id: slotMeasurementTimer" in source
    assert "targetSlot: slot" in source
    assert "host: slot.host" in source
    assert "\n    Timer {" not in source
    assert "required property var targetSlot" in helper_source
    assert "required property var host" in helper_source
    assert 'objectName: "chatMessageSlotMeasurementTimer"' in helper_source
    assert "interval: 0" in helper_source
    assert "repeat: false" in helper_source
    assert "host._cacheSlotHeight(targetSlot, targetSlot.item.implicitHeight)" in helper_source
    assert "host._cacheSlotHeight(slot, slot.item.implicitHeight)" not in source

def test_code_block_keeps_copy_feedback_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/chat/CodeBlock.qml")
    helper = _source(
        "prismqml/PrismQML/controls/chat/_internal/"
        "CodeBlockCopyFeedbackTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 180
    assert helper.exists()
    assert len(helper_source.splitlines()) < 60
    assert 'import "_internal" as ChatInternal' in source
    assert "ChatInternal.CodeBlockCopyFeedbackTimer {" in source
    assert "id: copiedTimer" in source
    assert "host: copyBtn" in source
    assert "required property var host" in helper_source
    assert 'objectName: "codeBlockCopyFeedbackTimer"' in helper_source
    assert "interval: Enums.duration.copyFeedback" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: host._copied = false" in helper_source
    assert "onTriggered: copyBtn._copied = false" not in source
    assert "\n            Timer {" not in source

def test_chat_message_list_keeps_scroll_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/chat/ChatMessageList.qml")
    helper = _source(
        "prismqml/PrismQML/controls/chat/_internal/"
        "ChatMessageListScrollToBottomTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 400
    assert helper.exists()
    assert len(helper_source.splitlines()) < 60
    assert 'import "_internal" as ChatInternal' in source
    assert "ChatInternal.ChatMessageListScrollToBottomTimer {" in source
    assert "id: scrollToBottomTimer" in source
    assert "host: control" in source
    assert source.count("\n    Timer {") == 0
    assert "required property var host" in helper_source
    assert 'objectName: "chatMessageListScrollToBottomTimer"' in helper_source
    assert "interval: 0" in helper_source
    assert "repeat: false" in helper_source
    assert "host._scrollPending = false" in helper_source
    assert "if (host._followBottom) host._scrollToBottom()" in helper_source
    assert "control._scrollPending = false" not in source
    assert "if (control._followBottom) control._scrollToBottom()" not in source

def test_chat_message_list_keeps_slot_layout_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/chat/ChatMessageList.qml")
    helper = _source(
        "prismqml/PrismQML/controls/chat/_internal/"
        "ChatMessageListSlotLayoutTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 350
    assert helper.exists()
    assert len(helper_source.splitlines()) < 90
    assert 'import "_internal" as ChatInternal' in source
    assert "ChatInternal.ChatMessageListSlotLayoutTimer {" in source
    assert "id: slotLayoutTimer" in source
    assert "host: control" in source
    assert source.count("\n    Timer {") == 0
    assert "required property var host" in helper_source
    assert 'objectName: "chatMessageListSlotLayoutTimer"' in helper_source
    assert "interval: 0" in helper_source
    assert "repeat: false" in helper_source
    for marker in (
        "host._layoutPending = false",
        "host.messageRepeater.itemAt",
        "host.messageColumn.height = nextY",
        "host._scheduleLoadRangeUpdate()",
        "host._scheduleScrollToBottom()",
        "host._setContentY(host.messageViewport.contentY + anchorDelta, false)",
    ):
        assert marker in helper_source
    assert "control._layoutPending = false" not in source
    assert "control.messageColumn.height = nextY" not in source

def test_chat_message_list_keeps_load_range_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/chat/ChatMessageList.qml")
    helper = _source(
        "prismqml/PrismQML/controls/chat/_internal/"
        "ChatMessageListLoadRangeTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 350
    assert helper.exists()
    assert len(helper_source.splitlines()) < 70
    assert 'import "_internal" as ChatInternal' in source
    assert "ChatInternal.ChatMessageListLoadRangeTimer {" in source
    assert "id: loadRangeTimer" in source
    assert "host: control" in source
    assert "required property var host" in helper_source
    assert 'objectName: "chatMessageListLoadRangeTimer"' in helper_source
    assert "interval: 0" in helper_source
    assert "repeat: false" in helper_source
    for marker in (
        "host._rangeUpdatePending = false",
        "host.messageRepeater.itemAt",
        "host._applyLoadRange(-1, -1)",
        "host._scheduleSlotLayout(0)",
        "host._findFirstLoadIndex(topY)",
        "host._findLastLoadIndex(bottomY)",
        "host._applyLoadRange(firstIndex, lastIndex)",
    ):
        assert marker in helper_source
    assert "control._rangeUpdatePending = false" not in source
    assert "control._applyLoadRange(firstIndex, lastIndex)" not in source

def test_chat_message_list_keeps_viewport_content_modularized():
    entry = _source("prismqml/PrismQML/controls/chat/ChatMessageList.qml")
    helper = _source(
        "prismqml/PrismQML/controls/chat/_internal/ChatMessageViewport.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 400
    assert helper.exists()
    assert len(helper_source.splitlines()) < 120
    assert 'import "_internal" as ChatInternal' in source
    assert "ChatInternal.ChatMessageViewport {" in source
    assert "required property var chatControl" in helper_source
    assert "required property var messageModel" in helper_source
    for alias in ("viewport", "contentColumn", "repeater"):
        assert f"property alias {alias}:" in helper_source
    for alias in ("messageViewport", "messageColumn", "messageRepeater"):
        assert f"property alias {alias}: messageContent." in source
    for marker in (
        "id: messageViewport",
        "id: messageColumn",
        "id: messageRepeater",
        "ChatMessageSlot {",
    ):
        assert marker not in source

def test_tip_popup_keeps_main_window_surface_modularized():
    entry = _source("prismqml/PrismQML/controls/feedback/Tooltip/TipPopup.qml")
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Tooltip/_internal/TipPopupWindow.qml"
    )
    mover = _source(
        "prismqml/PrismQML/controls/feedback/Tooltip/_internal/TipContentMover.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")
    mover_source = mover.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 370
    assert helper.exists()
    assert len(helper_source.splitlines()) < 180
    assert 'import "_internal" as TooltipInternal' in source
    assert "TooltipInternal.TipPopupWindow {" in source
    # 调用方内容先由 default property alias 收进暂存 Item,再必须由 TipContentMover
    # 显式 reparent 进原生弹层:跨窗口直接赋值 QQmlListProperty 不会搬运对象,
    # 旧写法(转发 control.contentData)实测一个字符都渲染不出来。
    assert "default property alias contentData: contentStaging.data" in source
    assert "TooltipInternal.TipContentMover {" in source
    assert "contentMover.moveContent()" in source
    assert source.count("onChildrenChanged: contentMover.moveContent()") == 2
    assert "control: control" in source
    # 弹层尺寸必须是公开属性:富自定义内容需要比默认 220x90 更宽的表面,
    # 硬编码会让调用方无从配置(桌宠余额气泡按设计需要 324 宽)。
    assert "property int viewWidth:" in source
    assert "property int viewHeight:" in source
    assert "viewWidth: control.viewWidth" in source
    assert "viewHeight: control.viewHeight" in source
    assert "internalItems: [contentStaging, popupWindowLoader, arrowWindowLoader, positionTracker]" in source
    assert "property alias customContentHost: customContentHost" in helper_source
    assert "required property var control" in mover_source
    assert "required property var internalItems" in mover_source
    assert "host.forceLayout()" in mover_source
    assert "required property var popupControl" in helper_source
    assert "required property var positionHelper" in helper_source
    assert "id: customContentHost" in helper_source
    assert helper_source.index("text: popupControl.title") < helper_source.index(
        "id: customContentHost"
    )
    assert helper_source.index("text: popupControl.content") < helper_source.index(
        "id: customContentHost"
    )
    assert 'objectName: "tipPopupSurface"' in helper_source
    assert "\n                id: popupWindow\n" not in source
    for marker in (
        'objectName: "tipPopupSurface"',
        'objectName: "tipPrimaryActionButton"',
        'objectName: "tipSecondaryActionButton"',
    ):
        assert marker not in source


def test_tip_popup_resolves_target_position_outside_qtobject_helper():
    entry = _source("prismqml/PrismQML/controls/feedback/Tooltip/TipPopup.qml")
    position_helper = _source(
        "prismqml/PrismQML/controls/feedback/Tooltip/_internal/TipPositionHelper.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = position_helper.read_text(encoding="utf-8")

    assert "function _resolveTargetGlobalPosition()" in source
    assert "var pos = posHelper.calculatePosition(_resolveTargetGlobalPosition())" in source
    assert "onTargetMoved: (globalPosition) => control._applyTrackedPosition(globalPosition)" in source
    assert "function calculatePosition(targetGlobalPosition)" in helper_source
    assert "target.mapToGlobal" not in helper_source
    assert source.index("popupWindow.show(); popupWindow.raise(); popupWindow.requestActivate()") < source.index(
        "var pos = posHelper.calculatePosition(_resolveTargetGlobalPosition())"
    )
