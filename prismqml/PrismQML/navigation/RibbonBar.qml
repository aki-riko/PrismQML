// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import "_internal"

// RibbonBar - Office-style ribbon bar 功能区
// Tabs are declared as children (RibbonTab), each hosting a row of RibbonGroup.
// The bar owns tab selection, the minimized/expanded panel and keyboard access.
// 标签由子项声明(RibbonTab), 每个标签承载一行 RibbonGroup。功能区负责标签选中、
// 折叠/展开面板与键盘可达。
Widget {
    id: control

    // ==================== Public Props 公开属性 ====================
    property int currentIndex: 0
    // Display state 显示状态: appBar_expanded (default) / appBar_compact (collapsed) / appBar_sticky
    property int displayState: Enums.commandBar.appBar_expanded
    // Open panel height; ribbon groups size themselves inside it
    // 展开面板高度; 分组在其内部自行定尺寸
    property int panelHeight: Enums.controlSize.commandBarButtonSize * 2
        + Enums.typography.captionCompact + Enums.spacing.m
    property bool keyboardEnabled: true
    // Caller tabs, collected from the declared RibbonTab children 调用方标签, 取自声明的 RibbonTab 子项
    // Only RibbonTab children join the ribbon contract; any other declared child
    // stays in the tab host and is ignored by selection. 只有 RibbonTab 子项参与功能区
    // 契约; 其它子项留在标签宿主内, 不参与选中逻辑。
    default property alias tabData: tabHost.data

    // ==================== Internal Props 内部属性 ====================
    // The ribbon is the display-state host its groups and buttons inherit from.
    // 功能区是分组与按钮继承显示状态的宿主。
    readonly property bool _isAppBarDisplayStateHost: true
    // childItems() is not reactive, so tab creation bumps this key.
    // childItems() 不具响应性, 因此标签增删时递增此键。
    property int _tabRevision: 0

    // ==================== Readonly State 只读状态 ====================
    readonly property bool minimized: displayState === Enums.commandBar.appBar_compact
    readonly property bool sticky: displayState === Enums.commandBar.appBar_sticky
    readonly property bool panelExpanded: displayState === Enums.commandBar.appBar_expanded
    readonly property string appBarStateName: sticky ? "sticky"
        : (minimized ? "compact" : "expanded")
    readonly property int tabCount: _tabItems.length
    readonly property int _tabStripHeight: Enums.controlSize.tabBarHeight
    readonly property real _openPanelHeight: Math.max(
        Enums.controlSize.commandBarButtonSize, panelHeight)
    readonly property var _tabItems: {
        var revision = _tabRevision
        return _collectTabs()
    }

    // ==================== Signals 信号 ====================
    signal currentChanged(int index)
    signal tabClicked(int index)
    signal expansionChanged(bool minimized)

    // ==================== Public Methods 公开方法 ====================
    function setCurrentIndex(index) {
        if (index < 0 || index >= _tabItems.length) return
        if (currentIndex === index) return
        currentIndex = index
    }

    function count() { return _tabItems.length }

    function tabAt(index) {
        return index >= 0 && index < _tabItems.length ? _tabItems[index] : null
    }

    function tabTitle(index) {
        var tab = tabAt(index)
        return tab ? (tab.title || "") : ""
    }

    function setDisplayState(state) { displayState = state }

    function minimize() { displayState = Enums.commandBar.appBar_compact }

    function expand() { displayState = Enums.commandBar.appBar_expanded }

    function pin() { displayState = Enums.commandBar.appBar_sticky }

    function toggleMinimized() {
        displayState = minimized ? Enums.commandBar.appBar_expanded
            : Enums.commandBar.appBar_compact
    }

    function cycleDisplayState() {
        var next = sticky ? Enums.commandBar.appBar_compact
            : (minimized ? Enums.commandBar.appBar_expanded
                : Enums.commandBar.appBar_sticky)
        displayState = next
        return next
    }

    // Report the active tab to a host that wants to run its command
    // 向需要执行命令的宿主上报当前标签
    function activateCurrentTab() {
        if (_tabItems.length > 0) tabClicked(currentIndex)
    }

    // ==================== Internal Methods 内部方法 ====================
    function _collectTabs() {
        var tabs = []
        var children = tabHost ? tabHost.children : []
        for (var i = 0; i < children.length; i++) {
            if (children[i].isRibbonTab === true) tabs.push(children[i])
        }
        return tabs
    }

    // Single writer of tabIndex/selected and the only clamp of currentIndex.
    // tabIndex/selected 的唯一写入者, 也是 currentIndex 的唯一收敛点。
    function _syncTabs() {
        var tabs = _tabItems
        if (tabs.length === 0) {
            if (currentIndex !== 0) currentIndex = 0
            return
        }
        var clamped = Math.max(0, Math.min(currentIndex, tabs.length - 1))
        for (var i = 0; i < tabs.length; i++) {
            tabs[i].tabIndex = i
            tabs[i].selected = (i === clamped)
        }
        if (clamped !== currentIndex) currentIndex = clamped
    }

    function _selectRelative(delta) {
        var total = _tabItems.length
        if (total === 0) return
        setCurrentIndex((currentIndex + delta + total) % total)
    }

    // ==================== Size 尺寸 ====================
    contentWidth: Enums.controlSize.chartDefaultWidth
    // The bar grows with the animated panel so collapsing really reclaims height.
    // 条高随动画面板增长, 折叠时真实回收高度。
    contentHeight: _tabStripHeight + panelHost.height
    activeFocusOnTab: keyboardEnabled
    onCurrentIndexChanged: {
        currentChanged(currentIndex)
        _syncTabs()
    }
    // Report the derived flag, not the raw state: the state change signal runs
    // before dependent bindings refresh. 上报派生标记而非原始状态: 状态变更信号先于
    // 依赖绑定刷新。
    onMinimizedChanged: expansionChanged(minimized)
    // The child list can notify before the new tab is appended, so re-sync once more
    // on the next event-loop turn. 子项列表的通知可能早于新标签页入列, 因此在下一个
    // 事件循环轮次再同步一次。
    on_TabRevisionChanged: {
        _syncTabs()
        Qt.callLater(control._syncTabs)
    }
    onKeyboardEnabledChanged: if (!keyboardEnabled && activeFocus) focus = false
    Keys.onLeftPressed: (event) => {
        control._selectRelative(-1)
        event.accepted = true
    }
    Keys.onRightPressed: (event) => {
        control._selectRelative(1)
        event.accepted = true
    }
    Keys.onReturnPressed: control.activateCurrentTab()
    Keys.onEnterPressed: control.activateCurrentTab()
    Keys.onSpacePressed: control.activateCurrentTab()
    Keys.onPressed: (event) => {
        if (event.key === Qt.Key_F1 && (event.modifiers & Qt.ControlModifier)) {
            control.toggleMinimized()
            event.accepted = true
        }
    }
    Component.onCompleted: _syncTabs()

    // ==================== Content 内容 ====================
    Rectangle {
        id: stripBackground

        objectName: "ribbonStripBackground"
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: control._tabStripHeight
        color: Enums.cardColor
    }

    Button {
        id: minimizeButton

        objectName: "ribbonMinimizeButton"
        anchors.right: parent.right
        anchors.rightMargin: Enums.spacing.xs
        anchors.verticalCenter: stripBackground.verticalCenter
        style: Enums.button.style_transparent
        flat: true
        icon: control.minimized ? Enums.icon.chevron_down : Enums.icon.chevron_up
        iconSize: Enums.iconSize.m
        preferredWidth: Enums.controlSize.commandBarButtonSize
        preferredHeight: Enums.controlSize.commandBarButtonSize
        onClicked: control.toggleMinimized()
    }

    Row {
        id: tabStrip

        objectName: "ribbonTabStrip"
        anchors.left: parent.left
        anchors.leftMargin: Enums.spacing.xs
        anchors.right: minimizeButton.left
        anchors.rightMargin: Enums.spacing.xs
        anchors.top: parent.top
        height: control._tabStripHeight
        spacing: Enums.spacing.none
        clip: true

        Repeater {
            id: tabStripRepeater
            model: control._tabItems

            RibbonTabButton {
                host: control
                objectName: "ribbonTabButton_" + index
                onActivated: (tabIndex) => control.setCurrentIndex(tabIndex)
            }
        }
    }

    Rectangle {
        id: headerDivider

        objectName: "ribbonStripDivider"
        anchors.top: stripBackground.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: Enums.border.thin
        color: Enums.stateColor.divider
    }

    Item {
        id: panelHost

        objectName: "ribbonPanelHost"
        anchors.top: headerDivider.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: control.minimized ? 0 : control._openPanelHeight
        clip: true

        Behavior on height {
            NumberAnimation {
                duration: Enums.duration.fast
                easing.type: Easing.OutCubic
            }
        }

        Rectangle {
            id: panelBackground

            anchors.fill: parent
            color: Enums.cardColor
        }

        Item {
            id: tabHost

            objectName: "ribbonTabHost"
            anchors.fill: parent
            onChildrenChanged: control._tabRevision++
        }
    }
}
