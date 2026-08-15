// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../icons"
import "../../../data/Label"

// FilterBarContent - Filter visual content and delegates 过滤栏视觉内容与委托
// Keeps FilterBarCore focused on public state, color strategies and methods.
// 将 FilterBarCore 入口限制为公开状态、颜色策略与方法。
Item {
    id: content

    // ==================== Required Props 必需属性 ====================
    required property var filterControl

    // ==================== Public Props 公开属性 ====================
    property alias itemRepeater: itemRepeater
    readonly property real contentWidth: filterRow.implicitWidth

    anchors.fill: parent

    // ==================== Content 内容 ====================
    NeumorphicShadow {
        parent: filterControl
        target: filterControl
        inset: true
        visible: Enums.isNeumorphism
    }

    Item {
        id: contentContainer
        parent: filterControl
        anchors.centerIn: parent
        width: filterRow.implicitWidth
        height: filterRow.implicitHeight

        // Sliding indicator for exclusive mode 互斥模式滑动指示器
        Rectangle {
            id: slidingIndicator

            // Use properties to allow forced refresh 使用属性以允许强制刷新
            property int targetIndex: filterControl.currentIndex
            property int refreshTrigger: 0  // Trigger recalculation 触发重新计算

            visible: filterControl.exclusive && itemRepeater.count > 0
            x: refreshTrigger >= 0 ? filterControl.getItemX(targetIndex) : 0
            width: refreshTrigger >= 0 ? filterControl.getItemWidth(targetIndex) : 0
            height: 30
            radius: Enums.surfaceRadius(Enums.radius.small)
            color: Enums.accentColor

            // Smooth sliding animation 平滑滑动动画
            Behavior on x { NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutCubic } }
            Behavior on width { NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutCubic } }
        }

        Row {
            id: filterRow
            spacing: Enums.spacing.xs

            Repeater {
                id: itemRepeater
                model: filterControl._safeItems

                // Refresh indicator after all items are created 所有项创建完成后刷新指示器
                onItemAdded: (index, item) => {
                    // Refresh when current item or any item before it is added (needed for x calculation) 当当前项或其之前的任何项添加时刷新（x 计算需要）
                    if (index <= filterControl.currentIndex) {
                        slidingIndicator.refreshTrigger++
                    }
                }

                Rectangle {
                    id: filterItem

                    // ==================== Required Props 必需属性 ====================
                    required property int index
                    required property var modelData

                    // ==================== Internal Props 内部属性 ====================
                    property bool selected: filterControl.exclusive ?
                        (index === filterControl.currentIndex) :
                        (filterControl._safeSelectedIndices.indexOf(index) >= 0)
                    property bool hovered: itemArea.containsMouse && filterControl.enabled
                    property bool pressed: itemArea.pressed

                    // ==================== Readonly State 只读状态 ====================
                    // Parsed item data 解析后的数据
                    readonly property var parsedData: filterControl.parseItem(modelData)
                    readonly property string itemIcon: parsedData.icon
                    readonly property string itemText: parsedData.text
                    readonly property bool hasIcon: itemIcon !== ""
                    readonly property bool hasText: itemText !== ""

                    width: itemContentRow.implicitWidth + Enums.spacing.xl * 2
                    height: 30
                    radius: Enums.surfaceRadius(Enums.radius.small)

                    // Background: transparent for exclusive (indicator handles it), colored for multi 背景：互斥模式透明（指示器处理），多选模式着色
                    color: filterControl.exclusive ?
                        (hovered && !selected ? Enums.stateColor.filterItemHover : Enums.transparent) :
                        filterControl.getItemBackgroundColor(selected, hovered)

                    // Scale animation - bounce effect for multi-select 缩放动画 - 多选模式弹性效果
                    scale: pressed ? 0.92 : 1.0
                    transformOrigin: Item.Center

                    // Animations 动画
                    HoverBehavior on color {
                        active: filterItem.hovered && !filterItem.pressed
                        enterDuration: Enums.duration.normal
                        easingType: Easing.OutCubic
                    }
                    Behavior on scale {
                        NumberAnimation {
                            duration: filterControl.exclusive ? Enums.duration.fast : Enums.duration.medium
                            easing.type: filterControl.exclusive ? Easing.OutCubic : Easing.OutBack
                            easing.overshoot: 2.5
                        }
                    }

                    // Content Row (icon + text) 内容行
                    Row {
                        id: itemContentRow
                        anchors.centerIn: parent
                        spacing: filterItem.hasIcon && filterItem.hasText ? Enums.spacing.xs : 0

                        // Icon 图标
                        Icon {
                            icon: filterItem.itemIcon
                            iconSize: filterControl.iconSize
                            color: filterControl.getItemTextColor(filterItem.selected)
                            visible: filterItem.hasIcon
                            anchors.verticalCenter: parent.verticalCenter

                            Behavior on color { ColorAnimation { duration: Enums.duration.normal; easing.type: Easing.OutCubic } }
                        }

                        // Text 文字
                        Label {
                            type: Enums.label.type_body_small
                            text: filterItem.itemText
                            color: filterControl.getItemTextColor(filterItem.selected)
                            visible: filterItem.hasText
                            anchors.verticalCenter: parent.verticalCenter

                            Behavior on color { ColorAnimation { duration: Enums.duration.normal; easing.type: Easing.OutCubic } }
                        }
                    }

                    // Interaction 交互
                    MouseArea {
                        id: itemArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: filterControl.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                        enabled: filterControl.enabled

                        onClicked: {
                            if (filterControl.exclusive) {
                                if (filterControl.currentIndex !== filterItem.index) {
                                    filterControl.currentIndex = filterItem.index
                                    filterControl.indexChanged(filterItem.index)
                                }
                            } else {
                                var idx = filterControl._safeSelectedIndices.indexOf(filterItem.index)
                                var newIndices = filterControl._safeSelectedIndices.slice()
                                if (idx >= 0) {
                                    newIndices.splice(idx, 1)
                                } else {
                                    newIndices.push(filterItem.index)
                                }
                                filterControl.selectedIndices = newIndices
                                filterControl.selectionChanged(newIndices)
                            }
                            filterControl.itemClicked(filterItem.index)
                        }
                    }
                }
            }
        }
    }
}
