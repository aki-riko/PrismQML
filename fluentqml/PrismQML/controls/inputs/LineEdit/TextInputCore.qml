// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."
import "../../icons"
import "../../buttons"
import "../../data"
import "../_internal"

// TextInputCore - Text input base class (extends InputCore) 文本输入框基类
// LineEdit extends this, supports Normal/Password/Search via inputType 支持普通/密码/搜索
InputCore {
    id: control
    focusTarget: textInput
    
    // ==================== Input Type 输入类型 ====================
    property int inputType: Enums.input.type_normal  // Normal/Password/Search
    
    // ==================== Public Props 公开属性 ====================
    property alias text: textInput.text
    property string placeholderText: ""
    property bool readOnly: false
    property int echoMode: inputType === Enums.input.type_password ? TextInput.Password : TextInput.Normal
    property int maximumLength: 32767
    property bool clearButtonEnabled: true
    property bool showPassword: false  // Show/hide in password mode 密码模式显示/隐藏
    
    // ==================== Search Signals 搜索信号 ====================
    signal searched(string text)
    signal cleared()
    
    // ==================== Collapsible Search 可折叠搜索框 ====================
    property bool collapsible: false  // Collapsible (search mode only) 是否可折叠
    property bool expanded: !collapsible || textInput.activeFocus || textInput.text.length > 0  // Expanded state 展开状态
    property int collapsedWidth: Enums.controlSize.inputHeightLarge - 4  // Collapsed width 折叠宽度
    property int expandedWidth: Enums.controlSize.listDefaultWidth  // Expanded width 展开宽度
    
    // ==================== Signals 信号 ====================
    signal textEdited(string text)
    signal accepted()
    signal editingFinished()
    
    // ==================== Bind InputCore State 绑定InputCore状态 ====================
    focused: textInput.activeFocus
    hovered: hoverHandler.hovered
    property alias textInput: textInput
    
    // ==================== Size 尺寸 ====================
    implicitWidth: (_isSearch && collapsible) ? (expanded ? expandedWidth : collapsedWidth) : 200
    implicitHeight: Enums.controlSize.inputHeight + 1
    radius: (_isSearch && collapsible && !expanded) ? height / 2 : Enums.radius.small + 1
    
    // Collapsed: transparent bg, no border 折叠状态下背景透明
    transparentBackground: _isSearch && collapsible && !expanded
    border.width: (_isSearch && collapsible && !expanded) ? 0 : 1
    border.color: (_isSearch && collapsible && !expanded) ? Enums.transparent : (Enums.stateColor.borderSubtle)
    showFocusedBorder: !(_isSearch && collapsible && !expanded)
    
    // Width animation 宽度动画
    Behavior on implicitWidth {
        NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutCubic }
    }
    Behavior on radius {
        NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutCubic }
    }
    
    // ==================== Internal State 内部状态 ====================
    readonly property bool _isPassword: inputType === Enums.input.type_password
    readonly property bool _isSearch: inputType === Enums.input.type_search
    readonly property int _actualEchoMode: _isPassword ? (showPassword ? TextInput.Normal : TextInput.Password) : TextInput.Normal
    // 收起时使用透明样式按钮
    readonly property bool _isCollapsedSearch: control._isSearch && control.collapsible && !control.expanded
    
    // ==================== Input Area 输入区域 ====================
    // Delay hide on collapse for animation 收起时延迟隐藏
    property bool _delayedVisible: !control.collapsible || control.expanded
    onExpandedChanged: {
        if (expanded) {
            // Show immediately when expanded 展开时立即显示
            textInput.visible = true
        } else {
            // Delay hide when collapsed 收起时延迟隐藏
            _hideTimer.restart()
        }
    }
    Timer {
        id: _hideTimer
        interval: 200  // Sync with width animation 与宽度动画同步
        onTriggered: if (!control.expanded) textInput.visible = false
    }
    
    TextInput {
        id: textInput
        anchors.left: parent.left
        anchors.right: actionBtn.visible ? actionBtn.left : (clearBtn.visible ? clearBtn.left : parent.right)
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: control.paddingLeft
        anchors.rightMargin: control.paddingRight
        visible: !control.collapsible || control.expanded  // Visible when not collapsible or expanded 非折叠或展开时可见
        opacity: (!control.collapsible || control.expanded) ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: Enums.duration.medium } }
        
        font.family: control.fontFamily
        font.pixelSize: control.fontSize
        color: control.inputTextColor
        selectionColor: control.selectionColor
        selectedTextColor: control.selectedTextColor
        selectByMouse: true
        clip: true  // Ensure text is clipped when collapsed 确保收起时文字被裁剪
        readOnly: control.readOnly
        echoMode: control._actualEchoMode
        maximumLength: control.maximumLength
        enabled: control.enabled
        
        onTextEdited: control.textEdited(text)
        onAccepted: {
            control.accepted()
            if (control._isSearch) control.searched(text)
        }
        onEditingFinished: control.editingFinished()
        
        // Placeholder text占位文本
        InputPlaceholderLabel {
            anchors.fill: parent
            text: control.placeholderText
            visible: !parent.text && !parent.activeFocus
        }
    }
    
    
    // ==================== Clear Button 清除按钮 ====================
    CloseButton {
        id: clearBtn
        anchors.right: actionBtn.visible ? actionBtn.left : parent.right
        anchors.rightMargin: actionBtn.visible ? Enums.spacing.xs : Enums.spacing.m
        anchors.verticalCenter: parent.verticalCenter
        size: Enums.spacing.xl
        iconSizeValue: Enums.iconSize.tiny
        normalIconColor: Enums.textColor.tertiary
        visible: control.clearButtonEnabled && textInput.text.length > 0 && !control.readOnly && (!control.collapsible || control.expanded)
        onClicked: {
            textInput.text = ""
            textInput.forceActiveFocus()
            if (control._isSearch) control.cleared()
        }
    }
    
    // ==================== Action Button (password toggle/search) 动作按钮 ====================
    InputActionButton {
        id: actionBtn
        anchors.right: parent.right
        anchors.rightMargin: _isCollapsedSearch ? 0 : Enums.spacing.s
        anchors.verticalCenter: parent.verticalCenter
        visible: control._isPassword || control._isSearch
        collapsed: _isCollapsedSearch
        collapsedSize: control.collapsedWidth
        icon: control._isPassword 
            ? (control.showPassword ? Enums.icon.eye_off : Enums.icon.eye)
            : Enums.icon.search
        onClicked: {
            if (control._isPassword) {
                control.showPassword = !control.showPassword
            } else if (control._isSearch) {
                // Collapsible: click to expand and focus 未展开时点击展开
                if (control.collapsible && !control.expanded) {
                    textInput.visible = true
                    textInput.forceActiveFocus()
                } else {
                    control.searched(textInput.text)
                }
            }
        }
    }
    
    // ==================== Hover Detection 悬浮检测 ====================
    HoverHandler {
        id: hoverHandler
    }
    
    // TapHandler 点击聚焦已在 InputCore 统一处理
}
