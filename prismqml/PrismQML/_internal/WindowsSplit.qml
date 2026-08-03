// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../navigation"
import "../controls/navigation"
import "../controls/data"
import ".."

// WindowsSplit - Expandable side navigation window 展开式侧边导航窗口
// The navigation panel keeps its expanded width and clips in compact mode.
// 导航面板保持展开宽度，紧凑模式通过裁剪显示。
NavigationWindowCore {
 id: window

 // ==================== Public Props 公开属性 ====================
 default property alias pages: _hiddenStack.data
 property var pageSources: []

 // ==================== Readonly State 只读状态 ====================
 readonly property int navCompactWidth: Enums.controlSize.navPanelCompactWidth
 readonly property int navExpandWidth: Enums.controlSize.navPanelExpandWidth

 windowTitle: "Window"
 titleBarHeight: Enums.window.titleBarHeight

 Component.onCompleted: {
 logTime("Window ready, lazyLoading: " + lazyLoading)
 // Apply both true and false so a persisted disabled state takes effect.
 // true 和 false 都执行，以确保持久化的关闭状态生效。
 if (_micaAvailable && MicaManager) {
 MicaManager.setMicaEffect(window, micaEnabled, Enums.isDark)
 }
 }
 
 content: Item {
 anchors.fill: parent
 anchors.topMargin: -window.titleBarHeight

 // Clear input focus from blank space. 点击空白区域清除输入焦点。
 MouseArea {
 anchors.fill: parent
 z: -999
 onClicked: parent.forceActiveFocus()
 }
 
 // Load the core UI asynchronously after the first window and splash frame.
 // 首个窗口与欢迎页帧渲染后再异步加载核心界面。
 Timer {
 id: startupTimer
 interval: Enums.window.splitStartupDelayMs
 running: true
 onTriggered: coreLoader.active = true
 }

 Loader {
 id: coreLoader
 anchors.fill: parent
 active: false
 asynchronous: true
 sourceComponent: coreComponent
 onLoaded: {
 window.navigationView = item.navAlias
 window.stackedWidget = item.stackAlias
 
 try {
 if (_hiddenStack.data.length > 0) {
 window._moveDefaultPages(
 _hiddenStack.data,
 window.stackedWidget.containerItem,
 "WindowsSplit"
 )
 }
 } finally {
 // Dismiss the splash after the home page is ready, not after the shell alone. 首页就绪后再关闭欢迎页，而不是仅等待框架壳。
 window._dismissSplashWhenReady(window.stackedWidget)
 }
 }
 }
 
 Component {
 id: coreComponent
 Item {
 id: componentRoot
 property alias navAlias: navInterface
 property alias stackAlias: stack

 anchors.fill: parent

 // Content area. 内容区域。
 ContentFrame {
 id: contentFrame
 anchors.left: parent.left
 anchors.leftMargin: window.navCompactWidth
 anchors.top: parent.top
 anchors.topMargin: window.titleBarHeight
 anchors.right: parent.right
 anchors.bottom: parent.bottom
 backgroundColor: window.contentBgColor
 cornerRadius: window.contentCornerRadius
 
 StackedWidget {
 id: stack
 property alias contentContainerAlias: stack.content

 anchors.fill: parent
 animationType: Enums.animation.popup
 lazyActivationDelay: navInterface.indicatorAnimationEnabled
     ? Enums.duration.dialog : Enums.duration.none

 // Bind externally stored page data. 绑定外部保存的页面数据。
 pageSources: window.pageSources
 lazyLoading: window.lazyLoading
 _pythonPageMode: window._pythonPageMode
 // Bind window.currentIndex to stack.currentIndex in one direction.
 // 单向绑定 window.currentIndex 到 stack.currentIndex；内部显示由 _displayIndex 驱动。
 currentIndex: window.currentIndex

 onCurrentChanged: (index) => {
 // Synchronize back after animation when needed. 动画结束后按需反向同步。
 if (window.currentIndex !== index) window.currentIndex = index
 }
 }
 
 Loader {
 objectName: "loadingOverlayLoader"
 anchors.fill: parent
 active: window._pythonLoading
 visible: active
 asynchronous: false
 sourceComponent: LoadingOverlay {
 objectName: "loadingOverlay"
 loading: window._pythonLoading
 backgroundColor: window.contentBgColor
 text: window.loadingText
 }
 }
 }
 
 // Navigation panel container. 导航面板容器。
 Item {
 id: navContainer
 property bool isAnimating: false

 anchors.left: parent.left
 anchors.top: parent.top
 anchors.topMargin: -window.titleBarHeight
 anchors.bottom: parent.bottom
 width: navInterface.isExpanded ? window.navExpandWidth : window.navCompactWidth
 clip: true
 z: Enums.zIndex.popup
 
 Behavior on width {
 NumberAnimation {
 id: navWidthAnim
 duration: Enums.duration.medium
 easing.type: Easing.OutCubic
 onRunningChanged: {
 navContainer.isAnimating = running
 if (!running && !navInterface.isExpanded) {
 navInterface._acrylicImageReady = false
 }
 }
 }
 }
 
 NavigationView {
 id: navInterface
 property bool _acrylicImageReady: false
 property string _acrylicSource: ""

 anchors.left: parent.left
 anchors.top: parent.top
 anchors.bottom: parent.bottom
 width: window.navExpandWidth
 model: window.navigationItems
 bottomItems: window.bottomNavigationItems
 showReturnButton: true
 // 单向绑定 window.currentIndex → navInterface.currentIndex
 currentIndex: window.currentIndex

 backgroundColor: window._micaActive ? Enums.transparent : Enums.backgroundColor
 acrylicEnabled: (isExpanded || navContainer.isAnimating) && window._micaActive && _acrylicImageReady
 acrylicImageSource: _acrylicSource

 onAboutToExpand: {
 if (window._micaActive && AcrylicHelper && AcrylicHelper.isAvailable) {
 var grabX = 0
 var grabY = 0
 var grabW = window.navExpandWidth
 var grabH = window.height
 var imageUrl = AcrylicHelper.grabAndBlur(window, grabX, grabY, grabW, grabH)
 if (imageUrl) {
 _acrylicSource = imageUrl
 _acrylicImageReady = true
 }
 }
 }

 onItemClicked: (index) => {
 window.currentIndex = index
 window.currentPageChanged(index)
 if (isExpanded) collapse()
 }
 onBottomItemClicked: (index) => {
 window._handleBottomItemClicked(index, navInterface, stack, window.pageSources)
 if (isExpanded) collapse()
 }
 }
 }
 
 // Click outside to collapse. 点击外部区域时收起。
 MouseArea {
 anchors.left: navContainer.right
 anchors.top: parent.top
 anchors.topMargin: window.titleBarHeight
 anchors.right: parent.right
 anchors.bottom: parent.bottom
 visible: navInterface.isExpanded
 z: Enums.zIndex.modal
 onClicked: navInterface.collapse()
 }
 }
 }
 }
 
 titleBarLeftMargin: navCompactWidth

 // Preserve default-property pages in a hidden staging item. 在隐藏暂存项中保留 default property 页面。
 Item { id: _hiddenStack; visible: false }
}
