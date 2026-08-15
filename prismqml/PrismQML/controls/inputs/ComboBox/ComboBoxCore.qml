// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import ".."
import "../../containers"
import "./_internal"
import "./_internal/ComboBoxMethods.js" as ComboBoxMethods
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// ComboBoxCore - Dropdown base class 下拉框基类
// ComboBox series extend this ComboBox系列继承此基类
Widget {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property var model: []  // Text array or object array 文本数组或对象数组
    property int currentIndex: -1
    property string currentText: ""
    property string placeholderText: {
        Translator._v
        return Translator.tr("placeholder_select")
    }
    property bool editable: false
    property bool useDefaultContent: true
    property int style: 0  // 0 = style_default
    property int feature: 0  // 0 = feature_none
    property int popupPlacement: 0  // Popup direction 弹出方向
    property int maxVisibleItems: -1  // Qt-style max visible items Qt风格最大可见项数
    property color accentColor: Enums.accentColor
    property int radius: Enums.surfaceRadius(Enums.radius.small)
    property bool focused: _inputFocused
    property bool isOpen: false
    property bool showFocusedBorder: style === 0
    property color focusedBorderColorLight: Enums.accentColor
    property color focusedBorderColorDark: Enums.accentColor
    property bool acceptWheel: false  // Whether to intercept wheel events 是否拦截滚轮事件
    property bool popupCloseOnClickOutside: true  // Close on click outside 点击外部关闭
    property Component popupContent: defaultPopupContent  // Popup content component 弹出内容组件
    property Component popupDelegate: defaultDelegate  // Delegate for items (subclass override) 项目委托
    property int popupItemHeight: Enums.controlSize.inputHeight  // Item height 项目高度

    // ==================== Internal Props 内部属性 ====================
    // Internal data storage 内部数据存储
    property var _itemDataMap: ({})  // {index: data}
    property var _itemIconMap: ({})  // {index: icon}
    property var _itemEnabledMap: ({})  // {index: enabled}
    property var _methods: ComboBoxMethods
    property bool _popupContentRequested: false
    property alias _popup: comboContent.popup
    property alias editableInput: comboContent.editableInput
    property alias mouseArea: comboContent.mouseArea
    property alias editableClickArea: comboContent.editableClickArea
    property alias comboTextMeasureLoader: comboContent.comboTextMeasureLoader

    // ==================== Readonly State 只读状态 ====================
    // Editable mode input focus state editable模式输入框聚焦状态
    readonly property bool _inputFocused: editable && editableInput.activeFocus
    // MouseArea disabled during close, read state directly 关闭期间直接读取状态
    // Editable mode needs to check both input and arrow area hover editable模式检测两个区域
    readonly property bool hovered: mouseArea.containsMouse || (editable && editableClickArea.containsMouse)
    readonly property bool pressed: mouseArea.pressed
    readonly property bool popupVisible: isOpen || _popup.isClosing
    readonly property color focusedBorderColor: Enums.isDark ? focusedBorderColorDark : focusedBorderColorLight
    readonly property int selectionStart: editable ? editableInput.selectionStart : 0
    readonly property int selectionEnd: editable ? editableInput.selectionEnd : 0
    readonly property string selectedText: editable ? editableInput.selectedText : ""
    readonly property var _safeModel:
        model === null || model === undefined ? []
        : (typeof model.length === "number" ? model : [])

    // Default delegate 默认委托
    property Component defaultDelegate: Component {
        MenuDelegate {
            id: menuDelegateItem

            property var _comboControl: ListView.view ? ListView.view.parentControl : null

            text: {
                if (modelData === undefined || modelData === null) return ""
                if (typeof modelData === "object") return modelData.text || modelData.toString()
                return modelData.toString()
            }
            icon: _comboControl ? _comboControl.itemIcon(index) : ""
            selected: _comboControl && index === _comboControl.currentIndex
            itemEnabled: _comboControl ? _comboControl.isItemEnabled(index) : true
            height: _comboControl ? _comboControl.popupItemHeight : Enums.comboBoxMetrics.itemHeight
            onClicked: {
                if (!_comboControl) return
                var oldIndex = _comboControl.currentIndex
                var oldText = _comboControl.currentText
                _comboControl.currentIndex = index
                _comboControl.currentText = _comboControl._getItemText(index)
                _comboControl.activated(index)
                _comboControl.textActivated(_comboControl.currentText)
                if (oldIndex !== index) _comboControl.indexChanged(index)
                if (oldText !== _comboControl.currentText) _comboControl.textChanged(_comboControl.currentText)
                _comboControl.indexUpdated()
                _comboControl.closePopup()
            }
        }
    }

    // Default popup content (uses popupDelegate) 默认弹出内容(使用popupDelegate)
    property Component defaultPopupContent: Component {
        ComboBoxPopupContent {
            control: control
        }
    }

    // ==================== Signals 信号 ====================
    signal activated(int index)
    signal textActivated(string text)  // Qt-style signal Qt风格信号
    signal indexChanged(int index)  // Migration signal - avoid currentIndex conflict 迁移信号-避免冲突
    signal textChanged(string text)  // Migration signal - avoid currentText conflict 迁移信号-避免冲突
    signal indexUpdated()  // Internal alias 内部别名
    signal wheelScrolled(real delta)  // Wheel event for subclass 滚轮事件供子类使用
    signal textEdited(string text)  // Editable mode signal editable模式信号

    // ==================== Public Methods 公开方法 ====================
    function count() { return _methods.count(_safeModel || []) }
    function addItem(text, userData) { _methods.addItem(control, text, userData) }
    function addItems(texts) { _methods.addItems(control, texts) }
    function removeItem(index) { _methods.removeItem(control, index) }
    function insertItem(index, text, userData) { _methods.insertItem(control, index, text, userData) }
    function insertItems(index, texts) { _methods.insertItems(control, index, texts) }  // Batch insert 批量插入
    function clear() { _methods.clear(control) }
    function clearEditText() { return _dispatchEditAction("clear", true) }
    function selectAll() { return _dispatchEditAction("selectAll", false) }
    function undo() { return _dispatchEditAction("undo", true) }
    function redo() { return _dispatchEditAction("redo", true) }
    function copy() { return _dispatchEditAction("copy", false) }
    function cut() { return _dispatchEditAction("cut", true) }
    function paste() { return _dispatchEditAction("paste", true) }
    function showPopup() { openPopup() }
    function hidePopup() { closePopup() }
    function itemText(index) { return _methods.itemText(_safeModel || [], index) }
    function findText(text) { return _methods.findText(_safeModel || [], text) }
    function setCurrentText(text) { _methods.setCurrentText(control, text) }
    function setItemText(index, text) { _methods.setItemText(control, index, text) }
    function currentData() { return _methods.currentData(control) }
    function itemData(index) { return _methods.itemData(control, index) }
    function setItemData(index, value) { _methods.setItemData(control, index, value) }
    function findData(data) { return _methods.findData(control, data) }
    function itemIcon(index) { return _methods.itemIcon(control, index) }
    function setItemIcon(index, icon) { _methods.setItemIcon(control, index, icon) }
    function setItemEnabled(index, isEnabled) { _methods.setItemEnabled(control, index, isEnabled) }
    function isItemEnabled(index) { return _methods.isItemEnabled(control, index) }

    function openPopup() {
        // Prevent duplicate open 防止重复打开
        if (isOpen) return

        _popupContentRequested = true
        // Calculate popup width: max(content width, control width) 弹出宽度：取内容宽度和控件宽度的最大值
        var contentW = _calcContentWidth()
        _popup.popupWidth = Math.max(contentW, control.width)
        // Let PopupWindowCore add its content padding exactly once.
        // 由 PopupWindowCore 统一补入一次内容内边距。
        var itemCount = (_safeModel || []).length
        var maxContentHeight = maxVisibleItems > 0
            ? maxVisibleItems * popupItemHeight
            : Math.max(0, Enums.comboBoxMetrics.popupMaxHeight
                - 2 * _popup.contentPadding)
        _popup.implicitContentHeight = Math.min(
            itemCount * popupItemHeight, maxContentHeight)
        _popup.openAtControl(control)
        isOpen = true
    }

    function closePopup() {
        if (!isOpen) return
        isOpen = false
        _popup.close()
    }

    function getCurrentIndex() { return currentIndex }
    function isEnabled() { return enabled }

    // ==================== Internal Methods 内部方法 ====================
    function _dispatchEditAction(actionName, mutatesText) {
        if (!editable || !useDefaultContent || !enabled
                || typeof editableInput[actionName] !== "function") return false
        var previousText = editableInput.text
        editableInput[actionName]()
        if (mutatesText && editableInput.text !== previousText) {
            if (currentIndex !== -1) currentIndex = -1
            if (currentText !== editableInput.text) {
                currentText = editableInput.text
                textEdited(currentText)
            }
        }
        return true
    }

    function _getItemText(index) { return _methods.getItemText(_safeModel || [], index) }
    function _hasMatchingItems(searchText) { return _methods.hasMatchingItems(_safeModel || [], searchText) }
    function _syncCurrentTextFromSelection() {
        if (editable && currentIndex === -1) return
        var safeModel = _safeModel || []
        var nextText = currentIndex >= 0 && currentIndex < safeModel.length
            ? _getItemText(currentIndex) : ""
        if (currentText !== nextText) currentText = nextText
    }

    // Calculate max content width from model items 根据model项计算最大内容宽度
    function _calcContentWidth() {
        var comboTextMeasure = comboTextMeasureLoader.item
        if (!comboTextMeasure) return 0
        var maxW = 0
        // Total horizontal padding: contentContainer margins(xs*2) + itemBg margins(xs*2) + text margins(l*2)
        // 总水平内边距：内容容器边距(xs*2) + 项背景边距(xs*2) + 文本边距(l*2)
        var itemPadding = Enums.spacing.l * 2 + Enums.spacing.xs * 4
        var safeModel = _safeModel || []
        for (var i = 0; i < safeModel.length; i++) {
            var text = _getItemText(i)
            if (!text) continue
            comboTextMeasure.text = text
            maxW = Math.max(maxW, comboTextMeasure.advanceWidth + itemPadding)
        }
        return Math.ceil(maxW)
    }

    // ==================== Size 尺寸 ====================
    // Content size (inherited from Widget) 内容尺寸（继承自Widget）
    contentWidth: Enums.comboBoxMetrics.defaultWidth
    contentHeight: Enums.controlSize.inputHeight

    onCurrentIndexChanged: _syncCurrentTextFromSelection()
    onModelChanged: _syncCurrentTextFromSelection()
    Component.onCompleted: _syncCurrentTextFromSelection()

    // ==================== Content 内容 ====================
    ComboBoxCoreContent {
        id: comboContent
        comboControl: control
    }
}
