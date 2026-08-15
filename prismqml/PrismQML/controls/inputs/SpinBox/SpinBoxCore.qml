// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."
import "_internal" as SpinBoxInternal

// SpinBoxCore - Number input base class (extends InputCore) 数字输入基类
// SpinBox/DoubleSpinBox extend this 继承此基类
// Supports inline mode (left/right buttons) and compact mode 支持内联模式和紧凑模式
InputCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    property real value: 0
    property real minimum: -Infinity
    property real maximum: Infinity
    property real stepSize: 1
    property int decimals: 0
    property string prefix: ""
    property string suffix: ""
    property bool editable: true
    // Wrap values beyond the range (max+1 -> min, min-1 -> max) 越界时回绕数值
    // Useful for cyclic domains such as time or angles; disabled by default 适用于时间或角度等循环域，默认关闭
    property bool wrap: false
    property bool spinButtonsVisible: true
    property bool compactMode: false  // Compact mode 紧凑模式
    property bool wheelOnlyWhenFocused: true  // Only allow wheel when focused 仅聚焦时允许滚轮

    // Held-button repeat matching native Windows SpinBox 模拟 Windows 原生微调框的长按重复
    // autoRepeat enables held-button repetition autoRepeat 控制是否启用长按重复
    // Delay and intervals use milliseconds 延迟与重复间隔单位均为毫秒
    property bool autoRepeat: true
    property int autoRepeatDelay: Enums.duration.spinBoxRepeatDelay
    property int autoRepeatInterval: Enums.duration.spinBoxRepeatInterval
    property int autoRepeatMinInterval: Enums.duration.spinBoxRepeatMinInterval

    // ==================== Internal Props 内部属性 ====================
    // Held-button repeat runtime state 长按重复运行状态
    property bool _repeatIsUp: true
    property int _repeatCurrentInterval: Enums.duration.spinBoxRepeatInterval
    property bool _buttonGroupInitialized: false

    // ==================== Readonly State 只读状态 ====================
    readonly property string displayValue: prefix + value.toFixed(decimals) + suffix
    readonly property Item _buttonGroup: spinButtonsLoader.item
    readonly property Item _increaseButton: _buttonGroup ? _buttonGroup.increaseButton : null
    readonly property Item _decreaseButton: _buttonGroup ? _buttonGroup.decreaseButton : null

    // ==================== Signals 信号 ====================
    signal valueUpdated(real value)  // Internal alias 内部别名
    signal valueModified(real value)  // Qt-style edit signal Qt风格编辑信号

    // ==================== Public Methods 公开方法 ====================
    function increase() {
        var previousValue = value
        var newVal = value + stepSize
        if (newVal > maximum) {
            value = wrap ? minimum : maximum
        } else {
            value = newVal
        }
        if (value === previousValue) return
        valueUpdated(value)
        valueModified(value)
    }

    function decrease() {
        var previousValue = value
        var newVal = value - stepSize
        if (newVal < minimum) {
            value = wrap ? maximum : minimum
        } else {
            value = newVal
        }
        if (value === previousValue) return
        valueUpdated(value)
        valueModified(value)
    }

    // Set range 设置范围
    function setRange(min, max) {
        minimum = min
        maximum = max
        value = Math.max(min, Math.min(max, value))
    }

    // Step up 步进
    function stepUp() { increase() }

    // Step down 步退
    function stepDown() { decrease() }

    // Set value 设置值
    function setValue(v) { value = Math.max(minimum, Math.min(maximum, v)) }
    function getValue() { return value }
    function isEnabled() { return enabled }

    // ==================== Internal Methods 内部方法 ====================
    function _startAutoRepeat(isUp) {
        if (!autoRepeat || !enabled) return
        _repeatIsUp = isUp
        autoRepeatTimer._inRepeatPhase = false
        autoRepeatTimer.start()
    }

    function _stopAutoRepeat() {
        autoRepeatTimer.stop()
        autoRepeatTimer._inRepeatPhase = false
    }

    function _triggerFeedback(isUp) {
        var button = isUp ? _increaseButton : _decreaseButton
        if (!button) return
        if (isUp) {
            upFeedbackTimer.restart()
            button.pseudoHovered = true
            button.pseudoPressed = true
        } else {
            downFeedbackTimer.restart()
            button.pseudoHovered = true
            button.pseudoPressed = true
        }
    }

    // Bind inherited InputCore state 绑定继承的 InputCore 状态
    focusTarget: textInput
    focused: textInput.activeFocus
    hovered: hoverHandler.hovered

    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.controlSize.spinBoxWidth
    implicitHeight: Enums.controlSize.inputHeight
    radius: Enums.surfaceRadius(Enums.radius.small)

    // ==================== Content 内容 ====================
    SpinBoxInternal.SpinBoxButtonGroups {
        id: buttonGroups
        spinControl: control
    }

    // Create only the button pair used by the active mode. 仅创建当前模式使用的按钮对。
    Loader {
        id: spinButtonsLoader
        anchors.fill: parent
        active: control.compactMode || control.spinButtonsVisible
        sourceComponent: control.compactMode
            ? buttonGroups.compactButtonsComponent : buttonGroups.inlineButtonsComponent
        z: Enums.zIndex.inputControls
        onItemChanged: {
            if (control._buttonGroupInitialized) control._stopAutoRepeat()
            else if (item) control._buttonGroupInitialized = true
        }
    }

    // Center input area 中央输入区域
    TextInput {
        id: textInput
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: control._buttonGroup
                            ? control._buttonGroup.textLeftInset : Enums.spacing.xs
        anchors.rightMargin: control._buttonGroup
                             ? control._buttonGroup.textRightInset : Enums.spacing.xs
        
        text: control.displayValue
        font.family: Enums.fontFamily
        font.pixelSize: control.fontSize
        color: control.inputTextColor
        selectionColor: control.selectionColor
        selectedTextColor: control.selectedTextColor
        selectByMouse: true
        readOnly: !control.editable
        enabled: control.enabled
        horizontalAlignment: Text.AlignHCenter
        
        validator: DoubleValidator { bottom: control.minimum; top: control.maximum; decimals: control.decimals }

        // Clamp values above maximum while editing instead of waiting for blur 编辑时立即钳制超过 maximum 的值
        // Prevent extreme intermediate text such as 99999999999 防止显示远超上限的中间值
        onTextChanged: {
            if (activeFocus) {
                var raw = text.replace(control.prefix, "").replace(control.suffix, "")
                var num = parseFloat(raw)
                if (!isNaN(num) && num > control.maximum) {
                    control.value = control.maximum
                    text = Qt.binding(function() { return control.displayValue })
                }
            }
        }

        onEditingFinished: {
            var num = parseFloat(text.replace(control.prefix, "").replace(control.suffix, ""))
            if (!isNaN(num)) {
                control.value = Math.max(control.minimum, Math.min(control.maximum, num))
                control.valueUpdated(control.value)
                control.valueModified(control.value)
            }
            // Re-establish binding to avoid breaking it 重新建立绑定避免破坏
            text = Qt.binding(function() { return control.displayValue })
        }
    }

    // Hover detection 悬浮检测
    HoverHandler {
        id: hoverHandler
    }
    
    // InputCore handles tap-to-focus centrally 点击聚焦由 InputCore 统一处理
    
    // Mouse wheel support 鼠标滚轮支持
    MouseArea {
        id: wheelHandler
        anchors.fill: parent
        z: Enums.zIndex.controls
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
        
        onWheel: function(wheel) {
            // Use the shared HoverHandler instead of this MouseArea's containsMouse 使用共享 HoverHandler 而非自身 containsMouse
            // InputCore's upper cursor MouseArea receives hover events first InputCore 上层光标区域会优先接收悬浮事件
            var canWheel = control.enabled && hoverHandler.hovered
            if (control.wheelOnlyWhenFocused && !textInput.activeFocus) {
                canWheel = false
            }
            
            if (canWheel) {
                if (wheel.angleDelta.y > 0) {
                    control.increase()
                    control._triggerFeedback(true)
                } else if (wheel.angleDelta.y < 0) {
                    control.decrease()
                    control._triggerFeedback(false)
                }
                textInput.forceActiveFocus()
                textInput.selectAll()
                wheel.accepted = true
            } else {
                wheel.accepted = false  // Let parent handle scroll 让父级处理滚动
            }
        }
    }
    
    // Held-button auto repeat 长按自动重复
    // Wait autoRepeatDelay, then repeat and accelerate toward the minimum interval 先等待延迟，再重复并逐步加速到最短间隔
    Timer {
        id: autoRepeatTimer

        property bool _inRepeatPhase: false

        interval: _inRepeatPhase
                  ? control._repeatCurrentInterval : control.autoRepeatDelay
        repeat: _inRepeatPhase
        onTriggered: {
            if (!_inRepeatPhase) {
                control._repeatCurrentInterval = control.autoRepeatInterval
                _inRepeatPhase = true
                start()
                return
            }
            if (control._repeatIsUp) control.increase()
            else control.decrease()
            // Accelerate each repeat toward the minimum interval 每次重复后向最短间隔收敛
            if (control.autoRepeatMinInterval > 0 &&
                control._repeatCurrentInterval > control.autoRepeatMinInterval) {
                var next = Math.max(control.autoRepeatMinInterval,
                                    Math.floor(control._repeatCurrentInterval * Enums.input.spinBoxRepeatAcceleration))
                if (next !== control._repeatCurrentInterval) {
                    control._repeatCurrentInterval = next
                }
            }
        }
    }

    // Wheel feedback timers 滚轮反馈计时器
    Timer {
        id: upFeedbackTimer
        interval: Enums.duration.fast
        onTriggered: {
            if (!control._increaseButton) return
            control._increaseButton.pseudoHovered = false
            control._increaseButton.pseudoPressed = false
        }
    }
    
    Timer {
        id: downFeedbackTimer
        interval: Enums.duration.fast
        onTriggered: {
            if (!control._decreaseButton) return
            control._decreaseButton.pseudoHovered = false
            control._decreaseButton.pseudoPressed = false
        }
    }
}
