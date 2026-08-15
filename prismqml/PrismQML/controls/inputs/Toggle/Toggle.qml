// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."
import "_internal" as ToggleInternal

// Toggle - Unified toggle control 统一切换控件
// Control via controlType: checkbox/radio/switch 通过controlType控制控件类型
// Control via type: default/indicator/subtitle 通过type控制显示形态
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property int controlType: Enums.toggle.control_checkbox
    property int type: Enums.toggle.type_default
    property string text: ""
    property string subtitle: ""
    property string icon: ""
    property int iconSize: Enums.iconSize.m
    property bool checked: false

    // CheckBox specific CheckBox专用
    property bool tristate: false
    property int checkState: checked ? Enums.toggle.state_checked : Enums.toggle.state_unchecked

    // ToggleSwitch specific ToggleSwitch专用
    property string textOn: { _tv; return Translator.tr("on") }
    property string textOff: { _tv; return Translator.tr("off") }

    // RadioButton specific RadioButton专用
    property bool autoExclusive: true

    // Custom colors 自定义颜色
    property color checkedColorLight: Enums.accentColor
    property color checkedColorDark: Enums.accentColor
    property color textColorLight: Enums.isVintageTicket ? Enums.foregroundColor
        : (Enums.isDark ? Enums.accentForeground : Enums.grayColors.textPrimaryLight)
    property color textColorDark: Enums.isVintageTicket ? Enums.foregroundColor
        : Enums.accentForeground

    // ==================== Internal Props 内部属性 ====================
    property bool _syncingCheckState: false

    // ==================== Readonly State 只读状态 ====================
    readonly property int _tv: Translator._v
    readonly property bool hovered: mouseArea.containsMouse
    readonly property bool pressed: mouseArea.pressed
    readonly property bool _isCheckBox: controlType === Enums.toggle.control_checkbox
    readonly property bool _isRadio: controlType === Enums.toggle.control_radio
    readonly property bool _isSwitch: controlType === Enums.toggle.control_switch
    readonly property bool _isIndicatorOnly: type === Enums.toggle.type_indicator
    readonly property bool _isSubtitle: type === Enums.toggle.type_subtitle

    readonly property color _checkedColor: Enums.isDark ? checkedColorDark : checkedColorLight
    readonly property color _textColor: {
        if (!enabled) return Enums.textColor.disabled
        return Enums.isDark ? textColorDark : textColorLight
    }

    // ==================== Signals 信号 ====================
    signal toggled(bool checked)
    signal stateModified(int newState)
    signal checkedStateChanged(bool checked)

    // ==================== Public Methods 公开方法 ====================
    // Toggle checked state 切换选中状态
    function toggleChecked() {
        _handleClick()
    }

    function getText() { return text }

    function isChecked() { return checked }

    function isEnabled() { return enabled }

    // ==================== Internal Methods 内部方法 ====================
    function _findRadioButtons(item, result) {
        if (!item) return
        for (var i = 0; i < item.children.length; i++) {
            var child = item.children[i]
            if (child !== control &&
                child.hasOwnProperty("checked") &&
                child.hasOwnProperty("autoExclusive") &&
                child.hasOwnProperty("controlType") &&
                child.controlType === Enums.toggle.control_radio &&
                child.autoExclusive) {
                result.push(child)
            }
            control._findRadioButtons(child, result)
        }
    }

    function _findRadioGroup() {
        var current = control.parent
        var maxDepth = 5
        var depth = 0
        while (current && depth < maxDepth) {
            var radios = []
            control._findRadioButtons(current, radios)
            if (radios.length > 0) return radios
            current = current.parent
            depth++
        }
        return []
    }

    function _uncheckSiblings() {
        if (!autoExclusive || !_isRadio) return
        var siblings = control._findRadioGroup()
        for (var i = 0; i < siblings.length; i++) {
            if (siblings[i].checked) siblings[i].checked = false
        }
    }

    // Click handler 点击处理
    function _handleClick() {
        if (_isRadio) {
            if (!checked) {
                _uncheckSiblings()
                checked = true
                toggled(checked)
            }
        } else if (_isCheckBox) {
            if (tristate) {
                checkState = checkState === Enums.toggle.state_unchecked
                    ? Enums.toggle.state_partially_checked
                    : (checkState === Enums.toggle.state_partially_checked
                       ? Enums.toggle.state_checked
                       : Enums.toggle.state_unchecked)
            } else {
                checkState = checked
                    ? Enums.toggle.state_unchecked
                    : Enums.toggle.state_checked
            }
            toggled(checked)
            stateModified(checkState)
        } else {
            checked = !checked
            checkedStateChanged(checked)
            toggled(checked)
        }
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: toggleContent.implicitWidth
    implicitHeight: {
        if (_isSubtitle)
            return Math.max(
                Enums.controlSize.emptyStateButtonHeight,
                toggleContent.contentLoaded
                    ? toggleContent.contentImplicitHeight + Enums.spacing.m
                    : Enums.controlSize.emptyStateButtonHeight
            )
        if (_isSwitch) return Enums.controlSize.switchHeight
        if (_isRadio) return Enums.controlSize.radioOuter
        return Enums.controlSize.checkboxOuter
    }

    onCheckedChanged: {
        if (_syncingCheckState) return
        _syncingCheckState = true
        checkState = checked ? Enums.toggle.state_checked : Enums.toggle.state_unchecked
        _syncingCheckState = false
    }

    onCheckStateChanged: {
        if (_syncingCheckState) return
        _syncingCheckState = true
        checked = checkState === Enums.toggle.state_checked
        _syncingCheckState = false
    }

    // ==================== Content 内容 ====================
    ToggleInternal.ToggleContent {
        id: toggleContent
        toggleControl: control
    }


    // Interaction 交互
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        enabled: control.enabled && !control._isSwitch
        hoverEnabled: true
        onClicked: control._handleClick()
    }
}
