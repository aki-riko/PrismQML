// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import "../.."
import "../../effects"
import QtQuick.Effects
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖
import QtQuick.Window  // 置于库import后:去前缀后保原生Window不被库覆盖

// PopupWindowCore - Unified popup window base class 统一弹出窗口基类
// All popup components should use this base 所有弹出组件应使用此基类
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property bool isOpen: false
    property bool isClosing: false  // Closing flag, prevent quick reopen 关闭标志
    property int popupWidth: 200
    property int popupHeight: 200
    property int popupRadius: Enums.radius.large
    property int shadowRadius: Enums.radius.large
    property bool modal: false
    property bool closeOnClickOutside: true
    property bool stealFocus: true  // Whether to steal focus when opening 打开时是否抢夺焦点
    property Item targetControl: null  // Trigger control 触发弹出的控件
    property int animationType: 0  // 0=expand, 1=slideDown (Fluent Design style) 动画类型
    property int referenceControlWidth: -1  // Reference control width for center alignment 参考控件宽度，用于居中对齐（-1=不居中，与控件左对齐）
    property bool _isPickerMode: false  // Internal: picker mode for center alignment 内部：Picker模式居中对齐
    property int _pickerRowHeight: 37  // Internal: row height for picker mode 内部：Picker模式行高
    
    // Popup content 弹出内容
    default property alias popupContent: contentContainer.data
    
    // ==================== Signals 信号 ====================
    signal opened()
    signal closed()
    signal aboutToShow()
    signal aboutToHide()
    
    // ==================== Public Methods 公开方法 ====================
    // 预热 native window handle —— 第一次 show() 在 Windows 上会同步阻塞
    // ~170ms 等 native surface 创建。在 hover/focus 等"用户即将点开"时机调用,
    // 让真正点击时走暖路径 (<5ms)。已预热则 no-op。
    // 真正的预热推到 Qt.callLater, 避免 hover 进入瞬间卡顿主线程。
    property bool _prewarmed: false
    property bool _prewarmScheduled: false
    function prewarm() {
        if (_prewarmed || _prewarmScheduled || isOpen) return
        _prewarmScheduled = true
        Qt.callLater(_doPrewarm)
    }
    function _doPrewarm() {
        if (_prewarmed || isOpen) {
            _prewarmScheduled = false
            return
        }
        var savedX = popupWindow.x, savedY = popupWindow.y
        popupWindow.x = -32000
        popupWindow.y = -32000
        popupWindow.show()
        popupWindow.hide()
        popupWindow.x = savedX
        popupWindow.y = savedY
        _prewarmed = true
        _prewarmScheduled = false
    }

    function open(x, y) {
        // Prevent open during closing animation 防止关闭期间打开
        if (isClosing) return

        aboutToShow()

        var posX = (x !== undefined && !isNaN(x)) ? x : 0
        var posY = (y !== undefined && !isNaN(y)) ? y : 0

        popupWindow.width = Math.max(Enums.popupMetrics.minWidth, popupWidth + Enums.popupMetrics.windowPadding)
        popupWindow.height = Math.max(Enums.popupMetrics.minHeight, popupHeight + Enums.popupMetrics.windowPadding)

        var screen = Screen
        if (screen) {
            if (posX + popupWindow.width > screen.width) {
                posX = Math.max(0, screen.width - popupWindow.width)
            }
            if (posY + popupWindow.height > screen.height) {
                posY = Math.max(0, screen.height - popupWindow.height)
            }
        }

        popupWindow.x = posX
        popupWindow.y = posY

        // Show window first, then trigger animation 先显示窗口，再触发动画
        popupWindow.show()
        popupWindow.raise()
        if (control.stealFocus) {
            popupWindow.requestActivate()
        }

        // Delay to trigger animation after window is visible 延迟触发动画
        showAnimTimer.start()
    }
    
    function openAtControl(targetCtrl) {
        if (!targetCtrl) return
        targetControl = targetCtrl
        var pos = targetCtrl.mapToGlobal(0, targetCtrl.height + Enums.popupMetrics.controlGap)
        // Calculate center offset when popup is wider than reference control 当弹出宽度大于参考控件宽度时计算居中偏移
        var refW = referenceControlWidth > 0 ? referenceControlWidth : targetCtrl.width
        var centerOffset = popupWidth > refW ? (popupWidth - refW) / 2 : 0
        open(pos.x - Enums.popupMetrics.panelOffset - centerOffset, pos.y - Enums.popupMetrics.panelOffset)
    }
    
    // Open popup above control with selected row aligned to control (Fluent Design Picker style) 在控件上方打开弹出框，选中行与控件对齐（Fluent Design Picker 风格）
    function openAtPicker(targetCtrl, rowHeight) {
        if (!targetCtrl) return
        targetControl = targetCtrl
        _isPickerMode = true
        _pickerRowHeight = rowHeight
        
        if (isClosing) return
        aboutToShow()
        
        var pos = _calcPickerPosition(targetCtrl, rowHeight)
        
        popupWindow.width = Math.max(Enums.popupMetrics.minWidth, popupWidth + Enums.popupMetrics.windowPadding)
        popupWindow.height = Math.max(Enums.popupMetrics.minHeight, popupHeight + Enums.popupMetrics.windowPadding)
        
        popupWindow.x = pos.x
        popupWindow.y = pos.y
        
        popupWindow.show()
        popupWindow.raise()
        popupWindow.requestActivate()
        showAnimTimer.start()
    }
    
    // Internal: calculate picker position 内部：计算Picker位置
    function _calcPickerPosition(targetCtrl, rowHeight) {
        var controlPos = targetCtrl.mapToGlobal(0, 0)
        
        // Wheel area height 滚轮区域高度
        var wheelAreaHeight = Enums.controlSize.wheelPickerAreaHeight
        // Selected row is at center of wheel area 选中行在滚轮区域中心
        var selectedRowCenterY = wheelAreaHeight / 2
        
        // Align selected row center with control center, fine-tune offset 选中行中心对齐控件中心，微调偏移
        var posY = controlPos.y + targetCtrl.height / 2 - selectedRowCenterY - Enums.spacing.xs - Enums.popupMetrics.panelOffset
        var posX = controlPos.x + (targetCtrl.width - popupWidth) / 2 - Enums.popupMetrics.panelOffset
        
        // Screen boundary check 屏幕边界检查
        var screen = Screen
        if (screen) {
            posX = Math.max(0, Math.min(posX, screen.width - popupWindow.width))
            posY = Math.max(0, Math.min(posY, screen.height - popupWindow.height))
        }
        return Qt.point(posX, posY)
    }
    
    function openAtMouse() {
        // Get cursor position from Qt.application 从Qt.application获取光标位置
        var cursorPos = Qt.point(0, 0)
        if (typeof cursor !== "undefined") {
            cursorPos = cursor.pos()
        }
        // Use mapFromGlobal if available, otherwise use screen cursor position 使用mapFromGlobal（如果可用），否则使用屏幕光标位置
        var mainWindow = control.Window.window
        if (mainWindow) {
            // Get global cursor position via Window 通过Window获取全局光标位置
            cursorPos = mainWindow.contentItem.mapToGlobal(0, 0)
            // Need actual cursor position, use transientParent trick 需要实际光标位置，使用 transientParent 技巧

        }
        open(cursorPos.x, cursorPos.y)
    }
    
    // Qt Menu API compat - popup at cursor position Qt菜单API兼容
    // mouseX, mouseY: local coordinates relative to triggerItem
    // triggerItem: the item that triggered the popup (e.g. MouseArea's parent)
    function popup(mouseX, mouseY, triggerItem) {
        // If called with mouse event coordinates 如果传入鼠标事件坐标
        if (mouseX !== undefined && mouseY !== undefined) {
            var sourceItem = triggerItem || control.parent
            if (sourceItem && sourceItem.mapToGlobal) {
                var globalPos = sourceItem.mapToGlobal(mouseX, mouseY)
                open(globalPos.x, globalPos.y)
                return
            }
        }
        openAtMouse()
    }
    
    // Popup at specific global position 在指定全局位置弹出
    function popupAt(globalX, globalY) {
        open(globalX, globalY)
    }
    
    function close() {
        if (!isOpen || isClosing) return
        aboutToHide()
        isClosing = true
        isOpen = false
        _isPickerMode = false  // Reset picker mode 重置Picker模式
        hideAnim.start()
        closed()
    }
    
    // Force reset all state - for system tray menu reopen 强制重置所有状态（系统托盘菜单重新打开使用）
    function forceReset() {
        showAnim.stop()
        hideAnim.stop()
        showAnimTimer.stop()
        popupWindow.hide()
        isOpen = false
        isClosing = false
        _clipHeight = 0
        _scale = 0.7   // [Anim C]
        popupPanel.opacity = 0
    }
    
    function toggle() {
        if (isOpen) close()
        else if (targetControl) openAtControl(targetControl)
    }
    
    // ==================== Internal Implementation 内部实现 ====================
    // Internal: animated clip height for drop-down effect 内部：下拉展开动画的裁剪高度
    property real _clipHeight: 0
    // [Anim C] Spring scale for iOS-style bounce 弹簧缩放
    property real _scale: 0.7
    // Follow parent control position (sync move on scroll) 跟随父控件位置变化
    property point _lastTargetGlobalPos: Qt.point(-1, -1)

    // ==================== Show Animation 弹出动画 ====================
    // [Anim C] iOS spring: OutBack overshoot 1.4, scale 0.7→1.0, 240ms
    ParallelAnimation {
        id: showAnim

        NumberAnimation {
            target: popupPanel
            property: "opacity"
            from: 0; to: 1
            duration: 120
            easing.type: Easing.OutQuad
        }
        NumberAnimation {
            target: control
            property: "_scale"
            from: 0.7; to: 1.0
            duration: 240
            easing.type: Easing.OutBack
            easing.overshoot: 1.4
        }
        NumberAnimation {
            target: control
            property: "_clipHeight"
            from: 0
            to: control.popupHeight
            duration: 1
            easing.type: Easing.Linear
        }
    }

    // ==================== Hide Animation 收起动画 ====================
    // [Anim C] Quick collapse with subtle InBack
    // ⚠️ Don't shrink _clipHeight here — clipContainer.height binds to it,
    // would clip out the panel before scale animation can play
    SequentialAnimation {
        id: hideAnim

        ParallelAnimation {
            NumberAnimation {
                target: popupPanel
                property: "opacity"
                to: 0
                duration: 100
                easing.type: Easing.InQuad
            }
            NumberAnimation {
                target: control
                property: "_scale"
                to: 0.85
                duration: 110
                easing.type: Easing.InBack
                easing.overshoot: 1.2
            }
        }

        ScriptAction {
            script: {
                popupWindow.hide()
                control.isClosing = false
                control._clipHeight = 0  // [Anim C] reset for next show
            }
        }
    }
    
    Timer {
        id: showAnimTimer
        interval: Enums.popupMetrics.showAnimDelayMs  // One frame delay 一帧延迟
        onTriggered: {
            control.isOpen = true
            showAnim.start()
            control.opened()
        }
    }
    
    // Follow parent control position (sync move on scroll) 跟随父控件位置变化
    Timer {
        id: positionTracker
        interval: Enums.popupMetrics.trackerIntervalMs  // 1000fps, update only on position change 仅位置变化时更新
        repeat: true
        running: control.isOpen && control.targetControl !== null
        onTriggered: {
            if (!control.targetControl) return
            
            // Get current global position of target control 获取目标控件当前全局位置
            var currentGlobalPos = control.targetControl.mapToGlobal(0, 0)
            
            // Skip if position unchanged (most common case) 位置未变则跳过（最常见情况）
            if (Math.abs(currentGlobalPos.x - control._lastTargetGlobalPos.x) < Enums.popupMetrics.positionEpsilon &&
                Math.abs(currentGlobalPos.y - control._lastTargetGlobalPos.y) < Enums.popupMetrics.positionEpsilon) {
                return
            }
            control._lastTargetGlobalPos = currentGlobalPos
            
            // Check if targetControl is in main window visible area 检查是否在可视区域
            var mainWindow = control.targetControl.Window.window
            if (mainWindow) {
                var localPos = control.targetControl.mapToItem(mainWindow.contentItem, 0, 0)
                // Close popup if targetControl scrolled out of view 滚动出视区则关闭
                if (localPos.y < -control.targetControl.height || localPos.y > mainWindow.height ||
                    localPos.x < -control.targetControl.width || localPos.x > mainWindow.width) {
                    control.close()
                    return
                }
            }
            
            var newX, newY
            if (control._isPickerMode) {
                var pos = control._calcPickerPosition(control.targetControl, control._pickerRowHeight)
                newX = pos.x
                newY = pos.y
            } else {
                // Normal mode: below control (reuse currentGlobalPos) 控件下方（复用当前全局坐标）
                // Calculate center offset when popup is wider than reference control 居中偏移
                var refW = control.referenceControlWidth > 0 ? control.referenceControlWidth : control.targetControl.width
                var centerOffset = control.popupWidth > refW ? (control.popupWidth - refW) / 2 : 0
                newX = currentGlobalPos.x - Enums.popupMetrics.panelOffset - centerOffset
                newY = currentGlobalPos.y + control.targetControl.height + Enums.popupMetrics.controlGap - Enums.popupMetrics.panelOffset
            }
            
            popupWindow.x = newX
            popupWindow.y = newY
        }
    }
    
    Window {
        id: popupWindow
        width: Math.max(Enums.popupMetrics.minWidth, control.popupWidth + Enums.popupMetrics.windowPadding)
        height: Math.max(Enums.popupMetrics.minHeight, control.popupHeight + Enums.popupMetrics.windowPadding)
        visible: false
        flags: Qt.ToolTip | Qt.FramelessWindowHint | Qt.NoFluentShadowWindowHint
        color: Enums.transparent
        
        // Auto close on focus lost 失焦自动关闭
        onActiveFocusItemChanged: {
            if (!activeFocusItem && control.isOpen && control.closeOnClickOutside) {
                Qt.callLater(function() {
                    if (!popupWindow.activeFocusItem && control.isOpen) {
                        control.close()
                    }
                })
            }
        }
        
        // Shadow Layer 阴影层 (z: background to ensure it's behind popupPanel)
        // Sync opacity with popupPanel for smooth fade animation 与面板同步透明度实现平滑淡入
        // Fluent: 模糊阴影; neo: 硬阴影(偏移纯色矩形)
        RectangularShadow {
            z: Enums.zIndex.background
            x: clipContainer.x
            y: clipContainer.y
            width: clipContainer.width
            height: clipContainer.height
            radius: control.popupRadius
            color: Enums.shadow.level4.color
            blur: Enums.shadow.level4.blur
            offset: Qt.vector2d(0, Enums.shadow.level4.offset)
            opacity: popupPanel.opacity
            visible: !Enums.isNeobrutalism
        }

        // neo 硬阴影: 偏移纯色矩形(弹层用 explicit 几何, 不用 NeoShadow 的 target)
        Rectangle {
            z: Enums.zIndex.background
            visible: Enums.isNeobrutalism
            x: clipContainer.x + Enums.neo.shadowOffset
            y: clipContainer.y + Enums.neo.shadowOffset
            width: clipContainer.width
            height: clipContainer.height
            radius: control.popupRadius
            color: Enums.neo.shadowColor
            opacity: popupPanel.opacity
        }
        
        // Clip container for drop-down animation 下拉动画裁剪容器
        Item {
            id: clipContainer
            x: Enums.popupMetrics.panelOffset
            y: Enums.popupMetrics.panelOffset
            width: control.popupWidth
            height: control._clipHeight
            clip: true
            
            // Popup panel 弹出面板
            Rectangle {
                id: popupPanel
                width: control.popupWidth
                height: control.popupHeight
                radius: control.popupRadius
                color: Enums.cardColor
                border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth : Enums.border.thin
                border.color: Enums.stateColor.border
                opacity: Enums.opacityLevel.invisible

                // [Anim C] Uniform scale, top-center origin (iOS spring style)
                transform: Scale {
                    origin.x: popupPanel.width / 2
                    origin.y: 0
                    xScale: control._scale
                    yScale: control._scale
                }

                // Content container 内容容器
                Item {
                    id: contentContainer
                    anchors.fill: parent
                    anchors.margins: Enums.spacing.xs
                }
            }
        }
    }
}
