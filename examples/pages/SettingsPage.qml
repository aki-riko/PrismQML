// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import QtQuick.Effects

// 导入组件
import PrismQML
import PrismQML as Fluent

// 设置组件页面
Item {
    id: root
    
    // Get parent window reference 获取父窗口引用
    readonly property var parentWindow: Window.window
    
    function iconPath(name) {
        return Fluent.Enums.iconPath + name + ".svg"
    }
    
    ScrollArea {
        anchors.fill: parent
        
        Column {
            width: parent ? parent.width : 0
            spacing: Fluent.Enums.spacing.xxl
            
            // 页面标题
            Column {
                width: parent ? parent.width : 0
                spacing: Fluent.Enums.spacing.xs
                Text { text: Fluent.Translator.tr("gallery_b4a4ca71fb7539c7", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
                Text { text: "prismqml.controls.settings"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.tertiary; font.family: Fluent.Enums.fontFamily }
            }
            
            // ==================== 实际功能设置 Functional Settings ====================
            SettingsCardGroup {
                title: Fluent.Translator.tr("gallery_248c888b290d234f", Fluent.Translator._v)
                width: parent ? parent.width : 0
                
                // 窗口类型
                SettingsCard {
                    readonly property var windowTypeValues:
                        ConfigManager ? ConfigManager.windowTypeOptions : []

                    objectName: "windowTypeSettingsCard"
                    width: parent ? parent.width : 0
                    title: Fluent.Translator.tr("gallery_6cc070864e568c6b", Fluent.Translator._v)
                    content: Fluent.Translator.tr("gallery_c58314ff3c291c53", Fluent.Translator._v)
                    icon: iconPath("Window")
                    type: Fluent.Enums.settingCard.type_combobox
                    model: windowTypeValues.map(function(value) {
                        return Fluent.Enums.windowType.typeNames[value]
                    })
                    currentIndex: ConfigManager
                        ? windowTypeValues.indexOf(ConfigManager.windowType)
                        : -1
                    onIndexSelected: function(idx) {
                        if (ConfigManager && idx >= 0 &&
                                idx < windowTypeValues.length) {
                            ConfigManager.setWindowType(windowTypeValues[idx])
                        }
                    }
                }
                
                // 云母效果
                SettingsCard {
                    width: parent ? parent.width : 0
                    title: Fluent.Translator.tr("gallery_491d8a1d801bb51f", Fluent.Translator._v)
                    content: Fluent.Translator.tr("gallery_73d650e292eac352", Fluent.Translator._v)
                    icon: iconPath("Blur")
                    type: Fluent.Enums.settingCard.type_switch
                    checked: ConfigManager ? ConfigManager.micaEnabled : false
                    onSwitchToggled: function(isChecked) {
                        if (parentWindow && parentWindow.setMicaEffectEnabled) {
                            parentWindow.setMicaEffectEnabled(isChecked)
                        }
                        if (ConfigManager) {
                            ConfigManager.setMicaEnabled(isChecked)
                        }
                    }
                }
                
                // DWM原生阴影
                SettingsCard {
                    width: parent ? parent.width : 0
                    title: Fluent.Translator.tr("gallery_1001f6a8b689600b", Fluent.Translator._v)
                    content: Fluent.Translator.tr("gallery_32df12f693e56719", Fluent.Translator._v)
                    icon: iconPath("SquareShadow")
                    type: Fluent.Enums.settingCard.type_switch
                    checked: ConfigManager ? ConfigManager.dwmShadow : true
                    onSwitchToggled: function(isChecked) {
                        if (ConfigManager) {
                            ConfigManager.setDwmShadow(isChecked)
                        }
                    }
                }
            }
            
            SettingsCardGroup {
                title: Fluent.Translator.tr("gallery_a1a42cd9b16e2162", Fluent.Translator._v)
                width: parent ? parent.width : 0
                
                // 应用主题 Application theme
                SettingsCard {
                    id: themeCard

                    readonly property var themeValues:
                        ConfigManager ? ConfigManager.themeOptions : []
                    readonly property int themeIndex: ConfigManager
                        ? themeValues.indexOf(ConfigManager.theme) : -1

                    objectName: "themeSettingsCard"
                    width: parent ? parent.width : 0
                    title: Fluent.Translator.tr("gallery_0e61f173997cf413", Fluent.Translator._v)
                    content: Fluent.Translator.tr("gallery_db463b04c2ffb6eb", Fluent.Translator._v)
                    icon: iconPath("DarkTheme")
                    type: Fluent.Enums.settingCard.type_combobox
                    model: [Fluent.Translator.tr("gallery_217cfe7db1e3d10a", Fluent.Translator._v), Fluent.Translator.tr("gallery_aa0819dfc4d8d782", Fluent.Translator._v), Fluent.Translator.tr("gallery_a6b75d0680322a61", Fluent.Translator._v)]
                    currentIndex: themeIndex >= 0 ? themeIndex : 0
                    
                    onIndexSelected: function(idx) {
                        if (idx >= 0 && idx < themeValues.length) {
                            ConfigManager.setTheme(themeValues[idx])
                        }
                    }
                }

                // Design skin 设计皮肤
                SettingsCard {
                    id: skinCard

                    readonly property var skinValues:
                        ConfigManager ? ConfigManager.skinOptions : []
                    readonly property int skinIndex: ConfigManager
                        ? skinValues.indexOf(ConfigManager.skin) : -1
                    readonly property int _translationVersion: Fluent.Translator._v
                    readonly property var skinLabels: {
                        _translationVersion
                        return [
                            Fluent.Translator.tr("skin_fluent_design"),
                            Fluent.Translator.tr("skin_neobrutalism"),
                            Fluent.Translator.tr("skin_vintage_ticket"),
                            Fluent.Translator.tr("skin_neumorphism")
                        ]
                    }

                    objectName: "skinSettingsCard"
                    width: parent ? parent.width : 0
                    title: {
                        _translationVersion
                        return Fluent.Translator.tr("design_skin")
                    }
                    content: {
                        _translationVersion
                        return Fluent.Translator.tr("design_skin_description")
                    }
                    icon: iconPath("Color")
                    type: Fluent.Enums.settingCard.type_combobox
                    model: skinLabels
                    currentIndex: skinIndex >= 0 ? skinIndex : 0

                    onIndexSelected: function(idx) {
                        if (idx >= 0 && idx < skinValues.length) {
                            ConfigManager.setSkin(skinValues[idx])
                        }
                    }
                }
                
                // 懒加载
                SettingsCard {
                    width: parent ? parent.width : 0
                    title: Fluent.Translator.tr("gallery_d05c55bc5b9d134b", Fluent.Translator._v)
                    content: Fluent.Translator.tr("gallery_e2748c46180717bc", Fluent.Translator._v)
                    icon: iconPath("Timer")
                    type: Fluent.Enums.settingCard.type_switch
                    checked: ConfigManager ? ConfigManager.lazyLoading : true
                    onSwitchToggled: function(isChecked) {
                        if (ConfigManager) {
                            ConfigManager.setLazyLoading(isChecked)
                        }
                    }
                }
                
                // DPI缩放
                SettingsCard {
                    id: dpiCard

                    readonly property var dpiValues:
                        ConfigManager ? ConfigManager.dpiScaleOptions : []

                    objectName: "dpiScaleSettingsCard"
                    width: parent ? parent.width : 0
                    title: Fluent.Translator.tr("gallery_2d406700ef62534f", Fluent.Translator._v)
                    content: Fluent.Translator.tr("gallery_c58314ff3c291c53", Fluent.Translator._v)
                    icon: iconPath("ResizeImage")
                    type: Fluent.Enums.settingCard.type_combobox
                    model: dpiValues.map(function(value) {
                        return value === 0 ? Fluent.Translator.tr("gallery_217cfe7db1e3d10a", Fluent.Translator._v) : value + "%"
                    })
                    currentIndex: ConfigManager
                        ? dpiValues.indexOf(ConfigManager.dpiScale)
                        : -1
                    onIndexSelected: function(idx) {
                        if (ConfigManager && idx >= 0 && idx < dpiValues.length) {
                            ConfigManager.setDpiScale(dpiValues[idx])
                        }
                    }
                }
                
                // 界面语言
                SettingsCard {
                    id: languageCard

                    readonly property var languages: Fluent.Translator.supportedLanguages
                    readonly property int languageIndex: {
                        for (var i = 0; i < languages.length; i++) {
                            if (languages[i].code === Fluent.Translator.language) return i
                        }
                        return 0
                    }

                    objectName: "languageSettingsCard"
                    width: parent ? parent.width : 0
                    title: Fluent.Translator.tr("gallery_3d13868593ae4eeb", Fluent.Translator._v)
                    content: Fluent.Translator.tr("gallery_0af6a6aa673343b7", Fluent.Translator._v)
                    icon: iconPath("LocalLanguage")
                    type: Fluent.Enums.settingCard.type_combobox
                    model: languages.map(lang => lang.nativeName)
                    currentIndex: languageIndex
                    
                    onIndexSelected: function(idx) {
                        if (idx >= 0 && idx < languages.length) {
                            var langCode = languages[idx].code
                            Fluent.Translator.setLanguage(langCode)
                        }
                    }
                }
                
                // 主题色
                SettingsCard {
                    objectName: "accentColorSettingsCard"
                    width: parent ? parent.width : 0
                    title: Fluent.Translator.tr("gallery_0f132a452ea8ac60", Fluent.Translator._v)
                    content: Fluent.Translator.tr("gallery_ac73d3f02e42efa3", Fluent.Translator._v)
                    icon: iconPath("Color")
                    type: Fluent.Enums.settingCard.type_color
                    defaultColor: Fluent.Enums.accentDefaults.accent
                    customColor: ConfigManager
                        ? ConfigManager.accentColor : Fluent.Enums.accentColor
                    useCustomColor: customColor.toString().toLowerCase()
                        !== defaultColor.toString().toLowerCase()
                    defaultColorText: Fluent.Translator.tr("gallery_af76608af89e9682", Fluent.Translator._v)
                    customColorText: Fluent.Translator.tr("gallery_781b07fdcb56b56a", Fluent.Translator._v)
                    chooseColorText: Fluent.Translator.tr("gallery_369b82fa0700db02", Fluent.Translator._v)
                    onCustomColorPicked: function(c) {
                        if (ConfigManager) {
                            ConfigManager.setAccentColor(c.toString())
                        }
                    }
                }
            }
            
            // ==================== SettingsCard 类型展示 ====================
            
            // 按钮类型
            ExampleCard {
                title: "SettingsCard - type_push"
                description: Fluent.Translator.tr("gallery_914e756532bd250d", Fluent.Translator._v)
                SettingsCard { 
                    width: 380
                    title: Fluent.Translator.tr("gallery_52d25a9e30ba94f1", Fluent.Translator._v)
                    content: Fluent.Translator.tr("gallery_551f2dc464fae243", Fluent.Translator._v)
                    icon: iconPath("Info")
                    type: Fluent.Enums.settingCard.type_push
                    buttonText: Fluent.Translator.tr("gallery_db8db0530432bd15", Fluent.Translator._v)
                }
            }
            
            // 主要按钮类型
            ExampleCard {
                title: "SettingsCard - type_primary_push"
                description: Fluent.Translator.tr("gallery_8e65e38666703464", Fluent.Translator._v)
                SettingsCard { 
                    width: 380
                    title: Fluent.Translator.tr("gallery_c8550237ba701f64", Fluent.Translator._v)
                    content: Fluent.Translator.tr("gallery_4dba5cf72a199d63", Fluent.Translator._v)
                    icon: iconPath("Save")
                    type: Fluent.Enums.settingCard.type_primary_push
                    buttonText: Fluent.Translator.tr("gallery_a3030bf8f16dc63c", Fluent.Translator._v)
                    onClicked: console.log("Primary button clicked")
                }
            }
            
            // 超链接类型
            ExampleCard {
                title: "SettingsCard - type_hyperlink"
                description: Fluent.Translator.tr("gallery_beaed9f02826599d", Fluent.Translator._v)
                SettingsCard { 
                    width: 380
                    title: Fluent.Translator.tr("gallery_8914957fc91d8750", Fluent.Translator._v)
                    content: Fluent.Translator.tr("gallery_2cce4a7e9cf9cb3d", Fluent.Translator._v)
                    icon: iconPath("QuestionCircle")
                    type: Fluent.Enums.settingCard.type_hyperlink
                    linkText: Fluent.Translator.tr("gallery_d1961d380a4d68c2", Fluent.Translator._v)
                    url: "https://github.com"
                }
            }
            
            // 开关类型
            ExampleCard {
                title: "SettingsCard - type_switch"
                description: Fluent.Translator.tr("gallery_582b6e71b6aeb922", Fluent.Translator._v)
                SettingsCard { 
                    width: 380
                    title: Fluent.Translator.tr("gallery_736cff237d7d9255", Fluent.Translator._v)
                    content: Fluent.Translator.tr("gallery_7adf0b48e0c26ee0", Fluent.Translator._v)
                    icon: iconPath("ArrowSync")
                    type: Fluent.Enums.settingCard.type_switch
                    checked: true
                    onText: Fluent.Translator.tr("gallery_8da97ddda990e7c4", Fluent.Translator._v)
                    offText: Fluent.Translator.tr("gallery_3fd47edce45b3603", Fluent.Translator._v)
                    onSwitchToggled: function(isChecked) { console.log("Switch:", isChecked) }
                }
            }
            
            // 下拉框类型
            ExampleCard {
                title: "SettingsCard - type_combobox"
                description: Fluent.Translator.tr("gallery_0fa997528dd177b4", Fluent.Translator._v)
                SettingsCard { 
                    width: 380
                    title: Fluent.Translator.tr("gallery_44fb814b166ed6ae", Fluent.Translator._v)
                    content: Fluent.Translator.tr("gallery_bd67011ea3772093", Fluent.Translator._v)
                    icon: iconPath("DarkTheme")
                    type: Fluent.Enums.settingCard.type_combobox
                    model: [Fluent.Translator.tr("gallery_217cfe7db1e3d10a", Fluent.Translator._v), Fluent.Translator.tr("gallery_aa0819dfc4d8d782", Fluent.Translator._v), Fluent.Translator.tr("gallery_a6b75d0680322a61", Fluent.Translator._v)]
                    currentIndex: 0
                    onIndexSelected: function(idx) { console.log("Selected:", idx) }
                }
            }
            
            // 滑块类型
            ExampleCard {
                title: "SettingsCard - type_range"
                description: Fluent.Translator.tr("gallery_c86ac18a0b13e88d", Fluent.Translator._v)
                SettingsCard { 
                    width: 380
                    title: Fluent.Translator.tr("gallery_8bf8b9780d342816", Fluent.Translator._v)
                    content: Fluent.Translator.tr("gallery_c8300c46e0364940", Fluent.Translator._v)
                    icon: iconPath("Speaker2")
                    type: Fluent.Enums.settingCard.type_range
                    from: 0
                    to: 100
                    value: 50
                    onRangeChanged: function(val) { console.log("Value:", val) }
                }
            }
            
            // 快捷键类型
            ExampleCard {
                title: "SettingsCard - type_shortcut"
                description: Fluent.Translator.tr("gallery_eb0b8b4e64fe083c", Fluent.Translator._v)
                SettingsCard { 
                    width: 380
                    title: Fluent.Translator.tr("gallery_ee2638183d3ea860", Fluent.Translator._v)
                    content: Fluent.Translator.tr("gallery_608ccbd8e0e252ce", Fluent.Translator._v)
                    icon: iconPath("Keyboard")
                    type: Fluent.Enums.settingCard.type_shortcut
                }
            }
            
            // ==================== 展开类型 Expand Types ====================
            
            // 选项类型
            ExampleCard {
                title: "SettingsCard - type_options"
                description: Fluent.Translator.tr("gallery_23a4bff729ae8251", Fluent.Translator._v)
                SettingsCard { 
                    width: 380
                    title: Fluent.Translator.tr("gallery_74b46009cf439128", Fluent.Translator._v)
                    content: Fluent.Translator.tr("gallery_f9cc4eee6d96db9e", Fluent.Translator._v)
                    icon: iconPath("Play")
                    type: Fluent.Enums.settingCard.type_options
                    options: [Fluent.Translator.tr("gallery_f323fc507d585565", Fluent.Translator._v), Fluent.Translator.tr("gallery_91a1d31663b93d6b", Fluent.Translator._v), Fluent.Translator.tr("gallery_fb1f260586829d95", Fluent.Translator._v)]
                    selectedIndex: 1
                    onOptionSelected: function(idx, txt) { console.log("Option:", idx, txt) }
                }
            }
            
            // 文件夹列表类型
            ExampleCard {
                title: "SettingsCard - type_folder_list"
                description: Fluent.Translator.tr("gallery_21680a285de1b212", Fluent.Translator._v)
                SettingsCard { 
                    width: 380
                    title: Fluent.Translator.tr("gallery_c8218193acec7663", Fluent.Translator._v)
                    content: Fluent.Translator.tr("gallery_8ccb568e459c7c3c", Fluent.Translator._v)
                    icon: iconPath("MusicNote2")
                    type: Fluent.Enums.settingCard.type_folder_list
                    addButtonText: Fluent.Translator.tr("gallery_45da2d9c85d15628", Fluent.Translator._v)
                    folders: ["/path/to/music", "/path/to/downloads"]
                    onFoldersUpdated: function(list) { console.log("Folders:", list) }
                }
            }
            
            // 颜色类型
            ExampleCard {
                title: "SettingsCard - type_color"
                description: Fluent.Translator.tr("gallery_03ecf0cfeaad9b9e", Fluent.Translator._v)
                SettingsCard { 
                    width: 380
                    title: Fluent.Translator.tr("gallery_7d5ce714f1d6c411", Fluent.Translator._v)
                    content: Fluent.Translator.tr("gallery_ac73d3f02e42efa3", Fluent.Translator._v)
                    icon: iconPath("Color")
                    type: Fluent.Enums.settingCard.type_color
                    defaultColor: Fluent.Enums.accentColor
                    customColor: Fluent.Enums.examplePageColors.settingsCustomAccent
                    defaultColorText: Fluent.Translator.tr("gallery_af76608af89e9682", Fluent.Translator._v)
                    customColorText: Fluent.Translator.tr("gallery_781b07fdcb56b56a", Fluent.Translator._v)
                    chooseColorText: Fluent.Translator.tr("gallery_369b82fa0700db02", Fluent.Translator._v)
                    onCustomColorPicked: function(c) { console.log("Color:", c) }
                }
            }
            
            // 设置卡片分组
            ExampleCard {
                title: "SettingsCardGroup"
                description: Fluent.Translator.tr("gallery_ee4385d9240af7c1", Fluent.Translator._v)
                SettingsCardGroup {
                    title: Fluent.Translator.tr("gallery_185b58c5903abc5f", Fluent.Translator._v)
                    width: 400
                    
                    SettingsCard { 
                        width: parent.width
                        title: Fluent.Translator.tr("gallery_788db1cfec2a3db5", Fluent.Translator._v)
                        content: Fluent.Translator.tr("gallery_bd67011ea3772093", Fluent.Translator._v)
                        icon: iconPath("DarkTheme")
                        type: Fluent.Enums.settingCard.type_combobox
                        model: [Fluent.Translator.tr("gallery_aa0819dfc4d8d782", Fluent.Translator._v), Fluent.Translator.tr("gallery_a6b75d0680322a61", Fluent.Translator._v), Fluent.Translator.tr("gallery_217cfe7db1e3d10a", Fluent.Translator._v)]
                    }
                    
                    SettingsCard { 
                        width: parent.width
                        title: Fluent.Translator.tr("gallery_d1d1bedf66228659", Fluent.Translator._v)
                        content: Fluent.Translator.tr("gallery_dc0158797445f3e1", Fluent.Translator._v)
                        icon: iconPath("Play")
                        type: Fluent.Enums.settingCard.type_switch
                        checked: true
                    }
                    
                    SettingsCard { 
                        width: parent.width
                        title: Fluent.Translator.tr("gallery_05f1293993aea38a", Fluent.Translator._v)
                        content: Fluent.Translator.tr("gallery_231b1081d5073e31", Fluent.Translator._v)
                        icon: iconPath("BrightnessHigh")
                        type: Fluent.Enums.settingCard.type_range
                        from: 50
                        to: 100
                        value: 100
                    }
                }
            }
        }
    }
}
