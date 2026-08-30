// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick as QtQ
import QtQuick.Layouts
import "../.."
import "_internal"
import QtQuick

// DataWidgetCore - Base class for ListWidget/TableWidget 数据组件基类
// Orchestrates model and scrolling state while DataWidgetContent owns rendering.
// 编排模型与滚动状态，渲染由 DataWidgetContent 负责。
Rectangle {
    id: root

    // ==================== Public Props 公开属性 ====================
    // Layout attached properties for parent layouts 供父布局使用的附加属性
    property bool layoutFillWidth: true
    property bool layoutFillHeight: true
    property int layoutAlignment: 0

    property string emptyText: ""
    property string footerText: ""
    property bool showFooter: false
    property int rowHeight: Enums.controlSize.tableHeaderHeight

    // Item count defaults to the internally maintained ListView count 项目数默认由内部 ListView 自维护
    property int itemCount: _autoItemCount

    // Header 表头
    property bool showHeader: false
    property int headerHeight: Enums.controlSize.tableHeaderHeight
    property Component headerContent: null

    // Horizontal scroll 横向滚动
    // Subclasses publish their total column width here. 子类在此提供列总宽度。
    property real contentTotalWidth: 0

    // Scrollbars 滚动条
    property bool showScrollBar: true
    property int scrollBarWidth: Enums.controlSize.scrollBarWidth

    // Smooth scroll 平滑滚动
    property bool smoothScroll: true
    property int scrollDuration: Enums.duration.scroll
    property real scrollStep: Enums.spacing.xxxl * 3
    property int scrollEasing: Easing.OutQuart

    // Card style 卡片风格
    property bool showShadow: true
    property var shadowLevel: Enums.shadow.level8
    property real cardMargin: Enums.spacing.m
    property bool borderVisible: true
    property int borderRadius: Enums.radius.large
    property color cardColor: Enums.cardColor

    readonly property int _effectiveBorderRadius: Enums.isVintageTicket
                                                   ? Enums.ticket.radius : borderRadius

    // Animation 动画
    property bool animated: true
    property bool hoverElevation: false
    property bool loading: false
    property int staggerDelay: Enums.duration.stagger

    // ListView access ListView 访问
    property alias listView: contentLayer.listView
    property alias contentDelegate: contentLayer.contentDelegate
    property alias listModel: contentLayer.listModel
    property alias spacing: contentLayer.spacing

    // ==================== Internal Props 内部属性 ====================
    property int _autoItemCount: 0
    property bool _horizontalScrollRequested: false
    property bool _horizontalScrollLifecycleReady: false
    property Item _horizontalScrollMixin: null

    // ==================== Readonly State 只读状态 ====================
    readonly property alias _needsVerticalScrollBar:
        contentLayer.needsVerticalScrollBar
    readonly property alias _needsHorizontalScrollBar:
        contentLayer.needsHorizontalScrollBar
    readonly property alias _reserveVerticalScrollBarGutter:
        contentLayer.reserveVerticalScrollBarGutter
    readonly property alias _reserveHorizontalScrollBarGutter:
        contentLayer.reserveHorizontalScrollBarGutter
    readonly property bool _hasHorizontalScroll:
        listView.width > 0 && contentTotalWidth > listView.width
    readonly property real _scrollBarGutter:
        Math.max(0, scrollBarWidth) + Enums.spacing.xs
    readonly property real _effectiveContentWidth:
        _hasHorizontalScroll ? contentTotalWidth : listView.width
    readonly property color headerColor: Enums.headerColor
    readonly property color borderColor: Enums.stateColor.borderLight
    readonly property color textColor: Enums.textColor.primary
    readonly property color secondaryColor: Enums.textColor.secondary
    readonly property color hoverColor: Enums.tableHoverColor
    readonly property color alternateColor: Enums.alternateRowColor
    readonly property color _headerEdgeShadowColor: Enums.stateColor.edgeShadow

    // ==================== Public Methods 公开方法 ====================
    function smoothScrollBy(delta) { contentLayer.scrollHelper.scrollBy(delta) }
    function smoothScrollTo(targetY) { contentLayer.scrollHelper.scrollTo(targetY) }

    function scrollToIndex(idx) {
        listView.positionViewAtIndex(idx, QtQ.ListView.Center)
    }

    // ==================== Internal Methods 内部方法 ====================
    // Prefer an explicit model count before ListView finishes its queued refresh.
    // ListView 完成排队刷新前优先读取模型显式计数。
    function _immediateModelItemCount() {
        var model = listView.model
        if (model === null || model === undefined) return 0
        if (typeof model === "number") return Math.max(0, Math.floor(model))
        if (typeof model.count === "number") return model.count
        if (typeof model.length === "number") return model.length
        return listView.count
    }

    // Publish synchronous model state now, then re-check the current model after queued bindings settle.
    // 立即发布同步模型状态，排队绑定稳定后再次读取当前模型，避免内部视图旧计数回写。
    function _refreshItemCount() {
        root._autoItemCount = root._immediateModelItemCount()
        Qt.callLater(function() { root._autoItemCount = root._immediateModelItemCount() })
    }

    // Coalesce geometry-dependent scrollbar state to avoid a binding loop.
    // 合并依赖几何的滚动条状态，避免视口与委托布局形成绑定环。
    function _scheduleScrollBarUpdate() {
        if (contentLayer.scrollViewportState)
            contentLayer.scrollViewportState.invalidate()
    }

    // Create the horizontal branch synchronously on first real overflow, then retain it.
    // 首次真实溢出时同步创建横向分支，随后常驻以保留滚动与表头状态。
    function _ensureHorizontalScrollMixin() {
        if (!_horizontalScrollLifecycleReady
                || !_hasHorizontalScroll || _horizontalScrollRequested) return
        _horizontalScrollMixin = contentLayer.createHorizontalScrollMixin()
        if (!_horizontalScrollMixin) return
        _horizontalScrollRequested = true
    }

    // Ignore transient pre-layout overflow, then enable synchronous runtime requests.
    // 忽略布局稳定前的瞬时溢出，随后启用运行期同步请求。
    function _finishHorizontalScrollInitialization() {
        _horizontalScrollLifecycleReady = true
        _ensureHorizontalScrollMixin()
    }

    Layout.fillWidth: layoutFillWidth
    Layout.fillHeight: layoutFillHeight
    Layout.alignment: layoutAlignment

    color: Enums.transparent
    implicitWidth: 200
    implicitHeight: 150

    onShowScrollBarChanged: _scheduleScrollBarUpdate()
    onScrollBarWidthChanged: _scheduleScrollBarUpdate()
    onWidthChanged: _scheduleScrollBarUpdate()
    onHeightChanged: _scheduleScrollBarUpdate()
    on_HasHorizontalScrollChanged: _ensureHorizontalScrollMixin()
    onListModelChanged: _refreshItemCount()

    Component.onCompleted: {
        _scheduleScrollBarUpdate()
        Qt.callLater(_finishHorizontalScrollInitialization)
    }

    // ==================== Content 内容 ====================
    Connections {
        function onRowsInserted() { root._refreshItemCount() }
        function onRowsRemoved() { root._refreshItemCount() }
        function onModelReset() { root._refreshItemCount() }
        function onLayoutChanged() { root._refreshItemCount() }
        function onCountChanged() { root._refreshItemCount() }

        // Subscribe only to QObject/QAbstractItemModel-style models 仅订阅 QObject/QAbstractItemModel 模型
        target: (listView.model && typeof listView.model === "object"
                 && typeof listView.model.length !== "number"
                 && (typeof listView.model.rowCount === "function"
                     || listView.model.modelReset !== undefined))
                ? listView.model : null
        ignoreUnknownSignals: true
    }

    DataWidgetContent {
        id: contentLayer

        dataControl: root
    }
}
