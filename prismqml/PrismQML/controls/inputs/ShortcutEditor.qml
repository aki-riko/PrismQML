// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "_internal" as InputInternal

// ShortcutEditor - Shortcut key editor 快捷键选择器
// Extends InputCore for unified input styling 继承InputCore统一输入框样式
// Features: key tags with Button, single/combo key modes 按键标签+单键/组合键模式
InputCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string shortcut: ""
    property string defaultShortcut: ""  // Default shortcut for reset 重置用默认快捷键
    property string placeholderText: { Translator._v; return Translator.tr("click_to_record") }
    property bool recording: false
    property bool allowSingleKey: false  // Allow single key without modifier 允许单键录制（无需修饰键）

    // ==================== Internal Props 内部属性 ====================
    property real _targetX: 0
    property real _smoothContentX: 0
    property Item _focusOverlay: null

    // ==================== Readonly State 只读状态 ====================
    readonly property var keyList: shortcut ? shortcut.split("+") : []
    readonly property bool _needsScroll: contentLayer.contentWidth > contentLayer.width

    // ==================== Signals 信号 ====================
    signal shortcutRecorded(string newShortcut)

    // ==================== Public Methods 公开方法 ====================
    function getShortcut() { return shortcut }
    function getDefaultShortcut() { return defaultShortcut }
    function reset() { shortcut = defaultShortcut; shortcutRecorded(shortcut) }
    function clear() { shortcut = ""; shortcutRecorded("") }

    // ==================== Internal Methods 内部方法 ====================
    // Only intercept wheel when content overflows 仅当内容溢出时拦截滚轮
    function _smoothScrollTo(x) {
        _targetX = Math.max(0, Math.min(x, contentLayer.contentWidth - contentLayer.width))
        _smoothContentX = _targetX
    }

    function _createFocusOverlay() {
        if (_focusOverlay) return
        var root = control.Window.contentItem
        if (!root) return
        _focusOverlay = focusOverlayComponent.createObject(root, { targetControl: control })
    }

    function _destroyFocusOverlay() {
        if (_focusOverlay) {
            _focusOverlay.destroy()
            _focusOverlay = null
        }
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: Math.max(Enums.controlSize.shortcutPickerMinWidth, contentLayer.contentRow.implicitWidth + Enums.spacing.xl * 2)
    implicitHeight: Enums.controlSize.inputHeightLarge
    focused: recording || keyCapture.activeFocus
    hovered: mouseArea.containsMouse
    on_SmoothContentXChanged: contentLayer.contentX = _smoothContentX
    onRecordingChanged: {
        if (recording) {
            keyCapture.forceActiveFocus(Qt.MouseFocusReason)
            _createFocusOverlay()
        } else {
            _destroyFocusOverlay()
        }
    }

    // ==================== Content 内容 ====================
    Behavior on _smoothContentX {
        NumberAnimation {
            duration: Enums.duration.medium;
            easing.type: Easing.OutCubic
        }
    }

    InputInternal.ShortcutEditorContent {
        id: contentLayer
        editorControl: control
        cancelButton: cancelBtn
    }

    // Focus overlay 失焦遮罩
    Component {
        id: focusOverlayComponent
        Item {
            property var targetControl: null

            function _isInsideTarget(mx, my) {
                if (!targetControl) return false
                var pos = targetControl.mapToItem(this, 0, 0)
                return mx >= pos.x && mx <= pos.x + targetControl.width &&
                       my >= pos.y && my <= pos.y + targetControl.height
            }

            anchors.fill: parent
            z: Enums.zIndex.overlay

            MouseArea {
                anchors.fill: parent
                propagateComposedEvents: true
                onPressed: (mouse) => {
                    if (!_isInsideTarget(mouse.x, mouse.y)) {
                        targetControl.recording = false
                    }
                    mouse.accepted = false
                }
            }
        }
    }

    // Keyboard capture 键盘捕获
    Item {
        id: keyCapture
        anchors.fill: parent
        focus: control.recording
        activeFocusOnTab: true

        Keys.onPressed: (event) => {
            if (!control.recording) return

            var keys = []
            if (event.modifiers & Qt.ControlModifier) keys.push("Ctrl")
            if (event.modifiers & Qt.ShiftModifier) keys.push("Shift")
            if (event.modifiers & Qt.AltModifier) keys.push("Alt")
            if (event.modifiers & Qt.MetaModifier) keys.push("Win")

            var keyName = ""
            if (event.key >= Qt.Key_A && event.key <= Qt.Key_Z) {
                keyName = String.fromCharCode(event.key)
            } else if (event.key >= Qt.Key_0 && event.key <= Qt.Key_9) {
                keyName = String.fromCharCode(event.key)
            } else if (event.key >= Qt.Key_F1 && event.key <= Qt.Key_F12) {
                keyName = "F" + (event.key - Qt.Key_F1 + 1)
            } else if (event.key === Qt.Key_Space) {
                keyName = "Space"
            } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                keyName = "Enter"
            } else if (event.key === Qt.Key_Tab) {
                keyName = "Tab"
            } else if (event.key === Qt.Key_Backspace) {
                keyName = "Backspace"
            } else if (event.key === Qt.Key_Delete) {
                keyName = "Delete"
            } else if (event.key === Qt.Key_Home) {
                keyName = "Home"
            } else if (event.key === Qt.Key_End) {
                keyName = "End"
            } else if (event.key === Qt.Key_PageUp) {
                keyName = "PageUp"
            } else if (event.key === Qt.Key_PageDown) {
                keyName = "PageDown"
            } else if (event.key === Qt.Key_Up) {
                keyName = "Up"
            } else if (event.key === Qt.Key_Down) {
                keyName = "Down"
            } else if (event.key === Qt.Key_Left) {
                keyName = "Left"
            } else if (event.key === Qt.Key_Right) {
                keyName = "Right"
            } else if (event.key === Qt.Key_Insert) {
                keyName = "Insert"
            } else if (event.key === Qt.Key_Escape) {
                control.recording = false
                event.accepted = true
                return
            }

            // Accept shortcut based on allowSingleKey mode 根据allowSingleKey模式接受快捷键
            if (keyName) {
                var shouldAccept = control.allowSingleKey ||
                                   keys.length > 0 ||
                                   (event.key >= Qt.Key_F1 && event.key <= Qt.Key_F12)
                if (shouldAccept) {
                    keys.push(keyName)
                    control.shortcut = keys.join("+")
                    control.shortcutRecorded(control.shortcut)
                    control.recording = false
                }
            }

            event.accepted = true
        }
    }

    // Click to record 点击录制
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        onClicked: {
            if (!control.enabled || control.recording) return
            control.recording = true
        }
    }

    // Cancel button 取消按钮
    CloseButton {
        id: cancelBtn
        anchors.right: parent.right
        anchors.rightMargin: Enums.spacing.m
        anchors.verticalCenter: parent.verticalCenter
        visible: control.recording
        z: Enums.zIndex.controlsAbove
        onClicked: control.recording = false
    }
}
