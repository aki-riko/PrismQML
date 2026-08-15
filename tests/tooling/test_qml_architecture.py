# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QML architecture boundaries and size gates. QML 架构边界与大小门禁。"""

from pathlib import Path, PurePosixPath

from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
QML_ROOT = ROOT / "prismqml" / "PrismQML"
OVERSIZED_QML_EXCEPTIONS = {
    "prismqml/PrismQML/PrismEnums/Metrics.qml",
}


def _source(relative_path: str) -> Path:
    return ROOT / relative_path


def _assert_modularized(entry_path: str, helper_path: str, helper_type: str) -> None:
    entry = _source(entry_path)
    helper = _source(helper_path)

    assert entry.exists()
    assert helper.exists()
    assert len(entry.read_text(encoding="utf-8").splitlines()) <= 700
    assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
    assert f"{helper_type} {{" in entry.read_text(encoding="utf-8")


def test_qml_files_respect_hard_size_limit():
    violations = []
    for path in sorted(QML_ROOT.rglob("*.qml")):
        relative = path.relative_to(ROOT).as_posix()
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > 700 and relative not in OVERSIZED_QML_EXCEPTIONS:
            violations.append(f"{relative}: {line_count} lines")

    assert violations == []


def test_windows_core_keeps_frame_modularized():
    entry = _source("prismqml/PrismQML/WindowsCore.qml")
    helper = _source(
        "prismqml/PrismQML/_internal/WindowsCoreFrame.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 500
    assert "WindowsCoreFrame {" in source
    assert "required property var targetWindow" in helper_source
    assert "property alias contentData: contentContainer.data" in helper_source
    assert "property alias leftPanelData: leftPanelContainer.data" in helper_source
    assert "id: windowFrame\n" not in source
    assert "id: contentContainer" not in source
    assert "WindowDragHandle {" not in source


def test_login_window_keeps_visual_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/auth/LoginWindow.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/auth/_internal/LoginWindowContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 300
    assert helper.exists()
    assert len(helper_source.splitlines()) < 500
    assert 'import "_internal"' in source
    assert "LoginWindowContent {" in source
    assert "required property var loginControl" in helper_source
    assert "property alias usernameInput: usernameInput" in helper_source
    assert "property alias passwordInput: passwordInput" in helper_source
    assert "MatrixRain {" not in source
    assert "ShadowedRectangle {" not in source
    assert 'objectName: "loginModeToggleArea"' not in source


def test_data_widget_core_keeps_visual_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/DataWidgetCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/_internal/DataWidgetContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 250
    assert helper.exists()
    assert len(helper_source.splitlines()) < 500
    assert 'import "_internal"' in source
    assert "DataWidgetContent {" in source
    assert "required property var dataControl" in helper_source
    assert "property alias listView: listView" in helper_source
    assert "property alias scrollViewportState: scrollViewportState" in helper_source
    assert "contentLayer.needsVerticalScrollBar" in source
    assert "function createHorizontalScrollMixin()" in helper_source
    assert "horizontalScrollMixinComponent.createObject(contentArea)" in helper_source
    assert "contentLayer.createHorizontalScrollMixin()" in source
    assert "RectangularShadow {" not in source
    assert "QtQ.ListView {" not in source
    assert "HorizontalScrollMixin {" not in source


def test_navigation_window_core_keeps_orchestration_modularized():
    entry = _source("prismqml/PrismQML/NavigationWindowCore.qml")
    loading = _source(
        "prismqml/PrismQML/_internal/NavigationWindowLoading.js"
    )
    routing = _source(
        "prismqml/PrismQML/_internal/NavigationWindowRouting.js"
    )
    source = entry.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    for helper in (loading, routing):
        assert helper.exists()
        helper_source = helper.read_text(encoding="utf-8")
        assert len(helper_source.splitlines()) < 500
        assert ".pragma library" in helper_source

    assert (
        'import "_internal/NavigationWindowLoading.js" '
        "as NavigationWindowLoading"
    ) in source
    assert (
        'import "_internal/NavigationWindowRouting.js" '
        "as NavigationWindowRouting"
    ) in source
    assert "NavigationWindowLoading.start(window, index)" in source
    assert "NavigationWindowLoading.completeVisual(window, index)" in source
    assert "NavigationWindowRouting.moveDefaultPages(window," in source
    assert "NavigationWindowRouting.syncSelection(window," in source
    assert "NavigationWindowRouting.handleBottomItemClicked(window," in source


def test_navigation_panel_keeps_background_layer_modularized():
    entry = _source("prismqml/PrismQML/navigation/NavigationPanelCore.qml")
    background = _source(
        "prismqml/PrismQML/navigation/_internal/NavigationPanelBackground.qml"
    )
    border = _source(
        "prismqml/PrismQML/navigation/_internal/NavigationPanelBorder.qml"
    )
    source = entry.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert 'import "_internal"' in source
    assert "NavigationPanelBackground {" in source
    assert "NavigationPanelBorder {" in source
    for helper in (background, border):
        assert helper.exists()
        helper_source = helper.read_text(encoding="utf-8")
        assert len(helper_source.splitlines()) < 300
        assert "required property var panel" in helper_source
        assert "readonly property var control: panel" in helper_source
    assert "z: -2" in background.read_text(encoding="utf-8")
    assert "id: bgCanvas" not in source
    assert "id: acrylicLayer" not in source
    assert "id: rightBorderCanvas" not in source
    assert "TicketPaper {" not in source


def test_button_core_keeps_behavior_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/buttons/Button/ButtonCore.qml"
    )
    logic = _source(
        "prismqml/PrismQML/controls/buttons/Button/_internal/ButtonLogic.js"
    )
    helper_paths = (
        (
            "prismqml/PrismQML/controls/buttons/Button/_internal/"
            "ButtonFeatureLoader.qml",
            "ButtonFeatureLoader",
        ),
        (
            "prismqml/PrismQML/controls/buttons/Button/_internal/"
            "ButtonInteraction.qml",
            "ButtonInteraction",
        ),
        (
            "prismqml/PrismQML/controls/buttons/Button/_internal/"
            "ButtonCountdown.qml",
            "ButtonCountdown",
        ),
    )
    source = entry.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert logic.exists()
    logic_source = logic.read_text(encoding="utf-8")
    assert len(logic_source.splitlines()) < 500
    assert ".pragma library" in logic_source
    assert "Enums" not in logic_source

    for relative_path, helper_type in helper_paths:
        helper = _source(relative_path)
        assert helper.exists()
        assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
        assert f"{helper_type} {{" in source

    assert 'import "_internal" as ButtonInternal' in source
    assert 'import "_internal/ButtonLogic.js" as ButtonLogic' in source
    assert "ButtonLogic.click(control, Enums)" in source
    assert "ButtonLogic.updateTargetColors(" in source
    assert "ButtonLogic.prewarmMenu(control, Enums," in source


def test_popup_window_core_keeps_animation_logic_modularized():
    _assert_modularized(
        "prismqml/PrismQML/controls/utils/PopupWindowCore.qml",
        "prismqml/PrismQML/controls/utils/_internal/PopupAnimations.qml",
        "PopupAnimations",
    )


def test_popup_window_core_keeps_positioning_and_prewarm_modularized():
    entry = _source("prismqml/PrismQML/controls/utils/PopupWindowCore.qml")
    helpers = (
        _source(
            "prismqml/PrismQML/controls/utils/_internal/PopupPositioning.js"
        ),
        _source(
            "prismqml/PrismQML/controls/utils/_internal/PopupPrewarm.js"
        ),
    )
    source = entry.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    for helper in helpers:
        assert helper.exists()
        helper_source = helper.read_text(encoding="utf-8")
        assert len(helper_source.splitlines()) < 500
        assert ".pragma library" in helper_source
        assert "Enums" not in helper_source

    assert (
        'import "_internal/PopupPositioning.js" as PopupPositioning'
        in source
    )
    assert 'import "_internal/PopupPrewarm.js" as PopupPrewarm' in source
    assert "PopupPositioning.calcControlsPopupPosition(" in source
    assert "PopupPositioning.applyTrackedPosition(" in source
    assert "PopupPrewarm.doPrewarm(" in source


def test_list_widget_keeps_data_and_selection_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/List/ListWidget.qml"
    )
    controller = _source(
        "prismqml/PrismQML/controls/data/List/_internal/ListDataController.js"
    )
    source = entry.read_text(encoding="utf-8")
    controller_source = controller.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert controller.exists()
    assert len(controller_source.splitlines()) < 500
    assert ".pragma library" in controller_source
    assert (
        'import "_internal/ListDataController.js" as ListDataController'
        in source
    )

    delegated_methods = (
        "addItem", "addItems", "insertItem", "insertItems", "takeItem",
        "item", "row", "currentItem", "setCurrentItem", "currentRow",
        "setCurrentRow", "selectedItems", "clearSelection", "selectAll",
        "setSelectionMode", "findItems", "sortItems", "clear",
        "setItemText", "setItemIcon", "setItemData", "itemData",
        "setItemCheckState", "itemCheckState", "setItemSelected",
        "handleItemClick", "updateSelectedRows",
    )
    for method in delegated_methods:
        assert f"function {method}(" in controller_source
        assert f"ListDataController.{method}(" in source


def test_stacked_widget_keeps_source_pages_modularized():
    _assert_modularized(
        "prismqml/PrismQML/controls/navigation/StackedWidget.qml",
        "prismqml/PrismQML/controls/navigation/_internal/StackedSourcePages.qml",
        "StackedSourcePages",
    )


def test_stacked_widget_keeps_switching_orchestration_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/StackedWidget.qml")
    source = entry.read_text(encoding="utf-8")
    assert len(source.splitlines()) < 500

    for relative_path, helper_type in (
        (
            "prismqml/PrismQML/controls/navigation/_internal/StackedLazyController.qml",
            "StackedLazyController",
        ),
        (
            "prismqml/PrismQML/controls/navigation/_internal/StackedVisibilityController.qml",
            "StackedVisibilityController",
        ),
    ):
        helper = _source(relative_path)
        assert helper.exists()
        assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
        assert f"{helper_type} {{" in source

    assert "lazyController.preloadLazyHelperWhenReady" in source
    assert "visibilityController.doAnimation" in source


def test_tab_widget_keeps_content_pages_modularized():
    _assert_modularized(
        "prismqml/PrismQML/controls/navigation/TabWidget.qml",
        "prismqml/PrismQML/controls/navigation/_internal/TabContentPages.qml",
        "TabContentPages",
    )


def test_tab_widget_keeps_tab_delegate_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/TabWidget.qml")
    helper = _source("prismqml/PrismQML/controls/navigation/_internal/TabItem.qml")

    assert len(entry.read_text(encoding="utf-8").splitlines()) < 500
    assert helper.exists()
    assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
    assert "TabItem {" in entry.read_text(encoding="utf-8")


def test_bar_chart_keeps_single_series_delegate_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/BarChartContent.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/BarChartBar.qml"
    )

    assert len(entry.read_text(encoding="utf-8").splitlines()) < 500
    assert helper.exists()
    assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
    assert entry.read_text(encoding="utf-8").count("BarChartBar {") == 2


def test_line_chart_content_keeps_canvas_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/LineChartContent.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/Chart/_internal/LineChartCanvas.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 300
    assert "LineChartCanvas {" in source
    assert "lineControl: root" in source
    assert "required property var lineControl" in helper_source
    assert "function paintSingleSeries(" in helper_source
    assert "function paintMultiSeries(" in helper_source
    assert "\n    Canvas {" not in source
    assert "function paintSingleSeries(" not in source
    assert "function paintMultiSeries(" not in source


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

    assert len(entry.read_text(encoding="utf-8").splitlines()) < 500
    assert helper.exists()
    assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
    assert "ChatMessageSlot {" in entry.read_text(encoding="utf-8")


def test_menu_core_keeps_visual_content_modularized():
    entry = _source("prismqml/PrismQML/controls/menus/MenuCore.qml")
    helper = _source("prismqml/PrismQML/controls/menus/_internal/MenuContent.qml")

    assert len(entry.read_text(encoding="utf-8").splitlines()) < 500
    assert helper.exists()
    assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
    assert "MenuContent {" in entry.read_text(encoding="utf-8")


def test_infobar_core_keeps_visual_content_modularized():
    entry = _source("prismqml/PrismQML/controls/feedback/InfoBar/InfoBarCore.qml")
    helper = _source(
        "prismqml/PrismQML/controls/feedback/InfoBar/_internal/InfoBarContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 250
    assert helper.exists()
    assert len(helper_source.splitlines()) < 400
    assert 'import "_internal" as InfoBarInternal' in source
    assert "InfoBarInternal.InfoBarContent {" in source
    assert "required property var infoBar" in helper_source
    assert "property alias customContent: customContentLoader.sourceComponent" in helper_source
    assert "readonly property real calculatedContentWidth" in helper_source
    assert "readonly property real horizontalContentHeight" in helper_source
    assert "readonly property real verticalContentHeight" in helper_source

    for marker in (
        "RectangularShadow {",
        "NeumorphicShadow {",
        "NeoShadow {",
        "CloseButton {",
        "ProgressBar {",
        "ProgressRing {",
        "\n    Loader {",
        "\n    Component {",
    ):
        assert marker not in source


def test_toast_keeps_visual_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Notification/Toast.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Notification/_internal/ToastContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 250
    assert helper.exists()
    assert len(helper_source.splitlines()) < 400
    assert 'import "_internal" as NotificationInternal' in source
    assert "NotificationInternal.ToastContent {" in source
    assert "required property var toast" in helper_source
    assert "property alias customContent: customContentLoader.sourceComponent" in helper_source
    assert "readonly property real calculatedContentWidth" in helper_source
    assert "readonly property real horizontalHeight" in helper_source
    assert "readonly property real verticalHeight" in helper_source

    for marker in (
        "RectangularShadow {",
        "NeumorphicShadow {",
        "NeoShadow {",
        "CloseButton {",
        "ProgressBar {",
        "ProgressRing {",
        "\n    Loader {",
        "\n    Component {",
    ):
        assert marker not in source


def test_calendar_picker_core_keeps_content_tree_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/DatePicker/CalendarPickerCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/DatePicker/_internal/"
        "CalendarPickerContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 200
    assert helper.exists()
    assert len(helper_source.splitlines()) < 450
    assert 'import "_internal" as DatePickerInternal' in source
    assert "DatePickerInternal.CalendarPickerContent {" in source
    assert "required property var calendarControl" in helper_source
    assert "property alias gridWrapperBehavior: gridWrapperBehavior" in helper_source
    assert "property alias dayGrid: dayGrid" in helper_source
    assert "property alias nextGrid: nextGrid" in helper_source
    assert "readonly property real gridContainerHeight" in helper_source

    for marker in (
        "\n    Column {",
        "\n    Timer {",
        "CalendarNavButton {",
        "Grid {",
        "Repeater {",
    ):
        assert marker not in source


def test_color_picker_keeps_content_and_popup_tree_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/ColorPicker/ColorPicker.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/ColorPicker/_internal/"
        "ColorPickerContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 220
    assert helper.exists()
    assert len(helper_source.splitlines()) < 350
    assert 'import "_internal" as ColorPickerInternal' in source
    assert "ColorPickerInternal.ColorPickerContent {" in source
    assert "required property var colorControl" in helper_source
    for alias in (
        "property alias circleLoader: circleLoader",
        "property alias popup: popup",
        "property alias paletteDialogLoader: paletteDialogLoader",
        "property alias dialogLoader: dialogLoader",
    ):
        assert alias in helper_source
    assert helper_source.count("parent: colorControl") == 6

    for marker in (
        "Loader {",
        "PopupWindowCore {",
        "ColorPickerTrigger {",
        "ColorPalette {",
        "ColorPickerDropdown {",
        "ColorPickerDialog {",
        "CustomButtonCore {",
        "Connections {",
    ):
        assert marker not in source


def test_filter_bar_core_keeps_visual_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/FilterBar/FilterBarCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/FilterBar/_internal/"
        "FilterBarContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 180
    assert helper.exists()
    assert len(helper_source.splitlines()) < 260
    assert 'import "_internal" as FilterBarInternal' in source
    assert "FilterBarInternal.FilterBarContent {" in source
    assert "required property var filterControl" in helper_source
    assert "property alias itemRepeater: itemRepeater" in helper_source
    assert "readonly property real contentWidth" in helper_source
    assert helper_source.count("parent: filterControl") == 2

    for marker in (
        "NeumorphicShadow {",
        "Repeater {",
        "MouseArea {",
        "Icon {",
        "Label {",
    ):
        assert marker not in source


def test_audio_waveform_keeps_visual_content_modularized():
    entry = _source("prismqml/PrismQML/controls/data/AudioWaveform.qml")
    helper = _source(
        "prismqml/PrismQML/controls/data/_internal/AudioWaveformContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 160
    assert helper.exists()
    assert len(helper_source.splitlines()) < 260
    assert 'import "_internal" as DataInternal' in source
    assert "DataInternal.AudioWaveformContent {" in source
    assert "required property var waveformControl" in helper_source
    assert "property alias waveformContainer: waveformContainer" in helper_source
    assert "property alias mouseArea: mouseArea" in helper_source
    assert helper_source.startswith(
        "// Copyright 2026 aki-riko\n"
        "// SPDX-License-Identifier: MIT\n"
        "// This file is part of PrismQML, licensed under MIT.\n\n"
        "import QtQuick\n"
        "import \"../../..\"\n"
        "import \"../../../effects\"\n\n"
        "// AudioWaveformContent"
    )
    assert "ShadowedRectangle {" in helper_source
    assert helper_source.count("parent: waveformControl") == 2

    for marker in (
        "ShadowedRectangle {",
        "Repeater {",
        "MouseArea {",
        "\n    Item {",
    ):
        assert marker not in source


def test_shortcut_editor_keeps_scrollable_content_modularized():
    entry = _source("prismqml/PrismQML/controls/inputs/ShortcutEditor.qml")
    helper = _source(
        "prismqml/PrismQML/controls/inputs/_internal/ShortcutEditorContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 230
    assert helper.exists()
    assert len(helper_source.splitlines()) < 150
    assert 'import "_internal" as InputInternal' in source
    assert "InputInternal.ShortcutEditorContent {" in source
    assert "required property var editorControl" in helper_source
    assert "required property var cancelButton" in helper_source
    assert "property alias contentRow: contentRow" in helper_source
    assert helper_source.startswith(
        "// Copyright 2026 aki-riko\n"
        "// SPDX-License-Identifier: MIT\n"
        "// This file is part of PrismQML, licensed under MIT.\n\n"
        "import QtQuick\n"
        "import \"../../..\"\n"
        "import \"../../buttons\"\n"
        "import \"../../data/Label\"\n\n"
        "// ShortcutEditorContent"
    )

    for marker in (
        "\n    Flickable {",
        "\n        Repeater {",
        "\n        Label {",
    ):
        assert marker not in source


def test_cycle_wheel_picker_keeps_scroll_buttons_modularized():
    entry = _source("prismqml/PrismQML/controls/inputs/CycleWheelPicker.qml")
    helper = _source(
        "prismqml/PrismQML/controls/inputs/_internal/"
        "CycleWheelPickerButtons.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 330
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert 'import "_internal" as InputInternal' in source
    assert "InputInternal.CycleWheelPickerButtons {" in source
    assert "required property var wheelControl" in helper_source
    assert "\nRectangle {\n" in helper_source
    assert helper_source.count("parent: wheelControl") == 1

    for marker in (
        "\n    Rectangle {",
        "\n        Icon {",
        "\n        MouseArea {",
    ):
        assert marker not in source


def test_segmented_control_keeps_delegate_visuals_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/SegmentedControl.qml")
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/SegmentedItem.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 230
    assert helper.exists()
    assert len(helper_source.splitlines()) < 130
    assert 'import "_internal" as NavigationInternal' in source
    assert "NavigationInternal.SegmentedItem {" in source
    assert "required property var segmentedControl" in helper_source
    assert "required property int index" in helper_source
    assert "required property var modelData" in helper_source
    assert "\nItem {\n" in helper_source
    assert "segmentedControl._scheduleSlideSync(false)" in helper_source
    assert "function _scheduleSlideSync(shouldAnimate)" in source
    assert "repeater.itemAt" in source

    violations = []
    for path, candidate in ((entry, source), (helper, helper_source)):
        violations.extend(
            violation
            for violation in scan_source_text(
                candidate, PurePosixPath(path.relative_to(ROOT).as_posix())
            )
            if violation.rule in {"QML008", "QML009"}
        )
    assert violations == []

    for marker in (
        "\n            Item {",
        "\n                Rectangle {",
        "\n                Row {",
        "\n                HoverHandler {",
        "\n                TapHandler {",
    ):
        assert marker not in source
