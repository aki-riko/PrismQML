// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../menus"
import "../../buttons"

// BreadcrumbDelegate - Breadcrumb item delegate with animations 面包屑项代理（含动画）
// Internal component for Breadcrumb 面包屑内部组件
Item {
    id: itemRow
    
    // ==================== Required Props 必需属性 ====================
    required property int index
    required property var modelData
    // Get control via parent chain (Repeater -> Row -> Breadcrumb) 通过父级链获取control
    readonly property var control: parent ? parent.parent : null
    
    // ==================== Helper Props 辅助属性 ====================
    // Null-safe accessors to prevent undefined errors during initialization 空值安全访问器，防止初始化时的undefined错误
    readonly property var _safeItems: control ? control._items : []
    readonly property bool _safeAnimated: control ? control.animated : false
    readonly property bool _safeHasOverflow: control ? control._hasOverflow : false
    readonly property int _safeMaxVisibleItems: control ? control.maxVisibleItems : 5
    readonly property int _safeRemoveFromIndex: control ? control._removeFromIndex : -1
    readonly property int _safeNewItemIndex: control ? control._newItemIndex : -1
    readonly property var _safeNewlyCollapsedIndices: control ? control._newlyCollapsedIndices : []
    readonly property var _safeNewlyShownIndices: control ? control._newlyShownIndices : []
    readonly property bool _safeShiftLeftActive: control ? control._shiftLeftActive : false
    readonly property bool _safeShiftRightActive: control ? control._shiftRightActive : false
    readonly property bool _safeEllipsisWillHide: control ? control._ellipsisWillHide : false
    readonly property var _safeCollapsedItems: control ? control._collapsedItems : []
    readonly property bool _safeShowIcons: control ? control.showIcons : true
    
    // ==================== Computed Props 计算属性 ====================
    readonly property bool isLast: index === _safeItems.length - 1
    readonly property bool isFirst: index === 0
    readonly property bool showElide: isFirst && _safeHasOverflow
    // Ellipsis should fade out when overflow ends 省略号在不再溢出时应淡出
    readonly property bool ellipsisWillHide: isFirst && _safeEllipsisWillHide
    readonly property bool isRemoving: _safeRemoveFromIndex >= 0 && index >= _safeRemoveFromIndex
    readonly property bool isNewItem: _safeNewItemIndex >= 0 && index === _safeNewItemIndex
    // Will become last item after removal 移除后将成为最后一项
    readonly property bool willBecomeLast: _safeRemoveFromIndex >= 0 && index === _safeRemoveFromIndex - 1
    // Collapsed middle items when overflow 溢出时折叠到省略号的中间项
    readonly property bool isCollapsedMiddle: _safeHasOverflow && index > 0 && index < _safeItems.length - (_safeMaxVisibleItems - 2)
    // Item being collapsed to ellipsis 正在折叠到省略号的项
    readonly property bool isCollapsingToEllipsis: _safeNewlyCollapsedIndices.indexOf(index) >= 0
    // Item being shown from ellipsis 正在从省略号恢复显示的项
    readonly property bool isShowingFromEllipsis: _safeNewlyShownIndices.indexOf(index) >= 0
    // Item needs to shift left (visible items after collapsed one) 需要向左位移的项（折叠项之后的可见项）
    readonly property bool needsShiftLeft: _safeShiftLeftActive && !isCollapsedMiddle && !isFirst && index > 0
    // Item needs to shift right (visible items after shown one) 需要向右位移的项（显示项之后的可见项）
    readonly property bool needsShiftRight: _safeShiftRightActive && !isCollapsedMiddle && !isFirst && index > 0 && !isShowingFromEllipsis

    // ==================== Size 尺寸 ====================
    width: rowContent.width
    height: control ? control.implicitHeight : Enums.controlSize.inputHeightCompact

    // Collapse middle items (after animation completes) 折叠中间项（动画完成后）
    visible: !isCollapsedMiddle || isCollapsingToEllipsis || isShowingFromEllipsis
    
    // ==================== Animation State 动画状态 ====================
    property real animOpacity: 1.0
    property real animX: 0
    property real animScale: 1.0
    property real animY: 0

    // Forward animation - slide in from right with scale and bounce 前进动画 - 从右侧滑入+缩放+弹性
    Component.onCompleted: {
        if (_safeAnimated && isNewItem) {
            animOpacity = 0
            animX = 40
            animScale = 0.85
            animY = -8
            var delay = index * 50
            enterAnimDelay.duration = delay
            enterAnim.restart()
        }
    }

    SequentialAnimation {
        id: enterAnim
        PauseAnimation {
            id: enterAnimDelay
            duration: 0
        }
        ParallelAnimation {
            NumberAnimation {
                target: itemRow
                property: "animOpacity"
                from: 0; to: 1
                duration: Enums.duration.dialog
                easing.type: Easing.OutCubic
            }
            NumberAnimation {
                target: itemRow
                property: "animX"
                from: 40; to: 0
                duration: Enums.duration.dialog + Enums.duration.fast
                easing.type: Easing.OutBack
                easing.overshoot: 1.7
            }
            NumberAnimation {
                target: itemRow
                property: "animScale"
                from: 0.85; to: 1.0
                duration: Enums.duration.dialog + Enums.duration.instant
                easing.type: Easing.OutBack
                easing.overshoot: 1.3
            }
            NumberAnimation {
                target: itemRow
                property: "animY"
                from: -8; to: 0
                duration: Enums.duration.dialog + Enums.duration.fast
                easing.type: Easing.OutBack
                easing.overshoot: 1.5
            }
        }
    }

    // ==================== States 状态 ====================
    states: [
        State {
            name: "removing"
            when: itemRow.isRemoving
            PropertyChanges {
                target: itemRow
                animOpacity: 0
                animX: 30
                animScale: 0.9
                animY: -5
            }
        },
        State {
            name: "collapsingToEllipsis"
            when: itemRow.isCollapsingToEllipsis
            PropertyChanges {
                target: itemRow
                animOpacity: 0
            }
        },
        State {
            name: "showingFromEllipsis"
            when: itemRow.isShowingFromEllipsis
        }
    ]

    transitions: [
        Transition {
            to: "removing"
            enabled: _safeAnimated
            SequentialAnimation {
                PauseAnimation {
                    id: removeAnimDelay
                    duration: {
                        // Reverse order delay - last item animates first 反向延迟 - 最后一项先动画
                        var totalRemoving = _safeItems.length - _safeRemoveFromIndex
                        var reverseIndex = totalRemoving - 1 - (index - _safeRemoveFromIndex)
                        var delay = reverseIndex * 50
                        if (delay < 0) delay = 0
                        return delay
                    }
                }
                ParallelAnimation {
                    NumberAnimation {
                        property: "animOpacity"
                        duration: Enums.duration.dialog
                        easing.type: Easing.OutCubic
                    }
                    NumberAnimation {
                        property: "animX"
                        duration: Enums.duration.dialog + Enums.duration.fast
                        easing.type: Easing.OutBack
                        easing.overshoot: 1.7
                    }
                    NumberAnimation {
                        property: "animScale"
                        duration: Enums.duration.dialog + Enums.duration.instant
                        easing.type: Easing.OutBack
                        easing.overshoot: 1.3
                    }
                    NumberAnimation {
                        property: "animY"
                        duration: Enums.duration.dialog + Enums.duration.fast
                        easing.type: Easing.OutBack
                        easing.overshoot: 1.5
                    }
                }
            }
        },
        Transition {
            to: "collapsingToEllipsis"
            enabled: _safeAnimated
            NumberAnimation {
                property: "animOpacity"
                duration: Enums.duration.slow
                easing.type: Easing.OutCubic
            }
        },
        Transition {
            to: "showingFromEllipsis"
            enabled: _safeAnimated
            NumberAnimation {
                property: "animOpacity"
                from: 0; to: 1
                duration: Enums.duration.slow
                easing.type: Easing.OutCubic
            }
        }
    ]

    // ==================== Visual Transform 视觉变换 ====================
    opacity: animOpacity
    transform: [
        Translate { 
            x: animX + (itemRow.needsShiftLeft || itemRow.isCollapsingToEllipsis ? (control ? control._shiftLeftOffset : 0) : 0)
                   + (itemRow.needsShiftRight ? (control ? control._shiftRightOffset : 0) : 0)
            y: animY 
        },
        Scale { origin.x: 0.5; origin.y: 0.5; xScale: animScale; yScale: animScale }
    ]
    
    // ==================== Content 内容 ====================
    Row {
        id: rowContent
        spacing: Enums.spacing.xxs
        height: control ? control.implicitHeight : Enums.controlSize.inputHeightCompact
        
        // Button 按钮
        Button {
            id: breadcrumbBtn
            anchors.verticalCenter: parent.verticalCenter
            style: Enums.button.style_transparent
            flat: true
            // Disable early when will become last to avoid color jump 提前禁用避免颜色跳变
            enabled: !itemRow.isLast && !itemRow.isRemoving && !itemRow.willBecomeLast
            text: modelData.text || ""
            icon: (_safeShowIcons && modelData.icon) ? modelData.icon : ""
            iconSize: Enums.iconSize.s
            onClicked: if (control) control.setCurrentItem(modelData.key)
        }
        
        // Chevron 箭头
        Item {
            id: chevronItem
            visible: !itemRow.isLast || itemRow.isRemoving
            width: visible ? Enums.iconSize.xs + Enums.spacing.xs : 0
            height: control ? control.implicitHeight : Enums.controlSize.inputHeightCompact
            
            // Chevron animation state 箭头动画状态
            property real chevronOpacity: 1.0
            property real chevronX: 0
            
            Icon {
                anchors.centerIn: parent
                icon: Enums.icon.chevron_right
                iconSize: Enums.controlSize.chevronIconSize
                color: Enums.secondaryForeground
                opacity: Enums.opacityLevel.secondary * parent.chevronOpacity
                transform: Translate { x: chevronItem.chevronX }
            }
            
            states: State {
                name: "hiding"
                when: itemRow.willBecomeLast
                PropertyChanges {
                    target: chevronItem
                    chevronOpacity: 0
                    chevronX: 30
                }
            }
            
            transitions: Transition {
                to: "hiding"
                enabled: _safeAnimated
                ParallelAnimation {
                    NumberAnimation {
                        property: "chevronOpacity"
                        duration: Enums.duration.dialog
                        easing.type: Easing.OutCubic
                    }
                    NumberAnimation {
                        property: "chevronX"
                        duration: Enums.duration.dialog + Enums.duration.fast
                        easing.type: Easing.OutBack
                        easing.overshoot: 1.7
                    }
                }
            }
        }
        
        // Elide button and chevron container 省略按钮和箭头容器
        Item {
            id: elideContainer
            // Stay visible during fade-out animation 在淡出动画期间保持可见
            visible: itemRow.showElide || itemRow.ellipsisWillHide
            width: elideWidth
            height: control ? control.implicitHeight : Enums.controlSize.inputHeightCompact
            anchors.verticalCenter: parent.verticalCenter
            clip: true
            
            // Animation state 动画状态
            property real elideOpacity: 1.0
            property real elideX: 0
            property real elideScale: 1.0
            property real elideY: 0
            property real elideWidth: elideRow.width
            
            Row {
                id: elideRow
                spacing: 0
                anchors.verticalCenter: parent.verticalCenter
                opacity: elideContainer.elideOpacity
                transform: [
                    Translate { x: elideContainer.elideX; y: elideContainer.elideY },
                    Scale { origin.x: 0.5; origin.y: 0.5; xScale: elideContainer.elideScale; yScale: elideContainer.elideScale }
                ]
                
                // Elide button 省略按钮
                Button {
                    id: elideBtn
                    anchors.verticalCenter: parent.verticalCenter
                    style: Enums.button.style_transparent
                    flat: true
                    icon: Enums.icon.more_horizontal
                    iconSize: Enums.iconSize.s
                    onClicked: elideMenu.show()
                }
                
                ContextMenu {
                    id: elideMenu
                    autoBindRightClick: false
                    Repeater {
                        model: _safeCollapsedItems
                        Action { text: modelData.text; onTriggered: if (control) control.setCurrentItem(modelData.key) }
                    }
                }
                
                // Elide chevron 省略号后的箭头
                Item {
                    width: Enums.iconSize.xs + Enums.spacing.xs
                    height: control ? control.implicitHeight : Enums.controlSize.inputHeightCompact
                    Icon {
                        anchors.centerIn: parent
                        icon: Enums.icon.chevron_right
                        iconSize: Enums.controlSize.chevronIconSize
                        color: Enums.secondaryForeground
                        opacity: Enums.opacityLevel.secondary
                    }
                }
            }
            
            states: State {
                name: "hiding"
                when: itemRow.ellipsisWillHide
                PropertyChanges {
                    target: elideContainer
                    elideOpacity: 0
                    elideX: 30
                    elideScale: 0.9
                    elideY: -5
                    elideWidth: 0
                }
            }
            
            transitions: Transition {
                to: "hiding"
                enabled: _safeAnimated
                ParallelAnimation {
                    NumberAnimation {
                        property: "elideOpacity"
                        duration: Enums.duration.dialog
                        easing.type: Easing.OutCubic
                    }
                    NumberAnimation {
                        property: "elideX"
                        duration: Enums.duration.dialog + Enums.duration.fast
                        easing.type: Easing.OutBack
                        easing.overshoot: 1.7
                    }
                    NumberAnimation {
                        property: "elideScale"
                        duration: Enums.duration.dialog + Enums.duration.instant
                        easing.type: Easing.OutBack
                        easing.overshoot: 1.3
                    }
                    NumberAnimation {
                        property: "elideY"
                        duration: Enums.duration.dialog + Enums.duration.fast
                        easing.type: Easing.OutBack
                        easing.overshoot: 1.5
                    }
                    NumberAnimation {
                        property: "elideWidth"
                        duration: Enums.duration.dialog + Enums.duration.fast
                        easing.type: Easing.OutCubic
                    }
                }
            }
        }
    }
}
