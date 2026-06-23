// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// 导入组件
import PrismQML as Fluent
import "../fluentqml/PrismQML/_internal" as FluentInternal
import "../fluentqml/PrismQML/controls/buttons"
import "../fluentqml/PrismQML/controls/containers"
import "../fluentqml/PrismQML/controls/feedback"

// PrismQML Gallery - 组件展示应用
// 使用QtObject作为根元素，动态创建窗口
QtObject {
    id: root
    
    // 从配置读取窗口类型 Read window type from config
    property int windowType: ConfigManager ? ConfigManager.windowType : Fluent.Enums.windowType.type_ms
    
    // ==================== Common Config 公共配置 ====================
    readonly property int windowWidth: 1200
    readonly property int windowHeight: 800
    readonly property string windowTitle: "PrismQML Gallery"
    readonly property string windowIcon: "qrc:/app_icon.svg"
    readonly property bool windowIconColored: true  // Use colored icon 使用彩色图标
    readonly property int shadowMode: (ConfigManager && ConfigManager.dwmShadow) ? Fluent.Enums.windowShadow.mode_native : Fluent.Enums.windowShadow.mode_none
    readonly property bool micaEnabled: ConfigManager ? ConfigManager.micaEnabled : false
    readonly property bool lazyLoading: ConfigManager ? ConfigManager.lazyLoading : true
    readonly property string loadingText: "加载中"
    
    // 图标路径解析函数
    function iconPath(name) {
        return Qt.resolvedUrl("../fluentqml/PrismQML/controls/icons/fluent/" + name + ".svg")
    }
    
    // 导航项配置
    property var navItems: [
        { "text": "按钮", "icon": iconPath("CursorClick") },
        { "text": "输入", "icon": iconPath("Keyboard") },
        { "text": "标签", "icon": iconPath("Tag") },
        { "text": "卡片", "icon": iconPath("CardUI") },
        { "text": "轮播", "icon": iconPath("SlideMultiple") },
        { "text": "反馈", "icon": iconPath("Alert") },
        { "text": "菜单", "icon": iconPath("Navigation") },
        { "text": "导航", "icon": iconPath("CompassNorthwest") },
        { "text": "容器", "icon": iconPath("LayoutRowFour") },
        { "text": "图表", "icon": iconPath("DataPie") },
        { "text": "图标", "icon": iconPath("Icons") },
        { "text": "特效", "icon": iconPath("Sparkle") }
    ]
    
    property var bottomNavItems: [
        { "text": "User", "icon": "qrc:/image/avatar/avatar.png", "selectable": false },
        { "text": "设置", "icon": iconPath("Settings"), "key": "SettingsPage" }
    ]
    
    property var pagePaths: [
        Qt.resolvedUrl("pages/ButtonPage.qml"),
        Qt.resolvedUrl("pages/InputPage.qml"),
        Qt.resolvedUrl("pages/LabelPage.qml"),
        Qt.resolvedUrl("pages/CardPage.qml"),
        Qt.resolvedUrl("pages/CarouselPage.qml"),
        Qt.resolvedUrl("pages/FeedbackPage.qml"),
        Qt.resolvedUrl("pages/MenuPage.qml"),
        Qt.resolvedUrl("pages/NavigationPage.qml"),
        Qt.resolvedUrl("pages/ContainerPage.qml"),
        Qt.resolvedUrl("pages/ChartPage.qml"),
        Qt.resolvedUrl("pages/IconPage.qml"),
        Qt.resolvedUrl("pages/EffectsPage.qml"),
        Qt.resolvedUrl("pages/SettingsPage.qml")
    ]
    
    // 窗口实例
    property var windowInstance: null
    
    // 根据类型选择组件
    property Component windowComponent: {
        switch (windowType) {
            case Fluent.Enums.windowType.type_fluent:
                return fluentWindowComponent
            case Fluent.Enums.windowType.type_ms:
                return msWindowComponent
            case Fluent.Enums.windowType.type_filled_split:
                return filledSplitWindowComponent
            default:
                return msWindowComponent
        }
    }
    
    // 公共初始化函数 Common init function
    function initWindow(win) {
        Fluent.Translator.setLanguage(Fluent.Enums.lang.zh_CN)
    }
    
    // 启动时创建窗口
    Component.onCompleted: {
        windowInstance = windowComponent.createObject(null)
    }
    
    Component.onDestruction: {
        if (windowInstance) windowInstance.destroy()
    }

    // ==================== Window Components ====================
    
    property Component fluentWindowComponent: Component {
        FluentInternal.WindowsSplit {
            width: root.windowWidth; height: root.windowHeight
            windowTitle: root.windowTitle
            windowIcon: root.windowIcon
            windowIconColored: root.windowIconColored
            shadowMode: root.shadowMode
            micaEnabled: root.micaEnabled
            lazyLoading: root.lazyLoading
            loadingText: root.loadingText
            navigationItems: root.navItems
            bottomNavigationItems: root.bottomNavItems
            pageSources: root.pagePaths
            Component.onCompleted: {
                root.initWindow(this)
                this._splashInstance = root.splashComponent.createObject(this.contentItem)
            }
            onBottomItemClicked: (index) => {
                // Handle function items (e.g., avatar click) 处理功能项（如头像点击）
                if (index === 0) {
                    console.log("Avatar clicked")
                }
            }
        }
    }
    
    property Component msWindowComponent: Component {
        FluentInternal.WindowsBar {
            width: root.windowWidth; height: root.windowHeight
            windowTitle: root.windowTitle
            windowIcon: root.windowIcon
            windowIconColored: root.windowIconColored
            shadowMode: root.shadowMode
            micaEnabled: root.micaEnabled
            lazyLoading: root.lazyLoading
            loadingText: root.loadingText
            navigationItems: root.navItems
            bottomNavigationItems: root.bottomNavItems
            pageSources: root.pagePaths
            Component.onCompleted: {
                root.initWindow(this)
                this._splashInstance = root.splashComponent.createObject(this.contentItem)
            }
            onBottomItemClicked: (index) => {
                if (index === 0) console.log("Avatar clicked")
            }
        }
    }
    
    property Component filledSplitWindowComponent: Component {
        FluentInternal.WindowsFilled {
            width: root.windowWidth; height: root.windowHeight
            windowTitle: root.windowTitle
            windowIcon: root.windowIcon
            windowIconColored: root.windowIconColored
            shadowMode: root.shadowMode
            micaEnabled: root.micaEnabled
            lazyLoading: root.lazyLoading
            loadingText: root.loadingText
            navigationItems: root.navItems
            bottomNavigationItems: root.bottomNavItems
            pageSources: root.pagePaths
            Component.onCompleted: {
                root.initWindow(this)
                this._splashInstance = root.splashComponent.createObject(this.contentItem)
            }
            onBottomItemClicked: (index) => {
                if (index === 0) console.log("Avatar clicked")
            }
        }
    }
    
    // ==================== Splash Screen 启动屏幕 ====================
    property Component splashComponent: Component {
        SplashScreen {
            iconSource: root.windowIcon
            title: root.windowTitle
            subtitle: "正在加载组件..."
            z: 9999
        }
    }
}
