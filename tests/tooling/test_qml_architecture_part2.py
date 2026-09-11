# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Domain bucket 2/7 of the former test_qml_architecture.py."""
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
        (
            "prismqml/PrismQML/controls/buttons/Button/_internal/"
            "ButtonSurface.qml",
            "ButtonSurface",
        ),
        (
            "prismqml/PrismQML/controls/buttons/Button/_internal/"
            "ButtonContentLayer.qml",
            "ButtonContentLayer",
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

def test_button_countdown_keeps_timer_component_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/buttons/Button/_internal/ButtonCountdown.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/buttons/Button/_internal/"
        "ButtonCountdownTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 80
    assert helper.exists()
    assert len(helper_source.splitlines()) < 80
    assert "Loader {" in source
    assert "sourceComponent: ButtonCountdownTimer {" in source
    assert "button: countdownLoader.button" in source
    assert "sourceComponent: Timer {" not in source
    assert "\n    Timer {" not in source
    assert helper_source.count("Timer {") == 1
    assert "\nTimer {" in helper_source
    assert "required property var button" in helper_source
    assert "interval: Enums.duration.countUp" in helper_source
    assert "repeat: true" in helper_source
    assert "running: button._countdownActive" in helper_source
    assert "button.countdownFinished()" in helper_source
    assert "countdownLoader" not in helper_source

def test_button_core_keeps_surface_visuals_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/buttons/Button/ButtonCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/buttons/Button/_internal/ButtonSurface.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 430
    assert helper.exists()
    assert len(helper_source.splitlines()) < 180
    assert 'import "_internal" as ButtonInternal' in source
    assert "ButtonInternal.ButtonSurface {" in source
    assert "required property var buttonControl" in helper_source
    for alias in (
        "background",
        "border",
        "bgColorAnimation",
        "borderColorAnimation",
    ):
        assert f"property alias {alias}:" in helper_source
    assert "readonly property real animatedPressShift:" in helper_source
    assert "readonly property var pressTransform:" in helper_source
    assert "RectangularShadow {" in helper_source
    assert "NeumorphicShadow {" in helper_source
    assert "sourceComponent: ButtonNeoShadow" in helper_source
    assert "ColorAnimation {" in helper_source
    assert "RectangularShadow {" not in source
    assert "NeumorphicShadow {" not in source
    assert "sourceComponent: ButtonNeoShadow" not in source
    assert "ColorAnimation {" not in source

def test_button_core_keeps_content_layer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/buttons/Button/ButtonCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/buttons/Button/_internal/ButtonContentLayer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 370
    assert helper.exists()
    assert len(helper_source.splitlines()) < 150
    assert "ButtonInternal.ButtonContentLayer {" in source
    assert "required property var buttonControl" in helper_source
    assert "required property var pressTransform" in helper_source
    assert "default property alias contentData: customContentContainer.data" in helper_source
    assert "property alias customContentContainer: customContentContainer" in helper_source
    assert "property alias contentLoader: contentLoader" in helper_source
    assert "ButtonContent {" in helper_source
    assert "Item {\n        id: customContentContainer" not in source
    assert "Loader {\n        id: contentLoader" not in source
    assert "ButtonContent {" not in source

def test_button_dropdown_keeps_surface_visuals_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/buttons/Button/ButtonDropdown.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/buttons/Button/_internal/"
        "ButtonDropdownSurface.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 350
    assert helper.exists()
    assert len(helper_source.splitlines()) < 160
    assert 'import "_internal" as ButtonInternal' in source
    assert "ButtonInternal.ButtonDropdownSurface {" in source
    assert "required property var dropdownControl" in helper_source
    for state in ("mainHovered", "mainPressed", "dropHovered", "dropPressed"):
        assert f"readonly property bool {state}:" in helper_source
        assert f"dropdownSurface.{state}" in source
    for marker in (
        "id: splitMainArea",
        "id: splitDropArea",
        "id: splitMainMouse",
        "id: splitDropMouse",
        "id: menuArrow",
    ):
        assert marker not in source

def test_button_dropdown_keeps_geometry_prewarm_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/buttons/Button/ButtonDropdown.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/buttons/Button/_internal/"
        "ButtonDropdownPrewarmTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 350
    assert helper.exists()
    assert len(helper_source.splitlines()) < 80
    assert helper_source.count("Timer {") == 1
    assert "\nTimer {" in helper_source
    assert "required property var dropdownControl" in helper_source
    assert "interval: 0" in helper_source
    assert "onTriggered: dropdownControl._prewarmMenuGeometry()" in helper_source
    assert "ButtonInternal.ButtonDropdownPrewarmTimer {" in source
    assert "id: geometryPrewarmTimer" in source
    assert "dropdownControl: dropdownFeature" in source
    assert "\n    Timer {" not in source
    assert "onTriggered: dropdownFeature._prewarmMenuGeometry()" not in source

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

def test_popup_window_core_keeps_lifecycle_timers_modularized():
    entry = _source("prismqml/PrismQML/controls/utils/PopupWindowCore.qml")
    prewarm = _source(
        "prismqml/PrismQML/controls/utils/_internal/PopupPrewarmTimer.qml"
    )
    lifecycle = _source(
        "prismqml/PrismQML/controls/utils/_internal/PopupLifecycleTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    prewarm_source = prewarm.read_text(encoding="utf-8")
    lifecycle_source = lifecycle.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    for helper in (prewarm, lifecycle):
        assert helper.exists()
        assert len(helper.read_text(encoding="utf-8").splitlines()) < 80
    assert "PopupPrewarmTimer {" in source
    assert "PopupLifecycleTimer {" in source
    assert "id: prewarmTimer" in source
    assert "id: lifecycleTimer" in source
    assert "host: control" in source
    assert "readonly property alias _lifecycleTimer: lifecycleTimer" in source
    assert "required property var host" in prewarm_source
    assert "required property var host" in lifecycle_source
    assert "interval: 0" in prewarm_source
    assert "host._doPrewarm()" in prewarm_source
    assert "Enums.popupMetrics.showAnimDelayMs" in lifecycle_source
    assert "PopupLifecycle.onTimer(host)" in lifecycle_source
    assert "\n    Timer {" not in source

def test_popup_position_tracker_keeps_update_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/utils/_internal/PopupPositionTracker.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/utils/_internal/PopupPositionUpdateTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 140
    assert helper.exists()
    assert len(helper_source.splitlines()) < 60
    assert 'import "." as PopupInternal' in source
    assert "PopupInternal.PopupPositionUpdateTimer {" in source
    assert "id: updateTimer" in source
    assert "host: tracker" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "popupPositionUpdateTimer"' in helper_source
    assert "interval: 0" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: host._updatePosition()" in helper_source
    assert "onTriggered: tracker._updatePosition()" not in source

def test_viewport_culling_keeps_evaluation_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/utils/ViewportCulling.qml")
    helper = _source(
        "prismqml/PrismQML/controls/utils/_internal/"
        "ViewportCullingEvaluationTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 120
    assert helper.exists()
    assert len(helper_source.splitlines()) < 60
    assert 'import "_internal" as UtilsInternal' in source
    assert "UtilsInternal.ViewportCullingEvaluationTimer {" in source
    assert "id: evaluationTimer" in source
    assert "host: root" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "viewportCullingTimer"' in helper_source
    assert "interval: 150" in helper_source
    assert "running: host._flickable !== null && host._hostWindowExposed" in helper_source
    assert "repeat: true" in helper_source
    assert "triggeredOnStart: true" in helper_source
    assert "onTriggered: host._updateVisibility()" in helper_source
    assert "onTriggered: root._updateVisibility()" not in source

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

def test_stacked_widget_keeps_direct_pages_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/navigation/StackedWidget.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/StackedDirectPages.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 480
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert "StackedDirectPages {" in source
    assert "property Item containerItem: directPages" in source
    assert "required property Item host" in helper_source
    assert 'objectName: "stackLayout"' in helper_source
    assert "host._displayIndex" in helper_source
    assert "child.width = Qt.binding" in helper_source
    assert "child.height = Qt.binding" in helper_source
    for marker in (
        "\n        id: stackLayout\n",
        "stackLayout.children",
        "child.width = Qt.binding",
        "child.height = Qt.binding",
    ):
        assert marker not in source

def test_stacked_widget_keeps_lazy_helper_loader_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/navigation/StackedWidget.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/"
        "StackedLazyHelperLoader.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 470
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert "StackedLazyHelperLoader {" in source
    assert helper_source.startswith("// Copyright 2026 aki-riko")
    assert "Loader {" in helper_source
    assert "required property Item host" in helper_source
    assert "host._asynchronousPageLoaderEnabled" in helper_source
    assert "host._configureLazyHelper(item)" in helper_source
    assert "host._flushPendingLazySwitch()" in helper_source
    for handler in ("onActiveChanged:", "onStatusChanged:", "onLoaded:"):
        assert helper_source.count(handler) == 1
        assert handler not in source
    assert "id: lazyHelperLoader" in source
    assert "host: control" in source
    assert "lazyHelperLoader.setSource(Qt.resolvedUrl" in source
    assert "lazyHelperLoader: lazyHelperLoader" in source
    assert "StackedLazyHelperLoader {\n        id: lazyHelperLoader\n        host: control\n" in source

def test_tab_widget_keeps_content_pages_modularized():
    _assert_modularized(
        "prismqml/PrismQML/controls/navigation/TabWidget.qml",
        "prismqml/PrismQML/controls/navigation/_internal/TabContentPages.qml",
        "TabContentPages",
    )

def test_tab_widget_keeps_tab_delegate_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/TabWidget.qml")
    tab_bar = _source("prismqml/PrismQML/controls/navigation/TabBar.qml")
    helper = _source("prismqml/PrismQML/controls/navigation/_internal/TabItem.qml")

    assert len(entry.read_text(encoding="utf-8").splitlines()) < 500
    tab_bar_source = tab_bar.read_text(encoding="utf-8")
    assert tab_bar.exists()
    assert len(tab_bar_source.splitlines()) < 500
    assert helper.exists()
    assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
    assert "TabBar {" in entry.read_text(encoding="utf-8")
    assert "TabItem {" in tab_bar_source

def test_tab_widget_keeps_edge_auto_scroll_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/TabWidget.qml")
    tab_bar = _source("prismqml/PrismQML/controls/navigation/TabBar.qml")
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/TabEdgeAutoScroll.qml"
    )
    source = entry.read_text(encoding="utf-8")
    tab_bar_source = tab_bar.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 450
    assert tab_bar.exists()
    assert len(tab_bar_source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert "TabEdgeAutoScroll {" in tab_bar_source
    assert "FrameAnimation {" in helper_source
    assert "required property Item host" in helper_source
    assert "required property Flickable tabFlickable" in helper_source
    assert "host._dragging" in helper_source
    assert "host._dragPointerRowX" in helper_source
    assert "frameTime" in helper_source
    assert "onTriggered:" in helper_source
    assert "var edgeMargin = 40" not in tab_bar_source
    assert "var step = 480 * frameTime" not in tab_bar_source
    assert "id: _edgeAutoScrollTimer" in tab_bar_source
    assert "host: control" in tab_bar_source
    assert "tabFlickable: tabFlickable" in tab_bar_source

def test_tab_widget_keeps_indicator_modularized():
    entry = _source("prismqml/PrismQML/controls/navigation/TabWidget.qml")
    tab_bar = _source("prismqml/PrismQML/controls/navigation/TabBar.qml")
    helper = _source(
        "prismqml/PrismQML/controls/navigation/_internal/TabIndicator.qml"
    )
    source = entry.read_text(encoding="utf-8")
    tab_bar_source = tab_bar.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 300
    assert tab_bar.exists()
    assert len(tab_bar_source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 250
    assert "TabIndicator {" in tab_bar_source
    assert "Item {" in helper_source
    for required_property in (
        "required property Item host",
        "required property Item tabBar",
        "required property Flickable tabFlickable",
        "required property var tabRepeater",
        "required property Item tabRow",
    ):
        assert required_property in helper_source
    for binding in (
        "host: control",
        "tabBar: tabBarBg",
        "tabFlickable: tabFlickable",
        "tabRepeater: tabRepeater",
        "tabRow: tabRow",
    ):
        assert binding in tab_bar_source
    assert "function _scheduleSync(animate)" in helper_source
    assert "function syncIndicator(animate)" in helper_source
    assert "SlidingIndicatorAnimation {" in helper_source
    assert "RectangularShadow {" in helper_source
    assert "NeumorphicShadow {" in helper_source
    assert "NeoShadow {" in helper_source
    assert "id: slidingIndicator" in tab_bar_source
    for marker in (
        "property int _currentTabKey:",
        "function _scheduleSync(animate)",
        "SlidingIndicatorAnimation {",
        "id: indicatorBg",
    ):
        assert marker not in tab_bar_source

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

def test_notification_manager_keeps_overlay_lifecycle_internal():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Notification/NotificationManager.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Notification/_internal/NotificationOverlayLifecycle.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 430
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert "NotificationOverlayLifecycle {" in source
    assert "required property var stackManager" in helper_source
    for marker in (
        "overlayComponent.createObject(null",
        "notification.closed.connect(function() { overlay.hide() })",
        "notification.destroy()",
        "stackManager.addToDesktopStack(overlay, position)",
        "stackManager.addToOutsideStack(overlay, position)",
    ):
        assert marker in helper_source
        assert marker not in source

def test_notification_manager_keeps_item_lifecycle_internal():
    entry = _source(
        "prismqml/PrismQML/controls/feedback/Notification/NotificationManager.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/feedback/Notification/_internal/NotificationItemLifecycle.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 410
    assert helper.exists()
    assert len(helper_source.splitlines()) < 80
    assert "NotificationItemLifecycle {" in source
    assert "required property var stackManager" in helper_source
    for marker in (
        "component.createObject(parentItem, properties)",
        "stackManager.addToStack(item, position)",
        "stackManager.setPosition(item, parentItem, position)",
        "stackManager.removeFromStack(item, position)",
        "item.destroy()",
    ):
        assert marker in helper_source
        assert marker not in source

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
