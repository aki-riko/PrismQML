# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Domain bucket 5/7 of the former test_qml_architecture.py."""
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

def test_viewport_mixin_keeps_init_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/utils/ViewportMixin.qml")
    helper = _source(
        "prismqml/PrismQML/controls/utils/_internal/ViewportInitTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 110
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert helper_source.count("Timer {") == 1
    assert "\nTimer {" in helper_source
    assert 'import "_internal" as UtilsInternal' in source
    assert "property Timer initTimer:" in source
    assert "UtilsInternal.ViewportInitTimer {" in source
    assert "host: mixin" in source
    assert "required property var host" in helper_source
    assert 'objectName: "viewportInitTimer"' in helper_source
    assert "interval: 50" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: host._init()" in helper_source
    assert "property Timer initTimer: Timer {" not in source
    assert "onTriggered: _init()" not in source

    # onCompleted must initialize synchronously AND arm the settle re-check.
    # Deferring to the timer alone let consumers read a stale default first.
    # onCompleted 必须同步初始化并同时挂上稳定后复算；只靠定时器会让消费者先读到过期默认值。
    assert "Component.onCompleted: {" in source
    assert "_init()" in source
    assert "initTimer.start()" in source

    # Ancestor and contentItem wiring must stay declarative so a destroyed
    # consumer leaves no stale callback. 祖先与 contentItem 连接必须保持声明式。
    assert "UtilsInternal.ViewportAncestorWatcher {" in source
    assert "UtilsInternal.ViewportContentWatcher {" in source
    assert ".contentYChanged.connect(" not in source
    assert ".heightChanged.connect(" not in source

def test_widget_keeps_center_children_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/containers/Widget.qml")
    helper = _source(
        "prismqml/PrismQML/controls/containers/_internal/"
        "WidgetCenterChildrenTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 160
    assert helper.exists()
    assert len(helper_source.splitlines()) < 40
    assert helper_source.count("Timer {") == 1
    assert "\nTimer {" in helper_source
    assert 'import "_internal" as ContainerInternal' in source
    assert "readonly property Loader _centerChildrenDelayed: Loader" in source
    assert "active: widget.centerContent" in source
    assert "onLoaded: widget._scheduleCenterChildren()" in source
    assert "sourceComponent: ContainerInternal.WidgetCenterChildrenTimer {" in source
    assert "host: widget" in source
    assert "required property Item host" in helper_source
    assert 'objectName: "widgetCenterChildrenTimer"' in helper_source
    assert "interval: Enums.duration.tick" in helper_source
    assert "repeat: false" in helper_source
    assert "for (var i = 0; i < host.children.length; i++)" in helper_source
    assert "if (host._isCenterableChild(child))" in helper_source
    assert "child.anchors.centerIn = host" in helper_source
    assert "sourceComponent: Timer {" not in source
    assert "for (var i = 0; i < widget.children.length; i++)" not in source

def test_menu_core_keeps_visual_content_modularized():
    entry = _source("prismqml/PrismQML/controls/menus/MenuCore.qml")
    helper = _source("prismqml/PrismQML/controls/menus/_internal/MenuContent.qml")

    assert len(entry.read_text(encoding="utf-8").splitlines()) < 500
    assert helper.exists()
    assert len(helper.read_text(encoding="utf-8").splitlines()) < 500
    assert "MenuContent {" in entry.read_text(encoding="utf-8")

def test_menu_core_keeps_logical_item_registry_modularized():
    entry = _source("prismqml/PrismQML/controls/menus/MenuCore.qml")
    helper = _source(
        "prismqml/PrismQML/controls/menus/_internal/MenuItemRegistry.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 410
    assert helper.exists()
    assert len(helper_source.splitlines()) < 80
    assert "MenuItemRegistry {" in source
    for marker in ("property var items: []", "function liveItems()",
                   "function measuredWidth(", "function measuredHeight()"):
        assert marker in helper_source
        assert marker not in source

def test_menu_core_keeps_submenu_open_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/menus/MenuCore.qml")
    helper = _source(
        "prismqml/PrismQML/controls/menus/_internal/MenuSubmenuOpenTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 500
    assert helper.exists()
    assert len(helper_source.splitlines()) < 80
    assert helper_source.count("Timer {") == 1
    assert "\nTimer {" in helper_source
    assert "required property var host" in helper_source
    assert "interval: Enums.duration.fast" in helper_source
    assert "repeat: false" in helper_source
    assert (
        "host._pendingSubmenuAction.hovered" in helper_source
    )
    assert "host._openSubmenuForAction(" in helper_source
    assert "MenuSubmenuOpenTimer {" in source
    assert "id: submenuOpenTimer" in source
    assert "host: control" in source
    assert "\n Timer {" not in source
    assert "interval: Enums.duration.fast" not in source
    assert "_pendingSubmenuAction && _pendingSubmenuAction.hovered" not in source

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

def test_date_time_picker_keeps_display_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/Picker/DateTimePicker.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/Picker/_internal/"
        "DateTimePickerDisplay.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 380
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert 'import "./_internal" as PickerInternal' in source
    assert "PickerInternal.DateTimePickerDisplay {" in source
    assert "required property var pickerControl" in helper_source
    assert "Repeater {" in helper_source
    assert "parent ? parent.width /" in helper_source
    assert "parent ? parent.height : 0" in helper_source
    assert "Row {" not in source
    assert "Repeater {" not in source

def test_date_time_picker_keeps_init_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/Picker/DateTimePicker.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/inputs/Picker/_internal/"
        "DateTimePickerInitTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 376
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "./_internal" as PickerInternal' in source
    assert "PickerInternal.DateTimePickerInitTimer {" in source
    assert "id: initTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "dateTimePickerInitTimer"' in helper_source
    assert "interval: 50" in helper_source
    assert "repeat: false" in helper_source
    assert "onTriggered: host._initWheelPositions()" in helper_source
    assert "control._initWheelPositions()" not in source

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

def test_cycle_wheel_picker_keeps_delegates_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/inputs/CycleWheelPicker.qml"
    )
    path_delegate = _source(
        "prismqml/PrismQML/controls/inputs/_internal/"
        "CycleWheelPickerPathDelegate.qml"
    )
    list_delegate = _source(
        "prismqml/PrismQML/controls/inputs/_internal/"
        "CycleWheelPickerListDelegate.qml"
    )
    source = entry.read_text(encoding="utf-8")
    path_source = path_delegate.read_text(encoding="utf-8")
    list_source = list_delegate.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 270
    assert path_delegate.exists()
    assert list_delegate.exists()
    assert len(path_source.splitlines()) < 100
    assert len(list_source.splitlines()) < 110
    assert 'import "_internal" as InputInternal' in source
    assert "InputInternal.CycleWheelPickerPathDelegate {" in source
    assert "InputInternal.CycleWheelPickerListDelegate {" in source
    for helper_source in (path_source, list_source):
        assert "required property var wheelControl" in helper_source
        assert "required property var modelData" in helper_source
        assert "wheelControl._distanceFromCenter" in helper_source
    assert "required property int index" in list_source
    assert "ListView.view.currentIndex" in list_source
    assert "PathView.isCurrentItem" in path_source

    for marker in (
        "\n        delegate: Item {",
        "property real distanceFromCenter:",
        "text: String(modelData)",
    ):
        assert marker not in source

def test_cycle_wheel_picker_keeps_repeat_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/inputs/CycleWheelPicker.qml")
    helper = _source(
        "prismqml/PrismQML/controls/inputs/_internal/"
        "CycleWheelPickerRepeatTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 255
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert 'import "_internal" as InputInternal' in source
    assert "InputInternal.CycleWheelPickerRepeatTimer {" in source
    assert "id: repeatTimer" in source
    assert "wheelControl: control" in source
    assert "\n    Timer {" not in source
    assert "required property var wheelControl" in helper_source
    assert 'objectName: "cycleWheelPickerRepeatTimer"' in helper_source
    assert "interval: wheelControl._repeatStarted" in helper_source
    assert "Enums.duration.wheelPickerRepeatInterval" in helper_source
    assert "Enums.duration.wheelPickerRepeatDelay" in helper_source
    assert "repeat: true" in helper_source
    assert "onTriggered: wheelControl._triggerRepeat()" in helper_source

def test_pips_pager_keeps_navigation_button_visuals_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/FlipView/PipsPagerCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/FlipView/_internal/"
        "PipsPagerNavButton.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 230
    assert helper.exists()
    assert len(helper_source.splitlines()) < 100
    assert 'import "_internal" as FlipViewInternal' in source
    assert "FlipViewInternal.PipsPagerNavButton {" in source
    assert "required property var pagerControl" in helper_source
    assert "required property bool isNext" in helper_source
    assert "pagerControl.next()" in helper_source
    assert "pagerControl.previous()" in helper_source
    assert "navButtonComponent.createObject(control" in source
    assert "ButtonCore {" not in source

def test_pips_pager_keeps_pips_content_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/FlipView/PipsPagerCore.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/FlipView/_internal/"
        "PipsPagerContent.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 150
    assert helper.exists()
    assert len(helper_source.splitlines()) < 150
    assert 'import "_internal" as FlipViewInternal' in source
    assert "FlipViewInternal.PipsPagerContent {" in source
    assert "required property var pagerControl" in helper_source
    assert "Repeater {" in helper_source
    assert "Behavior on _animatedScrollOffset" in helper_source
    assert "Item {\n        id: pipsContainer" not in source
    assert "Repeater {" not in source
    assert "property real _scrollOffset" not in source

def test_carousel_keeps_dynamic_factories_modularized():
    entry = _source("prismqml/PrismQML/controls/data/Carousel/Carousel.qml")
    helper = _source(
        "prismqml/PrismQML/controls/data/Carousel/_internal/"
        "CarouselFactories.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 320
    assert helper.exists()
    assert len(helper_source.splitlines()) < 180
    assert 'import "_internal" as CarouselInternal' in source
    assert "CarouselInternal.CarouselFactories {" in source
    assert "required property var carouselControl" in helper_source
    for component_name in (
        "contentAreaComponent",
        "indicatorComponent",
        "navButtonComponent",
    ):
        assert f"property alias {component_name}:" in helper_source
        assert f"carouselFactories.{component_name}.createObject(control" in source
    for marker in (
        "CarouselContent {",
        "FlipViewControls.PipsPager {",
        "CarouselNavButton {",
    ):
        assert marker not in source

def test_carousel_keeps_auto_play_timer_modularized():
    entry = _source(
        "prismqml/PrismQML/controls/data/Carousel/Carousel.qml"
    )
    helper = _source(
        "prismqml/PrismQML/controls/data/Carousel/_internal/"
        "CarouselAutoPlayTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 300
    assert helper.exists()
    assert len(helper_source.splitlines()) < 25
    assert "CarouselInternal.CarouselAutoPlayTimer {" in source
    assert "id: autoPlayTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "carouselAutoPlayTimer"' in helper_source
    assert "running: host.autoPlay && host._modelCount > 1" in helper_source
    assert "host.pauseOnHover && host._isHovered" in helper_source
    assert "repeat: true" in helper_source
    assert "interval: host.interval" in helper_source
    assert "onTriggered: host.next()" in helper_source

def test_confirm_dialog_keeps_countdown_timer_modularized():
    entry = _source("prismqml/PrismQML/controls/dialogs/ConfirmDialog.qml")
    helper = _source(
        "prismqml/PrismQML/controls/dialogs/_internal/"
        "ConfirmDialogCountdownTimer.qml"
    )
    source = entry.read_text(encoding="utf-8")
    helper_source = helper.read_text(encoding="utf-8")

    assert len(source.splitlines()) < 220
    assert helper.exists()
    assert len(helper_source.splitlines()) < 30
    assert 'import "_internal" as DialogInternal' in source
    assert "DialogInternal.ConfirmDialogCountdownTimer {" in source
    assert "id: countdownTimer" in source
    assert "host: control" in source
    assert "\n    Timer {" not in source
    assert "required property var host" in helper_source
    assert 'objectName: "confirmDialogCountdownTimer"' in helper_source
    assert "interval: 1000" in helper_source
    assert "repeat: true" in helper_source
    assert "host._countdownRemaining--" in helper_source
    assert "if (host._countdownRemaining === 0) running = false" in helper_source
