// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick.Layouts
import "../../../.."
import "../../../icons"
import "../../../data"
import "TreeWidgetCore.js" as Core
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// TreeView - Low-level tree view (QTreeView equivalent) 低阶树形视图（QTreeView 等价物）
// Inherits DataWidgetCore in lightweight mode without shadow or margin 继承 DataWidgetCore 的无阴影、无边距轻量模式
//
// Difference from high-level TreeWidget 与高阶 TreeWidget 的区别：
//   TreeView = QTreeView equivalent with rendering and expansion only TreeView 仅提供渲染与展开折叠
//   TreeWidget = QTreeWidget equivalent with model, selection, and full API TreeWidget 自带模型、选择与完整 API
DataWidgetCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var model: []
    property Component treeDelegate: null
    property int indentWidth: Enums.spacing.xl
    property int itemHeight: Enums.controlSize.treeItemHeight

    // ==================== Internal Props 内部属性 ====================
    property int _hoverIndex: -1

    // ==================== Signals 信号 ====================
    signal itemExpanded(var item)
    signal itemCollapsed(var item)
    signal itemClicked(var item, int index)

    // ==================== Public Methods 公开方法 ====================
    function expandAll() {
        Core.setExpandedRecursive(model, true)
        _rebuild()
    }

    function collapseAll() {
        Core.setExpandedRecursive(model, false)
        _rebuild()
    }

    function count() { return internalModel.count }

    // ==================== Internal Methods 内部方法 ====================
    function _rebuild() { Core.rebuildModel(control, internalModel) }

    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.controlSize.listDefaultWidth
    implicitHeight: Enums.controlSize.listDefaultHeight

    // Lightweight mode 轻量模式
    showShadow: false
    cardMargin: 0
    borderVisible: true
    showFooter: true
    showHeader: false
    // Bind directly because asynchronous incubation can finish the initial rebuild before the base tracker is ready.
    // 直接绑定内部模型计数，避免异步孵化时初次重建早于基类计数跟踪器就绪。
    itemCount: internalModel.count
    onModelChanged: _rebuild()
    contentDelegate: treeDelegate ? treeDelegate : defaultDelegate
    listModel: internalModel

    // ==================== Content 内容 ====================
    // Internal model 内部模型
    ListModel { id: internalModel }

    // Default delegate 默认委托
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
            property bool hovered: control._hoverIndex === index
            property bool pressed: _itemArea.pressed
            property real branchOffset: Enums.spacing.m + depth * control.indentWidth

            width: ListView.view ? ListView.view.width : 0
            height: control.itemHeight
            color: Enums.transparent

            scale: pressed ? 0.98 : 1.0
            Behavior on scale {
                NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic }
            }
            transformOrigin: Item.Center

            Rectangle {
                anchors.fill: parent
                anchors.margins: Enums.spacing.xxs
                radius: Enums.radius.small
                // Keep both animation endpoints opaque to avoid gray trails while moving across rows.
                // 动画两端都保持不透明，避免鼠标划过多行时出现灰色拖影。
                color: delegateRoot.hovered
                       ? Qt.tint(Enums.cardColor, Enums.stateColor.treeItemHover)
                       : Enums.cardColor
                HoverBehavior on color {
                    active: delegateRoot.hovered && !delegateRoot.pressed
                    enterDuration: Enums.duration.fast
                }
            }

            Row {
                id: contentRow
                anchors.left: parent.left
                anchors.leftMargin: Enums.spacing.xl + delegateRoot.branchOffset
                anchors.verticalCenter: parent.verticalCenter
                spacing: Enums.spacing.none

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

                property real expandEnd: Enums.spacing.xl + delegateRoot.branchOffset + Enums.controlSize.treeIndentSize + Enums.spacing.xs

                anchors.fill: parent
                hoverEnabled: true

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
