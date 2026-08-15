// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "_internal" as InputInternal

// PinInput - Fluent Design PIN input PIN码输入框
// Features: hover state, focus line, current cell highlight 悬浮状态/聚焦线/当前格高亮
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property int length: Enums.input.pinDefaultLength
    property string value: ""
    property bool password: true

    // ==================== Internal Props 内部属性 ====================
    property bool _syncingValue: false

    // ==================== Readonly State 只读状态 ====================
    readonly property bool focused: pinInput.activeFocus
    readonly property int selectionStart: pinInput.selectionStart
    readonly property int selectionEnd: pinInput.selectionEnd
    readonly property string selectedText: pinInput.selectedText
    readonly property int _cellRadius: Enums.surfaceRadius(Enums.radius.small)
    readonly property real _cellBorderWidth: Enums.surfaceBorderWidth(Enums.border.thin)

    // ==================== Signals 信号 ====================
    signal completed(string pin)
    signal valueModified(string pin)

    // ==================== Public Methods 公开方法 ====================
    function clear() { return _dispatchEditAction("clear") }
    function selectAll() { return _dispatchEditAction("selectAll") }
    function undo() { return _dispatchEditAction("undo") }
    function redo() { return _dispatchEditAction("redo") }
    function copy() { return _dispatchEditAction("copy") }
    function cut() { return _dispatchEditAction("cut") }
    function paste() { return _dispatchEditAction("paste") }

    function setFocus() {
        pinInput.forceActiveFocus()
    }

    function text() { return value }

    // Set echo mode (password) 设置回显模式
    function setEchoMode(mode) { password = (mode !== Enums.input.pinEchoModeNormal) }

    function isEnabled() { return enabled }

    // ==================== Internal Methods 内部方法 ====================
    function _focusInput() {
        pinInput.forceActiveFocus()
    }

    function _dispatchEditAction(actionName) {
        if (!pinInput || typeof pinInput[actionName] !== "function") return false
        pinInput[actionName]()
        return true
    }

    function _syncInputFromValue() {
        if (_syncingValue || !pinInput || pinInput.text === value) return
        _syncingValue = true
        pinInput.text = value
        if (value !== pinInput.text) value = pinInput.text
        _syncingValue = false
    }

    function _isCellSelected(index) {
        var rangeStart = Math.min(pinInput.selectionStart, pinInput.selectionEnd)
        var rangeEnd = Math.max(pinInput.selectionStart, pinInput.selectionEnd)
        return index >= rangeStart && index < rangeEnd
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: length * Enums.controlSize.pinBoxCellSize + (length - 1) * Enums.spacing.m
    implicitHeight: Enums.controlSize.pinBoxCellSize

    onValueChanged: _syncInputFromValue()
    Component.onCompleted: _syncInputFromValue()

    // ==================== Content 内容 ====================
    Row {
        anchors.centerIn: parent
        spacing: Enums.spacing.m

        Repeater {
            model: control.length

            InputInternal.PinInputCell {
                pinControl: control
            }
        }
    }

    // Hidden input 隐藏输入框
    TextInput {
        id: pinInput
        width: Enums.border.thin
        height: Enums.border.thin
        opacity: Enums.opacityLevel.invisible
        maximumLength: control.length
        inputMethodHints: Qt.ImhDigitsOnly
        enabled: control.enabled
        activeFocusOnTab: true

        onTextChanged: {
            if (control._syncingValue) return
            control._syncingValue = true
            control.value = text
            control._syncingValue = false
            control.valueModified(text)
            if (text.length === control.length) {
                control.completed(text)
            }
        }
    }
}
