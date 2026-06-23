// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick.Layouts
import QtQuick.Effects
import "../../../.."
import "../../../../effects"
import "../../../icons"
import "../../../inputs/Toggle"
import "../../../data"
import "../.."
import "../../../containers/ScrollBar"
import "../../../containers/Separator"
import "_internal"
import "TreeWidgetCore.js" as Core
import "TreeWidgetApi.js" as Api
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// TreeWidget - Fluent Design tree widget 树形组件
// QTreeWidget-style migration API subset QTreeWidget风格迁移接口子集
// Modular architecture: delegate + JS modules 模块化架构：委托 + JS 模块
Rectangle {
    id: control
    
    // ==================== Selection Mode 选择模式 ====================
    readonly property int noSelection: 0
    readonly property int singleSelection: 1
    readonly property int multiSelection: 2
    readonly property int extendedSelection: 3
    property int selectionMode: singleSelection

    // ==================== Public Props 公开属性 ====================
    property var model: []
    property int itemHeight: Enums.controlSize.treeItemHeight
    property int indentWidth: Enums.spacing.xl
    property int currentIndex: -1
    property bool checkable: false
    property color indicatorColor: Enums.accentColor
    property color checkedColor: Enums.accentColor
    property color checkedColorDark: Enums.accentColor
    property var headerLabels: []
    property int columnCount: 1
    property bool borderVisible: true
    property int borderRadius: Enums.radius.large
    property bool selectOnRightClick: false
    property bool smoothScroll: true
    property int scrollDuration: Enums.duration.scroll
    property real scrollStep: Enums.spacing.xxxl * 3

    // ==================== Signals 信号 ====================
    signal itemClicked(var item, int index)
    signal itemDoubleClicked(var item, int index)
    signal itemPressed(var item, int index)
    signal itemEntered(var item, int index)
    signal itemExpanded(var item)
    signal itemCollapsed(var item)
    signal itemChecked(var item, int checkState)
    signal currentItemChanged(var current, var previous)
    signal itemSelectionChanged()
    
    // ==================== Size & Style 尺寸和样式 ====================
    implicitWidth: Enums.controlSize.treeDefaultWidth
    implicitHeight: Enums.controlSize.treeDefaultHeight
    color: Enums.transparent
    
    // ==================== Internal State 内部状态 ====================
    property var _selectedIndices: []
    property var _previousItem: null
    property int _hoverIndex: -1
    // cardColor 可覆盖(默认主题卡片色): 透明场景设 cardColor:"transparent",与
    // DataWidgetCore 系列(ListView/TableView 等)API 一致。
    property color cardColor: Enums.cardColor
    readonly property color headerColor: Enums.headerColor
    readonly property color borderColor: Enums.stateColor.borderLight
    readonly property color textColor: Enums.textColor.primary
    readonly property color secondaryColor: Enums.textColor.secondary

    // ==================== Internal API (for delegate) 内部API ====================
    function _rebuildModel() { Core.rebuildModel(control, internalModel) }
    function _isIndexSelected(idx) { return Core.isIndexSelected(control, idx) }
    function _handleItemClick(idx, button, modifiers) { Core.handleItemClick(control, internalModel, idx, button, modifiers) }
    function _getItemObject(idx) { return Core.getItemObject(control, internalModel, idx) }
    function _toggleExpandAt(idx) { Core.toggleExpandAt(control, internalModel, idx) }
    function _toggleCheckAt(idx) { Core.toggleCheckAt(control, internalModel, idx) }
    function _findOriginalItem(pathStr) { return Core.findOriginalItem(control, pathStr) }
    function _flattenModel(items, depth, path) { return Core.flattenModel(items, depth, path) }
    function _findItemIndex(item) { return Core.findItemIndex(internalModel, item) }
    function _normalizeItem(item) { return Core.normalizeItem(item) }
    function _setExpandedRecursive(items, expanded) { Core.setExpandedRecursive(items, expanded) }
    function _sortRecursive(items, order) { Core.sortRecursive(items, order) }
    // ==================== QTreeWidget API ====================
    function topLevelItemCount() { return Api.topLevelItemCount(control) }
    function topLevelItem(index) { return Api.topLevelItem(control, index) }
    function addTopLevelItem(item) { Api.addTopLevelItem(control, item) }
    function addTopLevelItems(items) { Api.addTopLevelItems(control, items) }
    function insertTopLevelItem(index, item) { Api.insertTopLevelItem(control, index, item) }
    function insertTopLevelItems(index, items) { Api.insertTopLevelItems(control, index, items) }
    function takeTopLevelItem(index) { return Api.takeTopLevelItem(control, index) }
    function indexOfTopLevelItem(item) { return Api.indexOfTopLevelItem(control, item) }
    function currentItem() { return Api.currentItem(control) }
    function setCurrentItem(item) { Api.setCurrentItem(control, item) }
    function selectedItems() { return Api.selectedItems(control, internalModel) }
    function clearSelection() { Api.clearSelection(control) }
    function selectAll() { Api.selectAll(control, internalModel) }
    function setSelectionMode(mode) { Api.setSelectionMode(control, mode) }
    function expandItem(item) { Api.expandItem(control, internalModel, item) }
    function collapseItem(item) { Api.collapseItem(control, internalModel, item) }
    function expandAll() { Api.expandAll(control) }
    function collapseAll() { Api.collapseAll(control) }
    function isItemExpanded(item) { return Api.isItemExpanded(control, internalModel, item) }
    function setItemExpanded(item, expanded) { Api.setItemExpanded(control, internalModel, item, expanded) }
    function findItems(text, flags, column) { return Api.findItems(control, internalModel, text, flags, column) }
    function sortItems(column, order) { Api.sortItems(control, column, order) }
    function setHeaderLabels(labels) { Api.setHeaderLabels(control, labels) }
    function setHeaderLabel(label) { Api.setHeaderLabel(control, label) }
    function headerItem() { return Api.headerItem(control) }
    function clear() { Api.clear(control, internalModel) }
    function count() { return Api.count(internalModel) }
    function setItemText(item, column, text) { Api.setItemText(control, internalModel, item, column, text) }
    function itemText(item, column) { return Api.itemText(item, column) }
    function setItemIcon(item, column, icon) { Api.setItemIcon(control, internalModel, item, column, icon) }
    function setItemCheckState(item, column, state) { Api.setItemCheckState(control, internalModel, item, column, state) }
    function itemCheckState(item, column) { return Api.itemCheckState(item, column) }
    function setItemData(item, column, role, value) { Api.setItemData(control, item, column, role, value) }
    function itemData(item, column, role) { return Api.itemData(item, column, role) }
    function setBorderVisible(visible) { Api.setBorderVisible(control, visible) }
    function setBorderRadius(r) { Api.setBorderRadius(control, r) }
    function setIndentation(indent) { Api.setIndentation(control, indent) }
    function indentation() { return Api.indentation(control) }
    function scrollToItem(item, hint) { Api.scrollToItem(control, listView, item, hint) }
    function scrollToTop() { Api.scrollToTop(listView) }
    function scrollToBottom() { Api.scrollToBottom(listView) }
    function toggleExpandAt(idx) { _toggleExpandAt(idx) }
    function toggleCheckAt(idx) { _toggleCheckAt(idx) }

    ListModel { id: internalModel }
    
    Component.onCompleted: Core.rebuildModel(control, internalModel)
    onModelChanged: Core.rebuildModel(control, internalModel)

    // ==================== Shadow 阴影 ====================
    // Fluent: 模糊阴影; neo: 硬阴影
    RectangularShadow {
        anchors.fill: card
        radius: card.radius
        color: Enums.shadow.level2.color
        blur: Enums.shadow.level2.blur
        offset: Qt.vector2d(0, Enums.shadow.level2.offset)
        visible: !Enums.isNeobrutalism
    }

    NeoShadow {
        target: card
        visible: Enums.isNeobrutalism
        z: card.z - 1
    }

    // ==================== Card 卡片容器 ====================
    Rectangle {
        id: card
        anchors.fill: parent
        anchors.margins: Enums.spacing.m
        color: cardColor
        radius: borderRadius
        border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth : (borderVisible ? Enums.border.thin : 0)
        border.color: Enums.isNeobrutalism ? Enums.stateColor.border : borderColor
        
        ColumnLayout {
            anchors.fill: parent
            spacing: 0
            
            // Header 表头
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: Enums.controlSize.tableHeaderHeight
                color: headerColor
                radius: borderRadius
                visible: headerLabels.length > 0
                Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: parent.height / 2; color: parent.color }
                Row {
                    anchors.fill: parent
                    Repeater {
                        model: headerLabels
                        Label {
                            anchors.verticalCenter: parent.verticalCenter
                            type: Enums.label.type_caption
                            text: modelData || ""
                            font.bold: true
                            color: secondaryColor
                            width: (card.width - Enums.spacing.xl * 2) / Math.max(1, headerLabels.length)
                        }
                    }
                }
            }
            
            // Header separator 分隔线
            Separator { Layout.fillWidth: true; lineColor: borderColor; visible: headerLabels.length > 0 }
            
            // Content 内容
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                
                ListView {
                    id: listView
                    anchors.fill: parent
                    anchors.rightMargin: contentHeight > height ? Enums.spacing.xl : 0
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    interactive: false
                    model: internalModel
                    property var treeControl: control
                    delegate: TreeWidgetDelegate {}

                    add: Transition {
                        ParallelAnimation {
                            NumberAnimation {
                                property: "opacity"; from: 0; to: 1
                                duration: Enums.duration.enter
                                easing.type: Easing.OutCubic
                            }
                            NumberAnimation {
                                property: "y"; from: listView.contentY + 8
                                duration: Enums.duration.enter
                                easing.type: Easing.OutCubic
                            }
                        }
                    }

                    remove: Transition {
                        ParallelAnimation {
                            NumberAnimation {
                                property: "opacity"; to: 0
                                duration: Enums.duration.exit
                                easing.type: Easing.InCubic
                            }
                            NumberAnimation {
                                property: "x"; to: 30
                                duration: Enums.duration.exit
                                easing.type: Easing.InCubic
                            }
                        }
                    }

                    displaced: Transition {
                        NumberAnimation {
                            properties: "y"
                            duration: Enums.duration.medium
                            easing.type: Easing.OutQuart
                        }
                    }
                }
                
                SmoothScrollHelper {
                    id: scrollHelper
                    target: listView
                    orientation: Qt.Vertical
                    enabled: control.smoothScroll
                    duration: control.scrollDuration
                    step: control.scrollStep
                    bounceEnabled: true
                }
                
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
                }
                
                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.NoButton
                    onWheel: (event) => {
                        if (listView.contentHeight <= listView.height) {
                            event.accepted = false
                            return
                        }
                        scrollHelper.scrollBy(-event.angleDelta.y / 120 * scrollHelper.step)
                        event.accepted = true
                    }
                }
            }
            
            // Footer 底栏
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: Enums.controlSize.inputHeightCompact
                color: headerColor
                radius: borderRadius
                visible: internalModel.count > 0
                Rectangle { anchors.top: parent.top; width: parent.width; height: parent.height / 2; color: parent.color }
                Label { anchors.centerIn: parent; type: Enums.label.type_caption; text: Enums.trCount("total_items", internalModel.count); color: secondaryColor }
            }
        }
    }
}
