// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// Import components 导入组件
import PrismQML
import PrismQML as Fluent

// Navigation components page 导航组件页面
Item {
    id: root

    // ==================== Demo Models 演示模型 ====================
    // Shared model for the vertical navigation panels. Text and labels stay
    // ASCII on purpose: the Gallery i18n contract only localizes
    // user-visible literals, and these are component names.
    // 垂直导航面板共用模型。文本与标签刻意保持 ASCII：画廊 i18n 合同只本地化
    // 用户可见文案，而这些是组件名。
    readonly property var navPanelModel: [
        { "key": "home", "text": "Home", "icon": iconPath("Home") },
        { "key": "documents", "text": "Documents", "icon": iconPath("Document") },
        { "key": "search", "text": "Search", "icon": iconPath("Search") },
        { "key": "mail", "text": "Mail", "icon": iconPath("Mail") },
        { "key": "settings", "text": "Settings", "icon": iconPath("Settings") }
    ]
    readonly property var navPanelScrollModel: [
        { "key": "home", "text": "Home", "icon": iconPath("Home") },
        { "key": "documents", "text": "Documents", "icon": iconPath("Document") },
        { "key": "search", "text": "Search", "icon": iconPath("Search") },
        { "key": "mail", "text": "Mail", "icon": iconPath("Mail") },
        { "key": "people", "text": "People", "icon": iconPath("Person") },
        { "key": "calendar", "text": "Calendar", "icon": iconPath("Calendar") },
        { "key": "favorites", "text": "Favorites", "icon": iconPath("Star") },
        { "key": "reports", "text": "Reports", "icon": iconPath("ChartMultiple") },
        { "key": "folders", "text": "Folders", "icon": iconPath("Folder") },
        { "key": "settings", "text": "Settings", "icon": iconPath("Settings") }
    ]

    function iconPath(name) {
        return Fluent.Enums.iconPath + name + ".svg"
    }
    
    ScrollArea {
        anchors.fill: parent
        
        Column {
            width: parent ? parent.width : 0
            spacing: Fluent.Enums.spacing.xxl
            
            // Page title 页面标题
            Column {
                width: parent ? parent.width : 0
                spacing: Fluent.Enums.spacing.xs
                Text { text: Fluent.Translator.tr("gallery_416a19daaaa5e27a", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
                Text { text: "prismqml.controls.navigation"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
            }
            
            // Breadcrumbs 面包屑
            ExampleCard {
                title: Fluent.Translator.tr("gallery_6c3f7b6a12a97468", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_aefd232185a863d6", Fluent.Translator._v)
                Column {
                    spacing: Fluent.Enums.spacing.l
                    
                    // Basic breadcrumb 基础面包屑
                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_71fd13b9ab679678", Fluent.Translator._v)
                        Column {
                            spacing: Fluent.Enums.spacing.m
                            Breadcrumb { 
                                id: basicBreadcrumb
                                showIcons: false
                                Component.onCompleted: {
                                    addItem("home", Fluent.Translator.tr("gallery_203c08e0d44ac375", Fluent.Translator._v))
                                    addItem("docs", Fluent.Translator.tr("gallery_2687ccdbb1d2288a", Fluent.Translator._v))
                                    addItem("components", Fluent.Translator.tr("gallery_783d638053ea1897", Fluent.Translator._v))
                                    addItem("navigation", Fluent.Translator.tr("gallery_e72622fe470d04bc", Fluent.Translator._v))
                                }
                                onCurrentItemChanged: (key) => basicText.text = Fluent.Translator.tr("gallery_6245bfb449a7e29a") + key
                            }
                            Row {
                                spacing: Fluent.Enums.spacing.s
                                Button { text: Fluent.Translator.tr("gallery_9f63b859185cc52e", Fluent.Translator._v); onClicked: basicBreadcrumb.addItem("sub" + basicBreadcrumb.count, Fluent.Translator.tr("gallery_6fc800788812ce20") + basicBreadcrumb.count) }
                                Button { text: Fluent.Translator.tr("gallery_6e280f54e3f9a1b5", Fluent.Translator._v); onClicked: basicBreadcrumb.popItem() }
                            }
                            Text { id: basicText; text: Fluent.Translator.tr("gallery_af28875a2bfd7a3c", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
                        }
                    }
                    
                    // Breadcrumb with icons 带图标面包屑
                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_098537ecdc81e809", Fluent.Translator._v)
                        Column {
                            spacing: Fluent.Enums.spacing.m
                            Breadcrumb { 
                                id: iconBreadcrumb
                                showIcons: true
                                Component.onCompleted: {
                                    addItem("home", Fluent.Translator.tr("gallery_203c08e0d44ac375", Fluent.Translator._v), Fluent.Enums.icon.home)
                                    addItem("folder", Fluent.Translator.tr("gallery_7c7802d8adaed72e", Fluent.Translator._v), Fluent.Enums.icon.folder)
                                    addItem("docs", Fluent.Translator.tr("gallery_2687ccdbb1d2288a", Fluent.Translator._v), Fluent.Enums.icon.document)
                                    addItem("file", Fluent.Translator.tr("gallery_39932f24fe11a6ba", Fluent.Translator._v), Fluent.Enums.icon.document_text)
                                }
                                onCurrentItemChanged: (key) => iconText.text = Fluent.Translator.tr("gallery_6245bfb449a7e29a") + key
                            }
                            Row {
                                spacing: Fluent.Enums.spacing.s
                                Button { text: Fluent.Translator.tr("gallery_9f0d4e4656ee5dbc", Fluent.Translator._v); onClicked: iconBreadcrumb.addItem("img" + iconBreadcrumb.count, Fluent.Translator.tr("gallery_d24c10d37db0feea") + iconBreadcrumb.count, Fluent.Enums.icon.image) }
                                Button { text: Fluent.Translator.tr("gallery_6e280f54e3f9a1b5", Fluent.Translator._v); onClicked: iconBreadcrumb.popItem() }
                            }
                            Text { id: iconText; text: Fluent.Translator.tr("gallery_9931589c64452c89", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
                        }
                    }
                    
                    // Overflow demo 溢出演示
                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_3f8772eda407feb6", Fluent.Translator._v)
                        Column {
                            spacing: Fluent.Enums.spacing.m
                            Breadcrumb { 
                                id: overflowBreadcrumb
                                maxVisibleItems: 4
                                showIcons: true
                                Component.onCompleted: {
                                    addItem("root", Fluent.Translator.tr("gallery_42ee2863b6d776ff", Fluent.Translator._v), Fluent.Enums.icon.home)
                                    addItem("level1", Fluent.Translator.tr("gallery_a64ef18ab49bdc3d", Fluent.Translator._v), Fluent.Enums.icon.folder)
                                    addItem("level2", Fluent.Translator.tr("gallery_d5335a84faaada38", Fluent.Translator._v), Fluent.Enums.icon.folder)
                                    addItem("level3", Fluent.Translator.tr("gallery_646dd7daa0ffcf85", Fluent.Translator._v), Fluent.Enums.icon.folder)
                                    addItem("level4", Fluent.Translator.tr("gallery_4f4ceee94c6d268a", Fluent.Translator._v), Fluent.Enums.icon.folder)
                                    addItem("current", Fluent.Translator.tr("gallery_6be6c8248ec61181", Fluent.Translator._v), Fluent.Enums.icon.location)
                                }
                            }
                            Row {
                                spacing: Fluent.Enums.spacing.s
                                Button { text: Fluent.Translator.tr("gallery_65b1aa217f342c3b", Fluent.Translator._v); onClicked: overflowBreadcrumb.addItem("deep" + overflowBreadcrumb.count, Fluent.Translator.tr("gallery_e88300b4a20a8512") + overflowBreadcrumb.count, Fluent.Enums.icon.folder) }
                                Button { text: Fluent.Translator.tr("gallery_6e280f54e3f9a1b5", Fluent.Translator._v); onClicked: overflowBreadcrumb.popItem() }
                                Button { text: Fluent.Translator.tr("gallery_cb5d682bac3d1a2d", Fluent.Translator._v); onClicked: { overflowBreadcrumb.clear(); overflowBreadcrumb.addItem("root", Fluent.Translator.tr("gallery_42ee2863b6d776ff", Fluent.Translator._v), Fluent.Enums.icon.home) } }
                            }
                            Text { text: Fluent.Translator.tr("gallery_ef08bff1a9823248", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
                        }
                    }
                }
            }
            
            // Vertical navigation panels 垂直导航面板
            // Window-level panels: a sidebar, its compact icon rail, and a
            // mutually-exclusive toggle rail. They are plain Items, so they can
            // be inspected inside a page instead of only inside a window shell.
            // titleBarHeight is zeroed because the panels normally reserve the
            // window title-bar strip, which does not exist inside a page.
            // 窗口级面板：侧边栏、其紧凑图标栏，以及互斥切换栏。它们都是普通 Item，
            // 因此可以放在页面里查看。titleBarHeight 置零，因为面板默认会为窗口
            // 标题栏预留高度，而页面里没有标题栏。
            ExampleCard {
                title: "Vertical navigation"
                description: "NavigationView / NavigationBar / ToggleNavigationBar"
                ComponentCard {
                    label: "NavigationView (compact)"
                    Rectangle {
                        width: 48
                        height: 300
                        radius: Fluent.Enums.radius.large
                        color: Fluent.Enums.surfaceColor
                        border.width: Fluent.Enums.border.thin
                        border.color: Fluent.Enums.borderColor
                        clip: true
                        NavigationView {
                            width: parent.width
                            height: parent.height
                            showReturnButton: false
                            titleBarHeight: 0
                            paneDisplayMode: Fluent.Enums.navigation.pane_left_compact
                            model: root.navPanelModel
                            // The panels never move their own selection: they emit
                            // itemClicked and expect the host shell to push a new
                            // currentIndex back (single-direction binding). Inside a
                            // page this handler IS that shell.
                            // 面板不会自己改选中项: 它只发 itemClicked, 由宿主外壳回灌
                            // currentIndex（单向绑定）。页面里这段接线就是那个外壳。
                            onItemClicked: (index) => {
                                if (index >= 0 && index < root.navPanelModel.length)
                                    currentIndex = index
                            }
                        }
                    }
                }
                ComponentCard {
                    label: "NavigationView (expanded)"
                    Rectangle {
                        // Tall enough that 5 rows plus the pinned bottom item fit
                        // without overflow: otherwise the scroll fade dims the top row.
                        // 高度足以让 5 行加底部固定项不溢出, 否则滚动渐隐会把首行压暗。
                        width: 240
                        height: 340
                        radius: Fluent.Enums.radius.large
                        color: Fluent.Enums.surfaceColor
                        border.width: Fluent.Enums.border.thin
                        border.color: Fluent.Enums.borderColor
                        clip: true
                        NavigationView {
                            width: parent.width
                            height: parent.height
                            isExpanded: true
                            showReturnButton: false
                            titleBarHeight: 0
                            paneDisplayMode: Fluent.Enums.navigation.pane_left
                            model: root.navPanelModel
                            bottomItems: [
                                { "text": "Account", "icon": root.iconPath("Person"), "selectable": false }
                            ]
                            onItemClicked: (index) => {
                                if (index >= 0 && index < root.navPanelModel.length)
                                    currentIndex = index
                            }
                        }
                    }
                }
                ComponentCard {
                    label: "NavigationView (pane_left_minimal)"
                    Rectangle {
                        // Collapsed to the menu button; tapping it reveals the rail
                        // 折叠到只剩菜单按钮; 点击按钮即展开图标栏
                        width: 48
                        height: 300
                        radius: Fluent.Enums.radius.large
                        color: Fluent.Enums.surfaceColor
                        border.width: Fluent.Enums.border.thin
                        border.color: Fluent.Enums.borderColor
                        clip: true
                        NavigationView {
                            width: parent.width
                            height: parent.height
                            showReturnButton: false
                            titleBarHeight: 0
                            paneDisplayMode: Fluent.Enums.navigation.pane_left_minimal
                            model: root.navPanelModel
                            onItemClicked: (index) => {
                                if (index >= 0 && index < root.navPanelModel.length) {
                                    currentIndex = index
                                    closePane()
                                }
                            }
                        }
                    }
                }
                ComponentCard {
                    label: "NavigationBar"
                    Rectangle {
                        width: 68
                        height: 300
                        radius: Fluent.Enums.radius.large
                        color: Fluent.Enums.surfaceColor
                        border.width: Fluent.Enums.border.thin
                        border.color: Fluent.Enums.borderColor
                        clip: true
                        NavigationBar {
                            width: parent.width
                            height: parent.height
                            model: root.navPanelScrollModel
                            onItemClicked: (index) => {
                                if (index >= 0 && index < root.navPanelScrollModel.length)
                                    currentIndex = index
                            }
                        }
                    }
                }
                ComponentCard {
                    label: "ToggleNavigationBar"
                    Rectangle {
                        width: 220
                        height: 300
                        radius: Fluent.Enums.radius.large
                        color: Fluent.Enums.surfaceColor
                        border.width: Fluent.Enums.border.thin
                        border.color: Fluent.Enums.borderColor
                        clip: true
                        ToggleNavigationBar {
                            width: parent.width
                            height: parent.height
                            model: root.navPanelModel
                        }
                    }
                }
                ComponentCard {
                    label: "SegmentedControl (orientation: Qt.Vertical)"
                    SegmentedControl {
                        orientation: Qt.Vertical
                        items: ["General", "Appearance", "Advanced"]
                    }
                }
                ComponentCard {
                    label: "Pivot (orientation: Qt.Vertical)"
                    Pivot {
                        orientation: Qt.Vertical
                        items: [
                            { "key": "general", "text": "General" },
                            { "key": "appearance", "text": "Appearance" },
                            { "key": "advanced", "text": "Advanced" }
                        ]
                    }
                }
            }

            // Segmented controls 分段控件
            ExampleCard {
                title: Fluent.Translator.tr("gallery_e998714a526683d7", Fluent.Translator._v)
                description: "SegmentedControl / Pivot"
                Column {
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard { label: "SegmentedControl"; SegmentedControl { items: [Fluent.Translator.tr("gallery_96198518dab609f0", Fluent.Translator._v), Fluent.Translator.tr("gallery_5f04a01fe105bb4d", Fluent.Translator._v), Fluent.Translator.tr("gallery_74b97119bee5c66d", Fluent.Translator._v)] } }
                    ComponentCard { label: "Pivot"; Pivot { items: [Fluent.Translator.tr("gallery_5c55a67935af8f45", Fluent.Translator._v), Fluent.Translator.tr("gallery_2687ccdbb1d2288a", Fluent.Translator._v), Fluent.Translator.tr("gallery_d24c10d37db0feea", Fluent.Translator._v), Fluent.Translator.tr("gallery_c20f7618d330a854", Fluent.Translator._v)] } }
                }
            }
            
            // Selector bar 选择条
            // Chrome-less strip: only the selected cell carries the sliding pill.
            // 无边框条带: 只有选中项带滑动胶囊。
            ExampleCard {
                title: "SelectorBar"
                description: "Flat selector with a sliding pill"
                Column {
                    spacing: Fluent.Enums.spacing.l

                    ComponentCard {
                        label: "horizontal"
                        SelectorBar {
                            objectName: "gallerySelectorBar"
                            items: [
                                { key: "overview", text: "Overview" },
                                { key: "activity", text: "Activity" },
                                { key: "settings", text: "Settings", icon: "Settings" },
                                { key: "about", text: "About" }
                            ]
                            onItemClicked: (index, byUser) => selectorStatus.text = "invoked " + index
                            onCurrentItemChanged: (key) => selectorStatus.text = "selected " + key
                        }
                    }

                    Text {
                        id: selectorStatus
                        text: "selected overview"
                        font.family: Fluent.Enums.fontFamily
                        font.pixelSize: Fluent.Enums.typography.caption
                        color: Fluent.Enums.textColor.secondary
                    }

                    // Stacked, not side by side: each demo keeps its own caption line and
                    // no strip bleeds into a neighbour's column.
                    // 纵向堆叠而非并排: 每个示例各自成行, 条带不会侵入相邻示例的列。
                    ComponentCard {
                        label: "orientation: Qt.Vertical"
                        SelectorBar {
                            objectName: "gallerySelectorBarVertical"
                            orientation: Qt.Vertical
                            items: [
                                { key: "overview", text: "Overview" },
                                { key: "activity", text: "Activity" },
                                { key: "about", text: "About" }
                            ]
                        }
                    }

                    // Exactly two whole cells wide, so the resting state never shows a
                    // half-cut label; selecting a far cell scrolls the least amount that
                    // fits it.
                    // 宽度正好两整格, 因此静止状态不会出现半截标签; 选远端项时按最小滚动量移入。
                    ComponentCard {
                        label: "width: 272 (overflow)"
                        SelectorBar {
                            objectName: "gallerySelectorBarNarrow"
                            width: 272
                            items: [
                                { key: "overview", text: "Overview" },
                                { key: "activity", text: "Activity" },
                                { key: "settings", text: "Settings" },
                                { key: "about", text: "About" },
                                { key: "extra", text: "Extra" }
                            ]
                        }
                    }
                }
            }

            // Stepper progress bar 步骤进度条
            ExampleCard {
                title: Fluent.Translator.tr("gallery_ae9e675a583eeb35", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_e8ac692d3cae2e98", Fluent.Translator._v)
                ComponentCard {
                    label: "Stepper"
                    Column {
                        spacing: Fluent.Enums.spacing.m
                        Stepper { 
                            id: stepProgress
                            width: 500
                            steps: [
                                {text: Fluent.Translator.tr("gallery_3d5436ea23d2e9a2", Fluent.Translator._v), icon: "Clipboard"},
                                {text: Fluent.Translator.tr("gallery_f5e1243b0aa8c3c3", Fluent.Translator._v), icon: "Cart"},
                                {text: Fluent.Translator.tr("gallery_34e5636c63cc8f78", Fluent.Translator._v), icon: "Person"},
                                {text: Fluent.Translator.tr("gallery_a662b954e297a878", Fluent.Translator._v), icon: ""},
                                {text: Fluent.Translator.tr("gallery_5d3ba34cc66cea45", Fluent.Translator._v), icon: ""}
                            ]
                            currentStep: 2
                        }
                        Row {
                            spacing: Fluent.Enums.spacing.s
                            Button { text: Fluent.Translator.tr("gallery_da336fdc0dbd1818", Fluent.Translator._v); onClicked: stepProgress.stepBack() }
                            Button { text: Fluent.Translator.tr("gallery_acfc4e74a650e7df", Fluent.Translator._v); onClicked: stepProgress.stepNext() }
                        }
                    }
                }
            }
            
            // StackedWidget 动画类型展示
            ExampleCard {
                title: Fluent.Translator.tr("gallery_ee1f55ea470c1fb0", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_9f6fc091d21f095d", Fluent.Translator._v)
                Row {
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard {
                        label: "opacity"
                        Column {
                            spacing: Fluent.Enums.spacing.xs
                            StackedWidget {
                                id: opacityStack; width: 110; height: 55
                                animationType: Fluent.Enums.animation.opacity
                                Rectangle { color: Fluent.Enums.demoPalette.blue; Text { anchors.centerIn: parent; text: "1"; color: Fluent.Enums.accentForeground } }
                                Rectangle { color: Fluent.Enums.demoPalette.green; Text { anchors.centerIn: parent; text: "2"; color: Fluent.Enums.accentForeground } }
                            }
                            Row {
                                spacing: Fluent.Enums.spacing.xs
                                Button { text: "1"; width: 26; onClicked: opacityStack.currentIndex = 0 }
                                Button { text: "2"; width: 26; onClicked: opacityStack.currentIndex = 1 }
                            }
                        }
                    }
                    ComponentCard {
                        label: "popup"
                        Column {
                            spacing: Fluent.Enums.spacing.xs
                            StackedWidget {
                                id: popupStack; width: 110; height: 55
                                animationType: Fluent.Enums.animation.popup
                                Rectangle { color: Fluent.Enums.demoPalette.orange; Text { anchors.centerIn: parent; text: "1"; color: Fluent.Enums.accentForeground } }
                                Rectangle { color: Fluent.Enums.demoPalette.red; Text { anchors.centerIn: parent; text: "2"; color: Fluent.Enums.accentForeground } }
                            }
                            Row {
                                spacing: Fluent.Enums.spacing.xs
                                Button { text: "1"; width: 26; onClicked: popupStack.currentIndex = 0 }
                                Button { text: "2"; width: 26; onClicked: popupStack.currentIndex = 1 }
                            }
                        }
                    }
                    ComponentCard {
                        label: "popdown"
                        Column {
                            spacing: Fluent.Enums.spacing.xs
                            StackedWidget {
                                id: popdownStack; width: 110; height: 55
                                animationType: Fluent.Enums.animation.popdown
                                Rectangle { color: Fluent.Enums.demoPalette.sky; Text { anchors.centerIn: parent; text: "1"; color: Fluent.Enums.accentForeground } }
                                Rectangle { color: Fluent.Enums.demoPalette.lime; Text { anchors.centerIn: parent; text: "2"; color: Fluent.Enums.accentForeground } }
                            }
                            Row {
                                spacing: Fluent.Enums.spacing.xs
                                Button { text: "1"; width: 26; onClicked: popdownStack.currentIndex = 0 }
                                Button { text: "2"; width: 26; onClicked: popdownStack.currentIndex = 1 }
                            }
                        }
                    }
                    ComponentCard {
                        label: "slide"
                        Column {
                            spacing: Fluent.Enums.spacing.xs
                            StackedWidget {
                                id: slideStack; width: 110; height: 55
                                animationType: Fluent.Enums.animation.slide
                                Rectangle { color: Fluent.Enums.demoPalette.purple; Text { anchors.centerIn: parent; text: "1"; color: Fluent.Enums.accentForeground } }
                                Rectangle { color: Fluent.Enums.demoPalette.pink; Text { anchors.centerIn: parent; text: "2"; color: Fluent.Enums.accentForeground } }
                            }
                            Row {
                                spacing: Fluent.Enums.spacing.xs
                                Button { text: "1"; width: 26; onClicked: slideStack.currentIndex = 0 }
                                Button { text: "2"; width: 26; onClicked: slideStack.currentIndex = 1 }
                            }
                        }
                    }
                    ComponentCard {
                        label: "card"
                        Column {
                            spacing: Fluent.Enums.spacing.xs
                            StackedWidget {
                                id: cardStack; width: 110; height: 55
                                animationType: Fluent.Enums.animation.card
                                Rectangle { color: Fluent.Enums.demoPalette.cyan; Text { anchors.centerIn: parent; text: "1"; color: Fluent.Enums.accentForeground } }
                                Rectangle { color: Fluent.Enums.demoPalette.teal; Text { anchors.centerIn: parent; text: "2"; color: Fluent.Enums.accentForeground } }
                            }
                            Row {
                                spacing: Fluent.Enums.spacing.xs
                                Button { text: "1"; width: 26; onClicked: cardStack.currentIndex = 0 }
                                Button { text: "2"; width: 26; onClicked: cardStack.currentIndex = 1 }
                            }
                        }
                    }
                    ComponentCard {
                        label: "zoom"
                        Column {
                            spacing: Fluent.Enums.spacing.xs
                            StackedWidget {
                                id: zoomStack; width: 110; height: 55
                                animationType: Fluent.Enums.animation.zoom
                                Rectangle { color: Fluent.Enums.demoPalette.sky; Text { anchors.centerIn: parent; text: "1"; color: Fluent.Enums.accentForeground } }
                                Rectangle { color: Fluent.Enums.demoPalette.lime; Text { anchors.centerIn: parent; text: "2"; color: Fluent.Enums.accentForeground } }
                            }
                            Row {
                                spacing: Fluent.Enums.spacing.xs
                                Button { text: "1"; width: 26; onClicked: zoomStack.currentIndex = 0 }
                                Button { text: "2"; width: 26; onClicked: zoomStack.currentIndex = 1 }
                            }
                        }
                    }
                }
            }
            
            // Command bar views 命令栏视图
            ExampleCard {
                title: Fluent.Translator.tr("gallery_1b2a34ab3faa47a8", Fluent.Translator._v)
                description: "CommandBar (type_view)"
                ComponentCard {
                    label: "CommandBar View"
                    CommandBar { 
                        type: Fluent.Enums.commandBar.type_view
                        primaryCommands: [{text: Fluent.Translator.tr("gallery_50ef2f4cf6a46924", Fluent.Translator._v), icon: iconPath("DocumentAdd")}, {text: Fluent.Translator.tr("gallery_c771248e511fbf93", Fluent.Translator._v), icon: iconPath("FolderOpen")}, {text: Fluent.Translator.tr("gallery_a3030bf8f16dc63c", Fluent.Translator._v), icon: iconPath("Save")}, {separator: true}, {text: Fluent.Translator.tr("gallery_410a8e8a6bf253ac", Fluent.Translator._v), icon: iconPath("Cut")}, {text: Fluent.Translator.tr("gallery_63d90d977348ab1f", Fluent.Translator._v), icon: iconPath("Copy")}]
                    }
                }
            }
            
            // CommandBar
            ExampleCard {
                title: Fluent.Translator.tr("gallery_7e97e91f3221fc25", Fluent.Translator._v)
                description: "CommandBar"
                ComponentCard {
                    label: "CommandBar"
                    CommandBar { 
                        width: 380
                        primaryCommands: [
                            {icon: iconPath("DocumentAdd"), text: Fluent.Translator.tr("gallery_50ef2f4cf6a46924", Fluent.Translator._v)},
                            {icon: iconPath("FolderOpen"), text: Fluent.Translator.tr("gallery_c771248e511fbf93", Fluent.Translator._v)},
                            {icon: iconPath("Save"), text: Fluent.Translator.tr("gallery_a3030bf8f16dc63c", Fluent.Translator._v)}
                        ]
                        secondaryCommands: [
                            {icon: iconPath("Settings"), text: Fluent.Translator.tr("gallery_df3d58c7d84b85f2", Fluent.Translator._v)},
                            {icon: iconPath("QuestionCircle"), text: Fluent.Translator.tr("gallery_a57cfcb8428da408", Fluent.Translator._v)},
                            {icon: iconPath("QuestionCircle"), text: Fluent.Translator.tr("gallery_b5857e11ccce5cae", Fluent.Translator._v)},
                            {icon: iconPath("QuestionCircle"), text: Fluent.Translator.tr("gallery_e758fedc5fa97363", Fluent.Translator._v)},
                            {icon: iconPath("QuestionCircle"), text: Fluent.Translator.tr("gallery_8bdbd7f81a95dd3f", Fluent.Translator._v)},
                            {icon: iconPath("QuestionCircle"), text: Fluent.Translator.tr("gallery_11cf409424a0de6d", Fluent.Translator._v)}
                        ]
                    }
                }
            }
            
            // Pagination 分页器
            ExampleCard {
                title: Fluent.Translator.tr("gallery_4bf9ffa772b28b9d", Fluent.Translator._v)
                description: "Paginator"
                ComponentCard {
                    label: "Paginator"
                    Paginator { totalPages: 10; currentPage: 3 }
                }
            }
            
            // Menu bar 菜单栏
            ExampleCard {
                title: Fluent.Translator.tr("gallery_a304cb9cd6c523bb", Fluent.Translator._v)
                description: "MenuBar"
                ComponentCard {
                    label: "MenuBar"
                    MenuBar {
                        width: 400
                        items: [
                            {text: Fluent.Translator.tr("gallery_39932f24fe11a6ba", Fluent.Translator._v), children: [{text: Fluent.Translator.tr("gallery_50ef2f4cf6a46924", Fluent.Translator._v)}, {text: Fluent.Translator.tr("gallery_c771248e511fbf93", Fluent.Translator._v)}, {text: Fluent.Translator.tr("gallery_a3030bf8f16dc63c", Fluent.Translator._v)}]},
                            {text: Fluent.Translator.tr("gallery_051836569928a9f9", Fluent.Translator._v), children: [{text: Fluent.Translator.tr("gallery_926a50b98ece2667", Fluent.Translator._v)}, {text: Fluent.Translator.tr("gallery_03717b6f10700f87", Fluent.Translator._v)}]},
                            {text: Fluent.Translator.tr("gallery_a57cfcb8428da408", Fluent.Translator._v), children: [{text: Fluent.Translator.tr("gallery_52d25a9e30ba94f1", Fluent.Translator._v)}]}
                        ]
                    }
                }
            }

            // Command palette 命令面板
            ExampleCard {
                title: "CommandPalette"
                description: "Ctrl+K command surface"
                ComponentCard {
                    label: "CommandPalette"
                    Column {
                        spacing: Fluent.Enums.spacing.m
                        Button {
                            text: "Open palette (Ctrl+K)"
                            onClicked: galleryPalette.open()
                        }
                        Text {
                            id: galleryPaletteStatus
                            text: "No command ran yet"
                            font.pixelSize: Fluent.Enums.typography.caption
                            color: Fluent.Enums.textColor.secondary
                            font.family: Fluent.Enums.fontFamily
                        }
                    }
                }
            }

        }
    }

    // The palette is a modal overlay, so it lives at the page root rather than inside
    // a card: opening reparents it onto the window content item.
    // 命令面板是模态浮层, 因此挂在页面根而不是卡片里: 打开时会重挂到窗口内容项。
    CommandPalette {
        id: galleryPalette
        objectName: "galleryCommandPalette"
        shortcut: "Ctrl+K"
        placeholderText: "Type a command"
        hintText: "Up/Down navigate  Enter run  Esc close"
        items: [
            { key: "open-file", title: "Open File", subtitle: "Ctrl+O",
              section: "File", icon: iconPath("FolderOpen") },
            { key: "save-file", title: "Save File", subtitle: "Ctrl+S",
              section: "File", icon: iconPath("Save") },
            { key: "toggle-theme", title: "Toggle Theme", subtitle: "View",
              section: "View", icon: iconPath("DarkTheme"),
              keywords: ["dark", "light", "appearance"] },
            { key: "goto-navigation", title: "Go to Navigation", subtitle: "Go",
              section: "Navigate", icon: iconPath("Navigation") },
            { key: "open-settings", title: "Open Settings", subtitle: "Go",
              section: "Navigate", icon: iconPath("Settings") }
        ]
        onCommandTriggered: (key, item) => {
            galleryPaletteStatus.text = "Ran: " + key
        }
    }
}
