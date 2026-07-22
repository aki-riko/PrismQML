// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../.."
import "_internal"
import QtQuick.Controls as Controls
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
    property int popupRadius: Enums.isPrismDesign ? Enums.prismDesign.radiusPopup : Enums.radius.large
    property int shadowRadius: popupRadius
    readonly property color _popupBackground: Enums.isPrismDesign ? Enums.dialogColor : Enums.cardColor
    readonly property int _popupBorderWidth: Enums.isNeobrutalism ? Enums.neo.borderWidth : Enums.border.thin
    readonly property color _popupBorderColor: Enums.stateColor.border
    readonly property color _popupShadowColor: Enums.shadow.level8.color
    readonly property int _popupShadowBlur: Enums.shadow.level8.blur
    readonly property int _popupShadowOffset: Enums.shadow.level8.offset
    property bool modal: false
    property bool closeOnClickOutside: true
    property bool stealFocus: true  // Whether to steal focus when opening 打开时是否抢夺焦点
    property bool useInWindowPopup: false  // Render in the owning window to avoid a second native surface 页内渲染以避免第二个原生窗口
    property Item targetControl: null  // Trigger control 触发弹出的控件
    property int animationType: 0  // 0=expand, 1=slideDown (Fluent Design style) 动画类型
    property bool _isPickerMode: false  // Internal: picker mode for center alignment 内部：Picker模式居中对齐
    property bool _submenuPlacement: false  // Internal: right/left placement for anchored submenus 子菜单锚点定位
    property int _pickerRowHeight: 37  // Internal: row height for picker mode 内部：Picker模式行高

    // ==================== Internal Props 内部属性 ====================
    property bool _prewarmed: false
    property bool _prewarmScheduled: false
    // Internal: animated clip height for drop-down effect 内部：下拉展开动画的裁剪高度
    property real _clipHeight: 0
    // [Anim C] Spring scale for iOS-style bounce 弹簧缩放
    property real _scale: 0.7
    // Follow parent control position (sync move on scroll) 跟随父控件位置变化
    readonly property var _targetWindow: targetControl ? targetControl.Window.window : null
    readonly property Item _inlineParent: _targetWindow ? _targetWindow.contentItem : null
    readonly property int _outerWidth: Math.max(
        Enums.popupMetrics.minWidth,
        popupWidth + Enums.popupMetrics.windowPadding
    )
    readonly property int _outerHeight: Math.max(
        Enums.popupMetrics.minHeight,
        popupHeight + Enums.popupMetrics.windowPadding
    )
    readonly property bool _surfaceVisible: useInWindowPopup
        ? inlinePopup.visible
        : popupWindow.visible

    // Popup content 弹出内容
    default property alias popupContent: popupSurface.popupContent
    
    // ==================== Signals 信号 ====================
    signal opened()
    signal closed()
    signal aboutToShow()
    signal aboutToHide()
    
    // ==================== Public Methods 公开方法 ====================
    function _screenBoundsAt(globalX, globalY, sourceItem) {
        if (typeof WindowHelper !== "undefined" && WindowHelper
                && typeof WindowHelper.availableScreenGeometryAt === "function") {
            var geometry = WindowHelper.availableScreenGeometryAt(
                Math.round(globalX), Math.round(globalY))
            if (geometry && geometry.width > 0 && geometry.height > 0) {
                return {
                    left: geometry.x,
                    top: geometry.y,
                    right: geometry.x + geometry.width,
                    bottom: geometry.y + geometry.height
                }
            }
        }

        var screen = sourceItem && sourceItem.Screen ? sourceItem.Screen : Screen
        if (screen && screen.width > 0 && screen.height > 0) {
            var virtualX = typeof screen.virtualX === "number" ? screen.virtualX : 0
            var virtualY = typeof screen.virtualY === "number" ? screen.virtualY : 0
            return {
                left: virtualX,
                top: virtualY,
                right: virtualX + screen.width,
                bottom: virtualY + screen.height
            }
        }
        return null
    }

    // Keep inline surfaces inside their owning window. 页内弹层保持在宿主窗口内
    function _calcInlinePosition(globalX, globalY) {
        if (!_inlineParent) return Qt.point(0, 0)
        var localPos = _inlineParent.mapFromGlobal(globalX, globalY)
        var fitsHorizontally = _outerWidth <= _inlineParent.width
        var fitsVertically = _outerHeight <= _inlineParent.height
        var maxX = _inlineParent.width - _outerWidth
        var maxY = _inlineParent.height - _outerHeight
        return Qt.point(
            fitsHorizontally ? Math.max(0, Math.min(localPos.x, maxX)) : localPos.x,
            fitsVertically ? Math.max(0, Math.min(localPos.y, maxY)) : localPos.y
        )
    }

    function _calcSubmenuPosition() {
        if (!targetControl || !targetControl.mapToGlobal) return Qt.point(0, 0)

        var actionTop = targetControl.mapToGlobal(0, 0)
        var actionRight = targetControl.mapToGlobal(targetControl.width, 0)
        var actionCenter = targetControl.mapToGlobal(
            targetControl.width / 2, targetControl.height / 2)
        var outerWidth = _outerWidth
        var outerHeight = _outerHeight
        var panelOffset = Enums.popupMetrics.panelOffset
        var gap = Enums.spacing.xs + Enums.popupMetrics.controlGap
        var posX = actionRight.x + gap - panelOffset
        var posY = actionTop.y - panelOffset - Enums.spacing.xs
        var bounds = _screenBoundsAt(
            actionCenter.x,
            actionCenter.y,
            targetControl
        )

        if (bounds) {
            var leftPosX = actionTop.x - gap - outerWidth + panelOffset
            if (posX + outerWidth > bounds.right && leftPosX >= bounds.left) {
                posX = leftPosX
            }
            posX = Math.max(bounds.left, Math.min(posX, bounds.right - outerWidth))
            posY = Math.max(bounds.top, Math.min(posY, bounds.bottom - outerHeight))
        }
        return Qt.point(posX, posY)
    }

    // 预热 native window handle —— 第一次 show() 在 Windows 上会同步阻塞
    // ~170ms 等 native surface 创建。在 hover/focus 等"用户即将点开"时机调用,
    // 让真正点击时走暖路径 (<5ms)。已预热则 no-op。
    // 真正的预热推到 Qt.callLater, 避免 hover 进入瞬间卡顿主线程。
    function prewarm() {
        if (_prewarmed || _prewarmScheduled || isOpen) return
        if (useInWindowPopup) {
            _prewarmed = true
            return
        }
        _prewarmScheduled = true
        prewarmTimer.start()
    }
    function _doPrewarm() {
        if (useInWindowPopup) {
            _prewarmed = true
            _prewarmScheduled = false
            return
        }
        // A real open may win the race before this queued callback runs.
        // 真正打开可能先于排队预热执行，此时绝不能再 show+hide 把菜单藏掉。
        if (!_prewarmScheduled || _prewarmed || isOpen || popupWindow.visible) {
            if (popupWindow.visible) _prewarmed = true
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
        _openAtPosition(x, y, false)
    }

    function _openAtPosition(x, y, preservePlacement) {
        // Prevent open during closing animation 防止关闭期间打开
        if (isClosing) return
        if (preservePlacement !== true) _submenuPlacement = false

        aboutToShow()

        var posX = (x !== undefined && !isNaN(x)) ? x : 0
        var posY = (y !== undefined && !isNaN(y)) ? y : 0

        if (useInWindowPopup) {
            if (!_inlineParent) return
            var localPos = _calcInlinePosition(posX, posY)
            inlinePopup.x = localPos.x
            inlinePopup.y = localPos.y
            inlinePopup.open()
            _prewarmed = true
            _prewarmScheduled = false
            prewarmTimer.stop()
            showAnimTimer.start()
            return
        }

        popupWindow.width = _outerWidth
        popupWindow.height = _outerHeight

        var bounds = _screenBoundsAt(posX, posY, targetControl)
        if (bounds) {
            posX = Math.max(bounds.left, Math.min(posX, bounds.right - popupWindow.width))
            posY = Math.max(bounds.top, Math.min(posY, bounds.bottom - popupWindow.height))
        }

        popupWindow.x = posX
        popupWindow.y = posY

        // Show window first, then trigger animation 先显示窗口，再触发动画
        popupWindow.show()
        _prewarmed = true
        _prewarmScheduled = false
        prewarmTimer.stop()
        popupWindow.raise()
        if (control.stealFocus) {
            popupWindow.requestActivate()
        }

        // Delay to trigger animation after window is visible 延迟触发动画
        showAnimTimer.start()
    }
    
    function openAtControl(targetCtrl) {
        if (!targetCtrl) return
        _submenuPlacement = false
        targetControl = targetCtrl
        var pos = targetCtrl.mapToGlobal(0, targetCtrl.height + Enums.popupMetrics.controlGap)
        // Align standard control popups by their left edges. 标准控件弹层统一左边缘对齐
        open(pos.x - Enums.popupMetrics.panelOffset, pos.y - Enums.popupMetrics.panelOffset)
    }
    
    // Open popup above control with selected row aligned to control (Fluent Design Picker style) 在控件上方打开弹出框，选中行与控件对齐（Fluent Design Picker 风格）
    function openAtPicker(targetCtrl, rowHeight) {
        if (!targetCtrl) return
        _submenuPlacement = false
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
        _prewarmed = true
        _prewarmScheduled = false
        prewarmTimer.stop()
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
        if (isClosing || (!isOpen && !showAnimTimer.running && !_surfaceVisible)) return
        aboutToHide()
        showAnimTimer.stop()
        showAnim.stop()
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
        _prewarmScheduled = false
        prewarmTimer.stop()
        isOpen = false
        isClosing = false
        _clipHeight = 0
        _scale = 0.7   // [Anim C]
        _submenuPlacement = false
        popupSurface.opacity = 0
        if (useInWindowPopup) inlinePopup.close()
        else popupWindow.hide()
    }
    
    function toggle() {
        if (isOpen) close()
        else if (targetControl) openAtControl(targetControl)
    }

    // ==================== Internal Methods 内部方法 ====================
    function _applyTrackedPosition(currentGlobalPos) {
        var newX, newY
        if (_submenuPlacement) {
            var submenuPos = _calcSubmenuPosition()
            newX = submenuPos.x
            newY = submenuPos.y
        } else if (_isPickerMode) {
            var pickerPos = _calcPickerPosition(targetControl, _pickerRowHeight)
            newX = pickerPos.x
            newY = pickerPos.y
        } else {
            newX = currentGlobalPos.x - Enums.popupMetrics.panelOffset
            newY = currentGlobalPos.y + targetControl.height + Enums.popupMetrics.controlGap - Enums.popupMetrics.panelOffset
        }
        if (useInWindowPopup && _inlineParent) {
            var localPos = _calcInlinePosition(newX, newY)
            inlinePopup.x = localPos.x
            inlinePopup.y = localPos.y
        } else {
            popupWindow.x = newX
            popupWindow.y = newY
        }
    }
    
    // ==================== Content 内容 ====================
    Timer {
        id: prewarmTimer
        interval: 0
        onTriggered: control._doPrewarm()
    }

    // Show animation 弹出动画
    // [Anim C] iOS spring: OutBack overshoot 1.4, scale 0.7→1.0, 240ms
    ParallelAnimation {
        id: showAnim

        NumberAnimation {
            target: popupSurface
            property: "opacity"
            from: 0; to: 1
            duration: Enums.popupMetrics.showOpacityDuration
            easing.type: Easing.OutQuad
        }
        NumberAnimation {
            target: control
            property: "_scale"
            from: 0.7; to: 1.0
            duration: Enums.popupMetrics.showScaleDuration
            easing.type: Easing.OutBack
            easing.overshoot: 1.4
        }
        NumberAnimation {
            target: control
            property: "_clipHeight"
            from: 0
            to: control.popupHeight
            duration: Enums.popupMetrics.clipRevealDuration
            easing.type: Easing.Linear
        }
    }

    // Hide animation 收起动画
    // [Anim C] Quick collapse with subtle InBack
    // ⚠️ Don't shrink _clipHeight here — clipContainer.height binds to it,
    // would clip out the panel before scale animation can play
    SequentialAnimation {
        id: hideAnim

        ParallelAnimation {
            NumberAnimation {
                target: popupSurface
                property: "opacity"
                to: 0
                duration: Enums.popupMetrics.hideOpacityDuration
                easing.type: Easing.InQuad
            }
            NumberAnimation {
                target: control
                property: "_scale"
                to: 0.85
                duration: Enums.popupMetrics.hideScaleDuration
                easing.type: Easing.InBack
                easing.overshoot: 1.2
            }
        }

        ScriptAction {
            script: {
                if (control.useInWindowPopup) inlinePopup.close()
                else popupWindow.hide()
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
    
    PopupPositionTracker {
        target: control.targetControl
        targetWindow: control._targetWindow
        trackingEnabled: control.isOpen
        positionEpsilon: Enums.popupMetrics.positionEpsilon
        onTargetMoved: (globalPosition) => control._applyTrackedPosition(globalPosition)
        onTargetOutOfView: control.close()
    }

    Controls.Popup {
        id: inlinePopup

        parent: control._inlineParent ? control._inlineParent : control
        width: control._outerWidth
        height: control._outerHeight
        padding: 0
        // Preserve the requested anchor instead of centering an oversized popup.
        // 保持请求的锚点，避免超宽弹层被 Qt 自动居中后发生水平漂移。
        margins: -1
        modal: control.modal
        focus: control.stealFocus
        popupType: Controls.Popup.Item
        closePolicy: control.closeOnClickOutside
            ? Controls.Popup.CloseOnPressOutside | Controls.Popup.CloseOnEscape
            : Controls.Popup.NoAutoClose
        background: null
        contentItem: Item { id: inlinePopupContent }

        onClosed: {
            if (control.isOpen && !control.isClosing) {
                showAnim.stop()
                hideAnim.stop()
                showAnimTimer.stop()
                control.isOpen = false
                control._clipHeight = 0
                control._scale = 0.7
                popupSurface.opacity = 0
                control.closed()
            }
        }
    }
    
    Window {
        id: popupWindow
        width: control._outerWidth
        height: control._outerHeight
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
        
    }

    PopupSurface {
        id: popupSurface

        parent: control.useInWindowPopup
            ? inlinePopupContent
            : popupWindow.contentItem
        outerWidth: control._outerWidth
        outerHeight: control._outerHeight
        popupWidth: control.popupWidth
        popupHeight: control.popupHeight
        popupRadius: control.popupRadius
        popupBackground: control._popupBackground
        popupBorderWidth: control._popupBorderWidth
        popupBorderColor: control._popupBorderColor
        popupShadowColor: control._popupShadowColor
        popupShadowBlur: control._popupShadowBlur
        popupShadowOffset: control._popupShadowOffset
        clipHeight: control._clipHeight
        panelScale: control._scale
    }
}
