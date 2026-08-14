// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Window

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
            
        }
    }
}
