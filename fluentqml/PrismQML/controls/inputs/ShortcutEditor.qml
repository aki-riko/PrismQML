// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "../icons"
import "../buttons"
import "../data/Label"

// ShortcutEditor - Shortcut key editor 快捷键选择器
// Extends InputCore for unified input styling 继承InputCore统一输入框样式
// Features: key tags with Button, single/combo key modes 按键标签+单键/组合键模式
InputCore {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property string shortcut: ""
    property string defaultShortcut: ""  // Default shortcut for reset 重置用默认快捷键
    property string placeholderText: Translator.tr("click_to_record")
    property bool recording: false
    property bool allowSingleKey: false  // Allow single key without modifier 允许单键录制（无需修饰键）
    
    // ==================== Signals 信号 ====================
    signal shortcutRecorded(string newShortcut)
    signal shortcutModified(string newShortcut)  // Alias for compatibility 兼容别名
    
    // ==================== Readonly State 只读状态 ====================
    readonly property var keyList: shortcut ? shortcut.split("+") : []
    
    // ==================== Override InputCore State 覆盖基类状态 ====================
    focused: recording || keyCapture.activeFocus
    hovered: mouseArea.containsMouse
    
    // ==================== Fluent Design Compat Methods 兼容方法 ====================
    function getShortcut() { return shortcut }
    function getDefaultShortcut() { return defaultShortcut }
    function reset() { shortcut = defaultShortcut; shortcutRecorded(shortcut) }
    function clear() { shortcut = ""; shortcutRecorded("") }
    
    // ==================== Size 尺寸 ====================
    implicitWidth: Math.max(Enums.controlSize.shortcutPickerMinWidth, contentRow.implicitWidth + Enums.spacing.xl * 2)
    implicitHeight: Enums.controlSize.inputHeightLarge
    
    // ==================== Smooth Scroll 平滑滚动 ====================
    // Only intercept wheel when content overflows 仅当内容溢出时拦截滚轮
    readonly property bool _needsScroll: tagsFlickable.contentWidth > tagsFlickable.width
    property real _targetX: 0
    property real _smoothContentX: 0
    Behavior on _smoothContentX { NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutCubic } }
    on_SmoothContentXChanged: tagsFlickable.contentX = _smoothContentX
    function _smoothScrollTo(x) {
        _targetX = Math.max(0, Math.min(x, tagsFlickable.contentWidth - tagsFlickable.width))
        _smoothContentX = _targetX
    }

    // ==================== Focus Overlay 失焦遮罩 ====================
    property Item _focusOverlay: null

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

    // ==================== Content 内容 ====================
    // Scrollable key tags area 可滚动的按键标签区域
    Flickable {
        id: tagsFlickable
        anchors.left: parent.left
        anchors.right: cancelBtn.visible ? cancelBtn.left : parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: Enums.spacing.m
        anchors.rightMargin: Enums.spacing.m
        height: Enums.controlSize.shortcutKeyHeight
        contentWidth: contentRow.width
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        flickableDirection: Flickable.HorizontalFlick
        interactive: false  // Disable drag, use wheel only 禁用拖拽，仅用滚轮
        
        // Center content when not overflowing 内容不溢出时居中
        contentX: contentWidth <= width ? -(width - contentWidth) / 2 : 0
        
        // Wheel scroll handler 滚轮滚动处理
        MouseArea {
            anchors.fill: parent
            propagateComposedEvents: true
            onWheel: (wheel) => {
                if (control._needsScroll) {
                    control._smoothScrollTo(control._targetX - wheel.angleDelta.y * 0.5)
                    wheel.accepted = true
                } else {
                    wheel.accepted = false
                }
            }
            onClicked: (mouse) => {
                mouse.accepted = false
            }
            onPressed: (mouse) => {
                mouse.accepted = false
            }
        }
        
        Row {
            id: contentRow
            height: Enums.controlSize.shortcutKeyHeight
            spacing: Enums.spacing.s
            
            // Key tags container 按键标签容器
            Row {
                id: tagsRow
                anchors.verticalCenter: parent.verticalCenter
                spacing: Enums.spacing.xs
                visible: !control.recording && control.keyList.length > 0
                
                Repeater {
                    model: control.keyList
                    
                    // Single key tag using Button 单个按键标签复用Button
                    Item {
                        width: Math.min(keyBtn.implicitWidth, Enums.controlSize.shortcutKeyMaxWidth)
                        height: Enums.controlSize.shortcutKeyHeight
                        
                        Button {
                            id: keyBtn
                            anchors.fill: parent
                            style: Enums.button.style_primary
                            text: modelData
                            enabled: control.enabled
                        }
                    }
                }
            }
            
            // Placeholder text 占位符文本
            Label {
                type: Enums.label.type_body
                anchors.verticalCenter: parent.verticalCenter
                visible: !control.recording && control.keyList.length === 0
                text: control.placeholderText
                color: Enums.textColor.tertiary
            }
            
            // Recording indicator 录制中指示器
            Label {
                type: Enums.label.type_body
                anchors.verticalCenter: parent.verticalCenter
                visible: control.recording
                text: Translator.tr("recording")
                color: Enums.accentColor
                
                SequentialAnimation on opacity {
                    running: control.recording
                    loops: Animation.Infinite
                    NumberAnimation { to: 0.4; duration: Enums.duration.dialog }
                    NumberAnimation { to: 1; duration: Enums.duration.dialog }
                }
            }
        }
    }
    
    // ==================== Focus Overlay 失焦遮罩 ====================
    Component {
        id: focusOverlayComponent
        Item {
            property var targetControl: null
            anchors.fill: parent
            z: Enums.zIndex.overlay
            
            function _isInsideTarget(mx, my) {
                if (!targetControl) return false
                var pos = targetControl.mapToItem(this, 0, 0)
                return mx >= pos.x && mx <= pos.x + targetControl.width &&
                       my >= pos.y && my <= pos.y + targetControl.height
            }
            
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
    
    // ==================== Keyboard Capture 键盘捕获 ====================
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
                    control.shortcutModified(control.shortcut)
                    control.recording = false
                }
            }
            
            event.accepted = true
        }
    }
    
    // ==================== Click to Record 点击录制 ====================
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        onClicked: {
            if (!control.enabled || control.recording) return
            control.recording = true
        }
    }
    
    // ==================== Cancel Button 取消按钮 ====================
    CloseButton {
        id: cancelBtn
        anchors.right: parent.right
        anchors.rightMargin: Enums.spacing.m
        anchors.verticalCenter: parent.verticalCenter
        visible: control.recording
        z: Enums.zIndex.controlsAbove
        onClicked: control.recording = false
    }
    
    onRecordingChanged: {
        if (recording) {
            keyCapture.forceActiveFocus(Qt.MouseFocusReason)
            _createFocusOverlay()
        } else {
            _destroyFocusOverlay()
        }
    }
}
