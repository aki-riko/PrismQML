// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick as QtQ
import QtQuick.Effects
import "../.."
import "../icons"
import "../../effects"
import "Card"
import "../data/Label"
import "ScrollBar"

// TimelineCore - Timeline widget 时间线组件
// Supports grouped items with status icons and cards 支持分组项目、状态图标和卡片
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    // Items format: [{title: "已完成", status: "success", cards: [{text: "Task1", status: "success", strikeOut: true}]}, ...]
    // status: "success", "info", "warning", "error"
    property var items: []

    // Visual type: standard grouped timeline or generic graph timeline.
    // Graph cards may provide graph:{nodeLane,nodeColorIndex,segments:[{fromLane,toLane,colorIndex}]}
    // and labels:[{text,status}]. Group graph data draws lanes through date headers.
    property int type: Enums.timeline.type_standard
    property int graphLaneCount: 1
    property var graphPalette: Enums.chartColors.extendedPalette

    // 虚拟滚动:默认关(保持原 Column+Repeater 全量渲染,向后兼容)。
    // 开启后整个组件改用单层 ListView 渲染,把 items 拍平成行(组头行+卡片行),
    // 只渲染可见项,适合大列表(上千条)。开启时组件自身可滚动,需给定 height。
    // Virtual scrolling: off by default (keeps original full render, backward compatible).
    property bool virtualized: false

    // 选中项的 key 值(配合 selectedRole 高亮当前选中卡片);为空不高亮
    property string selectedRole: "commit"   // card 对象里用作唯一标识的字段名
    property var selectedKey: undefined        // 当前选中值(与 card[selectedRole] 比对)

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _graphMode: type === Enums.timeline.type_graph
    readonly property bool _usesVirtualList: virtualized || _graphMode
    readonly property real _graphWidth: Enums.spacing.timelineGraphPadding * 2
        + Math.max(1, graphLaneCount) * Enums.spacing.timelineGraphLane
    // 拍平 items 为线性行: [{kind:"header",groupIndex,title,status}, {kind:"card",groupIndex,cardIndex,...}, ...]
    readonly property var _flatRows: {
        if (!_usesVirtualList) return []
        var rows = []
        for (var g = 0; g < items.length; g++) {
            var grp = items[g] || {}
            rows.push({
                "kind": "header", "groupIndex": g,
                "title": grp.title || "", "status": grp.status || "info",
                "graphData": grp.graph || {}
            })
            var cards = grp.cards || []
            for (var c = 0; c < cards.length; c++) {
                var card = cards[c]
                rows.push({
                    "kind": "card", "groupIndex": g, "cardIndex": c,
                    "groupStatus": grp.status || "info",
                    "cardData": card,
                    "text": (typeof card === "string") ? card : (card.text || ""),
                    "description": (typeof card === "object") ? (card.description || "") : "",
                    "status": (typeof card === "object") ? (card.status || grp.status || "info") : (grp.status || "info"),
                    "strikeOut": (typeof card === "object") ? (card.strikeOut || false) : false,
                    "graphData": (typeof card === "object") ? (card.graph || {}) : {},
                    "isLastCard": c === cards.length - 1
                })
            }
        }
        return rows
    }

    // ==================== Signals 信号 ====================
    signal itemClicked(int groupIndex, string title)
    signal cardClicked(int groupIndex, int cardIndex, string text)
    // cardClickedData: 回传完整 card 对象(含调用方自定义字段,如业务 id/hash)
    // cardClickedData: emits the full card object (carrying caller's custom fields, e.g. business id/hash)
    signal cardClickedData(int groupIndex, int cardIndex, var cardData)
    // 虚拟滚动模式下滚动到接近底部时触发(用于分页加载更多)
    signal reachedEnd()

    // ==================== Internal Methods 内部方法 ====================
    // 把 _flatRows 增量同步到 _flatModel:
    // - 纯尾部追加(分页常态):只 append 新增行,现有行不动→contentY 不重置
    // - 其他变化(reset/搜索/切仓库):清空重填
    function _syncFlat() {
        if (!_usesVirtualList) return
        var rows = _flatRows
        var oldN = _flatModel.count
        var isAppend = rows.length >= oldN && oldN > 0
        // 校验前缀一致(纯追加的前提:前 oldN 行的 groupIndex/cardIndex/kind 不变)
        if (isAppend) {
            // 抽样校验首行+最后一旧行的标识,足以判断是否前缀稳定
            var f0 = _flatModel.get(0)
            if (!f0 || f0.kind !== rows[0].kind || f0.title !== (rows[0].title || "")
                || f0.text !== (rows[0].text || "")) {
                isAppend = false
            }
        }
        if (isAppend) {
            for (var i = oldN; i < rows.length; i++) _flatModel.append(rows[i])
        } else {
            _flatModel.clear()
            for (var j = 0; j < rows.length; j++) _flatModel.append(rows[j])
        }
    }

    function _getStatusColor(status) {
        switch (status) {
            case "success": return Enums.statusLevel.getColor("success")
            case "warning": return Enums.statusLevel.getColor("warning")
            case "error": return Enums.statusLevel.getColor("error")
            default: return Enums.accentColor  // info
        }
    }

    function _getStatusIcon(status) {
        switch (status) {
            case "success": return "Checkmark"      // 简单勾号，不带圆圈
            case "warning": return "Warning"        // 感叹号三角
            case "error": return "Dismiss"          // 简单X，不带圆圈
            default: return "Info"                  // info - i图标
        }
    }

    onVirtualizedChanged: _syncFlat()
    onTypeChanged: _syncFlat()
    on_FlatRowsChanged: _syncFlat()
    Component.onCompleted: _syncFlat()
    
    implicitWidth: 400
    implicitHeight: _usesVirtualList ? 400 : contentColumn.implicitHeight

    // ==================== Content 内容 ====================
    // 虚拟模式实际驱动 ListView 的 ListModel(增量同步,避免整体替换导致滚动跳顶)
    QtQ.ListModel { id: _flatModel }

    // Non-virtual content: full Column and Repeater 非虚拟内容：全量 Column 与 Repeater
    Column {
        id: contentColumn
        width: parent.width
        spacing: Enums.spacing.none
        visible: !control._usesVirtualList
        
        Repeater {
            model: items
            
            delegate: Item {
                id: groupItem

                required property var modelData
                required property int index

                width: contentColumn.width
                height: groupContent.height
                
                // Connector line 连接线（在图标下方）
                Rectangle {
                    x: 7  // 图标中心位置
                    y: Enums.spacing.timelineHeaderHeight  // 从标题下方开始
                    width: Enums.border.normal
                    height: parent.height - Enums.spacing.timelineHeaderHeight
                    color: Enums.stateColor.borderSubtle
                }
                
                Column {
                    id: groupContent
                    width: parent.width
                    spacing: Enums.spacing.none
                    
                    // Group header 分组标题
                    Item {
                        width: groupContent.width
                        height: Enums.spacing.timelineHeaderHeight
                        
                        Row {
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: Enums.spacing.m
                            
                            // Status icon 状态图标（圆形填充）
                            Rectangle {
                                width: Enums.controlSize.timelineIcon
                                height: Enums.controlSize.timelineIcon
                                radius: Enums.controlSize.timelineIcon / 2
                                anchors.verticalCenter: parent.verticalCenter
                                color: control._getStatusColor(groupItem.modelData.status || "info")
                                
                                Icon {
                                    anchors.centerIn: parent
                                    icon: control._getStatusIcon(groupItem.modelData.status || "info")
                                    iconSize: Enums.controlSize.timelineIconText
                                    color: Enums.accentForeground
                                }
                            }
                            
                            // Title 标题
                            Label {
                                type: Enums.label.type_body_strong
                                anchors.verticalCenter: parent.verticalCenter
                                text: groupItem.modelData.title || ""
                            }
                        }
                        
                        MouseArea {
                            anchors.fill: parent
                            onClicked: control.itemClicked(groupItem.index, groupItem.modelData.title || "")
                        }
                    }
                    
                    // Cards container 卡片容器
                    Column {
                        width: groupContent.width
                        spacing: Enums.spacing.m
                        leftPadding: Enums.spacing.timelineIndent  // 与标题对齐
                        topPadding: Enums.spacing.s
                        bottomPadding: Enums.spacing.l
                        
                        Repeater {
                            model: groupItem.modelData.cards || []
                            
                            delegate: Item {
                                id: cardItem

                                required property var modelData
                                required property int index

                                // Card status 卡片状态
                                property string cardStatus: typeof modelData === "object" ? (modelData.status || groupItem.modelData.status || "info") : (groupItem.modelData.status || "info")
                                property bool hasStrikeOut: typeof modelData === "object" ? (modelData.strikeOut || false) : false
                                property string cardText: typeof modelData === "string" ? modelData : (modelData.text || "")
                                // 可选副标题行(如提交的 hash·作者·日期);为空则不显示
                                property string cardDescription: typeof modelData === "object" ? (modelData.description || "") : ""

                                width: groupContent.width - 56
                                height: simpleCard.height
                                
                                Card {
                                    id: simpleCard
                                    cardType: Enums.card.type_hover
                                    width: parent.width
                                    height: cardContent.implicitHeight + Enums.spacing.l * 2
                                    clickEnabled: true
                                    onClicked: {
                                        control.cardClicked(groupItem.index, cardItem.index, cardItem.cardText)
                                        control.cardClickedData(groupItem.index, cardItem.index, cardItem.modelData)
                                    }
                                    
                                    Row {
                                        id: cardContent
                                        anchors.left: parent.left
                                        anchors.right: parent.right
                                        anchors.verticalCenter: parent.verticalCenter
                                        anchors.margins: Enums.spacing.l
                                        spacing: Enums.spacing.m
                                        
                                        // Card status icon 卡片状态图标
                                        Rectangle {
                                            width: Enums.controlSize.timelineCardIcon
                                            height: Enums.controlSize.timelineCardIcon
                                            radius: Enums.radius.medium
                                            anchors.verticalCenter: parent.verticalCenter
                                            color: control._getStatusColor(cardItem.cardStatus)
                                            
                                            Icon {
                                                anchors.centerIn: parent
                                                icon: control._getStatusIcon(cardItem.cardStatus)
                                                iconSize: Enums.controlSize.timelineCardIconText
                                                color: Enums.accentForeground
                                            }
                                        }
                                        
                                        // Card text 卡片文字(主标题 + 可选副标题)
                                        Column {
                                            width: parent.width - 24
                                            anchors.verticalCenter: parent.verticalCenter
                                            spacing: Enums.spacing.xxs

                                            Label {
                                                type: Enums.label.type_body
                                                width: parent.width
                                                text: cardItem.cardText
                                                color: cardItem.hasStrikeOut ? Enums.textColor.secondary : Enums.textColor.primary
                                                wrapMode: Text.Wrap
                                                font.strikeout: cardItem.hasStrikeOut
                                            }
                                            Label {
                                                type: Enums.label.type_caption
                                                width: parent.width
                                                visible: cardItem.cardDescription !== ""
                                                text: cardItem.cardDescription
                                                color: Enums.textColor.tertiary
                                                wrapMode: Text.Wrap
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Virtual content: flattened ListView renders visible rows 虚拟内容：拍平 ListView 仅渲染可见行
    QtQ.ListView {
        id: virtualList
        anchors.fill: parent
        visible: control._usesVirtualList
        model: control._usesVirtualList ? _flatModel : null
        clip: true
        cacheBuffer: 600
        reuseItems: true   // 复用 delegate,滚动时不重复实例化(大列表性能关键)
        interactive: false // 关原生 flick,交给 SmoothScrollHelper 接管(否则平滑滚动不生效)
        boundsBehavior: Flickable.StopAtBounds
        onContentYChanged: {
            if (contentHeight > height && contentY + height >= contentHeight - 600)
                control.reachedEnd()
        }

        delegate: Item {
            id: rowDelegate
            required property var model
            width: virtualList.width
            height: model.kind === "header" ? headerPart.height : cardPart.height
            clip: true   // 防止复用切换(header↔card)瞬间旧内容溢出残留("鬼影")

            // ---------- 组头行 ----------
            Item {
                id: headerPart
                visible: rowDelegate.model.kind === "header"
                width: parent.width
                height: visible ? Enums.spacing.timelineHeaderHeight + Enums.spacing.s : 0
                TimelineGraphLayer {
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: control._graphWidth
                    visible: control._graphMode
                    graphData: rowDelegate.model.graphData || {}
                    showNode: false
                    nodeY: 0
                    selected: false
                    graphPalette: control.graphPalette
                }
                Row {
                    anchors.left: parent.left
                    anchors.leftMargin: control._graphMode ? control._graphWidth : 0
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: Enums.spacing.m
                    Rectangle {
                        width: Enums.controlSize.timelineIcon
                        height: Enums.controlSize.timelineIcon
                        radius: Enums.controlSize.timelineIcon / 2
                        anchors.verticalCenter: parent.verticalCenter
                        color: control._getStatusColor(rowDelegate.model.status || "info")
                        visible: !control._graphMode
                        Icon {
                            anchors.centerIn: parent
                            icon: control._getStatusIcon(rowDelegate.model.status || "info")
                            iconSize: Enums.controlSize.timelineIconText
                            color: Enums.accentForeground
                        }
                    }
                    Label {
                        type: Enums.label.type_body_strong
                        anchors.verticalCenter: parent.verticalCenter
                        text: rowDelegate.model.title || ""
                    }
                }
            }

            // ---------- 卡片行 ----------
            Item {
                id: cardPart
                readonly property int shadowPadding: Enums.spacing.cardShadow
                // 当前选中高亮判定
                readonly property bool isSelected: control.selectedKey !== undefined
                    && !!rowDelegate.model.cardData
                    && (typeof rowDelegate.model.cardData === "object")
                    && rowDelegate.model.cardData[control.selectedRole] === control.selectedKey
                visible: rowDelegate.model.kind === "card"
                width: parent.width
                height: visible ? cardBox.y + cardBox.height + Enums.spacing.m : 0
                // 左侧连接线
                Rectangle {
                    x: 7; y: 0
                    width: Enums.border.normal
                    height: parent.height
                    color: Enums.stateColor.borderSubtle
                    visible: !control._graphMode
                }
                TimelineGraphLayer {
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: control._graphWidth
                    visible: control._graphMode
                    graphData: rowDelegate.model.graphData || {}
                    showNode: true
                    nodeY: cardBox.y + cardBox.height / 2
                    selected: cardPart.isSelected
                    graphPalette: control.graphPalette
                }
                Card {
                    id: cardBox
                    x: control._graphMode ? control._graphWidth : Enums.spacing.timelineIndent
                    y: cardPart.shadowPadding
                    // 右侧留出滚动条宽度 + 间距,避免卡片边缘与滚动条重叠
                    width: parent.width - x - Enums.spacing.xl
                    height: cardCol.implicitHeight + Enums.spacing.l * 2
                    // Graph cards use Fluent elevation and the Card token border.
                    // 图模式卡片使用 Fluent 层级动效与 Card 自带轻边框。
                    cardType: control._graphMode
                        ? Enums.card.type_elevated : Enums.card.type_hover
                    clickEnabled: true

                    onClicked: {
                        control.cardClicked(rowDelegate.model.groupIndex, rowDelegate.model.cardIndex, rowDelegate.model.text)
                        control.cardClickedData(rowDelegate.model.groupIndex, rowDelegate.model.cardIndex, rowDelegate.model.cardData)
                    }

                    // Fluent 左侧选中指示条(圆角 pill,accent 色,短竖条居中)
                    Rectangle {
                        anchors.left: parent.left
                        anchors.leftMargin: Enums.spacing.xs
                        anchors.verticalCenter: parent.verticalCenter
                        width: Enums.border.thick
                        radius: Enums.radius.micro
                        color: Enums.accentColor
                        height: cardPart.isSelected ? parent.height * 0.5 : 0
                        opacity: cardPart.isSelected ? 1 : 0
                        Behavior on height { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
                        Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
                    }
                    Column {
                        id: cardCol
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.margins: Enums.spacing.l
                        spacing: Enums.spacing.xxs
                        Label {
                            type: Enums.label.type_body
                            width: parent.width
                            text: rowDelegate.model.text || ""
                            color: (rowDelegate.model.strikeOut || false) ? Enums.textColor.secondary : Enums.textColor.primary
                            wrapMode: Text.Wrap
                            font.strikeout: rowDelegate.model.strikeOut || false
                        }
                        TimelineGraphLabels {
                            width: parent.width
                            visible: control._graphMode
                                && !!rowDelegate.model.cardData
                                && !!rowDelegate.model.cardData.labels
                                && rowDelegate.model.cardData.labels.length > 0
                            labels: visible ? rowDelegate.model.cardData.labels : []
                        }
                        Label {
                            type: Enums.label.type_caption
                            width: parent.width
                            visible: (rowDelegate.model.description || "") !== ""
                            text: rowDelegate.model.description || ""
                            color: Enums.textColor.tertiary
                            wrapMode: Text.Wrap
                        }
                    }
                }
            }
        }

        // 平滑滚动(滚轮缓动,与其他 Fluent 列表一致)
        SmoothScrollHelper {
            id: vScrollHelper
            target: virtualList
            orientation: Qt.Vertical
            handleWheel: true
            // 关回弹:virtualList 是 StopAtBounds,Flickable 会逐帧把越界 contentY 夹回边界。
            // 若开回弹(默认),helper 会把 _smoothY 设为越界负值做回弹动画,与 StopAtBounds 的
            // 夹取逐帧对抗 → 顶部/底部超滑时 contentY 在 0↔负值间抖动 → 时间线闪烁。
            bounceEnabled: false
        }

        // Fluent 风格滚动条
        ScrollBar {
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.margins: Enums.spacing.xxs
            target: virtualList
            scrollHelper: vScrollHelper
        }
    }
}
