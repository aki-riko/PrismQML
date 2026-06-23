// ComboBoxMethods.js - Qt-style migration methods ComboBox迁移方法
// Extracted from ComboBoxCore to reduce file size 从ComboBoxCore提取以减少文件大小

// @ts-nocheck
// pragma library - QML shared library QML共享库

// ==================== Item Management 项目管理 ====================

function count(model) {
    return model ? model.length : 0
}

function addItem(control, text, userData) {
    var newModel = control.model.slice()
    newModel.push(text)
    control.model = newModel
    if (control.model.length === 1) control.currentIndex = 0
}

function addItems(control, texts) {
    var newModel = control.model.slice()
    for (var i = 0; i < texts.length; i++) {
        newModel.push(texts[i])
    }
    control.model = newModel
    if (control.currentIndex < 0 && control.model.length > 0) control.currentIndex = 0
}

function removeItem(control, index) {
    if (index < 0 || index >= control.model.length) return
    var newModel = control.model.slice()
    newModel.splice(index, 1)
    control.model = newModel
    if (index < control.currentIndex) control.currentIndex--
    else if (index === control.currentIndex) {
        if (control.currentIndex >= control.model.length) control.currentIndex = control.model.length - 1
    }
}

function insertItem(control, index, text, userData) {
    if (index < 0) index = 0
    if (index > control.model.length) index = control.model.length
    var newModel = control.model.slice()
    newModel.splice(index, 0, text)
    control.model = newModel
    if (index <= control.currentIndex) control.currentIndex++
}

// Insert multiple items at index 批量插入多项
function insertItems(control, index, texts) {
    if (index < 0) index = 0
    if (index > control.model.length) index = control.model.length
    var newModel = control.model.slice()
    for (var i = 0; i < texts.length; i++) {
        newModel.splice(index + i, 0, texts[i])
    }
    control.model = newModel
    if (index <= control.currentIndex) control.currentIndex += texts.length
}

function clear(control) {
    control.model = []
    control.currentIndex = -1
}

// ==================== Text Methods 文本方法 ====================

function itemText(model, index) {
    if (index < 0 || index >= model.length) return ""
    return model[index]
}

function findText(model, text) {
    for (var i = 0; i < model.length; i++) {
        if (model[i] === text) return i
    }
    return -1
}

function setCurrentText(control, text) {
    var idx = findText(control.model, text)
    if (idx >= 0) control.currentIndex = idx
}

function setItemText(control, index, text) {
    if (index < 0 || index >= control.model.length) return
    var newModel = control.model.slice()
    if (typeof newModel[index] === 'object') {
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
    if (index < 0 || index >= control.model.length) return undefined
    if (typeof control.model[index] === 'object' && control.model[index].data !== undefined) {
        return control.model[index].data
    }
    return control._itemDataMap[index]
}

function setItemData(control, index, value) {
    if (index < 0 || index >= control.model.length) return
    control._itemDataMap[index] = value
}

function findData(control, data) {
    for (var i = 0; i < control.model.length; i++) {
        if (itemData(control, i) === data) return i
    }
    return -1
}

// ==================== Icon Methods 图标方法 ====================

function itemIcon(control, index) {
    if (index < 0 || index >= control.model.length) return ""
    if (typeof control.model[index] === 'object' && control.model[index].icon !== undefined) {
        return control.model[index].icon
    }
    return control._itemIconMap[index] || ""
}

function setItemIcon(control, index, icon) {
    if (index < 0 || index >= control.model.length) return
    control._itemIconMap[index] = icon
}

// ==================== Enabled State Methods 启用状态方法 ====================

function setItemEnabled(control, index, isEnabled) {
    if (index < 0 || index >= control.model.length) return
    control._itemEnabledMap[index] = isEnabled
}

function isItemEnabled(control, index) {
    if (index < 0 || index >= control.model.length) return true
    if (typeof control.model[index] === 'object' && control.model[index].enabled !== undefined) {
        return control.model[index].enabled
    }
    return control._itemEnabledMap[index] !== false
}

// ==================== Helper Methods 辅助方法 ====================

function getItemText(model, index) {
    if (index < 0 || index >= model.length) return ""
    if (typeof model[index] === 'object') {
        return model[index].text || model[index].toString()
    }
    return model[index].toString()
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
