// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."
import "../../icons"

// SpinBoxCore - Number input base class (extends InputCore) 数字输入基类
// SpinBox/DoubleSpinBox extend this 继承此基类
// Supports inline mode (left/right buttons) and compact mode 支持内联模式和紧凑模式
InputCore {
    id: control
    focusTarget: textInput
    
    // ==================== SpinBox Specific Props SpinBox特有属性 ====================
    property real value: 0
    property real minimum: -Infinity
    property real maximum: Infinity
    property real stepSize: 1
    property int decimals: 0
    property string prefix: ""
    property string suffix: ""
    property bool editable: true
    // wrap: 越界时是否回绕 (max+1 → min, min-1 → max)
    // 适合循环域场景如时间(0-23,0-59) / 角度(0-360)。默认 false 表示不回绕。
    property bool wrap: false
    property bool spinButtonsVisible: true
    property bool compactMode: false  // Compact mode 紧凑模式
    property bool wheelOnlyWhenFocused: true  // Only allow wheel when focused 仅聚焦时允许滚轮

    // 长按自动重复 (mimic Windows 原生 SpinBox)
    // autoRepeat: 是否启用长按自动重复
    // autoRepeatDelay: 按住后多久开始重复 (ms)
    // autoRepeatInterval: 重复初始间隔 (ms),数值越小越快
    // autoRepeatMinInterval: 加速后允许达到的最短间隔 (ms),0 表示不加速
    property bool autoRepeat: true
    property int autoRepeatDelay: 500
    property int autoRepeatInterval: 60
    property int autoRepeatMinInterval: 20

    // 长按重复运行时状态
    property bool _repeatIsUp: true
    property int _repeatCurrentInterval: 60

    // ==================== Signals 信号 ====================
    signal valueUpdated(real value)  // Internal alias 内部别名
    signal valueModified(real value)  // Qt-style edit signal Qt风格编辑信号
    
    // ==================== Readonly State 只读状态 ====================
    readonly property string displayValue: prefix + value.toFixed(decimals) + suffix

    // ==================== Public Methods 公开方法 ====================
    function increase() {
        var newVal = value + stepSize
        if (newVal > maximum) {
            value = wrap ? minimum : maximum
        } else {
            value = newVal
        }
        valueUpdated(value)
        valueModified(value)
    }

    function decrease() {
        var newVal = value - stepSize
        if (newVal < minimum) {
            value = wrap ? maximum : minimum
        } else {
            value = newVal
        }
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

    function _startAutoRepeat(isUp) {
        if (!autoRepeat || !enabled) return
        _repeatIsUp = isUp
        autoRepeatDelayTimer.start()
    }

    function _stopAutoRepeat() {
        autoRepeatDelayTimer.stop()
        autoRepeatTimer.stop()
    }

    function _triggerFeedback(isUp) {
        if (isUp) {
            upFeedbackTimer.restart()
            if (compactMode) { compactUpBtn.pseudoHovered = true; compactUpBtn.pseudoPressed = true }
            else { increaseBtn.pseudoHovered = true; increaseBtn.pseudoPressed = true }
        } else {
            downFeedbackTimer.restart()
            if (compactMode) { compactDownBtn.pseudoHovered = true; compactDownBtn.pseudoPressed = true }
            else { decreaseBtn.pseudoHovered = true; decreaseBtn.pseudoPressed = true }
        }
    }

    // Set value 设置值
    function setValue(v) { value = Math.max(minimum, Math.min(maximum, v)) }
    function getValue() { return value }
    function isEnabled() { return enabled }

    // ==================== Bind InputCore State 绑定InputCore状态 ====================
    focused: textInput.activeFocus
    hovered: hoverHandler.hovered
    
    // ==================== Size 尺寸 ====================
    implicitWidth: 130
    implicitHeight: Enums.controlSize.inputHeight
    radius: Enums.radius.small
    
    // ==================== Decrease Button (left, inline mode) 减号按钮（内联模式） ====================
    SpinBoxButton {
        id: decreaseBtn
        anchors.left: parent.left
        anchors.leftMargin: Enums.spacing.xs
        anchors.verticalCenter: parent.verticalCenter
        icon: Enums.icon.subtract
        visible: spinButtonsVisible && !compactMode
        enabled: control.enabled
        z: Enums.zIndex.controlsAbove
        onClicked: decrease()
        onButtonPressed: control._startAutoRepeat(false)
        onReleased: control._stopAutoRepeat()
    }

    // ==================== Input Area (center) 输入区域 ====================
    TextInput {
        id: textInput
        anchors.left: (spinButtonsVisible && !compactMode) ? decreaseBtn.right : parent.left
        anchors.right: compactMode ? compactBtnContainer.left : ((spinButtonsVisible && !compactMode) ? increaseBtn.left : parent.right)
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: Enums.spacing.xs
        anchors.rightMargin: Enums.spacing.xs
        
        text: control.displayValue
        font.family: control.fontFamily
        font.pixelSize: control.fontSize
        color: control.inputTextColor
        selectionColor: control.selectionColor
        selectedTextColor: control.selectedTextColor
        selectByMouse: true
        readOnly: !control.editable
        enabled: control.enabled
        horizontalAlignment: Text.AlignHCenter
        
        validator: DoubleValidator { bottom: control.minimum; top: control.maximum; decimals: control.decimals }

        // 实时 clamp: 用户输入超过 maximum 立即截断到 maximum (而不是等失焦才生效).
        // 防止显示 99999999999 这种远超进位上限的中间值.
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
    
    // ==================== Increase Button (right, inline mode) 加号按钮（内联模式） ====================
    SpinBoxButton {
        id: increaseBtn
        anchors.right: parent.right
        anchors.rightMargin: Enums.spacing.xs
        anchors.verticalCenter: parent.verticalCenter
        icon: Enums.icon.add
        visible: spinButtonsVisible && !compactMode
        enabled: control.enabled
        z: Enums.zIndex.controlsAbove
        onClicked: increase()
        onButtonPressed: control._startAutoRepeat(true)
        onReleased: control._stopAutoRepeat()
    }
    
    // ==================== Compact Buttons (right, compact mode) 紧凑按钮（紧凑模式） ====================
    // Inline mode: two separate clickable buttons 内联模式：两个独立可点击按钮
    Item {
        id: compactBtnContainer
        anchors.right: parent.right
        anchors.rightMargin: Enums.spacing.xxs
        anchors.verticalCenter: parent.verticalCenter
        width: Enums.spacing.xl + Enums.spacing.xs  // 20
        height: control.height - Enums.spacing.xs
        visible: compactMode
        z: Enums.zIndex.controlsAbove
        
        // Up button (extends ButtonCore) 增加按钮(继承ButtonCore)
        MiniSpinButton {
            id: compactUpBtn
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width
            height: parent.height / 2
            icon: Enums.icon.chevron_up
            enabled: control.enabled
            onClicked: control.increase()
            onButtonPressed: control._startAutoRepeat(true)
            onReleased: control._stopAutoRepeat()
        }

        // Down button (extends ButtonCore) 减少按钮(继承ButtonCore)
        MiniSpinButton {
            id: compactDownBtn
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width
            height: parent.height / 2
            icon: Enums.icon.chevron_down
            enabled: control.enabled
            onClicked: control.decrease()
            onButtonPressed: control._startAutoRepeat(false)
            onReleased: control._stopAutoRepeat()
        }
    }
    
    // ==================== Hover Detection 悬浮检测 ====================
    HoverHandler {
        id: hoverHandler
    }
    
    // TapHandler 点击聚焦已在 InputCore 统一处理
    
    // Mouse wheel support 鼠标滚轮支持
    MouseArea {
        id: wheelHandler
        anchors.fill: parent
        z: Enums.zIndex.controls
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
        
        onWheel: function(wheel) {
            // 用 hoverHandler.hovered 判断而不是自身 containsMouse,
            // 因为 InputCore 顶层 z=10 的光标 MouseArea 会拦走 hover 事件,
            // 导致本 MouseArea 的 containsMouse 永远是 false
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
    
    // ==================== Auto Repeat (long press) 长按自动重复 ====================
    // 按住按钮时,先等 autoRepeatDelay,再以 autoRepeatInterval 重复触发,
    // 持续触发后逐步加速到 autoRepeatMinInterval
    Timer {
        id: autoRepeatDelayTimer
        interval: control.autoRepeatDelay
        repeat: false
        onTriggered: {
            control._repeatCurrentInterval = control.autoRepeatInterval
            autoRepeatTimer.interval = control._repeatCurrentInterval
            autoRepeatTimer.start()
        }
    }

    Timer {
        id: autoRepeatTimer
        interval: control.autoRepeatInterval
        repeat: true
        onTriggered: {
            if (control._repeatIsUp) control.increase()
            else control.decrease()
            // 加速: 每次重复后把间隔向 minInterval 收敛 15%,直到达到下限
            if (control.autoRepeatMinInterval > 0 &&
                control._repeatCurrentInterval > control.autoRepeatMinInterval) {
                var next = Math.max(control.autoRepeatMinInterval,
                                    Math.floor(control._repeatCurrentInterval * 0.85))
                if (next !== control._repeatCurrentInterval) {
                    control._repeatCurrentInterval = next
                    autoRepeatTimer.interval = next
                }
            }
        }
    }

    // ==================== Wheel Feedback 滚轮反馈动画 ====================
    Timer {
        id: upFeedbackTimer
        interval: 100
        onTriggered: {
            if (compactMode) { compactUpBtn.pseudoHovered = false; compactUpBtn.pseudoPressed = false }
            else { increaseBtn.pseudoHovered = false; increaseBtn.pseudoPressed = false }
        }
    }
    
    Timer {
        id: downFeedbackTimer
        interval: 100
        onTriggered: {
            if (compactMode) { compactDownBtn.pseudoHovered = false; compactDownBtn.pseudoPressed = false }
            else { decreaseBtn.pseudoHovered = false; decreaseBtn.pseudoPressed = false }
        }
    }
}
