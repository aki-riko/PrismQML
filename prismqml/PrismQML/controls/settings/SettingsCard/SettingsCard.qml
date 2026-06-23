// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Dialogs
import "../../.."
import "../../icons"
import "../../buttons"
import "../../inputs"
import "../../data"
import "../../data/Label"
import "../../containers"

// SettingsCard - Unified setting card component 统一设置卡片组件
// Supports both normal and expandable modes 支持普通和展开两种模式
// Auto-render content based on type 根据类型自动渲染内容
Item {
    id: control
    
    // ==================== Translation Trigger 翻译触发器 ====================
    readonly property int _tv: Translator._v
    
    // ==================== Type 类型 ====================
    property int type: Enums.settingCard.type_push
    
    // ==================== Common Props 通用属性 ====================
    property string icon: ""
    property string title: ""
    property string content: ""
    property bool disabled: false
    
    // ==================== Expand Props 展开属性 ====================
    property bool expanded: false
    readonly property bool isExpandType: type === Enums.settingCard.type_options ||
                                         type === Enums.settingCard.type_folder_list ||
                                         type === Enums.settingCard.type_color
    
    // ==================== Push Button Props 按钮属性 ====================
    property string buttonText: ""
    property bool isPrimary: type === Enums.settingCard.type_primary_push
    
    // ==================== Hyperlink Props 超链接属性 ====================
    property string url: ""
    property string linkText: ""
    
    // ==================== Switch Props 开关属性 ====================
    property bool checked: false
    property string onText: { _tv; return Translator.tr("on") }
    property string offText: { _tv; return Translator.tr("off") }
    
    // ==================== ComboBox Props 下拉框属性 ====================
    property var model: []
    property int currentIndex: -1
    property string currentText: currentIndex >= 0 && currentIndex < model.length ? model[currentIndex] : ""
    property string placeholderText: Translator.tr("placeholder_select")
    
    // ==================== Range Props 滑块属性 ====================
    property real value: 0
    property real from: 0
    property real to: 100
    property real stepSize: 1
    
    // ==================== Shortcut Props 快捷键属性 ====================
    property string shortcut: ""
    property string shortcutPlaceholder: { _tv; return Translator.tr("click_to_record") }
    
    // ==================== Options Props 选项属性 ====================
    property var options: []
    property int selectedIndex: 0
    property string selectedText: options.length > 0 && selectedIndex >= 0 && selectedIndex < options.length ? 
                                  options[selectedIndex] : ""
    
    // ==================== Folder List Props 文件夹列表属性 ====================
    property var folders: []
    property string directory: ""
    property string addButtonText: Translator.tr("add_folder")
    
    // ==================== Custom Color Props 自定义颜色属性 ====================
    property color defaultColor: Enums.accentColor
    property color customColor: Enums.accentColor
    property bool useCustomColor: false
    property string defaultColorText: { _tv; return Translator.tr("default_color_text") }
    property string customColorText: { _tv; return Translator.tr("custom_color_text") }
    property string chooseColorText: { _tv; return Translator.tr("choose_color_text") }
    readonly property color currentColor: useCustomColor ? customColor : defaultColor
    
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
                if (val >= 0 && val < options.length) selectedIndex = val
                break
            case Enums.settingCard.type_folder_list:
                folders = val.slice()
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
                return folders.slice()
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
        if (folder === "" || folders.indexOf(folder) >= 0) return
        var newFolders = folders.slice()
        newFolders.push(folder)
        folders = newFolders
        folderAppended(folder)
        foldersUpdated(folders)
        if (!expanded) {
            expanded = true
            expandToggled(true)
        }
    }

    function removeFolder(folder) {
        var index = folders.indexOf(folder)
        if (index < 0) return
        var newFolders = folders.slice()
        newFolders.splice(index, 1)
        folders = newFolders
        folderDeleted(folder)
        foldersUpdated(folders)
    }

    function clearFolders() {
        folders = []
        foldersUpdated(folders)
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.controlSize.cardWidth
    implicitHeight: cardLoader.item ? cardLoader.item.implicitHeight : Enums.settingCard.height_no_content
    
    // ==================== Card Loader 卡片加载器 ====================
    Loader {
        id: cardLoader
        anchors.fill: parent
        sourceComponent: control.isExpandType ? expandCardComponent : normalCardComponent
    }
    
    // ==================== Normal Card Component 普通卡片组件 ====================
    Component {
        id: normalCardComponent
        SettingsCardCore {
            icon: control.icon
            title: control.title
            content: control.content
            disabled: control.disabled
            
            contentItem: SettingsCardContent {
                type: control.type
                buttonText: control.buttonText
                isPrimary: control.isPrimary
                url: control.url
                linkText: control.linkText
                checked: control.checked
                onText: control.onText
                offText: control.offText
                model: control.model
                currentIndex: control.currentIndex
                placeholderText: control.placeholderText
                value: control.value
                from: control.from
                to: control.to
                stepSize: control.stepSize
                shortcut: control.shortcut
                shortcutPlaceholder: control.shortcutPlaceholder
                
                onButtonClicked: control.clicked()
                onSwitchChanged: function(isChecked) {
                    control.checked = isChecked
                    control.switchToggled(isChecked)
                    control.toggled(isChecked)
                }
                onIndexSelected: function(index) {
                    // Don't imperatively assign control.currentIndex —
                    // it would break the outer binding set by users (e.g.
                    // `currentIndex: backend.fooIndex`). Callers are expected
                    // to update the data source in their onIndexSelected
                    // handler; the new value propagates back via binding.
                    // 不命令式赋值 control.currentIndex —— 那会破坏使用者
                    // 在 `currentIndex: backend.xxxIndex` 上的外部 binding。
                    // 调用方应在自己的 onIndexSelected 中更新数据源，新值
                    // 会通过原 binding 自动回流到视图。
                    control.indexSelected(index)
                    control.textSelected(control.model && index >= 0 && index < control.model.length ? control.model[index] : "")
                }
                onRangeValueChanged: function(val) {
                    control.value = val
                    control.rangeChanged(val)
                }
                onShortcutUpdated: function(s) {
                    control.shortcut = s
                    control.shortcutRecorded(s)
                }
                onLinkClicked: control.linkActivated()
            }
        }
    }
    
    // ==================== Expand Card Component 展开卡片组件（复用Expander）====================
    Component {
        id: expandCardComponent
        Expander {
            id: expanderCard

            // Store reference to root control 存储根控件引用
            readonly property Item rootControl: control

            title: rootControl.title
            content: rootControl.content
            icon: rootControl.icon
            expanded: rootControl.expanded
            disabled: rootControl.disabled
            // SettingsCard 的 expandComponent 内部已自带 verticalCenter padding 模式
            // (Item height = X.implicit + spacing.l*2), 显式设 contentPadding=0 退回旧行为,
            // 避免与引擎默认 spacing.l 双叠加. 业务侧直接用 Expander 不受影响.
            contentPadding: 0
            
            // Bind expanded state 绑定展开状态
            onToggled: {
                rootControl.expanded = expanderCard.expanded
                rootControl.expandToggled(rootControl.expanded)
            }
            
            // Header content based on type 根据类型显示头部内容
            headerContent: {
                switch (rootControl.type) {
                    case Enums.settingCard.type_options:
                        return optionsHeaderComponent
                    case Enums.settingCard.type_folder_list:
                        return folderListHeaderComponent
                    case Enums.settingCard.type_color:
                        return colorHeaderComponent
                    default:
                        return null
                }
            }
            
            // Expand content based on type 根据类型显示展开内容
            Loader {
                anchors.left: parent.left
                anchors.right: parent.right
                sourceComponent: {
                    switch (rootControl.type) {
                        case Enums.settingCard.type_options:
                            return optionsExpandComponent
                        case Enums.settingCard.type_folder_list:
                            return folderListExpandComponent
                        case Enums.settingCard.type_color:
                            return colorExpandComponent
                        default:
                            return null
                    }
                }
            }
        }
    }
    
    // ==================== Options Header Component 选项头部组件 ====================
    Component {
        id: optionsHeaderComponent
        Label {
            type: Enums.label.type_body
            text: control.selectedText
        }
    }
    
    // ==================== Options Expand Component 选项展开组件 ====================
    Component {
        id: optionsExpandComponent
        Column {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.leftMargin: Enums.spacing.xxxl
            spacing: Enums.spacing.l
            
            Repeater {
                model: control.options
                
                RadioButton {
                    text: modelData
                    checked: index === control.selectedIndex
                    onToggled: {
                        if (control.selectedIndex !== index) {
                            control.selectedIndex = index
                            control.optionSelected(index, modelData)
                        }
                    }
                }
            }
        }
    }
    
    // ==================== Folder List Header Component 文件夹列表头部组件 ====================
    Component {
        id: folderListHeaderComponent
        Button {
            text: control.addButtonText
            icon: Enums.icon.folder_add
            onClicked: folderDialog.open()
        }
    }
    
    // ==================== Folder List Expand Component 文件夹列表展开组件 ====================
    Component {
        id: folderListExpandComponent
        Column {
            anchors.left: parent.left
            anchors.right: parent.right
            spacing: 0
            
            Repeater {
                model: control.folders
                
                Item {
                    width: parent.width
                    height: Enums.settingCard.group_item_height
                    
                    Separator {
                        anchors.top: parent.top
                        width: parent.width
                        visible: index > 0
                    }
                    
                    Row {
                        anchors.fill: parent
                        anchors.leftMargin: Enums.spacing.xxxl
                        anchors.rightMargin: Enums.spacing.xl
                        spacing: Enums.spacing.xl
                        
                        Label {
                            type: Enums.label.type_body
                            text: modelData
                            anchors.verticalCenter: parent.verticalCenter
                            width: parent.width - removeBtn.width - parent.spacing
                            elide: Text.ElideMiddle
                        }
                        
                        Button {
                            id: removeBtn
                            icon: Enums.icon.dismiss
                            flat: true
                            anchors.verticalCenter: parent.verticalCenter
                            onClicked: control.removeFolder(modelData)
                        }
                    }
                }
            }
        }
    }
    
    // ==================== Color Header Component 颜色头部组件 ====================
    Component {
        id: colorHeaderComponent
        Label {
            type: Enums.label.type_body
            text: control.useCustomColor ? control.customColorText : control.defaultColorText
        }
    }
    
    // ==================== Color Expand Component 颜色展开组件 ====================
    Component {
        id: colorExpandComponent
        Column {
            anchors.left: parent.left
            anchors.right: parent.right
            spacing: 0

            Item {
                width: parent.width
                // 上下各 spacing.l 的纵向 padding, 与下方 group_item_height
                // 行内 verticalCenter 视觉一致, 之前只加 spacing.m (8) 总余量
                // 导致第一行 radio 与下方分隔线贴太紧, 第二行又显得空旷
                height: radioColumn.height + Enums.spacing.l * 2

                Column {
                    id: radioColumn
                    anchors.left: parent.left
                    anchors.leftMargin: Enums.spacing.xxxl
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: Enums.spacing.l

                    RadioButton {
                        text: control.customColorText
                        checked: control.useCustomColor
                        onToggled: {
                            if (!control.useCustomColor) {
                                control.useCustomColor = true
                                control.customColorPicked(control.customColor)
                            }
                        }
                    }

                    RadioButton {
                        text: control.defaultColorText
                        checked: !control.useCustomColor
                        onToggled: {
                            if (control.useCustomColor) {
                                control.useCustomColor = false
                                control.customColorPicked(control.defaultColor)
                            }
                        }
                    }
                }
            }

            Separator {
                width: parent.width
            }

            Item {
                width: parent.width
                // 跟 Item1 一致: row 高度 + 上下各 spacing.l, 不再用 group_item_height
                // (固定 53 + contentArea 底部 12 padding 叠加, 看着上紧下松)
                height: colorRow.height + Enums.spacing.l * 2

                Row {
                    id: colorRow
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.leftMargin: Enums.spacing.xxxl
                    anchors.rightMargin: Enums.spacing.xl
                    anchors.verticalCenter: parent.verticalCenter
                    
                    Label {
                        type: Enums.label.type_body
                        text: control.customColorText
                        anchors.verticalCenter: parent.verticalCenter
                        width: parent.width - chooseColorBtn.width - Enums.spacing.m
                    }
                    
                    Rectangle {
                        id: chooseColorBtn
                        width: Enums.settingCard.color_button_width
                        height: Enums.settingCard.color_block_height
                        radius: Enums.radius.small
                        color: chooseColorArea.containsMouse ? Enums.stateColor.controlBgHover : Enums.stateColor.controlBg
                        border.width: Enums.border.thin
                        border.color: Enums.stateColor.border
                        opacity: control.useCustomColor ? Enums.opacityLevel.visible : Enums.opacityLevel.disabled
                        anchors.verticalCenter: parent.verticalCenter
                        
                        Label {
                            type: Enums.label.type_body
                            anchors.centerIn: parent
                            text: control.chooseColorText
                        }
                        
                        MouseArea {
                            id: chooseColorArea
                            anchors.fill: parent
                            hoverEnabled: true
                            enabled: control.useCustomColor
                            onClicked: {
                                if (colorPickerLoader.item) {
                                    colorPickerLoader.item.open()
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    // ==================== Folder Dialog 文件夹对话框 ====================
    FolderDialog {
        id: folderDialog
        title: Translator.tr("choose_folder")
        currentFolder: control.directory !== "" ? "file:///" + control.directory : ""
        onAccepted: {
            var folderPath = decodeURIComponent(selectedFolder.toString().replace(/^(file:\/{2,3})/, ""))
            control.addFolder(folderPath)
        }
    }
    
    // ==================== Color Picker 颜色选择器 ====================
    // Only load when type is color 仅在类型为颜色时加载
    Loader {
        id: colorPickerLoader
        active: control.type === Enums.settingCard.type_color
        sourceComponent: Component {
            ColorPicker {
                id: colorPickerDialog
                visible: false  // Hidden trigger, only use popup 隐藏触发器，仅使用弹窗
                selectedColor: control.customColor
                onColorSelected: function(c) {
                    control.customColor = c
                    if (control.useCustomColor) {
                        control.customColorPicked(c)
                    }
                }
            }
        }
    }
}
