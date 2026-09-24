// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import PrismQML
import PrismQML as Fluent

// NavigationPanelShowcase - Gallery card for the window-level vertical panels
// 导航面板展示卡 - 窗口级垂直导航面板
// Extracted from NavigationPage so that page stays inside its line budget.
// 从 NavigationPage 抽出, 使该页面保持在行数预算内。
// The pane demonstrably expands and collapses in place: one NavigationView, an
// animated clipped frame, and the acrylic layer fed the same way the window shell
// feeds it. 面板在原地真实展开/折叠: 单个 NavigationView、带动画的裁剪外框, 以及按窗口
// 外壳同样方式喂图的亚克力层。
ExampleCard {
    id: showcase

    // ==================== Internal Props 内部属性 ====================
    // Shared model for the vertical navigation panels. Text and labels stay ASCII on
    // purpose: the Gallery i18n contract only localizes user-visible literals.
    // 垂直导航面板共用模型。文本刻意保持 ASCII: 画廊 i18n 合同只本地化用户可见文案。
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
    // Acrylic state, owned here exactly like the window shell owns it
    // 亚克力状态, 与窗口外壳一样由这里持有
    property string _paneAcrylicSource: ""
    property bool _paneAcrylicReady: false

    // ==================== Public Methods 公开方法 ====================
    function iconPath(name) {
        return Fluent.Enums.iconPath + name + ".svg"
    }

    // Display modes the merged NavigationView demo can switch between
    // 合并后的 NavigationView 示例可切换的显示模式
    function navPaneModes() {
        return [
            Fluent.Enums.navigation.pane_left,
            Fluent.Enums.navigation.pane_left_compact,
            Fluent.Enums.navigation.pane_left_minimal,
            Fluent.Enums.navigation.pane_auto
        ]
    }

    function setNavPaneMode(index) {
        var modes = navPaneModes()
        if (index >= 0 && index < modes.length) {
            galleryNavPane.paneDisplayMode = modes[index]
        }
    }

    function navPaneModeName(mode) {
        if (mode === Fluent.Enums.navigation.pane_left) return "left"
        if (mode === Fluent.Enums.navigation.pane_left_compact) return "left_compact"
        if (mode === Fluent.Enums.navigation.pane_left_minimal) return "left_minimal"
        if (mode === Fluent.Enums.navigation.pane_auto) return "auto"
        return "unspecified"
    }

    // Frame width the current mode asks for. Every mode except pane_auto follows the
    // pane's own expanded state; that is what makes the collapse animate instead of
    // leaving the frame at the design width.
    // 当前模式要求的外框宽度。除 pane_auto 外都跟随面板自身的展开状态; 这正是折叠能够
    // 动画化、而不是把外框留在设计宽度的原因。
    function navPaneTargetWidth() {
        var compact = Fluent.Enums.controlSize.navPanelCompactWidth
        var expanded = Fluent.Enums.controlSize.navPanelExpandWidth
        var index = navPaneModeBar.currentIndex
        // pane_auto is width-driven, so the host owns the width 宽度驱动, 由宿主给宽
        if (index === 3) return navPaneWidth.value
        // pane_left_minimal opens an overlay pane 极简模式开关浮层面板
        if (index === 2) return galleryNavPane.isPaneOpen ? expanded : compact
        return galleryNavPane.isExpanded ? expanded : compact
    }

    // Capture the acrylic backdrop the way the window shell does: once, on the way
    // into the expanded state, then reuse it until the pane collapses again.
    // 按窗口外壳的方式抓一次亚克力背景: 进入展开态时抓取, 折叠后再次展开时重抓。
    function capturePaneAcrylic() {
        if (typeof AcrylicHelper === "undefined" || !AcrylicHelper
                || !AcrylicHelper.isAvailable) {
            return
        }
        var hostWindow = navPaneFrame.Window.window
        if (!hostWindow) return
        var origin = navPaneFrame.mapToItem(null, 0, 0)
        var url = AcrylicHelper.grabAndBlur(
            hostWindow,
            Math.round(origin.x), Math.round(origin.y),
            Math.round(navPaneFrame.width), Math.round(navPaneFrame.height))
        if (url !== "") {
            _paneAcrylicSource = url
            _paneAcrylicReady = true
        }
    }

    // ==================== Size 尺寸 ====================
    title: "Vertical navigation"
    description: "NavigationView / NavigationBar / ToggleNavigationBar"

    // ==================== Content 内容 ====================
    ComponentCard {
        label: "NavigationView (expand / collapse + acrylic)"
        Column {
            spacing: Fluent.Enums.spacing.m

            SelectorBar {
                id: navPaneModeBar
                objectName: "galleryNavPaneModeBar"
                items: [
                    { "key": "left", "text": "Left" },
                    { "key": "compact", "text": "Compact" },
                    { "key": "minimal", "text": "Minimal" },
                    { "key": "auto", "text": "Auto" }
                ]
                onItemClicked: (index) => showcase.setNavPaneMode(index)
            }

            Row {
                spacing: Fluent.Enums.spacing.m

                Column {
                    spacing: Fluent.Enums.spacing.s

                    // The frame is a clipping host with an animated width, exactly like
                    // the window shell's nav container: the pane keeps its expanded
                    // geometry and is revealed or hidden instead of reflowing.
                    // 外框是与窗口外壳导航容器相同的"裁剪宿主 + 宽度动画": 面板保持展开几何,
                    // 靠裁剪露出或遮住, 而不是每帧重排。
                    Rectangle {
                        id: navPaneFrame
                        objectName: "galleryNavPaneFrame"
                        property bool isAnimating: false

                        width: showcase.navPaneTargetWidth()
                        height: 340
                        radius: Fluent.Enums.radius.large
                        color: Fluent.Enums.surfaceColor
                        border.width: Fluent.Enums.border.thin
                        border.color: Fluent.Enums.borderColor
                        clip: true

                        Behavior on width {
                            NumberAnimation {
                                duration: Fluent.Enums.duration.medium
                                easing.type: Easing.OutCubic
                                onRunningChanged: navPaneFrame.isAnimating = running
                            }
                        }

                        NavigationView {
                            id: galleryNavPane
                            objectName: "galleryNavPane"
                            // pane_auto reads the pane's own width, so auto follows the
                            // frame; every other mode keeps the design width and is
                            // clipped by the frame. pane_auto 读取自身宽度, 因此 auto
                            // 跟随外框; 其它模式保持设计宽度, 由外框裁剪。
                            width: navPaneModeBar.currentIndex === 3
                                ? navPaneFrame.width
                                : Fluent.Enums.controlSize.navPanelExpandWidth
                            height: parent.height
                            showReturnButton: false
                            // The panels normally reserve the window title-bar strip,
                            // which does not exist inside a page.
                            // 面板默认为窗口标题栏预留高度, 页面里没有标题栏。
                            titleBarHeight: 0
                            // Expanded is the useful default; the pane's own button
                            // collapses it to the icon rail from here.
                            // 默认展开更实用; 从这里起用面板自己的按钮即可折叠成图标栏。
                            paneDisplayMode: Fluent.Enums.navigation.pane_left
                            model: showcase.navPanelModel
                            bottomItems: [
                                { "text": "Account", "icon": showcase.iconPath("Person"), "selectable": false }
                            ]
                            acrylicEnabled: (isExpanded || navPaneFrame.isAnimating)
                                && showcase._paneAcrylicReady
                            acrylicImageSource: showcase._paneAcrylicSource
                            // The panels never move their own selection: they emit
                            // itemClicked and expect the host shell to push a new
                            // currentIndex back (single-direction binding). Inside a
                            // page this handler IS that shell.
                            // 面板不会自己改选中项: 它只发 itemClicked, 由宿主外壳回灌
                            // currentIndex（单向绑定）。页面里这段接线就是那个外壳。
                            onItemClicked: (index) => {
                                if (index >= 0 && index < showcase.navPanelModel.length)
                                    currentIndex = index
                            }
                            onAboutToExpand: showcase.capturePaneAcrylic()
                            onIsExpandedChanged: if (isExpanded) showcase.capturePaneAcrylic()
                            onIsPaneOpenChanged: if (isPaneOpen) showcase.capturePaneAcrylic()
                            onPaneDisplayModeChanged: {
                                navPaneModeBar.currentIndex =
                                    showcase.navPaneModes().indexOf(paneDisplayMode)
                                if (isExpanded) showcase.capturePaneAcrylic()
                            }
                            Component.onCompleted: navPaneModeBar.currentIndex =
                                showcase.navPaneModes().indexOf(paneDisplayMode)
                        }
                    }

                    Slider {
                        id: navPaneWidth
                        objectName: "galleryNavPaneWidth"
                        width: navPaneFrame.width
                        from: 120
                        to: 420
                        value: 380
                    }
                }

                Column {
                    spacing: Fluent.Enums.spacing.s

                    Label {
                        type: Fluent.Enums.label.type_caption
                        text: "mode: " + showcase.navPaneModeName(galleryNavPane.effectivePaneDisplayMode)
                    }
                    Label {
                        type: Fluent.Enums.label.type_caption
                        text: "expanded: " + galleryNavPane.isExpanded
                    }
                    Label {
                        type: Fluent.Enums.label.type_caption
                        text: "pane open: " + galleryNavPane.isPaneOpen
                    }
                    Label {
                        objectName: "galleryNavPaneFrameWidth"
                        type: Fluent.Enums.label.type_caption
                        text: "frame width: " + Math.round(navPaneFrame.width)
                    }
                    Label {
                        objectName: "galleryNavPaneAcrylicState"
                        type: Fluent.Enums.label.type_caption
                        text: "acrylic: " + (showcase._paneAcrylicReady ? "on" : "off")
                    }
                    Button {
                        text: "toggle()"
                        onClicked: galleryNavPane.toggle()
                    }
                    Button {
                        text: "togglePane()"
                        onClicked: galleryNavPane.togglePane()
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
                model: showcase.navPanelScrollModel
                onItemClicked: (index) => {
                    if (index >= 0 && index < showcase.navPanelScrollModel.length)
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
                model: showcase.navPanelModel
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
