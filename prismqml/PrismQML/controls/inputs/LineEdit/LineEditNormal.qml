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

// LineEditNormal - Normal/Password/Search input 普通/密码/搜索输入
// Internal module for LineEdit LineEdit内部模块
// Reuses TextInputCore logic 复用TextInputCore逻辑
Item {
    id: normalInput
    
    // ==================== Required Props 必需属性 ====================
    required property int inputType
    required property string placeholderText
    required property bool readOnly
    required property int maximumLength
    required property bool clearButtonEnabled
    // 可选输入过滤(由外层 LineEditCore 透传,默认 null/None 表示不限制)
    property var validator: null
    property int inputMethodHints: Qt.ImhNone
    required property bool showPassword
    required property bool collapsible
    required property int collapsedWidth
    required property int expandedWidth
    required property bool controlEnabled
    
    // Padding from InputCore 从基类继承的边距
    required property int paddingLeft
    required property int paddingRight
    
    // Text style from InputCore 从基类继承的文本样式
    required property string fontFamily
    required property int fontSize
    required property color inputTextColor
    required property color selectionColor
    required property color selectedTextColor
    
    // ==================== Output Props 输出属性 ====================
    property alias text: textInput.text
    readonly property bool focused: textInput.activeFocus
    readonly property bool hovered: hoverHandler.hovered
    property alias textInput: textInput
    
    // ==================== Signals 信号 ====================
    signal textEdited(string text)
    signal accepted()
    signal editingFinished()
    signal searched(string text)
    signal cleared()
    signal selectionChanged()  // Selection changed 选择变化
    
    // ==================== Internal State 内部状态 ====================
    readonly property bool _isPassword: inputType === Enums.input.type_password
    readonly property bool _isSearch: inputType === Enums.input.type_search
    readonly property int _actualEchoMode: _isPassword ? (showPassword ? TextInput.Normal : TextInput.Password) : TextInput.Normal
    readonly property bool expanded: !collapsible || textInput.activeFocus || textInput.text.length > 0
    
    // ==================== Collapsible Animation State 折叠动画状态 ====================
    property bool _textInputVisible: !collapsible || expanded
    // Collapsible: cover entire area when collapsed 收起时覆盖整个区域
    readonly property bool _isCollapsedSearch: normalInput._isSearch && normalInput.collapsible && !normalInput.expanded

    // ==================== Methods 方法 ====================
    function clear() { textInput.text = "" }
    function selectAll() { textInput.selectAll() }
    function forceActiveFocus() { textInput.forceActiveFocus() }

    // Undo last edit 撤销
    function undo() { textInput.undo() }

    // Redo last undone edit 重做
    function redo() { textInput.redo() }

    // Copy selected text 复制
    function copy() { textInput.copy() }

    // Cut selected text 剪切
    function cut() { textInput.cut() }

    // Paste from clipboard 粘贴
    function paste() { textInput.paste() }

    onExpandedChanged: {
        if (expanded) {
            // Show immediately when expanded 展开时立即显示
            _textInputVisible = true
        } else {
            // Delay hide when collapsed 收起时延迟隐藏
            _hideTimer.restart()
        }
    }
    Timer {
        id: _hideTimer
        interval: Enums.duration.medium
        onTriggered: if (!normalInput.expanded) normalInput._textInputVisible = false
    }
    
    // ==================== Input Field 输入框 ====================
    TextInput {
        id: textInput
        anchors.left: parent.left
        anchors.right: actionBtn.visible ? actionBtn.left : (clearBtn.visible ? clearBtn.left : parent.right)
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: normalInput.paddingLeft
        anchors.rightMargin: normalInput.paddingRight
        
        // Collapsible visibility & opacity animation 折叠可见性和透明度动画
        visible: normalInput._textInputVisible
        opacity: normalInput.expanded ? 1 : 0
        Behavior on opacity {
            enabled: normalInput.collapsible
            NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutCubic }
        }
        
        font.family: normalInput.fontFamily
        font.pixelSize: normalInput.fontSize
        color: normalInput.inputTextColor
        selectionColor: normalInput.selectionColor
        selectedTextColor: normalInput.selectedTextColor
        selectByMouse: true
        clip: true
        verticalAlignment: Text.AlignVCenter
        
        echoMode: normalInput._actualEchoMode
        readOnly: normalInput.readOnly
        maximumLength: normalInput.maximumLength
        // validator 接受 IntValidator / DoubleValidator / RegularExpressionValidator
        // 等任何 QValidator 子类。null 表示无过滤。
        validator: normalInput.validator
        inputMethodHints: normalInput.inputMethodHints
        enabled: normalInput.controlEnabled
        
        onTextEdited: normalInput.textEdited(text)
        onAccepted: {
            if (normalInput._isSearch) normalInput.searched(text)
            normalInput.accepted()
        }
        onEditingFinished: normalInput.editingFinished()
        onSelectedTextChanged: normalInput.selectionChanged()
        
        // Placeholder占位符
        InputPlaceholderLabel {
            anchors.fill: parent
            text: normalInput.placeholderText
            visible: !parent.text && !parent.activeFocus
        }
    }
    
    // ==================== Clear Button 清除按钮 ====================
    CloseButton {
        id: clearBtn
        anchors.right: actionBtn.visible ? actionBtn.left : parent.right
        anchors.rightMargin: Enums.spacing.m
        anchors.verticalCenter: parent.verticalCenter
        size: 20  // 缩小背板，原为 24
        iconSizeValue: Enums.controlSize.checkboxInner
        visible: normalInput.clearButtonEnabled && textInput.text.length > 0 && !normalInput._isSearch
        onClicked: {
            textInput.text = ""
            normalInput.cleared()
        }
    }
    
    // ==================== Action Button (Password/Search) 操作按钮 ====================
    InputActionButton {
        id: actionBtn
        anchors.centerIn: _isCollapsedSearch ? parent : undefined
        anchors.right: _isCollapsedSearch ? undefined : parent.right
        anchors.rightMargin: _isCollapsedSearch ? 0 : Enums.spacing.s
        anchors.verticalCenter: _isCollapsedSearch ? undefined : parent.verticalCenter
        visible: normalInput._isPassword || normalInput._isSearch
        collapsed: _isCollapsedSearch
        collapsedSize: normalInput.collapsedWidth
        icon: normalInput._isPassword 
            ? (normalInput.showPassword ? Enums.icon.eye_off : Enums.icon.eye)
            : Enums.icon.search
        onClicked: {
            if (normalInput._isPassword) {
                normalInput.showPassword = !normalInput.showPassword
            } else if (normalInput._isSearch) {
                if (_isCollapsedSearch) {
                    textInput.forceActiveFocus()
                } else {
                    normalInput.searched(textInput.text)
                }
            }
        }
    }
    
    // ==================== Hover Detection 悬浮检测 ====================
    HoverHandler {
        id: hoverHandler
    }
}
