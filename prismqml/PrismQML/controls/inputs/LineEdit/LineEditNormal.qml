// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."
import "../../icons"
import "../../buttons"
import "../../data"
import "../_internal"
import "_internal" as LineEditInternal

// LineEditNormal - Normal/Password/Search input 普通/密码/搜索输入
// Internal module for LineEdit LineEdit内部模块
// Implements normal single-line input behavior 实现普通单行输入行为
Item {
    id: normalInput
    
    // ==================== Required Props 必需属性 ====================
    required property int inputType
    required property string placeholderText
    required property bool readOnly
    required property int maximumLength
    required property bool clearButtonEnabled
    required property bool showPassword
    required property bool collapsible
    required property int collapsedWidth
    required property int expandedWidth
    required property bool controlEnabled
    
    // Padding from InputCore 从基类继承的边距
    required property int paddingLeft
    required property int paddingRight
    
    // Text style from InputCore 从基类继承的文本样式
    required property int fontSize
    required property color inputTextColor
    required property color selectionColor
    required property color selectedTextColor

    // ==================== Public Props 公开属性 ====================
    // Optional input filtering; null/None means unrestricted.
    // 可选输入过滤；null/None 表示不限制。
    property var validator: null
    property int inputMethodHints: Qt.ImhNone
    property alias text: textInput.text
    property alias textInput: textInput

    // ==================== Internal Props 内部属性 ====================
    property bool _textInputVisible: !collapsible || expanded

    // ==================== Readonly State 只读状态 ====================
    readonly property bool focused: textInput.activeFocus
    readonly property bool hovered: hoverHandler.hovered
    readonly property bool _isPassword: inputType === Enums.input.type_password
    readonly property bool _isSearch: inputType === Enums.input.type_search
    readonly property int _actualEchoMode: _isPassword ? (showPassword ? TextInput.Normal : TextInput.Password) : TextInput.Normal
    readonly property bool expanded: !collapsible || textInput.activeFocus || textInput.text.length > 0
    // Collapsible: cover entire area when collapsed 收起时覆盖整个区域
    readonly property bool _isCollapsedSearch: normalInput._isSearch && normalInput.collapsible && !normalInput.expanded

    // ==================== Signals 信号 ====================
    signal textEdited(string text)
    signal accepted()
    signal editingFinished()
    signal searched(string text)
    signal cleared()
    signal selectionChanged()  // Selection changed 选择变化

    // ==================== Public Methods 公开方法 ====================
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

    // ==================== Content 内容 ====================
    LineEditInternal.LineEditNormalHideTimer {
        id: _hideTimer

        host: normalInput
    }

    // Input field 输入框
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
        
        font.family: Enums.fontFamily
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
        // Accept any QValidator subclass; null means unrestricted.
        // 接受任意 QValidator 子类；null 表示无过滤。
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

        // Placeholder 占位符
        InputPlaceholderLabel {
            anchors.fill: parent
            text: normalInput.placeholderText
            visible: !parent.text && !parent.activeFocus
        }
    }

    // Clear button 清除按钮
    CloseButton {
        id: clearBtn
        anchors.right: actionBtn.visible ? actionBtn.left : parent.right
        anchors.rightMargin: Enums.spacing.m
        anchors.verticalCenter: parent.verticalCenter
        size: Enums.controlSize.lineEditClearButtonSize
        iconSizeValue: Enums.controlSize.checkboxInner
        visible: normalInput.clearButtonEnabled && textInput.text.length > 0 && !normalInput._isSearch
        onClicked: {
            textInput.text = ""
            normalInput.cleared()
        }
    }

    // Action button for password and search 密码与搜索操作按钮
    InputActionButton {
        id: actionBtn
        anchors.centerIn: _isCollapsedSearch ? parent : undefined
        anchors.right: _isCollapsedSearch ? undefined : parent.right
        anchors.rightMargin: _isCollapsedSearch ? 0 : Enums.spacing.s
        anchors.verticalCenter: _isCollapsedSearch ? undefined : parent.verticalCenter
        visible: normalInput._isPassword || normalInput._isSearch
        collapsed: _isCollapsedSearch
        collapsedSize: normalInput.collapsedWidth
        fillParentHeight: normalInput._isSearch
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

    // Hover detection 悬浮检测
    HoverHandler {
        id: hoverHandler
    }
}
