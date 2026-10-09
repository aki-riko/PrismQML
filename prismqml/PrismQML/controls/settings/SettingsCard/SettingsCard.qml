// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "_internal"

// SettingsCard - Unified setting card component 统一设置卡片组件
// Supports both normal and expandable modes 支持普通和展开两种模式
// Auto-render content based on type 根据类型自动渲染内容
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property int type: Enums.settingCard.type_push

    // Common properties 通用属性
    property string icon: ""
    property string title: ""
    property string content: ""
    property bool disabled: false
    
    // Expand properties 展开属性
    property bool expanded: false

    // Push button properties 按钮属性
    property string buttonText: ""
    property bool isPrimary: type === Enums.settingCard.type_primary_push
    
    // Hyperlink properties 超链接属性
    property string url: ""
    property string linkText: ""
    
    // Switch properties 开关属性
    property bool checked: false
    property string onText: { _tv; return Translator.tr("on") }
    property string offText: { _tv; return Translator.tr("off") }
    
    // ComboBox properties 下拉框属性
    property var model: []
    property int currentIndex: -1
    property string currentText: currentIndex >= 0 && currentIndex < _safeModel.length ? _safeModel[currentIndex] : ""
    property string placeholderText: { _tv; return Translator.tr("placeholder_select") }
    
    // Range properties 滑块属性
    property real value: 0
    property real from: 0
    property real to: 100
    property real stepSize: 1
    
    // Shortcut properties 快捷键属性
    property string shortcut: ""
    property string shortcutPlaceholder: { _tv; return Translator.tr("click_to_record") }
    
    // Options properties 选项属性
    property var options: []
    property int selectedIndex: 0
    property string selectedText: _safeOptions.length > 0 && selectedIndex >= 0 && selectedIndex < _safeOptions.length ?
                                  _safeOptions[selectedIndex] : ""
    
    // Folder list properties 文件夹列表属性
    property var folders: []
    property string directory: ""
    property string addButtonText: { _tv; return Translator.tr("add_folder") }
    
    // Custom color properties 自定义颜色属性
    property color defaultColor: Enums.accentColor
    property color customColor: Enums.accentColor
    property bool useCustomColor: false
    property string defaultColorText: { _tv; return Translator.tr("default_color_text") }
    property string customColorText: { _tv; return Translator.tr("custom_color_text") }
    property string chooseColorText: { _tv; return Translator.tr("choose_color_text") }

    // ==================== Readonly State 只读状态 ====================
    readonly property int _tv: Translator._v
    readonly property bool isExpandType: type === Enums.settingCard.type_options ||
                                         type === Enums.settingCard.type_folder_list ||
                                         type === Enums.settingCard.type_color
    readonly property color currentColor: useCustomColor ? customColor : defaultColor
    readonly property real _surfaceBorderWidth: Enums.surfaceBorderWidth(Enums.border.thin)
    readonly property color _surfaceBorderColor: Enums.surfaceBorderColor(
        Enums.stateColor.borderLight,
        Enums.stateColor.controlBg
    )
    readonly property var _safeModel:
        model === null || model === undefined ? []
        : (typeof model.length === "number" ? model : [])
    readonly property var _safeOptions:
        options === null || options === undefined ? []
        : (typeof options.length === "number" ? options : [])
    readonly property var _safeFolders:
        folders === null || folders === undefined ? []
        : (typeof folders.length === "number" ? folders : [])
    
    // ==================== Signals 信号 ====================
    signal clicked()
    signal toggled(bool checked)
    signal switchToggled(bool isChecked)
    signal indexSelected(int idx)
    signal textSelected(string txt)
    signal rangeChanged(real val)
    signal colorPicked(color c)
    signal shortcutRecorded(string keys)
    signal linkActivated()
    signal expandToggled(bool isExpanded)
    signal optionSelected(int idx, string txt)
    signal folderAppended(string path)
    signal folderDeleted(string path)
    signal foldersUpdated(var list)
    signal customColorPicked(color c)

    // ==================== Internal Methods 内部方法 ====================
    function _listOrEmpty(value) {
        return value && typeof value.length === "number" ? value : []
    }

    // ==================== Public Methods 公开方法 ====================
    function isChecked() { return checked }

    function setValue(val) {
        switch (type) {
            case Enums.settingCard.type_range:
                value = val
                break
            case Enums.settingCard.type_shortcut:
                shortcut = val
                break
            case Enums.settingCard.type_options:
                if (val >= 0 && val < _safeOptions.length) selectedIndex = val
                break
            case Enums.settingCard.type_folder_list:
                folders = _listOrEmpty(val).slice()
                break
            case Enums.settingCard.type_color:
                if (val === defaultColor) {
                    useCustomColor = false
                } else {
                    customColor = val
                    useCustomColor = true
                }
                break
        }
    }

    function getValue() {
        switch (type) {
            case Enums.settingCard.type_range:
                return value
            case Enums.settingCard.type_shortcut:
                return shortcut
            case Enums.settingCard.type_options:
                return selectedIndex
            case Enums.settingCard.type_folder_list:
                return _safeFolders.slice()
            case Enums.settingCard.type_color:
                return currentColor
            default:
                return null
        }
    }

    function toggle() {
        expanded = !expanded
        expandToggled(expanded)
    }

    function setExpanded(isExpand) {
        if (expanded !== isExpand) {
            expanded = isExpand
            expandToggled(expanded)
        }
    }

    function addFolder(folder) {
        if (folder === "" || _safeFolders.indexOf(folder) >= 0) return
        var newFolders = _safeFolders.slice()
        newFolders.push(folder)
        folders = newFolders
        folderAppended(folder)
        foldersUpdated(newFolders)
        if (!expanded) {
            expanded = true
            expandToggled(true)
        }
    }

    function removeFolder(folder) {
        var index = _safeFolders.indexOf(folder)
        if (index < 0) return
        var newFolders = _safeFolders.slice()
        newFolders.splice(index, 1)
        folders = newFolders
        folderDeleted(folder)
        foldersUpdated(newFolders)
    }

    function clearFolders() {
        folders = []
        foldersUpdated(folders)
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.controlSize.cardWidth
    implicitHeight: renderLayer.cardLoader.item ? renderLayer.cardLoader.item.implicitHeight : Enums.settingCard.height_no_content

    // ==================== Content 内容 ====================
    SettingsCardRenderLayer {
        id: renderLayer
        anchors.fill: parent
        cardControl: control
    }
}
