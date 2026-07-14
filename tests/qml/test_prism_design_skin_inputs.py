# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Light Prism Design input, state, surface, and feedback coverage."""

from test_prism_design_skin_support import rgb


def _verify_picker_and_filter(context):
    picker = context.build(b"""
import PrismQML
DateTimePicker {
}
""")
    assert picker.property("radius") == 10
    filter_bar = context.build(b"""
import PrismQML
FilterBarCore {
    items: ["All", "Open", "Closed"]
    currentIndex: 1
}
""")
    assert filter_bar.property("radius") == 10


def _verify_spin_box_and_calendar(context):
    spin_box = context.build(b"""
import PrismQML
SpinBoxCore {
    value: 3
    minimum: 0
    maximum: 10
}
""")
    assert spin_box.property("radius") == 10
    calendar_picker = context.build(b"""
import PrismQML
CalendarPicker {
}
""")
    assert calendar_picker.property("radius") == 10


def _build_text_and_chips(context):
    text_edit = context.build(b"""
import PrismQML
TextEdit {
    placeholderText: "Notes"
}
""")
    assert text_edit.property("radius") == 10
    context.build(b"""
import PrismQML
Chip {
    text: "Prism"
    checked: true
}
""")
    context.build(b"""
import PrismQML
PinInput {
    length: 4
}
""")


def _verify_unchecked_indicator(context):
    check_indicator = context.build(b"""
import PrismQML
CheckIndicator {
    checkState: 0
}
""")
    assert check_indicator.property("_indicatorRadius") == 10
    assert check_indicator.property("_indicatorBorderWidth") == 1
    assert rgb(check_indicator.property("_indicatorColor")) == (252, 254, 255)
    assert rgb(check_indicator.property("_indicatorBorderColor")) == (120, 173, 184)


def _verify_checked_indicator(context):
    checked_indicator = context.build(b"""
import PrismQML
CheckIndicator {
    checkState: 2
}
""")
    assert checked_indicator.property("_indicatorBorderWidth") == 1
    assert rgb(checked_indicator.property("_indicatorColor")) == (11, 127, 137)
    assert rgb(checked_indicator.property("_indicatorBorderColor")) == (7, 95, 104)
    assert rgb(checked_indicator.property("_checkIconColor")) == (255, 255, 255)


def _verify_radio_indicator(context):
    radio_indicator = context.load(
        "prismqml", "PrismQML", "controls", "inputs", "Toggle",
        "ToggleRadioIndicator.qml",
    )
    radio_indicator.setProperty("checked", True)
    assert radio_indicator.property("_indicatorBorderWidth") == 1
    assert rgb(radio_indicator.property("_indicatorColor")) == (11, 127, 137)
    assert rgb(radio_indicator.property("_borderColor")) == (7, 95, 104)
    assert rgb(radio_indicator.property("_innerDotColor")) == (255, 255, 255)


def _verify_switch_indicator(context):
    switch_indicator = context.load(
        "prismqml", "PrismQML", "controls", "inputs", "Toggle",
        "ToggleSwitchIndicator.qml",
    )
    assert switch_indicator.property("_trackBorderWidth") == 1
    assert rgb(switch_indicator.property("_trackColor")) == (252, 254, 255)
    assert rgb(switch_indicator.property("_trackBorderColor")) == (120, 173, 184)
    assert rgb(switch_indicator.property("_handleColor")) == (252, 254, 255)
    switch_indicator.setProperty("checked", True)
    assert rgb(switch_indicator.property("_trackColor")) == (11, 127, 137)
    assert rgb(switch_indicator.property("_trackBorderColor")) == (7, 95, 104)
    assert rgb(switch_indicator.property("_handleColor")) == (255, 255, 255)


def _verify_slider(context):
    slider = context.build(b"""
import PrismQML
Slider {
    width: 220
    value: 55
}
""")
    assert rgb(slider.property("handleColor")) == (252, 254, 255)
    assert rgb(slider.property("_trackColor")) == (221, 233, 237)
    assert rgb(slider.property("_progressColor")) == (11, 127, 137)
    assert slider.property("_handleBorderWidth") == 1
    assert rgb(slider.property("_handleBorderColor")) == (120, 173, 184)


def _verify_rating_and_drop_zone(context):
    rating = context.build(b"""
import PrismQML
Rating {
    value: 3
}
""")
    assert rgb(rating.property("_effectiveFillColor")) == (255, 220, 6)
    assert rgb(rating.property("_effectiveOutlineColor")) == (118, 138, 145)
    drop_zone = context.build(b"""
import PrismQML
DropZone {
    preferredWidth: 260
    preferredHeight: 140
}
""")
    assert drop_zone.property("radius") == 14


def _build_progress_states(context):
    context.build(b"""
import PrismQML
Progress {
    type: Enums.progress.type_bar_filled
    value: 45
    text: "45%"
}
""")
    context.build(b"""
import PrismQML
EmptyState {
    actionText: "Create"
}
""")
    context.build(b"""
import PrismQML
ResultState {
    state: "success"
    actionText: "Done"
}
""")


def _build_state_widget_and_offline(context):
    context.build(b"""
import PrismQML
StateWidget {
    stateType: Enums.state.type_result
    severity: "success"
    actionText: "OK"
}
""")
    context.build(b"""
import PrismQML
OfflineState {
    retryText: "Retry"
}
""")


def _build_expander_and_group(context):
    context.build(b"""
import PrismQML
Expander {
    title: "More"
    content: "Details"
    expanded: true
}
""")
    context.build(b"""
import PrismQML
GroupBox {
    title: "Options"
}
""")


def _build_command_bar_and_widget(context):
    context.build(b"""
import PrismQML
CommandBar {
    type: Enums.commandBar.type_view
    primaryCommands: [{ "text": "Open", "icon": "FolderOpen" }]
}
""")
    context.build(b"""
import PrismQML
Widget {
    preferredWidth: 220
    preferredHeight: 80
    toolTipText: "Prism tooltip"
}
""")


def _build_dialogs(context):
    context.build(b"""
import PrismQML
ProgressDialog {
    title: "Loading"
    content: "Please wait"
    progress: 45
}
""")
    context.build(b"""
import PrismQML
UpdateDialog {
    version: "1.2.3"
    currentVersion: "1.2.2"
    notes: "Prism skin update"
}
""")


def _build_desktop_notification(context):
    context.build(b"""
import PrismQML
DesktopNotification {
    title: "Prism"
    message: "Container feedback"
    severity: "success"
    duration: Enums.duration.persistent
}
""")


def _verify_skeleton(context):
    skeleton = context.build(b"""
import PrismQML
Skeleton {
    shape: Enums.skeleton.shape_rect
    width: 80
    height: 24
}
""")
    assert skeleton.property("_radius") == 10


def _verify_code_block(context):
    code_block = context.build(b"""
import PrismQML
CodeBlock {
    code: "print('prism')"
    language: "python"
}
""")
    assert code_block.property("_radius") == 14
    assert rgb(code_block.property("_blockBackground")) == (247, 252, 254)


def _verify_chat_bubble(context):
    chat_bubble = context.build(b"""
import PrismQML
ChatBubble {
    width: 420
    role: "assistant"
    content: "Hello Prism"
}
""")
    assert chat_bubble.property("_bubbleRadius") == 18
    assert chat_bubble.property("_bubbleTailRadius") == 10


def _build_color_controls(context):
    context.build(b"""
import PrismQML
ColorPicker {
    type: Enums.colorPicker.type_picker
}
""")
    context.build(b"""
import PrismQML
GradientSlider {
    width: 180
}
""")
    context.build(b"""
import PrismQML
ColorPickerDialog {
    title: "Pick"
}
""")


def _verify_login_window(context):
    login_window = context.build(b"""
import PrismQML
LoginWindow {
    width: 640
    height: 520
    matrixEnabled: false
    errorMessage: "Invalid credentials"
}
""")
    assert login_window.property("_cardRadius") == 24
    assert login_window.property("_errorRadius") == 10


def verify_light_inputs_and_surfaces(context):
    _verify_picker_and_filter(context)
    _verify_spin_box_and_calendar(context)
    _build_text_and_chips(context)
    _verify_unchecked_indicator(context)
    _verify_checked_indicator(context)
    _verify_radio_indicator(context)
    _verify_switch_indicator(context)
    _verify_slider(context)
    _verify_rating_and_drop_zone(context)
    _build_progress_states(context)
    _build_state_widget_and_offline(context)
    _build_expander_and_group(context)
    _build_command_bar_and_widget(context)
    _build_dialogs(context)
    _build_desktop_notification(context)
    _verify_skeleton(context)
    _verify_code_block(context)
    _verify_chat_bubble(context)
    _build_color_controls(context)
    _verify_login_window(context)
