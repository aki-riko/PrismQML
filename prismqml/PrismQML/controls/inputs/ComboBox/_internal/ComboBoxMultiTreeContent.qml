// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../../.."
import "../../../containers/ScrollBar"
import "../../../data"
import "../../../menus"
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// ComboBoxMultiTreeContent - Multi-tree visual and popup content 多选树视觉与弹层内容
// Keeps the public entry focused on selection state and tree orchestration
// 将公开入口限制为选择状态与树编排。
Item {
    id: content

    // ==================== Required Props 必需属性 ====================
    required property var comboControl

    // ==================== Public Props 公开属性 ====================
    property alias flatListModel: internalFlatListModel
    property alias tokenFlickable: tokenFlickable
    property alias popupContent: treePopupContent

    anchors.fill: parent

    // ==================== Content 内容 ====================
    // Use ListModel for animation support 使用ListModel以支持动画
    ListModel {
        id: internalFlatListModel
    }

    // Popup content override 弹窗内容覆盖
    Component {
        id: treePopupContent

        Column {
            anchors.fill: parent
            spacing: Enums.spacing.none

            // Search box 搜索框
            PopupSearchBox {
                id: searchBox
                width: parent.width
                searchEnabled: content.comboControl.searchEnabled
                placeholderText: content.comboControl.searchPlaceholder
                onSearchTextChanged: (text) => content.comboControl._searchText = text
            }

            // Tree content 树内容
            Item {
                id: treeContainer

                readonly property bool needsScroll: treeListView.contentHeight > treeListView.height

                width: parent.width
                height: parent.height - (content.comboControl.searchEnabled
                    ? Enums.comboBoxMetrics.searchBoxHeight : 0)

                ListView {
                    id: treeListView
                    anchors.fill: parent
                    anchors.rightMargin: treeContainer.needsScroll
                        ? Enums.comboBoxMetrics.scrollBarRightMargin : 0
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    interactive: false
                    model: content.comboControl._flatListModel

                    delegate: TreeMenuDelegate {
                        width: treeListView.width
                        text: model.text
                        depth: model.depth
                        hasChildren: model.hasChildren
                        expanded: model.expanded
                        checkable: true
                        checkState: model.selected ? 2 : (model.isPartialSelected ? 1 : 0)

                        onToggleExpand: content.comboControl._toggleExpand(model.nodeId)
                        onCheckToggled: content.comboControl._toggleSelection(JSON.parse(model.path))
                    }

                    // Smooth scroll 平滑滚动
                    PopupSmoothScroll {
                        flickable: treeListView
                        enabled: treeContainer.needsScroll
                    }
                }

                Loader {
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.margins: Enums.spacing.xxs
                    width: Enums.comboBoxMetrics.scrollBarWidth
                    active: treeContainer.needsScroll
                    sourceComponent: ScrollBarEntry {
                        flickable: treeListView
                        width: Enums.comboBoxMetrics.scrollBarWidth
                    }
                }
            }
        }
    }

    // Token display area 标签显示区域 (use base class arrow) 使用基类箭头
    Flickable {
        id: tokenFlickable
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: Enums.spacing.m
        anchors.rightMargin: Enums.comboBoxMetrics.arrowAreaWidth
        height: Enums.spacing.xxxl
        contentWidth: tokenRow.width
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        flickableDirection: Flickable.HorizontalFlick
        interactive: false

        Row {
            id: tokenRow
            height: Enums.spacing.xxxl
            spacing: Enums.spacing.xs

            // Placeholder text 占位符文本
            Label {
                type: Enums.label.type_body
                text: content.comboControl.placeholderText
                color: Enums.textColor.disabled
                visible: content.comboControl._leafSelectedPaths.length === 0
                anchors.verticalCenter: parent.verticalCenter
            }

            // Token tags 标签 (only show leaf nodes 只显示叶子节点)
            Repeater {
                model: content.comboControl._leafSelectedPaths

                delegate: MultiSelectToken {
                    id: tokenDelegate
                    required property int index
                    required property var modelData

                    readonly property var _control: content.comboControl

                    text: modelData[modelData.length - 1] || ""
                    tokenIndex: index
                    anchors.verticalCenter: parent.verticalCenter

                    onRemoveClicked: (idx) => {
                        var pathToRemove = tokenDelegate._control._leafSelectedPaths[idx]
                        var pathStr = tokenDelegate._control._pathToString(pathToRemove)
                        var newPaths = tokenDelegate._control._safeSelectedPaths.filter(function(p) {
                            return tokenDelegate._control._pathToString(p) !== pathStr
                        })
                        tokenDelegate._control.selectedPaths = newPaths
                        tokenDelegate._control.selectionChanged(
                            tokenDelegate._control._safeSelectedPaths)
                        tokenDelegate._control._updateSelectionStates()
                    }
                }
            }
        }
    }
}
