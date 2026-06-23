// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import "../../.."
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// ScrollAreaList - Virtualized list scroll area 虚拟化列表滚动区域
// Only renders visible items 只渲染可见项
// Refactored to use SmoothScrollHelper 重构为使用SmoothScrollHelper
Item {
    id: control
    
    // ==================== Props 属性 ====================
    property var model: []
    property Component delegate: null
    property int itemHeight: 40
    property int spacing: 0  // 列表项间距 (用于卡片化场景需要间隙时)
    property bool reuseItems: false  // delegate 复用 (Qt 5.15+, 避免大列表频繁 create/destroy)
    property int cacheBuffer: -1  // -1 = 用引擎默认值 itemHeight*10; 长 delegate 场景可调小
    // 重 delegate (含 ComboBox/SpinBox/复杂布局) 场景: 用 Loader.asynchronous 包一层,
    // ListView instantiate Loader 几乎零开销, 真卡片内容下一帧异步填充, 首次滚动不卡
    property bool delegateAsync: false
    property bool showScrollBar: true
    property bool alwaysShowScrollBar: false  // true=滚动条常显, false=AsNeeded
    property int scrollBarWidth: Enums.controlSize.scrollBarWidth
    property bool smoothScroll: true
    property int scrollDuration: Enums.duration.scroll
    property real scrollStep: Enums.spacing.xxxl * 3
    property int scrollEasing: Easing.OutQuart
    // 边界 bounce: true=继续滚露出空白回弹 (默认), false=硬切到边界 (避免顶部/底部空白闪烁)
    property bool bounceEnabled: true
    property int currentIndex: -1
    property bool selectable: true
    
    // ==================== Expose props 暴露属性 ====================
    property alias contentY: listView.contentY
    property alias contentHeight: listView.contentHeight
    readonly property alias listView: listView
    readonly property int count: listView.count
    
    // ==================== Signals 信号 ====================
    signal itemClicked(int index, var item)
    signal indexChanged(int index)

    // ==================== Public Methods 公开方法 ====================
    function scrollToIndex(index) { scrollHelper.scrollTo(index * itemHeight) }
    function scrollToTop() { scrollHelper.scrollToStart() }
    function scrollToBottom() { scrollHelper.scrollToEnd() }
    function smoothScrollTo(targetY) { scrollHelper.scrollTo(targetY) }
    function smoothScrollBy(delta) { scrollHelper.scrollBy(delta) }

    // ==================== ListView 列表视图 ====================
    ListView {
        id: listView
        anchors.fill: parent
        anchors.rightMargin: showScrollBar && contentHeight > height ? scrollBarWidth + Enums.spacing.xs : 0

        model: control.model
        // delegateAsync 模式: 包一层 Loader.asynchronous=true, ListView instantiate
        // 极快; 真 delegate 下一帧异步填充, 首次滚动平滑
        delegate: control.delegateAsync ? asyncDelegate : control.delegate
        spacing: control.spacing
        reuseItems: control.reuseItems
        clip: true
        interactive: false
        cacheBuffer: control.cacheBuffer >= 0 ? control.cacheBuffer : itemHeight * 10
        currentIndex: control.currentIndex
        onCurrentIndexChanged: control.indexChanged(currentIndex)

        highlight: selectable ? highlightComp : null
        highlightFollowsCurrentItem: true
        highlightMoveDuration: Enums.duration.fast
    }

    // 异步 delegate 包装: Loader 几乎零创建成本, 真组件下一帧填充。
    // 关键: ListView 把 index/model 注入到 Loader (它才是 ListView 的直接 delegate),
    // Loader.item (sourceComponent 实例) 拿不到。这里显式 reify 成 Loader 的 properties
    // (delegateIndex / delegateModel), 业务 delegate 内用 parent.delegateIndex /
    // parent.delegateModel 访问。
    Component {
        id: asyncDelegate
        Loader {
            width: ListView.view ? ListView.view.width : 0
            height: control.itemHeight
            asynchronous: true
            sourceComponent: control.delegate
            // 关键: ListView 注入的 index/model 在 Loader scope 可见, binding 成 properties
            // 让 Loader.item 通过 parent 访问
            property int delegateIndex: index
            property var delegateModel: model
        }
    }
    
    Component {
        id: highlightComp
        Rectangle {
            color: Enums.stateColor.accentLight
            radius: Enums.radius.small
            Rectangle {
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                width: Enums.border.thick
                height: Enums.spacing.xl
                radius: Enums.radius.micro
                color: Enums.accentColor
            }
        }
    }
    
    // ==================== Smooth Scroll Helper 平滑滚动助手 ====================
    SmoothScrollHelper {
        id: scrollHelper
        target: listView
        orientation: Qt.Vertical
        enabled: control.smoothScroll
        duration: control.scrollDuration
        step: control.scrollStep
        easing: control.scrollEasing
        bounceEnabled: control.bounceEnabled
        handleWheel: true
    }
    
    // ==================== Scrollbar 滚动条 ====================
    ScrollBar {
        id: vBar
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.margins: Enums.spacing.xxs
        
        target: listView
        scrollHelper: scrollHelper
        orientation: Qt.Vertical
        barWidth: scrollBarWidth
        visible: showScrollBar && (alwaysShowScrollBar || listView.contentHeight > listView.height)
    }
}
