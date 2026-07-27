// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."
import "../../icons"

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

    // ==================== Readonly State 只读状态 ====================
    readonly property string displayValue: prefix + value.toFixed(decimals) + suffix

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

    // Bind inherited InputCore state 绑定继承的 InputCore 状态
    focusTarget: textInput
    focused: textInput.activeFocus
    hovered: hoverHandler.hovered

    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.controlSize.spinBoxWidth
    implicitHeight: Enums.controlSize.inputHeight
    radius: Enums.radius.small

    // ==================== Content 内容 ====================
    // Decrease button for inline mode 内联模式减号按钮
    SpinBoxButton {
        id: decreaseBtn
        anchors.left: parent.left
        anchors.leftMargin: Enums.spacing.xs
        anchors.verticalCenter: parent.verticalCenter
        icon: Enums.icon.subtract
        visible: spinButtonsVisible && !compactMode
        enabled: control.enabled
        z: Enums.zIndex.inputControls
        onClicked: decrease()
        onButtonPressed: control._startAutoRepeat(false)
        onReleased: control._stopAutoRepeat()
    }

    // Center input area 中央输入区域
    TextInput {
        id: textInput
        anchors.left: (spinButtonsVisible && !compactMode) ? decreaseBtn.right : parent.left
        anchors.right: compactMode ? compactBtnContainer.left : ((spinButtonsVisible && !compactMode) ? increaseBtn.left : parent.right)
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: Enums.spacing.xs
        anchors.rightMargin: Enums.spacing.xs
        
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
    
    // Increase button for inline mode 内联模式加号按钮
    SpinBoxButton {
        id: increaseBtn
        anchors.right: parent.right
        anchors.rightMargin: Enums.spacing.xs
        anchors.verticalCenter: parent.verticalCenter
        icon: Enums.icon.add
        visible: spinButtonsVisible && !compactMode
        enabled: control.enabled
        z: Enums.zIndex.inputControls
        onClicked: increase()
        onButtonPressed: control._startAutoRepeat(true)
        onReleased: control._stopAutoRepeat()
    }
    
    // Compact buttons on the right 右侧紧凑按钮
    // Inline mode: two separate clickable buttons 内联模式：两个独立可点击按钮
    Item {
        id: compactBtnContainer
        anchors.right: parent.right
        anchors.rightMargin: Enums.spacing.xxs
        anchors.verticalCenter: parent.verticalCenter
        width: Enums.spacing.xl + Enums.spacing.xs  // 20
        height: control.height - Enums.spacing.xs
        visible: compactMode
        z: Enums.zIndex.inputControls
        
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
            // Accelerate each repeat toward the minimum interval 每次重复后向最短间隔收敛
            if (control.autoRepeatMinInterval > 0 &&
                control._repeatCurrentInterval > control.autoRepeatMinInterval) {
                var next = Math.max(control.autoRepeatMinInterval,
                                    Math.floor(control._repeatCurrentInterval * Enums.input.spinBoxRepeatAcceleration))
                if (next !== control._repeatCurrentInterval) {
                    control._repeatCurrentInterval = next
                    autoRepeatTimer.interval = next
                }
            }
        }
    }

    // Wheel feedback timers 滚轮反馈计时器
    Timer {
        id: upFeedbackTimer
        interval: Enums.duration.fast
        onTriggered: {
            if (compactMode) { compactUpBtn.pseudoHovered = false; compactUpBtn.pseudoPressed = false }
            else { increaseBtn.pseudoHovered = false; increaseBtn.pseudoPressed = false }
        }
    }
    
    Timer {
        id: downFeedbackTimer
        interval: Enums.duration.fast
        onTriggered: {
            if (compactMode) { compactDownBtn.pseudoHovered = false; compactDownBtn.pseudoPressed = false }
            else { decreaseBtn.pseudoHovered = false; decreaseBtn.pseudoPressed = false }
        }
    }
}
