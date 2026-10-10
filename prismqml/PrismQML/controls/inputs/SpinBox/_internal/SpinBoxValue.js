// SpinBoxValue - Number box value, expression and edit-commit rules 数字框数值/表达式/提交规则
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

.pragma library

// ==================== Value stepping 数值步进 ====================
// increase / decrease - Step the value with optional wrapping 步进数值并支持可选回绕
function increase(control) {
    var previousValue = control.value
    var nextValue = control.value + control.stepSize
    if (nextValue > control.maximum) {
        control.value = control.wrap ? control.minimum : control.maximum
    } else {
        control.value = nextValue
    }
    _emitValueChange(control, previousValue)
}

function decrease(control) {
    var previousValue = control.value
    var nextValue = control.value - control.stepSize
    if (nextValue < control.minimum) {
        control.value = control.wrap ? control.maximum : control.minimum
    } else {
        control.value = nextValue
    }
    _emitValueChange(control, previousValue)
}

function _emitValueChange(control, previousValue) {
    if (control.value === previousValue) return
    control.valueUpdated(control.value)
    control.valueModified(control.value)
}

// ==================== Held-button repeat 长按重复 ====================
function startAutoRepeat(control, timer, isUp) {
    if (!control.autoRepeat || !control.enabled) return
    control._repeatIsUp = isUp
    timer._inRepeatPhase = false
    timer.start()
}

function stopAutoRepeat(timer) {
    timer.stop()
    timer._inRepeatPhase = false
}

// ==================== Edit commit 编辑提交 ====================
// shouldClampWhileEditing - Live clamp decision while typing 输入过程中的实时钳制判定
function shouldClampWhileEditing(control, text, disabledMode) {
    var raw = _stripAffixes(control, text)
    // An unfinished expression must not be clamped mid-typing
    // 未完成的表达式不能在输入过程中被钳制
    if (control.acceptsExpression && isExpression(raw)) return false
    // Reject mode must not overwrite the committed value mid-typing
    // 拒绝模式不得在输入过程中覆盖已提交的值
    if (control.validationMode === disabledMode) return false
    var number = parseFloat(raw)
    return !isNaN(number) && number > control.maximum
}

// commitEditedValue - Apply the edited text 应用编辑后的文本
function commitEditedValue(control, text, disabledMode) {
    var number = resolveEditedValue(control, _stripAffixes(control, text))
    if (isNaN(number)) return
    var bounded = Math.max(control.minimum, Math.min(control.maximum, number))
    // InvalidInputDisabled rejects instead of clamping 拒绝模式直接拒绝而不是钳制
    if (control.validationMode === disabledMode && bounded !== number) return
    control.value = bounded
    control.valueUpdated(control.value)
    control.valueModified(control.value)
}

// resolveEditedValue - Evaluate expressions when enabled 启用时求值表达式
function resolveEditedValue(control, raw) {
    var source = String(raw)
    if (control.acceptsExpression && isExpression(source)) {
        return evaluate(source)
    }
    return parseFloat(source)
}

function _stripAffixes(control, text) {
    return String(text)
        .replace(control.prefix, "")
        .replace(control.suffix, "")
}

// ==================== Expression evaluation 表达式求值 ====================
// isExpression - True when the text needs evaluation 需要求值时返回 true
// A leading sign alone still denotes a plain number 仅前导符号仍视为普通数字
function isExpression(text) {
    var source = String(text).replace(/\s+/g, "")
    if (source.length === 0) return false
    if (source.charAt(0) === "+" || source.charAt(0) === "-") {
        source = source.slice(1)
    }
    return /[+\-*/()]/.test(source)
}

// evaluate - Recursive descent evaluator, NaN on any malformed input
// 递归下降求值器, 任何非法输入返回 NaN
function evaluate(text) {
    var state = { text: String(text).replace(/\s+/g, ""), index: 0 }
    if (state.text.length === 0) return NaN
    var value = _parseSum(state)
    if (isNaN(value) || !isFinite(value)) return NaN
    if (state.index !== state.text.length) return NaN
    return value
}

function _parseSum(state) {
    var value = _parseProduct(state)
    while (state.index < state.text.length) {
        var operator = state.text.charAt(state.index)
        if (operator === "+") {
            state.index += 1
            value += _parseProduct(state)
        } else if (operator === "-") {
            state.index += 1
            value -= _parseProduct(state)
        } else {
            break
        }
    }
    return value
}

function _parseProduct(state) {
    var value = _parseUnary(state)
    while (state.index < state.text.length) {
        var operator = state.text.charAt(state.index)
        if (operator === "*") {
            state.index += 1
            value *= _parseUnary(state)
        } else if (operator === "/") {
            state.index += 1
            value /= _parseUnary(state)
        } else {
            break
        }
    }
    return value
}

function _parseUnary(state) {
    var character = state.text.charAt(state.index)
    if (character === "+") {
        state.index += 1
        return _parseUnary(state)
    }
    if (character === "-") {
        state.index += 1
        return -_parseUnary(state)
    }
    return _parsePrimary(state)
}

function _parsePrimary(state) {
    var character = state.text.charAt(state.index)
    if (character === "(") {
        state.index += 1
        var value = _parseSum(state)
        if (state.text.charAt(state.index) !== ")") return NaN
        state.index += 1
        return value
    }
    var start = state.index
    while (state.index < state.text.length) {
        var current = state.text.charAt(state.index)
        var isDigit = current >= "0" && current <= "9"
        if (isDigit || current === "." || current === "e" || current === "E") {
            state.index += 1
        } else {
            break
        }
    }
    if (state.index === start) return NaN
    var number = parseFloat(state.text.slice(start, state.index))
    return isNaN(number) ? NaN : number
}
