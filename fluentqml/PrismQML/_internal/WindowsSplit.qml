// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../navigation"
import "../controls/navigation"
import "../controls/data"
import ".."

// Window - Expandable side navigation window 展开式侧边导航窗口
// nav panel is 320px wide, compact mode just clips to 48px
// 导航栏本身320px宽，紧凑模式只是裁剪显示到48px
NavigationWindowCore {
 id: window
 
 windowTitle: "Window"
 titleBarHeight: Enums.window.titleBarHeight
 
 // 兼容原有的 default property 语法，将初始元素缓存到一个不显示的节点
 Item { id: _hiddenStack; visible: false }
 default property alias pages: _hiddenStack.data
 
 // Navigation panel width constants 导航栏宽度常量
 readonly property int navCompactWidth: Enums.controlSize.navPanelCompactWidth
 readonly property int navExpandWidth: Enums.controlSize.navPanelExpandWidth
 
 // ==================== Lazy Loading Properties 懒加载属性 ====================
 property list<Component> pageComponents
 property var pageSources: []
 
 Component.onCompleted: {
 logTime("Window ready, lazyLoading: " + lazyLoading)
 // 无论 micaEnabled 是 true 或 false 都 apply,确保持久化关闭状态生效
 // (NavigationWindowCore 已有同样逻辑,这里是子类的额外初始化点)
 if (_micaAvailable && MicaManager) {
 MicaManager.setMicaEffect(window, micaEnabled, Enums.isDark)
 }
 }
 
 content: Item {
 anchors.fill: parent
 anchors.topMargin: -window.titleBarHeight

 // 点击空白区域清除输入焦点
 MouseArea {
 anchors.fill: parent
 z: -999
 onClicked: parent.forceActiveFocus()
 }
 
 // ==================== 异步加载核心UI ====================
 // Delay activate Loader to ensure Window and Splash rendering first 延迟激活以便首先渲染并展示窗口及SplashScreen
 Timer {
 id: startupTimer
 interval: 50
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
 
 if (_hiddenStack.data.length > 0) {
 let container = window.stackedWidget.containerItem
 let items = []
 for(let i=0; i<_hiddenStack.data.length; i++) {
 items.push(_hiddenStack.data[i])
 }
 for(let i=0; i<items.length; i++) {
 let child = items[i]
 child.parent = container
 child.width = Qt.binding(function() { return container.width })
 child.height = Qt.binding(function() { return container.height })
 child.x = 0
 child.y = 0
 child.scale = 1
 child.visible = (i === window.stackedWidget.currentIndex)
 child.opacity = (i === window.stackedWidget.currentIndex ? 1 : 0)
 }
 }
 
 // 等主页(首屏)真正加载完成再关欢迎页, 而非框架壳加载完就关
 window._dismissSplashWhenReady(window.stackedWidget)
 }
 }
 
 Component {
 id: coreComponent
 Item {
 id: componentRoot
 anchors.fill: parent
 property alias navAlias: navInterface
 property alias stackAlias: stack
 
 // ==================== Content Area 内容区域 ====================
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
 anchors.fill: parent
 animationType: Enums.animation.popup

 // 绑定外部保存的页面数据
 pageComponents: window.pageComponents
 pageSources: window.pageSources
 lazyLoading: window.lazyLoading
 // 单向绑定 window.currentIndex → stack.currentIndex
 // currentIndex 为纯输入, StackedWidget 内部不再命令式写它
 // (改用 _displayIndex 驱动显示), 故声明式绑定不会被打破。
 currentIndex: window.currentIndex

 // Alias to access its layout component quickly 快捷方式绑定访问其内部容器
 property alias contentContainerAlias: stack.content
 onCurrentChanged: (index) => {
 // 反向同步 (动画结束后), 通常 window.currentIndex 已被设
 if (window.currentIndex !== index) window.currentIndex = index
 }
 }
 
 LoadingOverlay {
 anchors.fill: parent
 loading: window._pythonLoading
 backgroundColor: window.contentBgColor
 text: window.loadingText
 }
 }
 
 // ==================== Navigation Panel Container 导航面板容器 ====================
 Item {
 id: navContainer
 anchors.left: parent.left
 anchors.top: parent.top
 anchors.topMargin: -window.titleBarHeight
 anchors.bottom: parent.bottom
 width: navInterface.isExpanded ? window.navExpandWidth : window.navCompactWidth
 clip: true
 z: Enums.zIndex.popup
 
 property bool isAnimating: false
 
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

 property bool _acrylicImageReady: false
 property string _acrylicSource: ""

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
 
 // Click Outside to Collapse
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
}
