// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick as QtQ  // 原生ListView别名:去前缀后库ListView会覆盖原生,用QtQ.ListView断循环依赖
import QtQuick.Effects
import QtQuick.Layouts
import "../.."
import "../../effects"
import "../data"
import "../containers/ScrollBar"
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// DataWidgetCore - Base class for ListWidget/TableWidget 数据组件基类
// Refactored to use SmoothScrollHelper 重构为使用SmoothScrollHelper
Rectangle {
    id: root
    
    // ==================== Layout Attached Properties 布局附加属性 ====================
    // 用于父布局的附加属性，让数据组件能够填满可用空间
    property bool layoutFillWidth: true
    property bool layoutFillHeight: true
    property int layoutAlignment: 0
    Layout.fillWidth: layoutFillWidth
    Layout.fillHeight: layoutFillHeight
    Layout.alignment: layoutAlignment
    
    // ==================== Public Props 公开属性 ====================
    property string emptyText: ""  // Empty state text 空状态文本
    property string footerText: ""  // Footer text template ({count} placeholder) 底部文本模板
    property bool showFooter: false  // Whether to show the count footer 是否显示底部计数栏
    property int rowHeight: Enums.controlSize.tableHeaderHeight  // Row height 行高
    // itemCount: 列表项数量。默认自维护(跟踪内部 listView 的 model),
    // 子类(如 TableWidget 用 rowCount)可覆盖。
    // 注意: 不能写 `itemCount: listView.count` —— QAbstractListModel 延迟注入时
    // ListView.count 的 countChanged 不触发绑定重算(getter 实时但绑定不更新),
    // 故用 Connections 显式监听 model 信号刷新 _autoItemCount(见下方)。
    property int itemCount: _autoItemCount
    property int _autoItemCount: 0
    
    // Header 表头
    property bool showHeader: false  // Show header 显示表头
    property int headerHeight: Enums.controlSize.tableHeaderHeight
    property Component headerContent: null  // Header content component 表头内容组件

    // Horizontal scroll 横向滚动
    // 子类 (TableWidget 等) 计算所有列总像素宽度赋给这个属性, 当大于 listView.width 时
    // listView.contentWidth 撑开, HorizontalScrollMixin 自动启用横向滚动 (flick / scrollbar / shift+wheel).
    // 默认 0 = 内容贴合 listView 宽度, 不启用横向滚动.
    property real contentTotalWidth: 0

    // 横向滚动实际是否启用 (内部派生标志, 子类 delegate 据此切换 row width 算法)
    readonly property bool _hasHorizontalScroll: contentTotalWidth > listView.width
    // delegate 应用的有效内容宽度: 启用横向滚动时撑到 contentTotalWidth, 否则贴 listView.width
    readonly property real _effectiveContentWidth: _hasHorizontalScroll ? contentTotalWidth : listView.width
    
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

    // Animation 动画
    property bool animated: true
    property bool hoverElevation: false
    property bool loading: false
    property int staggerDelay: Enums.duration.stagger
    
    // ListView access ListView访问
    property alias listView: listView
    property alias contentDelegate: listView.delegate
    property alias listModel: listView.model
    property alias spacing: listView.spacing  // 透传内部ListView间距(此处listView为本地id,alias合法;子类勿用control.listView.spacing三级alias)

    // ==================== itemCount 自维护 ====================
    // Qt.callLater 确保在 ListView 处理完 model 变化后再读 count(同帧直接读会差一拍)。
    function _refreshItemCount() { Qt.callLater(function() { root._autoItemCount = listView.count }) }
    onListModelChanged: _refreshItemCount()
    Connections {
        // 仅当 model 是 QAbstractItemModel(QObject, 有 rowCount/modelReset) 时挂信号;
        // 排除 JS 数组/QVariantList(有 length, 非 QObject, 赋给 target 会报
        // "Unable to assign QVariantList to QObject*")。判据同 TableWidget。
        target: (listView.model && typeof listView.model === 'object'
                 && typeof listView.model.length !== 'number'
                 && (typeof listView.model.rowCount === 'function'
                     || listView.model.modelReset !== undefined))
                ? listView.model : null
        ignoreUnknownSignals: true
        function onRowsInserted() { root._refreshItemCount() }
        function onRowsRemoved() { root._refreshItemCount() }
        function onModelReset() { root._refreshItemCount() }
        function onLayoutChanged() { root._refreshItemCount() }
        function onCountChanged() { root._refreshItemCount() }
    }
    
    // Expose scroll helper for external use 暴露滚动助手供外部使用
    function smoothScrollBy(delta) { scrollHelper.scrollBy(delta) }
    function smoothScrollTo(targetY) { scrollHelper.scrollTo(targetY) }

    // ==================== Helper Methods 辅助方法 ====================
    function scrollToIndex(idx) {
        listView.positionViewAtIndex(idx, QtQ.ListView.Center)
    }

    // ==================== Colors 颜色 ====================
    // cardColor 可覆盖(默认取主题卡片色): 透明/无卡片场景设 cardColor:"transparent"。
    // 配 showShadow:false + borderVisible:false 可得纯透明数据列表(如便签编辑器)。
    property color cardColor: Enums.cardColor
    readonly property color headerColor: Enums.headerColor
    readonly property color borderColor: Enums.stateColor.borderLight
    readonly property color textColor: Enums.textColor.primary
    readonly property color secondaryColor: Enums.textColor.secondary
    readonly property color hoverColor: Enums.tableHoverColor
    readonly property color alternateColor: Enums.alternateRowColor
    
    // ==================== Size 尺寸 ====================
    implicitWidth: 200
    implicitHeight: 150
    color: "transparent"  // 透明背景，避免直角露出圆角卡片外
    
    // ==================== Wheel Handler 滚轮处理 ====================
    MouseArea {
        id: wheelArea
        anchors.fill: parent
        acceptedButtons: Qt.NoButton
        hoverEnabled: hoverElevation

        onWheel: (event) => {
            if (listView.contentHeight <= listView.height) {
                event.accepted = false
                return
            }
            scrollHelper.scrollBy(-event.angleDelta.y / 120 * scrollHelper.step)
            event.accepted = true
        }
    }

    // ==================== Shadow 阴影 ====================
    RectangularShadow {
        id: shadowEffect
        anchors.fill: card
        radius: card.radius
        visible: showShadow && !Enums.isNeobrutalism

        // Active shadow level — 销毁时序里 Enums singleton 的 _metrics 可能先被拆,
        // 导致 Enums.shadow 整个 undefined,旧的 `|| Enums.shadow.level2` 兜底本身也会炸。
        // 故 fallback 用不依赖任何 singleton 的纯字面量静态对象,且取值全程三元守卫。
        readonly property var _staticFallbackShadow: ({ color: "transparent", blur: 0, offset: 0 })
        property var _resolvedLevel: hoverElevation && wheelArea.containsMouse
                                   ? (Enums.shadow ? Enums.shadow.level4 : null) : shadowLevel
        property var _activeLevel: _resolvedLevel
                                 || (Enums.shadow ? Enums.shadow.level2 : null)
                                 || _staticFallbackShadow
        color: _activeLevel ? _activeLevel.color : "transparent"
        blur: _activeLevel ? _activeLevel.blur : 0
        offset.x: 0
        offset.y: _activeLevel ? _activeLevel.offset : 0

        Behavior on blur {
            enabled: root.animated && hoverElevation
            NumberAnimation { duration: Enums.duration.elevation; easing.type: Easing.OutCubic }
        }
        Behavior on offset {
            enabled: root.animated && hoverElevation
            NumberAnimation { duration: Enums.duration.elevation; easing.type: Easing.OutCubic }
        }
    }

    // neo 硬阴影
    NeoShadow {
        target: card
        visible: showShadow && Enums.isNeobrutalism
        z: card.z - 1
    }

    // ==================== Card 卡片容器 ====================
    Rectangle {
        id: card
        anchors.fill: parent
        anchors.margins: cardMargin
        color: cardColor
        radius: borderRadius
        // neo: 粗黑边(neo 下始终显边, 靠边+硬阴影区分)
        border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth : (borderVisible ? Enums.border.thin : 0)
        border.color: Enums.isNeobrutalism ? Enums.stateColor.border : (borderVisible ? Enums.stateColor.borderLight : "transparent")

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Enums.spacing.micro
            spacing: Enums.spacing.none
            
            // ==================== Header 表头 ====================
            Rectangle {
                Layout.fillWidth: true
                height: root.headerHeight
                color: headerColor
                radius: borderRadius
                visible: showHeader
                
                // Bottom half fill 底部半圆填充
                Rectangle {
                    anchors.bottom: parent.bottom
                    width: parent.width
                    height: parent.height / 2
                    color: parent.color
                }
                
                // Header content loader 表头内容加载器
                // 横向滚动激活时, mixin 自动绑定 headerLoader.x = -listView.contentX
                Item {
                    anchors.fill: parent
                    clip: true
                    Loader {
                        id: headerLoader
                        y: 0
                        width: root.contentTotalWidth > listView.width ? root.contentTotalWidth : listView.width
                        height: parent.height
                        sourceComponent: headerContent
                    }
                }
            }
            
            // Header separator 表头分隔线
            Rectangle {
                Layout.fillWidth: true
                height: Enums.border.thin
                color: borderColor
                visible: showHeader
            }

            // Header floating shadow 表头浮起阴影
            Rectangle {
                Layout.fillWidth: true
                height: 4
                visible: showHeader && listView.contentY > 0
                opacity: Math.min(1, listView.contentY / 20)
                gradient: Gradient {
                    GradientStop { position: 0; color: Qt.rgba(0, 0, 0, 0.06) }
                    GradientStop { position: 1; color: "transparent" }
                }
                Behavior on opacity {
                    enabled: root.animated
                    NumberAnimation { duration: Enums.duration.fast }
                }
            }
            
            // ==================== Body 主体区(恒定伸缩容器) ====================
            // contentArea / emptyArea / skeletonArea 三者互斥, 原先各自用
            // Layout.fillHeight 绑 itemCount/loading 在 ColumnLayout 里抢高度。
            // 但 QtQuick.Layouts 在 fillHeight 绑定值**异步变化**(QAbstractListModel
            // 延迟注入 → itemCount 经 Connections+callLater 迟到更新)时不重新分配尺寸,
            // 导致内容区塌成 0 高(实测复现)。故包一个恒定 fillHeight:true 的容器,
            // Layout 永远只有这一个伸缩项尺寸恒定; 三区改用 anchors.fill + visible
            // 切换(anchors 对 visible 异步变化可靠响应)。
            Item {
                id: bodyContainer
                Layout.fillWidth: true
                Layout.fillHeight: true

            // ==================== Content 内容区域 ====================
            Item {
                id: contentArea
                anchors.fill: parent
                visible: itemCount > 0 || loading
                opacity: loading ? 0 : 1
                Behavior on opacity {
                    enabled: root.animated
                    NumberAnimation { duration: Enums.duration.enter; easing.type: Easing.OutCubic }
                }
                
                QtQ.ListView {
                    id: listView
                    anchors.fill: parent
                    clip: true
                    boundsBehavior: Flickable.DragAndOvershootBounds
                    interactive: false
                    cacheBuffer: 600
                    reuseItems: true
                    contentWidth: root.contentTotalWidth > width ? root.contentTotalWidth : width

                    // ==================== Transitions 过渡动画 ====================
                    add: Transition {
                        enabled: root.animated
                        ParallelAnimation {
                            NumberAnimation {
                                property: "opacity"; from: 0; to: 1
                                duration: Enums.duration.enter
                                easing.type: Easing.OutCubic
                            }
                            NumberAnimation {
                                property: "y"; from: listView.contentY + 12
                                duration: Enums.duration.enter
                                easing.type: Easing.OutCubic
                            }
                        }
                    }

                    remove: Transition {
                        enabled: root.animated
                        ParallelAnimation {
                            NumberAnimation {
                                property: "opacity"; to: 0
                                duration: Enums.duration.exit
                                easing.type: Easing.InCubic
                            }
                            NumberAnimation {
                                property: "x"; to: 40
                                duration: Enums.duration.exit
                                easing.type: Easing.InCubic
                            }
                        }
                    }

                    displaced: Transition {
                        enabled: root.animated
                        NumberAnimation {
                            properties: "y"
                            duration: Enums.duration.medium
                            easing.type: Easing.OutQuart
                        }
                    }
                }
                
                // ==================== Smooth Scroll Helper 平滑滚动助手 ====================
                SmoothScrollHelper {
                    id: scrollHelper
                    target: listView
                    orientation: Qt.Vertical
                    enabled: root.smoothScroll
                    duration: root.scrollDuration
                    step: root.scrollStep
                    easing: root.scrollEasing
                    bounceEnabled: true
                }
                
                // ==================== Custom Scrollbar 自定义滚动条 ====================
                ScrollBar {
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.rightMargin: Enums.spacing.xxs

                    target: listView
                    scrollHelper: scrollHelper
                    orientation: Qt.Vertical
                    barWidth: Enums.spacing.s
                    visible: listView.contentHeight > listView.height
                    z: Enums.zIndex.controlsAbove
                }

                // ==================== Horizontal scroll mixin 横向滚动 ====================
                // mixin 内部封装 hScrollHelper / 横向 ScrollBar / Shift+wheel 路由,
                // 与 TableView 等其他可横向滚动组件共用同一套实现.
                HorizontalScrollMixin {
                    id: hScrollMixin
                    anchors.fill: parent
                    target: listView
                    headerContainer: headerLoader
                    smoothScroll: root.smoothScroll
                    scrollDuration: root.scrollDuration
                    scrollStep: root.scrollStep
                    scrollEasing: root.scrollEasing
                    barWidth: Enums.spacing.s
                }
            }

            // ==================== Empty State 空状态 ====================
            Item {
                id: emptyArea
                anchors.fill: parent
                visible: itemCount === 0 && !loading

                opacity: visible ? 1 : 0
                scale: visible ? 1 : 0.95
                Behavior on opacity {
                    enabled: root.animated
                    NumberAnimation { duration: Enums.duration.enter; easing.type: Easing.OutCubic }
                }
                Behavior on scale {
                    enabled: root.animated
                    NumberAnimation { duration: Enums.duration.enter; easing.type: Easing.OutCubic }
                }

                Label {
                    anchors.centerIn: parent
                    type: Enums.label.type_body
                    text: emptyText
                    color: secondaryColor
                }
            }

            // ==================== Loading Skeleton 骨架屏 ====================
            Item {
                id: skeletonArea
                anchors.fill: parent
                visible: loading

                opacity: loading ? 1 : 0
                Behavior on opacity {
                    enabled: root.animated
                    NumberAnimation { duration: Enums.duration.enter; easing.type: Easing.OutCubic }
                }

                Column {
                    anchors.fill: parent
                    anchors.margins: Enums.spacing.m
                    spacing: Enums.spacing.s

                    Repeater {
                        model: Math.min(5, Math.max(3, Math.floor((skeletonArea.height - Enums.spacing.m * 2) / (root.rowHeight + Enums.spacing.s))))
                        Skeleton {
                            width: parent.width
                            height: root.rowHeight - Enums.spacing.s
                            loading: root.loading
                        }
                    }
                }
            }
            }  // bodyContainer (恒定 fillHeight 容器, 包 contentArea/emptyArea/skeletonArea)

            // ==================== Footer 底栏 ====================
            Rectangle {
                id: footerBar
                Layout.fillWidth: true
                height: Enums.controlSize.inputHeightCompact
                color: headerColor
                radius: borderRadius
                visible: showFooter && itemCount > 0

                opacity: visible ? 1 : 0
                Behavior on opacity {
                    enabled: root.animated
                    NumberAnimation { duration: Enums.duration.normal; easing.type: Easing.OutCubic }
                }

                // Top half fill 顶部半圆填充
                Rectangle {
                    anchors.top: parent.top
                    width: parent.width
                    height: parent.height / 2
                    color: parent.color
                }

                Label {
                    anchors.centerIn: parent
                    type: Enums.label.type_caption
                    text: footerText ? footerText.replace("{count}", itemCount) : Enums.trCount("total_items", itemCount)
                    font.pixelSize: Enums.typography.caption - 1
                    color: secondaryColor
                }
            }
        }
    }
}
