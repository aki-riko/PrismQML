// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../../.."
import "../../../menus"
import QtQuick  // After library import: unprefixed native types stay unshadowed 置于库import后:去前缀后保原生类型不被库覆盖

// ComboBoxItemDelegate - Default candidate row for ComboBox popups 下拉框默认候选项行
// A ListView delegate cannot receive required properties from its view, so the host
// control arrives through the owning list view's ComboBoxPopupContent.parentControl.
// ListView 委托无法从所属视图接收 required 属性, 因此宿主控件经所属列表视图上的
// ComboBoxPopupContent.parentControl 传入。
MenuDelegate {
    id: menuDelegateItem

    // ==================== Internal Props 内部属性 ====================
    property var _comboControl: ListView.view ? ListView.view.parentControl : null
    // Visible row mapped back to its source model index: a narrowed candidate list
    // must not renumber icons, item data, enabled flags or activated().
    // 可见行映射回源模型下标: 候选被收窄后不得改变图标、项目数据、禁用态与 activated()。
    property int _delegateIndex: _comboControl && _comboControl._search
        ? _comboControl._search.sourceIndex(index) : index

    // ==================== Content 内容 ====================
    text: {
        if (modelData === undefined || modelData === null) return ""
        if (typeof modelData === "object") return modelData.text || modelData.toString()
        return modelData.toString()
    }
    icon: _comboControl ? _comboControl.itemIcon(_delegateIndex) : ""
    selected: _comboControl && _delegateIndex === _comboControl.currentIndex
    itemEnabled: _comboControl ? _comboControl.isItemEnabled(_delegateIndex) : true
    height: _comboControl ? _comboControl.popupItemHeight : Enums.comboBoxMetrics.itemHeight
    onClicked: {
        if (!_comboControl) return
        var oldIndex = _comboControl.currentIndex
        var oldText = _comboControl.currentText
        var clickedIndex = _delegateIndex
        _comboControl.currentIndex = clickedIndex
        _comboControl.currentText = _comboControl._getItemText(clickedIndex)
        _comboControl.activated(clickedIndex)
        _comboControl.textActivated(_comboControl.currentText)
        if (oldIndex !== clickedIndex) _comboControl.indexChanged(clickedIndex)
        if (oldText !== _comboControl.currentText) _comboControl.textChanged(_comboControl.currentText)
        _comboControl.indexUpdated()
        _comboControl.closePopup()
    }
}
