// ComboBoxMethods.js - Qt-style migration methods ComboBox迁移方法
// Extracted from ComboBoxCore to reduce file size 从ComboBoxCore提取以减少文件大小

// @ts-nocheck
// pragma library - QML shared library QML共享库

// ==================== Item Management 项目管理 ====================

function count(model) {
    return model ? model.length : 0
}

function _copyMapWithShift(source, startIndex, delta, removedIndex) {
    var result = ({})
    for (var key in source) {
        var index = Number(key)
        if (index === removedIndex) continue
        var targetIndex = index >= startIndex ? index + delta : index
        result[targetIndex] = source[key]
    }
    return result
}

function _shiftMetadata(control, startIndex, delta, removedIndex) {
    control._itemDataMap = _copyMapWithShift(control._itemDataMap, startIndex, delta, removedIndex)
    control._itemIconMap = _copyMapWithShift(control._itemIconMap, startIndex, delta, removedIndex)
    control._itemEnabledMap = _copyMapWithShift(control._itemEnabledMap, startIndex, delta, removedIndex)
}

function _setMapValue(source, index, value) {
    var result = ({})
    for (var key in source) result[key] = source[key]
    result[index] = value
    return result
}

function _hasMapValue(source, index) {
    return source && source.hasOwnProperty(index)
}

function addItem(control, text, userData) {
    var newModel = (control._safeModel || []).slice()
    var newIndex = newModel.length
    newModel.push(text)
    control.model = newModel
    if (userData !== undefined) setItemData(control, newIndex, userData)
    if ((control._safeModel || []).length === 1) control.currentIndex = 0
}

function addItems(control, texts) {
    var newModel = (control._safeModel || []).slice()
    var safeTexts = texts && typeof texts.length === "number" ? texts : []
    for (var i = 0; i < safeTexts.length; i++) {
        newModel.push(safeTexts[i])
    }
    control.model = newModel
    if (control.currentIndex < 0 && (control._safeModel || []).length > 0) control.currentIndex = 0
}

function removeItem(control, index) {
    if (index < 0 || index >= (control._safeModel || []).length) return
    var newModel = (control._safeModel || []).slice()
    newModel.splice(index, 1)
    control.model = newModel
    _shiftMetadata(control, index + 1, -1, index)
    if (index < control.currentIndex) control.currentIndex--
    else if (index === control.currentIndex) {
        if (control.currentIndex >= (control._safeModel || []).length) control.currentIndex = (control._safeModel || []).length - 1
    }
}

function insertItem(control, index, text, userData) {
    if (index < 0) index = 0
    if (index > (control._safeModel || []).length) index = (control._safeModel || []).length
    var newModel = (control._safeModel || []).slice()
    newModel.splice(index, 0, text)
    _shiftMetadata(control, index, 1, -1)
    control.model = newModel
    if (userData !== undefined) setItemData(control, index, userData)
    if (index <= control.currentIndex) control.currentIndex++
}

// Insert multiple items at index 批量插入多项
function insertItems(control, index, texts) {
    if (index < 0) index = 0
    if (index > (control._safeModel || []).length) index = (control._safeModel || []).length
    var newModel = (control._safeModel || []).slice()
    var safeTexts = texts && typeof texts.length === "number" ? texts : []
    for (var i = 0; i < safeTexts.length; i++) {
        newModel.splice(index + i, 0, safeTexts[i])
    }
    _shiftMetadata(control, index, safeTexts.length, -1)
    control.model = newModel
    if (index <= control.currentIndex) control.currentIndex += safeTexts.length
}

function clear(control) {
    control.model = []
    control._itemDataMap = ({})
    control._itemIconMap = ({})
    control._itemEnabledMap = ({})
    control.currentIndex = -1
}

// ==================== Text Methods 文本方法 ====================

function itemText(model, index) {
    return getItemText(model, index)
}

function findText(model, text) {
    if (!model || typeof model.length !== "number") return -1
    for (var i = 0; i < model.length; i++) {
        if (getItemText(model, i) === text) return i
    }
    return -1
}

function setCurrentText(control, text) {
    var idx = findText(control._safeModel || [], text)
    if (idx >= 0) control.currentIndex = idx
}

function setItemText(control, index, text) {
    if (index < 0 || index >= (control._safeModel || []).length) return
    var newModel = (control._safeModel || []).slice()
    if (newModel[index] && typeof newModel[index] === 'object') {
        newModel[index].text = text
    } else {
        newModel[index] = text
    }
    control.model = newModel
}

// ==================== Data Methods 数据方法 ====================

function currentData(control) {
    return itemData(control, control.currentIndex)
}

function itemData(control, index) {
    if (index < 0 || index >= (control._safeModel || []).length) return undefined
    if (_hasMapValue(control._itemDataMap, index)) return control._itemDataMap[index]
    var item = (control._safeModel || [])[index]
    if (item && typeof item === 'object' && item.data !== undefined) {
        return item.data
    }
    return undefined
}

function setItemData(control, index, value) {
    if (index < 0 || index >= (control._safeModel || []).length) return
    control._itemDataMap = _setMapValue(control._itemDataMap, index, value)
}

function findData(control, data) {
    for (var i = 0; i < (control._safeModel || []).length; i++) {
        if (itemData(control, i) === data) return i
    }
    return -1
}

// ==================== Icon Methods 图标方法 ====================

function itemIcon(control, index) {
    if (index < 0 || index >= (control._safeModel || []).length) return ""
    if (_hasMapValue(control._itemIconMap, index)) return control._itemIconMap[index]
    var item = (control._safeModel || [])[index]
    if (item && typeof item === 'object' && item.icon !== undefined) {
        return item.icon
    }
    return ""
}

function setItemIcon(control, index, icon) {
    if (index < 0 || index >= (control._safeModel || []).length) return
    control._itemIconMap = _setMapValue(control._itemIconMap, index, icon)
}

// ==================== Enabled State Methods 启用状态方法 ====================

function setItemEnabled(control, index, isEnabled) {
    if (index < 0 || index >= (control._safeModel || []).length) return
    control._itemEnabledMap = _setMapValue(control._itemEnabledMap, index, isEnabled)
}

function isItemEnabled(control, index) {
    if (index < 0 || index >= (control._safeModel || []).length) return true
    if (_hasMapValue(control._itemEnabledMap, index)) return control._itemEnabledMap[index]
    var item = (control._safeModel || [])[index]
    if (item && typeof item === 'object' && item.enabled !== undefined) {
        return item.enabled
    }
    return true
}

// ==================== Helper Methods 辅助方法 ====================

function getItemText(model, index) {
    if (!model || typeof model.length !== "number" || index < 0 || index >= model.length) return ""
    var item = model[index]
    if (item === null || item === undefined) return ""
    if (typeof item === 'object') {
        return item.text || item.toString()
    }
    return item.toString()
}

function hasMatchingItems(model, searchText) {
    if (!searchText) return false
    var lowerSearch = searchText.toLowerCase()
    for (var i = 0; i < model.length; i++) {
        var text = getItemText(model, i).toLowerCase()
        if (text.indexOf(lowerSearch) !== -1) {
            return true
        }
    }
    return false
}
