// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import "../../.."
import ".."
import "../../../effects"
import QtQuick.Effects
import "../../data"
import "../../icons"
import "../../utils"
import "../../containers"
import "../../menus"
import "./_internal"
import "./_internal/ComboBoxMethods.js" as ComboBoxMethods
import "../_internal" as InputsInternal
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// ComboBoxCore - Dropdown base class 下拉框基类
// ComboBox series extend this ComboBox系列继承此基类
Widget {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property var model: []  // Text array or object array 文本数组或对象数组
    property int currentIndex: -1
    property string currentText: currentIndex >= 0 && currentIndex < model.length ? _getItemText(currentIndex) : ""
    property string placeholderText: "Select"
    property bool editable: false
    property bool useDefaultContent: true
    property int style: 0  // 0 = style_default
    property int feature: 0  // 0 = feature_none
    property int popupPlacement: 0  // Popup direction 弹出方向
    property int maxVisibleItems: -1  // Qt-style max visible items Qt风格最大可见项数
    property color accentColor: Enums.accentColor
    
    // ==================== Focus State 焦点状态 ====================
    // Editable mode input focus state editable模式输入框聚焦状态
    readonly property bool _inputFocused: editable && editableInput.activeFocus
    property bool focused: _inputFocused
    
    // Internal data storage 内部数据存储
    property var _itemDataMap: ({})  // {index: data}
    property var _itemIconMap: ({})  // {index: icon}
    property var _itemEnabledMap: ({})  // {index: enabled}
    
    // ==================== Import Methods Module 导入方法模块 ====================
    property var _methods: ComboBoxMethods
    
    // ==================== Qt-Style Migration Methods Qt风格迁移方法 ====================
    function count() { return _methods.count(model) }
    function addItem(text, userData) { _methods.addItem(control, text, userData) }
    function addItems(texts) { _methods.addItems(control, texts) }
    function removeItem(index) { _methods.removeItem(control, index) }
    function insertItem(index, text, userData) { _methods.insertItem(control, index, text, userData) }
    function insertItems(index, texts) { _methods.insertItems(control, index, texts) }  // Batch insert 批量插入
    function clear() { _methods.clear(control) }
    
    // Show popup 显示下拉列表
    function showPopup() { openPopup() }

    // Hide popup 隐藏下拉列表
    function hidePopup() { closePopup() }
    function itemText(index) { return _methods.itemText(model, index) }
    function findText(text) { return _methods.findText(model, text) }
    function setCurrentText(text) { _methods.setCurrentText(control, text) }
    function setItemText(index, text) { _methods.setItemText(control, index, text) }
    
    // ==================== Data Methods 数据方法 ====================
    function currentData() { return _methods.currentData(control) }
    function itemData(index) { return _methods.itemData(control, index) }
    function setItemData(index, value) { _methods.setItemData(control, index, value) }
    function findData(data) { return _methods.findData(control, data) }
    
    // ==================== Icon Methods 图标方法 ====================
    function itemIcon(index) { return _methods.itemIcon(control, index) }
    function setItemIcon(index, icon) { _methods.setItemIcon(control, index, icon) }
    
    // ==================== Enabled State Methods 启用状态方法 ====================
    function setItemEnabled(index, isEnabled) { _methods.setItemEnabled(control, index, isEnabled) }
    function isItemEnabled(index) { return _methods.isItemEnabled(control, index) }
    
    // ==================== Internal Helper Methods 内部辅助方法 ====================
    function _getItemText(index) { return _methods.getItemText(model, index) }
    function _hasMatchingItems(searchText) { return _methods.hasMatchingItems(model, searchText) }
    
    // ==================== Signals 信号 ====================
    signal activated(int index)
    signal textActivated(string text)  // Qt-style signal Qt风格信号
    signal indexChanged(int index)  // Migration signal - avoid currentIndex conflict 迁移信号-避免冲突
    signal textChanged(string text)  // Migration signal - avoid currentText conflict 迁移信号-避免冲突
    signal indexUpdated()  // Internal alias 内部别名
    signal wheelScrolled(real delta)  // Wheel event for subclass 滚轮事件供子类使用
    signal textEdited(string text)  // Editable mode signal editable模式信号
    
    // ==================== Readonly State 只读状态 ====================
    // MouseArea disabled during close, read state directly 关闭期间直接读取状态
    // Editable mode needs to check both input and arrow area hover editable模式检测两个区域
    readonly property bool hovered: mouseArea.containsMouse || (editable && editableClickArea.containsMouse)
    readonly property bool pressed: mouseArea.pressed
    readonly property bool popupVisible: isOpen || comboPopup.isClosing
    property bool isOpen: false
    
    // ==================== Focus Border Control 聚焦底线控制 ====================
    property bool showFocusedBorder: style === 0
    property color focusedBorderColorLight: Enums.accentColor
    property color focusedBorderColorDark: Enums.accentColor
    property bool acceptWheel: false  // Whether to intercept wheel events 是否拦截滚轮事件
    readonly property color focusedBorderColor: Enums.isDark ? focusedBorderColorDark : focusedBorderColorLight

    // ==================== Popup Config (subclass override) 弹出窗口配置 ====================
    property bool popupCloseOnClickOutside: true  // Close on click outside 点击外部关闭
    property Component popupContent: defaultPopupContent  // Popup content component 弹出内容组件
    property Component popupDelegate: defaultDelegate  // Delegate for items (subclass override) 项目委托
    property int popupItemHeight: Enums.controlSize.inputHeight  // Item height 项目高度

    // Default delegate 默认委托
    property Component defaultDelegate: Component {
        MenuDelegate {
            id: menuDelegateItem
            text: {
                if (modelData === undefined || modelData === null) return ""
                if (typeof modelData === "object") return modelData.text || modelData.toString()
                return modelData.toString()
            }
            selected: _comboControl && index === _comboControl.currentIndex
            property var _comboControl: ListView.view ? ListView.view.parentControl : null
            onClicked: {
                if (!_comboControl) return
                var oldIndex = _comboControl.currentIndex
                var oldText = _comboControl.currentText
                _comboControl.currentIndex = index
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

    // ==================== Public Methods 公共方法 ====================
    // Calculate max content width from model items 根据model项计算最大内容宽度
    function _calcContentWidth() {
        var maxW = 0
        // Total horizontal padding: contentContainer margins(xs*2) + itemBg margins(xs*2) + text margins(l*2)
        // 总水平内边距：内容容器边距(xs*2) + 项背景边距(xs*2) + 文本边距(l*2)
        var itemPadding = Enums.spacing.l * 2 + Enums.spacing.xs * 4
        for (var i = 0; i < model.length; i++) {
            var text = _getItemText(i)
            if (!text) continue
            comboTextMeasure.text = text
            maxW = Math.max(maxW, comboTextMeasure.advanceWidth + itemPadding)
        }
        return Math.ceil(maxW)
    }

    function openPopup() {
        // Prevent duplicate open 防止重复打开
        if (isOpen) return

        // Calculate popup width: max(content width, control width) 弹出宽度：取内容宽度和控件宽度的最大值
        var contentW = _calcContentWidth()
        comboPopup.popupWidth = Math.max(contentW, control.width)
        // Set reference width for center alignment 设置参考宽度用于居中对齐
        comboPopup.referenceControlWidth = control.width
        // Calculate height from model length 直接用model长度计算高度
        var itemCount = model.length
        var calcHeight = itemCount * Enums.comboBoxMetrics.itemHeight + Enums.comboBoxMetrics.popupPadding
        comboPopup.popupHeight = Math.min(calcHeight, maxVisibleItems > 0 ? (maxVisibleItems * Enums.comboBoxMetrics.itemHeight + Enums.comboBoxMetrics.popupPadding) : Enums.comboBoxMetrics.popupMaxHeight)
        comboPopup.openAtControl(control)
        isOpen = true
    }

    function closePopup() {
        if (!isOpen) return
        isOpen = false
        comboPopup.close()
    }

    function getCurrentIndex() { return currentIndex }
    function isEnabled() { return enabled }

    // ==================== Size 尺寸 ====================
    // Content size (inherited from Widget) 内容尺寸（继承自Widget）
    contentWidth: Enums.comboBoxMetrics.defaultWidth
    contentHeight: Enums.controlSize.inputHeight
    property int radius: Enums.isNeobrutalism ? Enums.neo.radius : Enums.radius.small

    // ==================== Style Helper 样式辅助 ====================
    ComboBoxStyleHelper {
        id: styleHelper
        control: control
    }

    // ==================== Shadow Layer 阴影层 (在背景下方) ====================
    // Fluent: 模糊阴影。Neobrutalism: 硬阴影(纯黑, 展开时转橙强调)。
    RectangularShadow {
        anchors.fill: background
        radius: background.radius
        color: Enums.shadow.level2.color
        blur: Enums.shadow.level2.blur
        offset: Qt.vector2d(0, Enums.shadow.level2.offset)
        visible: style === 0 && !Enums.isNeobrutalism  // Only for default style 仅默认样式
    }

    // Neobrutalism 硬阴影: 复用 NeoShadow 组件; 展开时 accent=true 转橙强调。
    NeoShadow {
        target: background
        visible: Enums.isNeobrutalism && style === 0
        accent: control.popupVisible
        z: background.z - 1
    }

    // ==================== Background 背景 ====================
    Rectangle {
        id: background
        anchors.fill: parent
        radius: control.radius
        clip: false

        layer.enabled: true
        layer.effect: OpacityMask {
            mask: Rectangle {
                width: background.width
                height: background.height
                radius: background.radius
            }
        }

        // ==================== Fluent Design Style Fluent Design样式 ====================
        // Unified with Button/LineEdit controlBg series 与Button/LineEdit统一使用controlBg系列
        // 颜色由 token 层在 neo 下自动返回白面/灰, 无需控件分支。
        color: {
            if (style !== 0) return styleHelper.getBackgroundColor()  // Other styles keep original 其他样式保持原样
            if (!control.enabled) return Enums.stateColor.controlBgDisabled
            if (control.popupVisible) return Enums.stateColor.controlBgPressed
            if (control.pressed) return Enums.stateColor.controlBgPressed
            if (control.hovered) return Enums.stateColor.controlBgHover
            return Enums.stateColor.controlBg
        }

        // Color animation (not applied during close to avoid delay) 颜色动画
        Behavior on color {
            enabled: !comboPopup.isClosing
            ColorAnimation { duration: Enums.duration.fast }
        }

        // Fluent Design 边框:亮/暗主题各用低透明度描边,具体取值见 StateColor.pickerBorder
        border.width: style !== 0 ? 0
            : (Enums.isNeobrutalism ? Enums.neo.borderWidth : Enums.border.thin)
        border.color: Enums.isNeobrutalism && style === 0
            ? (!control.enabled ? Qt.rgba(0, 0, 0, 0.4)
               : (control.popupVisible ? Enums.neo.primary : Enums.neo.borderColor))
            : styleHelper.getBorderColor()
    }
    
    // Focus accent line (ONLY for editable mode) 聚焦主题色底线(仅editable模式)
    FocusLine {
        showLine: !Enums.isNeobrutalism && control.editable && editableInput.activeFocus && showFocusedBorder
        lineColor: control.focusedBorderColor
        parentRadius: control.radius
        visible: !Enums.isNeobrutalism && control.editable && showFocusedBorder
    }
    
    
    // Current text (non-editable mode) 当前文本
    Label {
        anchors.left: parent.left
        anchors.right: arrow.left
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: Enums.spacing.l
        anchors.rightMargin: Enums.spacing.m
        type: Enums.label.type_body
        text: control.currentText !== "" ? control.currentText : control.placeholderText
        color: styleHelper.getTextColor()
        // 需要显式 NoWrap：type_body 默认 WordWrap 与 elide 冲突，造成窄宽下换行而不是尾部省略
        wrapMode: Text.NoWrap
        elide: Text.ElideRight
        clip: true
        visible: !control.editable && control.useDefaultContent
    }
    
    // Editable input (editable mode) 可编辑输入框
    TextInput {
        id: editableInput
        anchors.left: parent.left
        anchors.right: arrow.left
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: Enums.spacing.l
        anchors.rightMargin: Enums.spacing.m
        text: control.currentText
        font.family: Enums.fontFamily
        font.pixelSize: Enums.typography.body
        color: styleHelper.getTextColor()
        selectionColor: Enums.accentColor  // Connect to accent color 接入主题色
        selectedTextColor: Enums.accentForeground
        selectByMouse: true
        visible: control.editable && control.useDefaultContent
        enabled: control.enabled
        
        InputsInternal.InputPlaceholderLabel {
            anchors.fill: parent
            text: control.placeholderText
            visible: !parent.text && !parent.activeFocus
        }
        
        onTextEdited: {
            control.currentText = text
            if (control.textEdited) control.textEdited(text)
        }
    }

    // Dropdown arrow 下拉箭头
    ChevronIcon {
        id: arrow
        anchors.right: parent.right
        anchors.rightMargin: Enums.spacing.l
        anchors.verticalCenter: parent.verticalCenter
        animated: true
        isOpen: control.isOpen
        color: control.enabled 
            ? (control.style === 1 ? Enums.accentForeground : Enums.textColor.secondary) 
            : Enums.stateColor.indicatorActive
    }
    
    // ==================== Interaction 交互 ====================
    // Editable mode: only respond to arrow area clicks, let TextInput work editable模式
    // Non-editable mode: whole area responds 非editable模式
    MouseArea {
        id: mouseArea
        anchors.fill: control.editable ? undefined : parent
        anchors.right: control.editable ? parent.right : undefined
        anchors.top: control.editable ? parent.top : undefined
        anchors.bottom: control.editable ? parent.bottom : undefined
        width: control.editable ? Enums.comboBoxMetrics.arrowAreaWidth : undefined  // editable模式下只覆盖箭头区域
        enabled: control.enabled && !comboPopup.isClosing
        hoverEnabled: true
        // 鼠标 hover 进入时预热 popup native window, 让随后的点击不卡 ~170ms
        onContainsMouseChanged: {
            if (containsMouse && comboPopup.prewarm) comboPopup.prewarm()
        }
        onClicked: {
            if (control.isOpen && !comboPopup.isClosing) {
                closePopup()
            } else if (!control.isOpen && !comboPopup.isClosing) {
                openPopup()
            }
        }
        onWheel: (wheel) => {
            var delta = wheel.angleDelta.y !== 0 ? wheel.angleDelta.y : wheel.angleDelta.x
            control.wheelScrolled(delta)
            wheel.accepted = control.acceptWheel
        }
    }
    
    // Editable mode: focus input area when clicked 点击输入框区域时聚焦
    MouseArea {
        id: editableClickArea
        anchors.left: parent.left
        anchors.right: mouseArea.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        visible: control.editable
        enabled: control.enabled && control.editable
        hoverEnabled: true
        cursorShape: Qt.IBeamCursor
        onClicked: editableInput.forceActiveFocus()
    }

    // ==================== Content Width Measurement 内容宽度测量 ====================
    // TextMetrics to measure popup item text width 用TextMetrics测量弹出菜单项文本宽度
    TextMetrics {
        id: comboTextMeasure
        font.family: Enums.fontFamily
        font.pixelSize: Enums.typography.body
    }

    // ==================== Popup Window (use unified base) 弹出窗口 ====================
    // Expose popup for subclass access 暴露popup供子类访问
    property alias _popup: comboPopup

    PopupWindowCore {
        id: comboPopup
        popupWidth: control.width
        popupHeight: Enums.comboBoxMetrics.popupDefaultHeight
        closeOnClickOutside: control.popupCloseOnClickOutside
        
        onClosed: {
            if (control.isOpen) control.isOpen = false
        }
        
        Loader {
            anchors.fill: parent
            sourceComponent: control.popupContent
            
            onLoaded: {
                if (item && item.hasOwnProperty('control')) {
                    item.control = control
                }
            }
        }
    }
}
