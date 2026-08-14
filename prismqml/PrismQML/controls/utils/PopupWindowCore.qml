// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../.."
import "_internal"
import "_internal/PopupLifecycle.js" as PopupLifecycle
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
    property int contentPadding: Enums.spacing.xs  // Core-owned panel padding 基类统一管理的面板内边距
    // Preferred content size drives the panel size unless popupWidth/popupHeight is overridden.
    // 首选内容尺寸自动推导面板尺寸；显式设置 popupWidth/popupHeight 时以外框尺寸为准。
    property int implicitContentWidth: Math.max(
        0, Enums.popupMetrics.defaultSize - 2 * contentPadding)
    property int implicitContentHeight: Math.max(
        0, Enums.popupMetrics.defaultSize - 2 * contentPadding)
    property int popupWidth: implicitContentWidth + 2 * contentPadding
    property int popupHeight: implicitContentHeight + 2 * contentPadding
    // Actual content viewport after applying the panel padding. 应用面板内边距后的真实内容视口。
    readonly property int availableContentWidth: Math.max(
        0, popupWidth - 2 * contentPadding)
    readonly property int availableContentHeight: Math.max(
        0, popupHeight - 2 * contentPadding)
    property int popupRadius: Enums.surfaceRadius(Enums.radius.large)
    property int shadowRadius: popupRadius
    readonly property color _popupBackground: Enums.cardColor
    readonly property real _popupBorderWidth: Enums.surfaceBorderWidth(Enums.border.thin)
    readonly property color _popupBorderColor: Enums.stateColor.border
    readonly property color _popupShadowColor: Enums.shadow.level8.color
    readonly property int _popupShadowBlur: Enums.shadow.level8.blur
    readonly property int _popupShadowOffset: Enums.shadow.level8.offset
    readonly property real _popupNeumorphicShadowBlur: Enums.neumorphism.popupShadowBlur
    readonly property real _popupNeumorphicShadowOffset: Enums.neumorphism.popupShadowOffset
    readonly property real _popupNeumorphicShadowSpread: Enums.neumorphism.popupShadowSpread
    // The panel inset and native surface size must follow the active shadow contract.
    // 面板内缩与原生表面尺寸必须跟随当前阴影合同。
    readonly property real _panelOffset: Enums.isNeumorphism
        ? Enums.neumorphism.popupShadowMargin : Enums.popupMetrics.panelOffset
    property bool modal: false
    property bool closeOnClickOutside: true
    property bool stealFocus: true  // Whether to steal focus when opening 打开时是否抢夺焦点
    property bool useInWindowPopup: false  // Render in the owning window to avoid a second native surface 页内渲染以避免第二个原生窗口
    property bool useQtPopupWindow: false  // Render with Qt Quick Controls Popup.Window 使用Qt管理的原生弹出窗口
    property bool constrainToAvailableScreen: true  // Keep clear of taskbars and reserved system UI 避让任务栏与系统保留区
    property Item targetControl: null  // Trigger control 触发弹出的控件
    property int animationType: 0  // 0=expand, 1=slideDown (Fluent Design style) 动画类型
    property bool verticalCenterExpand: false  // Expand vertically from the center 从中心向上下两侧垂直展开
    property bool _isPickerMode: false  // Internal: picker mode for center alignment 内部：Picker模式居中对齐
    property bool _submenuPlacement: false  // Internal: right/left placement for anchored submenus 子菜单锚点定位
    property int _pickerRowHeight: 37  // Internal: row height for picker mode 内部：Picker模式行高

    // ==================== Internal Props 内部属性 ====================
    property bool _prewarmed: false
    property bool _prewarmScheduled: false
    property bool _prewarmingQtPopup: false
    property Item _prewarmFocusItem: null
    property bool _ownerReleaseInProgress: false
    property bool _nativeWindowRequested: false
    property bool _openRequested: false
    property bool _surfaceRecoveryScheduled: false
    property int _surfaceRecoveryAttemptCount: 0
    readonly property int _maxSurfaceRecoveryAttempts: 1
    readonly property alias _lifecycleTimer: lifecycleTimer
    readonly property bool _isPopupWindowCore: true
    // Internal: animated clip height for drop-down effect 内部：下拉展开动画的裁剪高度
    property real _clipHeight: 0
    // [Anim C] Spring scale for iOS-style bounce 弹簧缩放
    property real _scale: 0.7
    // Follow parent control position (sync move on scroll) 跟随父控件位置变化
    readonly property var _targetWindow: targetControl ? targetControl.Window.window : null
    readonly property Item _inlineParent: _targetWindow ? _targetWindow.contentItem : null
    readonly property bool _usesControlsPopup: useInWindowPopup || useQtPopupWindow
    readonly property var _popupWindow: popupWindowLoader.item
    readonly property int _outerWidth: Math.max(
        Enums.popupMetrics.minWidth, Math.ceil(popupWidth + 2 * _panelOffset))
    readonly property int _outerHeight: Math.max(
        Enums.popupMetrics.minHeight, Math.ceil(popupHeight + 2 * _panelOffset))
    readonly property bool _surfaceVisible: _usesControlsPopup
        ? (inlinePopup ? inlinePopup.visible : false) : (_popupWindow ? _popupWindow.visible : false)

    // Popup content 弹出内容
    default property alias popupContent: popupSurface.popupContent
    
    // ==================== Signals 信号 ====================
    signal opened()
    signal closed()
    signal aboutToShow()
    signal aboutToHide()
    
    // ==================== Public Methods 公开方法 ====================
    function _boundsFromGeometry(geometry) {
        if (!geometry || geometry.width <= 0 || geometry.height <= 0) return null
        return {
            left: geometry.x,
            top: geometry.y,
            right: geometry.x + geometry.width,
            bottom: geometry.y + geometry.height
        }
    }

    function _screenBoundsAt(globalX, globalY, sourceItem) {
        var geometry = null
        if (typeof WindowHelper !== "undefined" && WindowHelper) {
            if (constrainToAvailableScreen
                    && typeof WindowHelper.availableScreenGeometryAt === "function") {
                geometry = WindowHelper.availableScreenGeometryAt(
                    Math.round(globalX), Math.round(globalY))
            } else if (!constrainToAvailableScreen
                    && typeof WindowHelper.screenGeometryAt === "function") {
                geometry = WindowHelper.screenGeometryAt(
                    Math.round(globalX), Math.round(globalY))
            }
            var injectedBounds = _boundsFromGeometry(geometry)
            if (injectedBounds) return injectedBounds
        }

        var screen = sourceItem && sourceItem.Screen ? sourceItem.Screen : Screen
        if (screen && screen.width > 0 && screen.height > 0) {
            var virtualX = typeof screen.virtualX === "number" ? screen.virtualX : 0
            var virtualY = typeof screen.virtualY === "number" ? screen.virtualY : 0
            return _boundsFromGeometry({
                x: virtualX, y: virtualY,
                width: screen.width, height: screen.height
            })
        }
        return null
    }

    function _calcControlsPopupPosition(globalX, globalY) {
        if (!_inlineParent) return Qt.point(0, 0)
        // Popup.Window owns a top-level Qt::Popup surface and may cross the
        // host window boundary. Only Popup.Item needs host-window clamping.
        // Popup.Window由Qt管理顶层弹层，可越过宿主边界；仅页内Popup.Item需夹紧。
        if (useQtPopupWindow) {
            var bounds = _screenBoundsAt(globalX, globalY, targetControl)
            if (bounds) {
                globalX = Math.max(
                    bounds.left,
                    Math.min(globalX, bounds.right - _outerWidth)
                )
                globalY = Math.max(
                    bounds.top,
                    Math.min(globalY, bounds.bottom - _outerHeight)
                )
            }
            return _inlineParent.mapFromGlobal(globalX, globalY)
        }
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
        var panelOffset = _panelOffset
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
        if (!useQtPopupWindow && !_ensureNativeWindow()) return
        _prewarmScheduled = true
        prewarmTimer.start()
    }
    function _ensureNativeWindow() {
        if (_usesControlsPopup) return null
        _nativeWindowRequested = true
        if (!_popupWindow) {
            console.warn("PopupWindowCore failed to create the native popup window")
            return null
        }
        return _popupWindow
    }
    function _finishQtPopupPrewarm() {
        var ownerWindow = control.Window.window
        var focusItem = _prewarmFocusItem
        _prewarmingQtPopup = false
        _prewarmFocusItem = null
        if (!_prewarmScheduled || isOpen || inlinePopup.visible) return
        if (ownerWindow) ownerWindow.requestActivate()
        if (focusItem) focusItem.forceActiveFocus()
        _prewarmed = true
        _prewarmScheduled = false
    }
    function _doPrewarm() {
        if (useInWindowPopup) {
            _prewarmed = true
            _prewarmScheduled = false
            return
        }
        if (useQtPopupWindow) {
            if (!_prewarmScheduled || _prewarmed || isOpen || inlinePopup.visible) {
                if (inlinePopup.visible) _prewarmed = true
                _prewarmScheduled = false
                return
            }
            var savedInlineX = inlinePopup.x, savedInlineY = inlinePopup.y
            _prewarmingQtPopup = true
            _prewarmFocusItem = control.Window.window
                ? control.Window.window.activeFocusItem
                : null
            inlinePopup.x = -32000
            inlinePopup.y = -32000
            inlinePopup.open()
            inlinePopup.close()
            inlinePopup.x = savedInlineX
            inlinePopup.y = savedInlineY
            Qt.callLater(control._finishQtPopupPrewarm)
            return
        }
        // A real open may win the race before this queued callback runs.
        // 真正打开可能先于排队预热执行，此时绝不能再 show+hide 把菜单藏掉。
        var nativeWindow = _ensureNativeWindow()
        if (!nativeWindow) {
            _prewarmScheduled = false
            return
        }
        if (!_prewarmScheduled || _prewarmed || isOpen || nativeWindow.visible) {
            if (nativeWindow.visible) _prewarmed = true
            _prewarmScheduled = false
            return
        }
        var savedX = nativeWindow.x, savedY = nativeWindow.y
        nativeWindow.x = -32000
        nativeWindow.y = -32000
        nativeWindow.show()
        nativeWindow.hide()
        nativeWindow.x = savedX
        nativeWindow.y = savedY
        _prewarmed = true
        _prewarmScheduled = false
    }

    function _clearQtPopupOwner() {
        if (!useQtPopupWindow
                || typeof WindowHelper === "undefined" || !WindowHelper
                || typeof WindowHelper.clearPopupWindowOwner !== "function") return
        var popup = inlinePopupContent.Window.window
        var owner = control._targetWindow ? control._targetWindow : control.Window.window
        if (popup && owner) WindowHelper.clearPopupWindowOwner(popup, owner)
    }

    // Qt may retain the owner capture after the opening click has finished.
    // Qt 可能在打开点击结束后仍保留宿主捕获，阻断弹层子项的首击。
    function _releaseQtPopupCapture() {
        if (!useQtPopupWindow
                || typeof WindowHelper === "undefined" || !WindowHelper
                || typeof WindowHelper.releasePopupWindowCapture !== "function") return
        var popup = inlinePopupContent.Window.window
        var owner = control._targetWindow ? control._targetWindow : control.Window.window
        if (popup && owner) WindowHelper.releasePopupWindowCapture(popup, owner)
    }
    function _showCurrentSurface() {
        if (_usesControlsPopup) {
            if (!_inlineParent) return false
            inlinePopup.open()
            return inlinePopup.visible
        }
        var nativeWindow = _popupWindow
        if (!nativeWindow) return false
        nativeWindow.show()
        nativeWindow.raise()
        if (stealFocus) nativeWindow.requestActivate()
        return nativeWindow.visible
    }
    function _startOpenAnimation() {
        showAnim.start()
    }
    function _resetOpenAppearance() {
        showAnim.stop()
        hideAnim.stop()
        _clipHeight = 0
        _scale = verticalCenterExpand ? 0 : 0.7
        popupSurface.opacity = 0
    }
    function _handleSurfaceClosed() {
        PopupLifecycle.handleSurfaceClosed(control)
    }
    // A hidden/minimized owner invalidates every popup surface mode. Reset the
    // shared lifecycle before the owner can be restored. 隐藏或最小化宿主会使
    // 所有弹层 surface 失效；宿主恢复前统一重置生命周期。
    function _releasePopupForUnavailableOwner() {
        if (_ownerReleaseInProgress) return
        var owner = control._targetWindow ? control._targetWindow : control.Window.window
        if (owner && owner.visible
                && owner.visibility !== Window.Hidden
                && owner.visibility !== Window.Minimized) return
        _ownerReleaseInProgress = true
        if (useQtPopupWindow) _clearQtPopupOwner()
        forceReset()
        _ownerReleaseInProgress = false
    }
    function open(x, y) {
        _openAtPosition(x, y, false)
    }
    function _openAtPosition(x, y, preservePlacement) {
        if (preservePlacement !== true) _submenuPlacement = false

        // Create the native content host before aboutToShow so content-sized
        // popups can measure their items while the host is still hidden.
        // 在 aboutToShow 前创建原生内容宿主，确保隐藏状态下仍能正确测量内容尺寸。
        var nativeWindow = _usesControlsPopup ? null : _ensureNativeWindow()
        if (_usesControlsPopup && !_inlineParent) return
        if (!_usesControlsPopup && !nativeWindow) return
        // Keep repeated requests idempotent while opening or open. 打开中或已打开时保持幂等。
        if (!PopupLifecycle.beginOpen(control)) return
        aboutToShow()
        if (!_openRequested || isClosing) return

        var pickerPos = _isPickerMode
            ? _calcPickerPosition(targetControl, _pickerRowHeight) : null
        var posX = pickerPos
            ? pickerPos.x : ((x !== undefined && !isNaN(x)) ? x : 0)
        var posY = pickerPos
            ? pickerPos.y : ((y !== undefined && !isNaN(y)) ? y : 0)

        if (_usesControlsPopup) {
            _prewarmingQtPopup = false
            _prewarmFocusItem = null
            var localPos = _calcControlsPopupPosition(posX, posY)
            inlinePopup.x = localPos.x
            inlinePopup.y = localPos.y
            _showCurrentSurface()
            _prewarmed = true
            _prewarmScheduled = false
            prewarmTimer.stop()
            PopupLifecycle.scheduleCompletion(control)
            return
        }

        nativeWindow.width = _outerWidth
        nativeWindow.height = _outerHeight

        var bounds = _screenBoundsAt(posX, posY, targetControl)
        if (bounds) {
            posX = Math.max(bounds.left, Math.min(posX, bounds.right - nativeWindow.width))
            posY = Math.max(bounds.top, Math.min(posY, bounds.bottom - nativeWindow.height))
        }

        nativeWindow.x = posX
        nativeWindow.y = posY

        // Show window first, then trigger animation 先显示窗口，再触发动画
        _showCurrentSurface()
        _prewarmed = true
        _prewarmScheduled = false
        _prewarmingQtPopup = false
        _prewarmFocusItem = null
        prewarmTimer.stop()
        // Delay to trigger animation after window is visible 延迟触发动画
        PopupLifecycle.scheduleCompletion(control)
    }
    function openAtControl(targetCtrl) {
        if (!targetCtrl) return
        _submenuPlacement = false
        targetControl = targetCtrl
        var pos = targetCtrl.mapToGlobal(0, targetCtrl.height + Enums.popupMetrics.controlGap)
        // Align standard control popups by their left edges. 标准控件弹层统一左边缘对齐
        open(pos.x - _panelOffset, pos.y - _panelOffset)
    }
    
    // Open popup above control with selected row aligned to control (Fluent Design Picker style) 在控件上方打开弹出框，选中行与控件对齐（Fluent Design Picker 风格）
    function openAtPicker(targetCtrl, rowHeight) {
        if (!targetCtrl) return
        _submenuPlacement = false
        targetControl = targetCtrl
        _isPickerMode = true
        _pickerRowHeight = rowHeight
        _openAtPosition(undefined, undefined, false)
    }
    // Internal: calculate picker position 内部：计算Picker位置
    function _calcPickerPosition(targetCtrl, rowHeight) {
        var controlPos = targetCtrl.mapToGlobal(0, 0)
        // Wheel area height 滚轮区域高度
        var wheelAreaHeight = Enums.controlSize.wheelPickerAreaHeight
        // Selected row is at center of wheel area 选中行在滚轮区域中心
        var selectedRowCenterY = wheelAreaHeight / 2
        
        // Align selected row center with control center, fine-tune offset 选中行中心对齐控件中心，微调偏移
        var posY = controlPos.y + targetCtrl.height / 2 - selectedRowCenterY - Enums.spacing.xs - _panelOffset
        var posX = controlPos.x + (targetCtrl.width - popupWidth) / 2 - _panelOffset
        // Screen boundary check 屏幕边界检查
        var screen = Screen
        if (screen) {
            posX = Math.max(0, Math.min(posX, screen.width - _outerWidth))
            posY = Math.max(0, Math.min(posY, screen.height - _outerHeight))
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
        if (!PopupLifecycle.canClose(control, _surfaceVisible)) return
        aboutToHide()
        PopupLifecycle.beginClose(control)
        showAnim.stop()
        _isPickerMode = false  // Reset picker mode 重置Picker模式
        hideAnim.start()
        closed()
    }

    // Finish geometry-changing entrance motion before a child handles a press.
    // 子项处理按下事件前结束会改变命中区域的入场动画。
    function stabilizeInteraction() {
        if (!showAnim.running) return
        showAnim.stop()
        popupSurface.opacity = 1
        _scale = 1
        _clipHeight = popupHeight
    }
    // Force reset all state - for system tray menu reopen 强制重置所有状态（系统托盘菜单重新打开使用）
    function forceReset() {
        PopupLifecycle.forceReset(control)
        _prewarmScheduled = false
        _prewarmingQtPopup = false
        _prewarmFocusItem = null
        prewarmTimer.stop()
        _isPickerMode = false
        _submenuPlacement = false
        if (_usesControlsPopup) inlinePopup.close()
        else if (_popupWindow) _popupWindow.hide()
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
            newX = currentGlobalPos.x - _panelOffset
            newY = currentGlobalPos.y + targetControl.height + Enums.popupMetrics.controlGap - _panelOffset
        }
        if (_usesControlsPopup && _inlineParent) {
            var localPos = _calcControlsPopupPosition(newX, newY)
            inlinePopup.x = localPos.x
            inlinePopup.y = localPos.y
        } else if (_popupWindow) {
            _popupWindow.x = newX
            _popupWindow.y = newY
        }
    }
    
    // ==================== Content 内容 ====================
    Timer {
        id: prewarmTimer
        interval: 0
        onTriggered: control._doPrewarm()
    }

    Timer {
        id: lifecycleTimer
        interval: Enums.popupMetrics.showAnimDelayMs
        onTriggered: PopupLifecycle.onTimer(control)
    }

    // Show animation 弹出动画
    // [Anim C] Spring scale or vertical center expansion 弹簧缩放或垂直中心展开
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
            from: control.verticalCenterExpand ? 0 : 0.7; to: 1.0
            duration: Enums.popupMetrics.showScaleDuration
            easing.type: control.verticalCenterExpand ? Easing.OutCubic : Easing.OutBack
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
                to: control.verticalCenterExpand ? 0 : 0.85
                duration: Enums.popupMetrics.hideScaleDuration
                easing.type: control.verticalCenterExpand ? Easing.InCubic : Easing.InBack
                easing.overshoot: 1.2
            }
        }

        ScriptAction {
            script: {
                if (control._usesControlsPopup) inlinePopup.close()
                else if (control._popupWindow) control._popupWindow.hide()
                control.isClosing = false
                control._clipHeight = 0  // [Anim C] reset for next show
            }
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
        padding: Enums.spacing.none
        // Preserve the requested anchor instead of centering an oversized popup.
        // 保持请求的锚点，避免超宽弹层被 Qt 自动居中后发生水平漂移。
        margins: -1
        modal: control.modal
        focus: control.stealFocus && !control._prewarmingQtPopup
        popupType: control.useQtPopupWindow
            ? Controls.Popup.Window
            : Controls.Popup.Item
        closePolicy: control.closeOnClickOutside
            ? Controls.Popup.CloseOnPressOutside | Controls.Popup.CloseOnEscape
            : Controls.Popup.NoAutoClose
        background: null
        contentItem: Item { id: inlinePopupContent }

        onAboutToHide: control._clearQtPopupOwner()
        onClosed: {
            PopupLifecycle.handleSurfaceClosed(control)
            if (!control._openRequested) {
                control._isPickerMode = false
                control._submenuPlacement = false
            }
        }
        onOpened: {
            if (control.useQtPopupWindow
                    && typeof WindowHelper !== "undefined" && WindowHelper) {
                WindowHelper.ensurePopupWindowOwner(
                    inlinePopupContent.Window.window,
                    control._targetWindow ? control._targetWindow : control.Window.window
                )
            }
        }
    }

    Connections {
        function onNativeCloseAccepted() { control._clearQtPopupOwner() }
        function onVisibleChanged() { control._releasePopupForUnavailableOwner() }
        function onVisibilityChanged() { control._releasePopupForUnavailableOwner() }

        target: control._targetWindow
        ignoreUnknownSignals: true
    }
    
    Loader {
        id: popupWindowLoader
        active: control._nativeWindowRequested && !control._usesControlsPopup
        asynchronous: false

        sourceComponent: Component {
            PopupNativeWindow {
                popupControl: control
            }
        }
    }

    PopupSurface {
        id: popupSurface

        _interactionHost: control
        parent: control._usesControlsPopup
            ? inlinePopupContent
            : (control._popupWindow ? control._popupWindow.contentItem : null)
        outerWidth: control._outerWidth
        outerHeight: control._outerHeight
        popupWidth: control.popupWidth
        popupHeight: control.popupHeight
        contentPadding: control.contentPadding
        panelOffset: control._panelOffset
        popupRadius: control.popupRadius
        popupBackground: control._popupBackground
        popupBorderWidth: control._popupBorderWidth
        popupBorderColor: control._popupBorderColor
        popupShadowColor: control._popupShadowColor
        popupShadowBlur: control._popupShadowBlur
        popupShadowOffset: control._popupShadowOffset
        popupNeumorphicShadowBlur: control._popupNeumorphicShadowBlur
        popupNeumorphicShadowOffset: control._popupNeumorphicShadowOffset
        popupNeumorphicShadowSpread: control._popupNeumorphicShadowSpread
        clipHeight: control._clipHeight
        panelScale: control._scale
        verticalCenterExpand: control.verticalCenterExpand
    }
}
