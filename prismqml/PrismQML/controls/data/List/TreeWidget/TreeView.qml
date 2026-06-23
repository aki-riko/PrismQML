// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick.Layouts
import "../../../.."
import "../../../icons"
import "../../../data"
import "TreeWidgetCore.js" as Core
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// TreeView - 低阶树形视图 (QTreeView 等价物)
// 继承 DataWidgetCore,轻量模式(无阴影/无margin)
//
// 与 TreeWidget (高阶) 区别:
//   TreeView = QTreeView 等价物,只渲染+展开折叠,无 addItem/selection 等 API
//   TreeWidget     = QTreeWidget 等价物,自带 model + selection + 完整 API
DataWidgetCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var model: []
    property Component treeDelegate: null
    property int indentWidth: Enums.spacing.xl
    property int itemHeight: Enums.controlSize.treeItemHeight

    // ==================== Signals 信号 ====================
    signal itemExpanded(var item)
    signal itemCollapsed(var item)
    signal itemClicked(var item, int index)

    // ==================== Lightweight mode 轻量模式 ====================
    showShadow: false
    cardMargin: 0
    borderVisible: true
    showFooter: true
    showHeader: false
    // itemCount 由基类 DataWidgetCore 自维护(Connections 跟踪 model 信号)

    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.controlSize.listDefaultWidth
    implicitHeight: Enums.controlSize.listDefaultHeight

    // ==================== Internal 内部 ====================
    property int _hoverIndex: -1

    onModelChanged: _rebuild()
    contentDelegate: treeDelegate ? treeDelegate : defaultDelegate

    // ==================== Public Methods 公开方法 ====================
    function _rebuild() { Core.rebuildModel(control, internalModel) }

    // ==================== Public API 公共 API ====================
    function expandAll() {
        Core.setExpandedRecursive(model, true)
        _rebuild()
    }

    function collapseAll() {
        Core.setExpandedRecursive(model, false)
        _rebuild()
    }

    function count() { return internalModel.count }

    // ==================== Internal Model 内部模型 ====================
    ListModel { id: internalModel }
    listModel: internalModel

    // ==================== Default Delegate 默认委托 ====================
    Component {
        id: defaultDelegate

        Rectangle {
            id: delegateRoot
            required property int index
            required property var model

            property string itemText: model.text || ""
            property string itemIcon: model.icon || ""
            property int depth: model.depth || 0
            property bool hasChildren: model.hasChildren || false
            property bool expanded: model.expanded || false

            width: ListView.view ? ListView.view.width : 0
            height: control.itemHeight
            color: Enums.transparent

            property bool hovered: control._hoverIndex === index
            property bool pressed: _itemArea.pressed
            property real branchOffset: Enums.spacing.m + depth * control.indentWidth

            scale: pressed ? 0.98 : 1.0
            Behavior on scale {
                NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic }
            }
            transformOrigin: Item.Center

            Rectangle {
                anchors.fill: parent
                anchors.margins: Enums.spacing.xxs
                radius: Enums.radius.small
                color: delegateRoot.hovered ? Enums.stateColor.treeItemHover : Enums.transparent
                Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
            }

            Row {
                id: contentRow
                anchors.left: parent.left
                anchors.leftMargin: Enums.spacing.xl + delegateRoot.branchOffset
                anchors.verticalCenter: parent.verticalCenter
                spacing: 0

                Item {
                    width: Enums.controlSize.treeIndentSize
                    height: Enums.controlSize.treeIndentSize
                    visible: delegateRoot.hasChildren
                    Icon {
                        anchors.centerIn: parent
                        iconSize: Enums.iconSize.tiny
                        color: Enums.textColor.secondary
                        icon: Enums.icon.chevron_right
                        rotation: delegateRoot.expanded ? 90 : 0
                        Behavior on rotation { NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutBack } }
                    }
                }

                Item {
                    width: Enums.controlSize.treeIndentSize
                    height: Enums.controlSize.treeIndentSize
                    visible: !delegateRoot.hasChildren
                }

                Item { width: Enums.spacing.xs; height: 1 }

                Icon {
                    iconSize: Enums.controlSize.treeIndentSize
                    visible: delegateRoot.itemIcon !== ""
                    icon: delegateRoot.itemIcon
                    color: Enums.textColor.primary
                }

                Item { width: delegateRoot.itemIcon !== "" ? Enums.spacing.s : 0; height: 1 }

                Label {
                    type: Enums.label.type_caption
                    text: delegateRoot.itemText
                    color: Enums.textColor.primary
                    elide: Text.ElideRight
                }
            }

            MouseArea {
                id: _itemArea
                anchors.fill: parent
                hoverEnabled: true
                property real expandEnd: Enums.spacing.xl + delegateRoot.branchOffset + Enums.controlSize.treeIndentSize + Enums.spacing.xs

                onEntered: control._hoverIndex = delegateRoot.index
                onExited: { if (control._hoverIndex === delegateRoot.index) control._hoverIndex = -1 }
                onClicked: (mouse) => {
                    if (delegateRoot.hasChildren && mouse.x <= expandEnd) {
                        Core.toggleExpandAt(control, internalModel, delegateRoot.index)
                        return
                    }
                    control.itemClicked(Core.getItemObject(control, internalModel, delegateRoot.index), delegateRoot.index)
                }
                onDoubleClicked: {
                    if (delegateRoot.hasChildren) Core.toggleExpandAt(control, internalModel, delegateRoot.index)
                }
            }
        }
    }
}