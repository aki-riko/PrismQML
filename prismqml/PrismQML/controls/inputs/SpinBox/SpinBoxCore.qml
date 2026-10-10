// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."
import "_internal" as SpinBoxInternal
import "_internal/SpinBoxValue.js" as SpinBoxValue

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
    // Icon units drawn beside the value 数值两侧绘制的图标单位
    // Accept a Fluent icon name, emoji or image path (svg/png/qrc/file) 支持 Fluent 图标名/emoji/图片路径
    property string prefixIcon: ""
    property string suffixIcon: ""
    property int iconSize: Enums.iconSize.s
    property bool iconThemeAware: true  // Tint unit icons with the control color 是否用控件颜色给图标单位着色
    property bool editable: true
    // Wrap values beyond the range (max+1 -> min, min-1 -> max) 越界时回绕数值
    // Useful for cyclic domains such as time or angles; disabled by default 适用于时间或角度等循环域，默认关闭
    property bool wrap: false
    property bool spinButtonsVisible: true
    property bool compactMode: false  // Compact mode 紧凑模式
    property bool wheelOnlyWhenFocused: true  // Only allow wheel when focused 仅聚焦时允许滚轮
    // Expression and validation extensions 表达式与校验扩展
    property bool acceptsExpression: false
    property int validationMode: Enums.input.validation_invalid_input_overridden

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
    // Unit icons reserve their own room by padding, never by shrinking the field
    // 图标单位用内边距自留空间,不靠压缩输入框来腾地方
    readonly property real _unitIconInset: iconSize + Enums.spacing.xs

    // ==================== Signals 信号 ====================
    signal valueUpdated(real value)  // Internal alias 内部别名
    signal valueModified(real value)  // Qt-style edit signal Qt风格编辑信号

    // ==================== Public Methods 公开方法 ====================
    function increase() { SpinBoxValue.increase(control) }

    function decrease() { SpinBoxValue.decrease(control) }

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
        SpinBoxValue.startAutoRepeat(control, autoRepeatTimer, isUp)
    }

    function _stopAutoRepeat() { SpinBoxValue.stopAutoRepeat(autoRepeatTimer) }

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

    // Resolve edited text into a number, evaluating expressions when enabled
    // 把编辑文本解析为数值, 启用时先求值表达式
    function _resolveEditedValue(raw) {
        var source = String(raw)
        if (acceptsExpression && SpinBoxExpression.isExpression(source)) {
            return SpinBoxExpression.evaluate(source)
        }
        return parseFloat(source)
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
        // The unit icon takes padding, so the field keeps its full width and typing,
        // caret scrolling and clipping behave exactly as without icons
        // 图标单位只占内边距：输入框宽度不变,输入、光标滚动与裁切行为与无图标时一致
        leftPadding: control.prefixIcon !== "" ? control._unitIconInset : 0
        rightPadding: control.suffixIcon !== "" ? control._unitIconInset : 0

        validator: control.acceptsExpression
                   ? expressionValidator : doubleValidator

        // Clamp values above maximum while editing instead of waiting for blur 编辑时立即钳制超过 maximum 的值
        // Prevent extreme intermediate text such as 99999999999 防止显示远超上限的中间值
        onTextChanged: {
            if (activeFocus && SpinBoxValue.shouldClampWhileEditing(
                    control, text, Enums.input.validation_invalid_input_disabled)) {
                control.value = control.maximum
                text = Qt.binding(function() { return control.displayValue })
            }
        }

        onEditingFinished: {
            SpinBoxValue.commitEditedValue(
                control, text, Enums.input.validation_invalid_input_disabled)
            // Re-establish binding to avoid breaking it 重新建立绑定避免破坏
            text = Qt.binding(function() { return control.displayValue })
        }

        DoubleValidator { id: doubleValidator; bottom: control.minimum; top: control.maximum; decimals: control.decimals }

        // Expression mode only restricts the character set 表达式模式只限制字符集
        RegularExpressionValidator { id: expressionValidator; regularExpression: /^[0-9eE+\-*\/(). ]*$/ }
    }

    // Optional icon units 可选图标单位
    SpinBoxInternal.SpinBoxUnitIcons {
        id: unitIcons
        spinControl: control
        textInputItem: textInput
    }

    // Hover detection 悬浮检测
    HoverHandler {
        id: hoverHandler
    }
    
    // InputCore handles tap-to-focus centrally 点击聚焦由 InputCore 统一处理
    
    // Mouse wheel support 鼠标滚轮支持
    MouseArea {
        id: wheelHandler

        // Wheel support must not override text or button pointer lookup.
        // 滚轮支持不能覆盖文本或按钮的指针命中。
        property bool _cursorShapeTransparent: true

        anchors.fill: parent
        z: Enums.zIndex.controls
        // Pointer-only wheel surface: the wheel needs a pointer and this area never reads
        // containsMouse, so touch needs no hover tracking here.
        // 纯指针滚轮面: 滚轮必须有指针, 本区域也不读取 containsMouse, 触摸端无需 hover 追踪。
        hoverEnabled: !Touch.isTouch
        acceptedButtons: Qt.NoButton
        
        onWheel: function(wheel) {
            // Use the shared HoverHandler instead of this MouseArea's containsMouse 使用共享 HoverHandler 而非自身 containsMouse
            // InputCore's upper cursor MouseArea receives hover events first InputCore 上层光标区域会优先接收悬浮事件
            var canWheel = control.enabled && hoverHandler.hovered
            if (control.wheelOnlyWhenFocused && !textInput.activeFocus) {
                canWheel = false
            }
            
            if (canWheel) {
                var delta = WheelEventUtils.verticalDelta(wheel)
                if (delta > 0) {
                    control.increase()
                    control._triggerFeedback(true)
                } else if (delta < 0) {
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
    SpinBoxInternal.SpinBoxAutoRepeatTimer {
        id: autoRepeatTimer
        spinControl: control
    }

    // Wheel feedback timers 滚轮反馈计时器
    SpinBoxInternal.SpinBoxFeedbackTimer {
        id: upFeedbackTimer
        spinControl: control
        increase: true
    }
    
    SpinBoxInternal.SpinBoxFeedbackTimer {
        id: downFeedbackTimer
        spinControl: control
        increase: false
    }
}
