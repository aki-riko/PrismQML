// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../inputs"
import "../../buttons"
import "../../data"
import "../../data/Label"

// SettingsCardContent - Setting card content component 设置卡片内容组件
// Renders different content based on type 根据类型渲染不同内容
Item {
    id: root
    
    // ==================== Translation Trigger 翻译触发器 ====================
    readonly property int _tv: Translator._v
    
    // ==================== Required Props 必需属性 ====================
    required property int type
    
    // ==================== Push Button Props 按钮属性 ====================
    property string buttonText: ""
    property bool isPrimary: false
    
    // ==================== Switch Props 开关属性 ====================
    property bool checked: false
    property string onText: { _tv; return Translator.tr("on") }
    property string offText: { _tv; return Translator.tr("off") }
    
    // ==================== ComboBox Props 下拉框属性 ====================
    property var model: []
    property int currentIndex: -1
    property string placeholderText: Translator.tr("placeholder_select")
    
    // ==================== Range Props 滑块属性 ====================
    property real value: 0
    property real from: 0
    property real to: 100
    property real stepSize: 1
    
    // ==================== Shortcut Props 快捷键属性 ====================
    property string shortcut: ""
    property string shortcutPlaceholder: Translator.tr("click_to_record")
    
    // ==================== Hyperlink Props 超链接属性 ====================
    property string url: ""
    property string linkText: ""
    
    // ==================== Signals 信号 ====================
    signal buttonClicked()
    signal switchChanged(bool checked)
    signal indexSelected(int index)
    signal rangeValueChanged(real value)
    signal shortcutUpdated(string newShortcut)
    signal linkClicked()
    
    // ==================== Size 尺寸 ====================
    implicitWidth: contentLoader.item ? contentLoader.item.implicitWidth : 0
    implicitHeight: contentLoader.item ? contentLoader.item.implicitHeight : 0
    
    // ==================== Content Loader 内容加载器 ====================
    Loader {
        id: contentLoader
        anchors.fill: parent
        sourceComponent: {
            switch (root.type) {
                case Enums.settingCard.type_push:
                case Enums.settingCard.type_primary_push:
                    // Only show button if buttonText is not empty 只有buttonText非空时才显示按钮
                    return root.buttonText !== "" ? pushButtonComponent : null
                case Enums.settingCard.type_hyperlink:
                    return hyperlinkComponent
                case Enums.settingCard.type_switch:
                    return switchComponent
                case Enums.settingCard.type_combobox:
                    return comboBoxComponent
                case Enums.settingCard.type_range:
                    return rangeComponent
                case Enums.settingCard.type_shortcut:
                    return shortcutComponent
                default:
                    return null
            }
        }
    }
    
    // ==================== Push Button Component 按钮组件 ====================
    Component {
        id: pushButtonComponent
        Button {
            text: root.buttonText
            style: root.type === Enums.settingCard.type_primary_push ? 
                   Enums.button.style_primary : Enums.button.style_default
            onClicked: root.buttonClicked()
        }
    }
    
    // ==================== Hyperlink Component 超链接组件 ====================
    Component {
        id: hyperlinkComponent
        Button {
            text: root.linkText
            style: Enums.button.style_hyperlink
            onClicked: {
                if (root.url !== "") {
                    Qt.openUrlExternally(root.url)
                }
                root.linkClicked()
            }
        }
    }
    
    // ==================== Switch Component 开关组件 ====================
    Component {
        id: switchComponent
        ToggleSwitch {
            text: root.checked ? root.onText : root.offText
            checked: root.checked
            onCheckedStateChanged: function(isChecked) {
                root.checked = isChecked
                root.switchChanged(isChecked)
            }
        }
    }
    
    // ==================== ComboBox Component 下拉框组件 ====================
    Component {
        id: comboBoxComponent
        ComboBox {
            model: root.model
            currentIndex: root.currentIndex
            placeholderText: root.placeholderText
            implicitWidth: Enums.settingCard.combobox_width
            onIndexChanged: function(index) {
                // Don't imperatively assign root.currentIndex — it would
                // break the outer binding SettingsCard.currentIndex has on
                // us, preventing future data-source updates from reaching
                // the ComboBox. Let data flow stay one-way: source -> view.
                // 不命令式赋值 root.currentIndex —— 那会破坏外层 SettingsCard
                // 的 binding，导致后续数据源变化无法再回到视图。
                // 保持单向数据流：source -> view。
                root.indexSelected(index)
            }
        }
    }
    
    // ==================== Range Component 滑块组件 ====================
    Component {
        id: rangeComponent
        Row {
            spacing: Enums.spacing.l
            
            Label {
                type: Enums.label.type_body
                text: Math.round(root.value)
                anchors.verticalCenter: parent.verticalCenter
                width: Enums.settingCard.value_label_width
                horizontalAlignment: Text.AlignRight
            }
            
            Slider {
                value: root.value
                from: root.from
                to: root.to
                stepSize: root.stepSize
                implicitWidth: Enums.settingCard.slider_width
                anchors.verticalCenter: parent.verticalCenter
                onValueModified: function(val) {
                    root.value = val
                    root.rangeValueChanged(val)
                }
            }
        }
    }
    
    // ==================== Shortcut Component 快捷键组件 ====================
    Component {
        id: shortcutComponent
        ShortcutEditor {
            shortcut: root.shortcut
            placeholderText: root.shortcutPlaceholder
            onShortcutModified: function(newShortcut) {
                root.shortcut = newShortcut
                root.shortcutUpdated(newShortcut)
            }
        }
    }
}
