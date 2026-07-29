// @ts-nocheck
// DateTimeHelpers.js - Model builders for DateTimePicker 日期时间选择器模型构建

// ==================== Display Helpers 显示辅助 ====================

function getMonthName(translator, m) {
    var keys = ["january", "february", "march", "april", "may", "june", 
                "july", "august", "september", "october", "november", "december"]
    return translator.tr(keys[m - 1])
}

function localeNameForLanguage(language, systemLocaleName) {
    var normalizedLanguage = String(language || "en").replace("-", "_")
    var normalizedSystem = String(systemLocaleName || "").replace("-", "_")
    if (normalizedLanguage.indexOf("_") >= 0) return normalizedLanguage
    if (normalizedSystem.split("_")[0] === normalizedLanguage) return normalizedSystem
    return normalizedLanguage
}

function dateFieldOrder(dateFormat) {
    var fieldByToken = { "y": "year", "M": "month", "d": "day" }
    var order = []
    var quoted = false
    for (var i = 0; i < dateFormat.length; i++) {
        var token = dateFormat.charAt(i)
        if (token === "'") {
            if (dateFormat.charAt(i + 1) === "'") i++
            else quoted = !quoted
            continue
        }
        var field = quoted ? "" : fieldByToken[token]
        if (field && order.indexOf(field) < 0) order.push(field)
    }
    return order.length === 3 ? order : ["year", "month", "day"]
}

function usesDateUnitSuffixes(language) {
    var languageCode = String(language || "").replace("-", "_").split("_")[0]
    return ["zh", "ja", "ko"].indexOf(languageCode) >= 0
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

function buildMonthModel(useNumericMonth, suffix, translator) {
    var arr = []
    if (useNumericMonth) {
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

function isDateFieldVisible(control, field) {
    if (field === "year") return control._showYear
    if (field === "month") return control._showMonth
    if (field === "day") return control._showDay
    return false
}

function buildDateFieldModel(control, field) {
    if (field === "year") return control._buildYearModel()
    if (field === "month") return control._buildMonthModel()
    if (field === "day") return control._buildDayModel()
    return []
}

function dateFieldIndex(control, field) {
    if (field === "year") return control._tempYear - control.minYear
    if (field === "month") return control._tempMonth - 1
    if (field === "day") return control._tempDay - 1
    return 0
}

function setDateFieldIndex(control, field, index) {
    if (field === "year") {
        control._tempYear = control.minYear + index
        control._updateDayWheel()
    } else if (field === "month") {
        control._tempMonth = index + 1
        control._updateDayWheel()
    } else if (field === "day") {
        control._tempDay = index + 1
    }
}

// ==================== Display Model 显示模型 ====================

function buildDateDisplayPart(control, translator, field) {
    var hasValue = false
    var text = translator.tr(field)
    if (field === "year") {
        hasValue = control.year > 0
        if (hasValue) text = String(control.year) + control._yearSuffix
    } else if (field === "month") {
        hasValue = control.month > 0
        if (hasValue) text = control._usesDateUnitSuffixes
            ? String(control.month) + control._monthSuffix
            : getMonthName(translator, control.month)
    } else if (field === "day") {
        hasValue = control.day > 0
        if (hasValue) text = String(control.day) + control._daySuffix
    }
    return { text: text, hasValue: hasValue }
}

function buildHourDisplayPart(control, translator) {
    var displayHour = control.hour
    if (control._is12Hour && control.hour >= 0) {
        displayHour = control.hour % 12
        if (displayHour === 0) displayHour = 12
    }
    return {
        text: control.hour >= 0 ? displayHour + control._hourSuffix : translator.tr("hour"),
        hasValue: control.hour >= 0
    }
}

function buildTimeDisplayModel(control, translator) {
    var model = []
    if (control._showHour) model.push(buildHourDisplayPart(control, translator))
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
    return model
}

function buildDisplayModel(control, translator) {
    var model = []
    if (control._hasDate) {
        for (var i = 0; i < control._dateFieldOrder.length; i++) {
            var field = control._dateFieldOrder[i]
            if (isDateFieldVisible(control, field)) {
                model.push(buildDateDisplayPart(control, translator, field))
            }
        }
    }
    return control._hasTime ? model.concat(buildTimeDisplayModel(control, translator)) : model
}
