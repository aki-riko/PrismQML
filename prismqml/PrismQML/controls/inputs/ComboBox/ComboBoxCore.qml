// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import ".."
import "../../containers"
import "./_internal"
import "./_internal/ComboBoxMethods.js" as ComboBoxMethods
import QtQuick  // After library import: unprefixed native types stay unshadowed 置于库import后:去前缀后保原生类型不被库覆盖

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
    // Optional explicit popup width. Zero keeps the content/control auto sizing.
    // 可选的显式弹层宽度；为 0 时保持内容/控件自动计算。
    property int popupWidthOverride: 0
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
    property alias defaultPopupContent: coreActions.defaultPopupContent
    property alias _popup: comboContent.popup
    property alias _search: searchState
    property alias editableInput: comboContent.editableInput
    property alias mouseArea: comboContent.mouseArea
    property alias editableClickArea: comboContent.editableClickArea
    property alias comboTextMeasureLoader: comboContent.comboTextMeasureLoader

    // ==================== Readonly State 只读状态 ====================
    // Editable mode input focus state editable模式输入框聚焦状态
    readonly property bool _inputFocused: editable && editableInput.activeFocus
    // MouseArea disabled during close, read state directly 关闭期间直接读取状态
    // Editable mode needs to check both input and arrow area hover editable模式检测两个区域
    // Touch has no hover preview: on touch the hover treatment follows the press. Mapping at
    // the source covers every consumer (ComboBoxStyleHelper + ComboBoxCoreContent).
    // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效; 在源头映射可覆盖全部消费者。
    readonly property bool hovered: Touch.feedback(
        mouseArea.containsMouse || (editable && editableClickArea.containsMouse),
        mouseArea.pressed || (editable && editableClickArea.pressed)
    )
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
        ComboBoxItemDelegate {}
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
    function clearEditText() { return coreActions._dispatchEditAction("clear", true) }
    function selectAll() { return coreActions._dispatchEditAction("selectAll", false) }
    function undo() { return coreActions._dispatchEditAction("undo", true) }
    function redo() { return coreActions._dispatchEditAction("redo", true) }
    function copy() { return coreActions._dispatchEditAction("copy", false) }
    function cut() { return coreActions._dispatchEditAction("cut", true) }
    function paste() { return coreActions._dispatchEditAction("paste", true) }
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
        _popup.popupWidth = popupWidthOverride > 0
            ? popupWidthOverride : Math.max(contentW, control.width)
        // Let PopupWindowCore add its content padding exactly once.
        // 由 PopupWindowCore 统一补入一次内容内边距。
        // Reserve room for the candidates actually shown, which the type-to-search
        // filter may have narrowed. 只为实际可见的候选预留高度, 输入即搜索可能已收窄候选。
        var itemCount = _search.visibleModel.length
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

    function _getItemText(index) { return _methods.getItemText(_safeModel || [], index) }
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
    // Replacing the whole model may leave the derived model binding one turn
    // behind inside this notification, so the sync above can still read the
    // previous list and keep a stale currentText whenever currentIndex did not
    // change. Re-calibrate once on the next turn to cover that path.
    // 整表替换模型时，本次通知回调里可能仍读到替换前的模型；若 currentIndex 恰好没变，
    // 上面那次同步会沿用旧文本。下一拍再校准一次，覆盖这条路径。
    onModelChanged: {
        _syncCurrentTextFromSelection()
        Qt.callLater(_syncCurrentTextFromSelection)
    }
    Component.onCompleted: _syncCurrentTextFromSelection()
    // Editable mode keeps the candidate list and the control's own focus state in
    // step: opening the list focuses the input, and losing that focus dismisses the
    // list, so the control can never show itself as unfocused while the list stays
    // open. Non-editable dropdowns keep the native surface's own focus handling.
    // 可编辑模式让候选列表与控件自身聚焦态保持一致: 展开即聚焦输入框, 失焦即收起候选,
    // 因此不会出现控件已失焦而候选仍展开的状态; 非可编辑下拉维持原生表面的焦点处理。
    onIsOpenChanged: {
        if (isOpen && editable && useDefaultContent) editableInput.forceActiveFocus()
    }

    // ==================== Content 内容 ====================
    ComboBoxCoreActions {
        id: coreActions
        comboControl: control
    }

    // Type-to-search state shared by the editable input, the candidate list and the
    // delegate's index mapping. 输入即搜索状态, 由可编辑输入框、候选列表与委托下标映射共用。
    ComboBoxSearchState {
        id: searchState

        model: control._safeModel
        open: control.isOpen
        onOpenRequested: control.openPopup()
    }

    ComboBoxCoreContent {
        id: comboContent
        comboControl: control
    }

    // The candidate surface deliberately takes no focus in editable mode, so its own
    // focus-loss guard can never fire; the input owns that state and closes here.
    // 可编辑模式的候选表面刻意不持有焦点, 其自身的失焦守卫永远不会触发;
    // 该状态由输入框持有, 因此在这里收起候选。
    Connections {
        function onActiveFocusChanged() {
            if (!editable || !useDefaultContent || editableInput.activeFocus) return
            if (isOpen) closePopup()
        }

        target: editableInput
    }
}
