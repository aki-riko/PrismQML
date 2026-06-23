// @ts-nocheck
// DateTimeHelpers.js - Model builders for DateTimePicker 日期时间选择器模型构建

// ==================== Display Helpers 显示辅助 ====================

function getMonthName(translator, m) {
    var keys = ["january", "february", "march", "april", "may", "june", 
                "july", "august", "september", "october", "november", "december"]
    return translator.tr(keys[m - 1])
}

function pad(n) { 
    return n < 10 ? "0" + n : String(n) 
}

function getDaysInMonth(y, m) { 
    return new Date(y, m, 0).getDate() 
}

function get24Hour(h12, isAm) {
    if (isAm) return h12 === 12 ? 0 : h12
    return h12 === 12 ? 12 : h12 + 12
}

// ==================== Model Builders 模型构建 ====================

function buildYearModel(minYear, maxYear, suffix) {
    var arr = []
    for (var i = minYear; i <= maxYear; i++) arr.push(i + suffix)
    return arr
}

function buildMonthModel(yearFirst, suffix, translator) {
    var arr = []
    if (yearFirst) {
        for (var i = 1; i <= 12; i++) arr.push(i + suffix)
    } else {
        for (var i = 1; i <= 12; i++) arr.push(getMonthName(translator, i))
    }
    return arr
}

function buildDayModel(year, month, suffix) {
    var maxDays = getDaysInMonth(year, month)
    var arr = []
    for (var i = 1; i <= maxDays; i++) arr.push(i + suffix)
    return arr
}

function buildHour24Model(suffix) {
    var arr = []
    for (var i = 0; i < 24; i++) arr.push(i + suffix)
    return arr
}

function buildHour12Model(suffix) {
    var arr = []
    for (var i = 1; i <= 12; i++) arr.push(i + suffix)
    return arr
}

function buildMinuteModel(suffix) {
    var arr = []
    for (var i = 0; i < 60; i++) arr.push(pad(i) + suffix)
    return arr
}

function buildSecondModel(suffix) {
    var arr = []
    for (var i = 0; i < 60; i++) arr.push(pad(i) + suffix)
    return arr
}

// ==================== Display Model 显示模型 ====================

function buildDisplayModel(control, translator) {
    var model = []
    
    if (control._hasDate) {
        if (control._yearFirst) {
            if (control._showYear) model.push({ 
                text: control.year > 0 ? control.year + control._yearSuffix : translator.tr("year"), 
                hasValue: control.year > 0 
            })
            if (control._showMonth) model.push({ 
                text: control.month > 0 ? control.month + control._monthSuffix : translator.tr("month"), 
                hasValue: control.month > 0 
            })
            if (control._showDay) model.push({ 
                text: control.day > 0 ? control.day + control._daySuffix : translator.tr("day"), 
                hasValue: control.day > 0 
            })
        } else {
            if (control._showMonth) model.push({ 
                text: control.month > 0 ? getMonthName(translator, control.month) : translator.tr("month"), 
                hasValue: control.month > 0 
            })
            if (control._showDay) model.push({ 
                text: control.day > 0 ? String(control.day) : translator.tr("day"), 
                hasValue: control.day > 0 
            })
            if (control._showYear) model.push({ 
                text: control.year > 0 ? String(control.year) : translator.tr("year"), 
                hasValue: control.year > 0 
            })
        }
    }
    
    if (control._hasTime) {
        if (control._showHour) {
            var displayHour = control.hour
            if (control._is12Hour && control.hour >= 0) {
                displayHour = control.hour % 12
                if (displayHour === 0) displayHour = 12
            }
            model.push({ 
                text: control.hour >= 0 ? displayHour + control._hourSuffix : translator.tr("hour"), 
                hasValue: control.hour >= 0 
            })
        }
        if (control._showMinute) model.push({ 
            text: control.minute >= 0 ? pad(control.minute) + control._minuteSuffix : translator.tr("minute"), 
            hasValue: control.minute >= 0 
        })
        if (control._showSecond) model.push({ 
            text: control.second >= 0 ? pad(control.second) + control._secondSuffix : translator.tr("second"), 
            hasValue: control.second >= 0 
        })
        if (control._is12Hour) model.push({ 
            text: control.hour >= 0 ? (control.hour < 12 ? control._amText : control._pmText) : control._amText, 
            hasValue: control.hour >= 0 
        })
    }
    
    return model
}
