// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import QtQuick.Effects

// 导入组件
import PrismQML as Fluent
import "../../fluentqml/FluentQML/controls/buttons"
import "../../fluentqml/FluentQML/controls/settings"
import "../../fluentqml/FluentQML/controls/settings/SettingsCard"
import "../../fluentqml/FluentQML/controls/inputs"
import "../../fluentqml/FluentQML/controls/containers"

// 设置组件页面
Item {
    id: root
    
    // Get parent window reference 获取父窗口引用
    readonly property var parentWindow: Window.window
    
    function iconPath(name) {
        return Qt.resolvedUrl("../../fluentqml/FluentQML/controls/icons/fluent/" + name + ".svg")
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
                Text { text: "设置组件"; font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
                Text { text: "fluentqml.controls.settings"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.tertiary; font.family: Fluent.Enums.fontFamily }
            }
            
            // ==================== 实际功能设置 Functional Settings ====================
            SettingsCardGroup {
                title: "窗口设置"
                width: parent ? parent.width : 0
                
                // 窗口类型
                SettingsCard {
                    width: parent ? parent.width : 0
                    title: "窗口类型"
                    content: "重启生效"
                    icon: iconPath("Window")
                    type: Fluent.Enums.settingCard.type_combobox
                    model: Fluent.Enums.windowType.typeNames
                    currentIndex: ConfigManager ? ConfigManager.windowType : 0
                    onIndexSelected: function(idx) {
                        if (ConfigManager && idx >= 0) {
                            ConfigManager.setWindowType(idx)
                        }
                    }
                }
                
                // 云母效果
                SettingsCard {
                    width: parent ? parent.width : 0
                    title: "云母效果"
                    content: "仅 Windows 11 支持"
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
                    title: "DWM 原生阴影"
                    content: "Windows 原生窗口阴影"
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
                title: "应用设置"
                width: parent ? parent.width : 0
                
                // 应用主题 Application theme
                SettingsCard {
                    id: themeCard
                    width: parent ? parent.width : 0
                    title: "应用主题"
                    content: "调整应用外观"
                    icon: iconPath("DarkTheme")
                    type: Fluent.Enums.settingCard.type_combobox
                    model: ["跟随系统", "浅色", "深色"]
                    
                    property var themeValues: ["auto", "light", "dark"]
                    
                    Component.onCompleted: {
                        // 根据当前主题设置初始索引
                        // Set initial index based on current theme
                        if (ThemeManager) {
                            var currentTheme = ThemeManager.theme
                            var idx = themeValues.indexOf(currentTheme)
                            currentIndex = idx >= 0 ? idx : 0
                        }
                    }
                    
                    onIndexSelected: function(idx) {
                        if (ThemeManager && idx >= 0 && idx < themeValues.length) {
                            ThemeManager.setThemeFromQml(themeValues[idx])
                        }
                    }
                }

                // 设计皮肤 Design skin (Fluent / Neobrutalism)
                SettingsCard {
                    id: skinCard
                    width: parent ? parent.width : 0
                    title: "设计皮肤"
                    content: "切换设计语言：Fluent 圆角模糊阴影 / 新粗野粗黑边硬阴影"
                    icon: iconPath("Color")
                    type: Fluent.Enums.settingCard.type_combobox
                    model: ["Fluent", "新粗野 Neobrutalism"]

                    property var skinValues: ["fluent", "neobrutalism"]

                    Component.onCompleted: {
                        if (ThemeManager) {
                            var idx = skinValues.indexOf(ThemeManager.skin)
                            currentIndex = idx >= 0 ? idx : 0
                        }
                    }

                    onIndexSelected: function(idx) {
                        if (ThemeManager && idx >= 0 && idx < skinValues.length) {
                            ThemeManager.setSkinFromQml(skinValues[idx])
                        }
                    }
                }
                
                // 懒加载
                SettingsCard {
                    width: parent ? parent.width : 0
                    title: "懒加载"
                    content: "延迟加载页面内容"
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
                    width: parent ? parent.width : 0
                    title: "DPI 缩放"
                    content: "重启生效"
                    icon: iconPath("ResizeImage")
                    type: Fluent.Enums.settingCard.type_combobox
                    model: ["跟随系统", "100%", "125%", "150%", "175%", "200%"]
                    
                    property var dpiValues: [0, 100, 125, 150, 175, 200]
                    property int lastSavedIndex: -1
                    
                    Component.onCompleted: {
                        if (ConfigManager) {
                            var scale = ConfigManager.dpiScale
                            var idx = dpiValues.indexOf(scale)
                            idx = idx >= 0 ? idx : 0
                            lastSavedIndex = idx
                            currentIndex = idx
                        }
                    }
                    
                    onIndexSelected: function(idx) {
                        if (idx !== lastSavedIndex && ConfigManager) {
                            var value = dpiValues[idx]
                            ConfigManager.setDpiScale(value)
                            lastSavedIndex = idx
                        }
                    }
                }
                
                // 界面语言
                SettingsCard {
                    id: languageCard
                    width: parent ? parent.width : 0
                    title: "界面语言"
                    content: "选择显示语言"
                    icon: iconPath("LocalLanguage")
                    type: Fluent.Enums.settingCard.type_combobox
                    
                    property var languages: Fluent.Translator.supportedLanguages
                    model: languages.map(lang => lang.nativeName)
                    
                    Component.onCompleted: {
                        var currentLang = Fluent.Translator.language
                        for (var i = 0; i < languages.length; i++) {
                            if (languages[i].code === currentLang) {
                                currentIndex = i
                                break
                            }
                        }
                    }
                    
                    onIndexSelected: function(idx) {
                        if (idx >= 0 && idx < languages.length) {
                            var langCode = languages[idx].code
                            Fluent.Translator.setLanguage(langCode)
                        }
                    }
                }
                
                // 主题色
                SettingsCard {
                    width: parent ? parent.width : 0
                    title: "主题色"
                    content: "选择默认或自定义颜色"
                    icon: iconPath("Color")
                    type: Fluent.Enums.settingCard.type_color
                    defaultColor: Fluent.Enums.accentDefaults.accent
                    defaultColorText: "默认颜色"
                    customColorText: "自定义颜色"
                    chooseColorText: "选择颜色"
                    onCustomColorPicked: function(c) {
                        if (ThemeManager) {
                            ThemeManager.setAccentColor(c)
                        }
                    }
                }
            }
            
            // ==================== SettingsCard 类型展示 ====================
            
            // 按钮类型
            ExampleCard {
                title: "SettingsCard - type_push"
                description: "按钮设置卡片"
                SettingsCard { 
                    width: 380
                    title: "关于"
                    content: "查看软件信息"
                    icon: iconPath("Info")
                    type: Fluent.Enums.settingCard.type_push
                    buttonText: "查看"
                }
            }
            
            // 主要按钮类型
            ExampleCard {
                title: "SettingsCard - type_primary_push"
                description: "主要按钮设置卡片"
                SettingsCard { 
                    width: 380
                    title: "保存设置"
                    content: "保存当前配置"
                    icon: iconPath("Save")
                    type: Fluent.Enums.settingCard.type_primary_push
                    buttonText: "保存"
                    onClicked: console.log("Primary button clicked")
                }
            }
            
            // 超链接类型
            ExampleCard {
                title: "SettingsCard - type_hyperlink"
                description: "超链接设置卡片"
                SettingsCard { 
                    width: 380
                    title: "帮助文档"
                    content: "查看在线帮助"
                    icon: iconPath("QuestionCircle")
                    type: Fluent.Enums.settingCard.type_hyperlink
                    linkText: "打开文档"
                    url: "https://github.com"
                }
            }
            
            // 开关类型
            ExampleCard {
                title: "SettingsCard - type_switch"
                description: "开关设置卡片"
                SettingsCard { 
                    width: 380
                    title: "自动更新"
                    content: "启用自动检查更新"
                    icon: iconPath("ArrowSync")
                    type: Fluent.Enums.settingCard.type_switch
                    checked: true
                    onText: "开启"
                    offText: "关闭"
                    onSwitchToggled: function(isChecked) { console.log("Switch:", isChecked) }
                }
            }
            
            // 下拉框类型
            ExampleCard {
                title: "SettingsCard - type_combobox"
                description: "下拉框设置卡片"
                SettingsCard { 
                    width: 380
                    title: "主题模式"
                    content: "选择界面主题"
                    icon: iconPath("DarkTheme")
                    type: Fluent.Enums.settingCard.type_combobox
                    model: ["跟随系统", "浅色", "深色"]
                    currentIndex: 0
                    onIndexSelected: function(idx) { console.log("Selected:", idx) }
                }
            }
            
            // 滑块类型
            ExampleCard {
                title: "SettingsCard - type_range"
                description: "滑块设置卡片"
                SettingsCard { 
                    width: 380
                    title: "音量"
                    content: "调整系统音量"
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
                description: "快捷键设置卡片"
                SettingsCard { 
                    width: 380
                    title: "快捷键"
                    content: "设置全局快捷键"
                    icon: iconPath("Keyboard")
                    type: Fluent.Enums.settingCard.type_shortcut
                }
            }
            
            // ==================== 展开类型 Expand Types ====================
            
            // 选项类型
            ExampleCard {
                title: "SettingsCard - type_options"
                description: "选项设置卡片（展开式）"
                SettingsCard { 
                    width: 380
                    title: "启动行为"
                    content: "选择程序启动时的行为"
                    icon: iconPath("Play")
                    type: Fluent.Enums.settingCard.type_options
                    options: ["最小化到托盘", "显示主窗口", "恢复上次状态"]
                    selectedIndex: 1
                    onOptionSelected: function(idx, txt) { console.log("Option:", idx, txt) }
                }
            }
            
            // 文件夹列表类型
            ExampleCard {
                title: "SettingsCard - type_folder_list"
                description: "文件夹列表设置卡片（展开式）"
                SettingsCard { 
                    width: 380
                    title: "音乐文件夹"
                    content: "管理音乐库文件夹"
                    icon: iconPath("MusicNote2")
                    type: Fluent.Enums.settingCard.type_folder_list
                    addButtonText: "添加文件夹"
                    folders: ["/path/to/music", "/path/to/downloads"]
                    onFoldersUpdated: function(list) { console.log("Folders:", list) }
                }
            }
            
            // 颜色类型
            ExampleCard {
                title: "SettingsCard - type_color"
                description: "颜色设置卡片（展开式）"
                SettingsCard { 
                    width: 380
                    title: "主题颜色"
                    content: "选择默认或自定义颜色"
                    icon: iconPath("Color")
                    type: Fluent.Enums.settingCard.type_color
                    defaultColor: Fluent.Enums.accentColor
                    customColor: "#ff6b6b"
                    defaultColorText: "默认颜色"
                    customColorText: "自定义颜色"
                    chooseColorText: "选择颜色"
                    onCustomColorPicked: function(c) { console.log("Color:", c) }
                }
            }
            
            // 设置卡片分组
            ExampleCard {
                title: "SettingsCardGroup"
                description: "设置卡片分组容器"
                SettingsCardGroup {
                    title: "个性化设置"
                    width: 400
                    
                    SettingsCard { 
                        width: parent.width
                        title: "主题"
                        content: "选择界面主题"
                        icon: iconPath("DarkTheme")
                        type: Fluent.Enums.settingCard.type_combobox
                        model: ["浅色", "深色", "跟随系统"]
                    }
                    
                    SettingsCard { 
                        width: parent.width
                        title: "动画效果"
                        content: "启用界面动画"
                        icon: iconPath("Play")
                        type: Fluent.Enums.settingCard.type_switch
                        checked: true
                    }
                    
                    SettingsCard { 
                        width: parent.width
                        title: "透明度"
                        content: "调整窗口透明度"
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
