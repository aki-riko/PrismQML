// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."
import "../../icons"
import "../../data/Label"

// Toggle - Unified toggle control 统一切换控件
// Control via controlType: checkbox/radio/switch 通过controlType控制控件类型
// Control via type: default/indicator/subtitle 通过type控制显示形态
Item {
    id: control

    // ==================== Translation Trigger 翻译触发器 ====================
    readonly property int _tv: Translator._v

    // ==================== Control Type 控件类型 ====================
    property int controlType: Enums.toggle.control_checkbox

    // ==================== Display Type 显示类型 ====================
    property int type: Enums.toggle.type_default

    // ==================== Content Props 内容属性 ====================
    property string text: ""
    property string subtitle: ""
    property string icon: ""
    property int iconSize: Enums.iconSize.m
    property bool checked: false

    // CheckBox specific CheckBox专用
    property bool tristate: false
    property int checkState: checked ? 2 : 0  // 0=Unchecked, 1=Partial, 2=Checked

    // ToggleSwitch specific ToggleSwitch专用
    property string textOn: { _tv; return Translator.tr("on") }
    property string textOff: { _tv; return Translator.tr("off") }

    // RadioButton specific RadioButton专用
    property bool autoExclusive: true

    // ==================== Custom Colors 自定义颜色 ====================
    property color checkedColorLight: Enums.accentColor
    property color checkedColorDark: Enums.accentColor
    property color textColorLight: Enums.isDark ? Enums.accentForeground : "black"
    property color textColorDark: Enums.accentForeground

    // ==================== Signals 信号 ====================
    signal toggled(bool checked)
    signal stateModified(int newState)
    signal checkedStateChanged(bool checked)

    // ==================== State 状态 ====================
    readonly property bool hovered: mouseArea.containsMouse
    readonly property bool pressed: mouseArea.pressed

    // ==================== Internal 内部属性 ====================
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

    // ==================== Size 尺寸 ====================
    implicitWidth: mainRow.implicitWidth
    implicitHeight: {
        if (_isSubtitle)
            return Math.max(Enums.controlSize.emptyStateButtonHeight, contentLoader.item ? contentLoader.item.implicitHeight + Enums.spacing.m : Enums.controlSize.emptyStateButtonHeight)
        if (_isSwitch) return Enums.controlSize.switchHeight
        if (_isRadio) return Enums.controlSize.radioOuter
        return Enums.controlSize.checkboxOuter
    }

    // Toggle checked state 切换选中状态
    function toggleChecked() {
        _handleClick()
    }

    // ==================== RadioButton Auto Exclusive 单选按钮自动互斥 ====================
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

    // ==================== Click Handler 点击处理 ====================
    function _handleClick() {
        if (_isRadio) {
            if (!checked) {
                _uncheckSiblings()
                checked = true
                toggled(checked)
            }
        } else if (_isCheckBox) {
            if (tristate) {
                checkState = (checkState + 1) % 3
                checked = checkState === 2
            } else {
                checked = !checked
                checkState = checked ? 2 : 0
            }
            toggled(checked)
            stateModified(checkState)
        } else {
            checked = !checked
            checkedStateChanged(checked)
            toggled(checked)
        }
    }

    // ==================== Public Methods 公共方法 ====================
    function getText() { return text }


    function isChecked() { return checked }


    function isEnabled() { return enabled }

    // ==================== Layout 布局 ====================
    Row {
        id: mainRow
        anchors.verticalCenter: parent.verticalCenter
        spacing: _isIndicatorOnly ? 0 : (_isSubtitle ? Enums.spacing.l : Enums.spacing.m)

        // Indicator 指示器
        Loader {
            id: indicatorLoader
            anchors.verticalCenter: _isSubtitle ? undefined : parent.verticalCenter
            anchors.top: _isSubtitle ? parent.top : undefined
            anchors.topMargin: _isSubtitle ? Enums.spacing.xxs : 0
            sourceComponent: {
                if (control._isSwitch) return switchIndicator
                if (control._isRadio) return radioIndicator
                return checkboxIndicator
            }
        }

        // Content 内容
        Loader {
            id: contentLoader
            anchors.verticalCenter: parent.verticalCenter
            active: !control._isIndicatorOnly && (control.text !== "" || control.subtitle !== "")
            sourceComponent: control._isSubtitle ? subtitleContent : defaultContent
        }
    }

    // ==================== CheckBox Indicator 复选框指示器 ====================
    Component {
        id: checkboxIndicator
        ToggleCheckIndicator {
            checkState: control.checkState
            enabled: control.enabled
            hovered: control.hovered
            pressed: control.pressed
            checkedColor: control._checkedColor
        }
    }

    // ==================== Radio Indicator 单选按钮指示器 ====================
    Component {
        id: radioIndicator
        ToggleRadioIndicator {
            checked: control.checked
            enabled: control.enabled
            hovered: control.hovered
            pressed: control.pressed
        }
    }

    // ==================== Switch Indicator 开关指示器 ====================
    Component {
        id: switchIndicator
        ToggleSwitchIndicator {
            checked: control.checked
            enabled: control.enabled
            checkedColor: control._checkedColor
            onClicked: control._handleClick()
        }
    }

    // ==================== Default Content 默认内容 ====================
    Component {
        id: defaultContent
        ToggleDefaultContent {
            text: control.text
            icon: control.icon
            iconSize: control.iconSize
            textColor: control._textColor
            showIcon: control._isCheckBox
        }
    }

    // ==================== Subtitle Content 副标题内容 ====================
    Component {
        id: subtitleContent
        ToggleSubtitleContent {
            text: control.text
            subtitle: control.subtitle
            textColor: control._textColor
        }
    }


    // ==================== Interaction 交互 ====================
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        enabled: control.enabled && !control._isSwitch
        hoverEnabled: true
        onClicked: control._handleClick()
    }
}
