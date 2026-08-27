// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// 导入组件
import PrismQML as Fluent
import "../prismqml/PrismQML/_internal" as FluentInternal
import "../prismqml/PrismQML/controls/buttons"
import "../prismqml/PrismQML/controls/containers"

// PrismQML Gallery - 组件展示应用
// 使用QtObject作为根元素，动态创建窗口
QtObject {
    id: root
    
    // 从配置读取窗口类型 Read window type from config
    property int windowType: ConfigManager ? ConfigManager.windowType : Fluent.Enums.windowType.type_ms
    // Runtime changes apply after the next full restart. 运行时变更在下次完整启动后生效。
    property bool _startupLazyLoading: true
    // ==================== Common Config 公共配置 ====================
    readonly property int windowWidth: 1200
    readonly property int windowHeight: 800
    readonly property string windowTitle: "PrismQML Gallery"
    readonly property string windowIcon: "qrc:/app_icon.svg"
    readonly property bool windowIconColored: true  // Use colored icon 使用彩色图标
    readonly property int shadowMode: (ConfigManager && ConfigManager.dwmShadow) ? Fluent.Enums.windowShadow.mode_native : Fluent.Enums.windowShadow.mode_none
    readonly property bool micaEnabled: ConfigManager ? ConfigManager.micaEnabled : false
    readonly property bool lazyLoading: _startupLazyLoading
    readonly property string loadingText: Fluent.Translator.tr("gallery_d04fcbda737fc0c6", Fluent.Translator._v)
    readonly property string splashSubtitle: Fluent.Translator.tr("gallery_12422784480e8784", Fluent.Translator._v)
    
    // 图标路径解析函数
    function iconPath(name) {
        return Qt.resolvedUrl("../prismqml/PrismQML/controls/icons/fluent/" + name + ".svg")
    }
    
    // 导航项配置
    property var navItems: [
        { "text": Fluent.Translator.tr("gallery_ad1c50c9367c756d", Fluent.Translator._v), "icon": iconPath("CursorClick") },
        { "text": Fluent.Translator.tr("gallery_2087c777c06fefe5", Fluent.Translator._v), "icon": iconPath("Keyboard") },
        { "text": Fluent.Translator.tr("gallery_1d0fd5f9336d9103", Fluent.Translator._v), "icon": iconPath("Tag") },
        { "text": Fluent.Translator.tr("gallery_6d23f04b26967d64", Fluent.Translator._v), "icon": iconPath("LayoutRowFour") },
        { "text": Fluent.Translator.tr("gallery_fb5640f8e12e3337", Fluent.Translator._v), "icon": iconPath("CardUI") },
        { "text": Fluent.Translator.tr("gallery_85f05ecc2a4f3f5d", Fluent.Translator._v), "icon": iconPath("SlideMultiple") },
        { "text": Fluent.Translator.tr("gallery_8cb443ab83797881", Fluent.Translator._v), "icon": iconPath("DataPie") },
        { "text": Fluent.Translator.tr("gallery_4ce4cafdd0561280", Fluent.Translator._v), "icon": iconPath("Navigation") },
        { "text": Fluent.Translator.tr("gallery_e72622fe470d04bc", Fluent.Translator._v), "icon": iconPath("CompassNorthwest") },
        { "text": Fluent.Translator.tr("gallery_8b2106ca13719cb2", Fluent.Translator._v), "icon": iconPath("Alert") },
        { "text": Fluent.Translator.tr("gallery_0d720eeea26466dd", Fluent.Translator._v), "icon": iconPath("Icons") },
        { "text": Fluent.Translator.tr("gallery_8829dbcbcfce6e54", Fluent.Translator._v), "icon": iconPath("Sparkle") },
        { "text": Fluent.Translator.tr("gallery_736cff237d7d9255", Fluent.Translator._v), "icon": iconPath("ArrowSync") }
    ]
    
    property var bottomNavItems: [
        { "text": "User", "icon": "qrc:/image/avatar/avatar.png", "selectable": false },
        { "text": Fluent.Translator.tr("gallery_df3d58c7d84b85f2", Fluent.Translator._v), "icon": iconPath("Settings"), "key": "SettingsPage" }
    ]
    
    property var pagePaths: [
        Qt.resolvedUrl("pages/ButtonPage.qml"),
        Qt.resolvedUrl("pages/InputPage.qml"),
        Qt.resolvedUrl("pages/LabelPage.qml"),
        Qt.resolvedUrl("pages/ContainerPage.qml"),
        Qt.resolvedUrl("pages/CardPage.qml"),
        Qt.resolvedUrl("pages/CarouselPage.qml"),
        Qt.resolvedUrl("pages/ChartPage.qml"),
        Qt.resolvedUrl("pages/MenuPage.qml"),
        Qt.resolvedUrl("pages/NavigationPage.qml"),
        Qt.resolvedUrl("pages/FeedbackPage.qml"),
        Qt.resolvedUrl("pages/IconPage.qml"),
        Qt.resolvedUrl("pages/EffectsPage.qml"),
        Qt.resolvedUrl("pages/AutoUpdatePage.qml"),
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
    
    // 启动时创建窗口
    Component.onCompleted: {
        _startupLazyLoading = ConfigManager ? ConfigManager.lazyLoading : true
        windowInstance = windowComponent.createObject(null)
    }

    Component.onDestruction: {
        if (windowInstance) windowInstance.destroy()
    }

    // ==================== Window Components ====================
    
    property Component fluentWindowComponent: Component {
        FluentInternal.WindowsSplit {
            width: root.windowWidth; height: root.windowHeight
            visible: false
            splashEnabled: false
            windowTitle: root.windowTitle
            windowIcon: root.windowIcon
            windowIconColored: root.windowIconColored
            shadowMode: root.shadowMode
            micaEnabled: root.micaEnabled
            lazyLoading: root.lazyLoading
            loadingText: root.loadingText
            splashSubtitle: root.splashSubtitle
            navigationItems: root.navItems
            bottomNavigationItems: root.bottomNavItems
            pageSources: root.pagePaths
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
            visible: false
            splashEnabled: false
            windowTitle: root.windowTitle
            windowIcon: root.windowIcon
            windowIconColored: root.windowIconColored
            shadowMode: root.shadowMode
            micaEnabled: root.micaEnabled
            lazyLoading: root.lazyLoading
            loadingText: root.loadingText
            splashSubtitle: root.splashSubtitle
            navigationItems: root.navItems
            bottomNavigationItems: root.bottomNavItems
            pageSources: root.pagePaths
            onBottomItemClicked: (index) => {
                if (index === 0) console.log("Avatar clicked")
            }
        }
    }
    
    property Component filledSplitWindowComponent: Component {
        FluentInternal.WindowsFilled {
            width: root.windowWidth; height: root.windowHeight
            visible: false
            splashEnabled: false
            windowTitle: root.windowTitle
            windowIcon: root.windowIcon
            windowIconColored: root.windowIconColored
            shadowMode: root.shadowMode
            micaEnabled: root.micaEnabled
            lazyLoading: root.lazyLoading
            loadingText: root.loadingText
            splashSubtitle: root.splashSubtitle
            navigationItems: root.navItems
            bottomNavigationItems: root.bottomNavItems
            pageSources: root.pagePaths
            onBottomItemClicked: (index) => {
                if (index === 0) console.log("Avatar clicked")
            }
        }
    }
    
}
