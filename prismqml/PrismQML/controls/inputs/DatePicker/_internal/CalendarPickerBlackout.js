// CalendarPickerBlackout - Date list membership helpers 日期列表归属辅助
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

.pragma library

// pad - Two digit field 两位字段
function pad(value) {
    return value < 10 ? "0" + value : String(value)
}

// key - Stable yyyy-MM-dd identity of a date 日期的 yyyy-MM-dd 稳定标识
function key(date) {
    if (date === null || date === undefined) return ""
    return date.getFullYear() + "-" + pad(date.getMonth() + 1) + "-" + pad(date.getDate())
}

// _list - Normalise a caller supplied date list 规范化调用方传入的日期列表
function _list(dates) {
    if (dates === null || dates === undefined) return []
    return typeof dates.length === "number" ? dates : []
}

// containsDate - True when the list holds the same calendar day 列表是否包含同一自然日
function containsDate(dates, date) {
    var target = key(date)
    if (target === "") return false
    var entries = _list(dates)
    for (var index = 0; index < entries.length; ++index) {
        var entry = entries[index]
        if (entry === null || entry === undefined) continue
        if (entry instanceof Date) {
            if (key(entry) === target) return true
        } else if (String(entry) === target) {
            return true
        }
    }
    return false
}

// toggleDate - Add or remove one day, returning a new list 增删一天并返回新列表
function toggleDate(dates, date) {
    var target = key(date)
    if (target === "") return _list(dates).slice()
    var entries = _list(dates)
    var result = []
    var removed = false
    for (var index = 0; index < entries.length; ++index) {
        var entry = entries[index]
        var sameDay = entry instanceof Date
            ? key(entry) === target : String(entry) === target
        if (sameDay) {
            removed = true
            continue
        }
        result.push(entry)
    }
    if (!removed) result.push(new Date(date.getFullYear(), date.getMonth(), date.getDate()))
    return result
}
