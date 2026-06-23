// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../utils"
import "../../../effects"
import "../../data"
import ".."
import "../../containers/ScrollBar"
import "../../inputs/Toggle"
import "_internal"

// ComboBoxMulti - Multi-selection dropdown with tag display 多选下拉框
// Extends ComboBoxCore for consistent styling 继承ComboBoxCore保持样式一致
ComboBoxCore {
    id: control
    
    // ==================== Disable Base Content 禁用基类内容 ====================
    useDefaultContent: false
    // Only intercept wheel when content overflows 仅当内容溢出时拦截滚轮
    acceptWheel: tokenFlickable.contentWidth > tokenFlickable.width
    
    // ==================== Multi-Select Props 多选属性 ====================
    property var selectedIndices: []
    
    // ==================== Signals 信号 ====================
    signal selectionChanged(var indices, var items)
    
    // ==================== Size Override 尺寸覆盖 ====================
    implicitWidth: 220
    
    // ==================== Smooth Scroll 平滑滚动 ====================
    property real _smoothContentX: 0
    property real _targetX: 0
    on_SmoothContentXChanged: tokenFlickable.contentX = _smoothContentX
    
    Behavior on _smoothContentX {
        NumberAnimation {
            duration: Enums.duration.medium
            easing.type: Easing.OutQuart
        }
    }
    
    function smoothScrollTo(targetX) {
        var maxX = Math.max(0, tokenFlickable.contentWidth - tokenFlickable.width)
        _targetX = Math.max(0, Math.min(maxX, targetX))
        _smoothContentX = _targetX
    }
    
    // ==================== Wheel Scroll Handler 滚轮滚动处理 ====================
    // Use base class wheel signal 使用基类滚轮信号
    onWheelScrolled: (delta) => smoothScrollTo(_targetX - delta * 0.8)
    
    // ==================== Token Display Area 标签显示区域 ====================
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
        interactive: false  // Disable drag, use wheel only 禁用拖拽，仅用滚轮

        Row {
            id: tokenRow
            height: Enums.spacing.xxxl
            spacing: Enums.spacing.xs
            
            // Placeholder text 占位符文本
            Label {
                type: Enums.label.type_body
                text: control.placeholderText
                color: Enums.textColor.disabled
                visible: control.selectedIndices.length === 0
                anchors.verticalCenter: parent.verticalCenter
            }
            
            // Token tags 标签
            Repeater {
                model: control.selectedIndices
                
                delegate: MultiSelectToken {
                    id: tokenDelegate
                    required property int index
                    required property var modelData
                    
                    readonly property int itemIndex: modelData
                    readonly property var _control: control  // Capture control reference 捕获control引用
                    
                    text: {
                        if (itemIndex < 0 || itemIndex >= _control.model.length) return ""
                        var item = _control.model[itemIndex]
                        return typeof item === 'object' ? (item.text || item) : item
                    }
                    tokenIndex: index
                    anchors.verticalCenter: parent.verticalCenter
                    
                    onRemoveClicked: (idx) => {
                        var newIndices = tokenDelegate._control.selectedIndices.slice()
                        newIndices.splice(idx, 1)
                        tokenDelegate._control.selectedIndices = newIndices
                        var items = []
                        for (var i = 0; i < newIndices.length; i++) items.push(tokenDelegate._control.model[newIndices[i]])
                        tokenDelegate._control.selectionChanged(newIndices, items)
                    }
                }
            }
        }
    }

    // ==================== Override Popup Content 覆盖弹出内容 ====================
    popupContent: Component {
        Item {
            id: multiPopupContainer
            width: parent ? parent.width : control.width
            height: parent ? parent.height : Enums.comboBoxMetrics.popupDefaultHeight
            
            readonly property bool needsScroll: multiFlickable.contentHeight > multiFlickable.height
            
            Flickable {
                id: multiFlickable
                anchors.fill: parent
                anchors.rightMargin: multiPopupContainer.needsScroll ? Enums.comboBoxMetrics.scrollBarRightMargin : 0
                contentWidth: width
                contentHeight: multiColumn.height
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                interactive: false  // Disable native scroll, use smooth scroll 禁用原生滚动，使用平滑滚动
                
                // Smooth scroll 平滑滚动
                PopupSmoothScroll { flickable: multiFlickable; enabled: multiPopupContainer.needsScroll }
                
                Column {
                    id: multiColumn
                    width: parent.width
                    
                    Repeater {
                        model: control.model
                        
                        delegate: Rectangle {
                            width: multiColumn.width
                            height: Enums.comboBoxMetrics.itemHeight
                            radius: Enums.radius.small
                            
                            property bool selected: control.selectedIndices.indexOf(index) >= 0
                            
                            color: {
                                if (itemArea.pressed) return Enums.stateColor.menuItemPressed
                                if (itemArea.containsMouse) return Enums.stateColor.menuItemHover
                                return Enums.transparent
                            }
                            
                            Row {
                                anchors.left: parent.left
                                anchors.leftMargin: Enums.spacing.l
                                anchors.verticalCenter: parent.verticalCenter
                                spacing: Enums.spacing.m
                                
                                // Checkbox indicator 复选框指示器
                                CheckIndicator {
                                    anchors.verticalCenter: parent.verticalCenter
                                    checkState: selected ? 2 : 0
                                    hovered: itemArea.containsMouse
                                    pressed: itemArea.pressed
                                    checkedColor: control.accentColor
                                }
                                
                                Label {
                                    type: Enums.label.type_body
                                    text: typeof modelData === 'object' ? (modelData.text || modelData) : modelData
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                            }
                            
                            MouseArea {
                                id: itemArea
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: {
                                    var idx = control.selectedIndices.indexOf(index)
                                    var newIndices = control.selectedIndices.slice()
                                    if (idx >= 0) newIndices.splice(idx, 1)
                                    else newIndices.push(index)
                                    control.selectedIndices = newIndices
                                    
                                    var items = []
                                    for (var i = 0; i < newIndices.length; i++) items.push(control.model[newIndices[i]])
                                    control.selectionChanged(newIndices, items)
                                }
                            }
                        }
                    }
                }
            }
            
            // Scrollbar 滚动条
            Loader {
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.margins: Enums.spacing.xxs
                width: Enums.comboBoxMetrics.scrollBarWidth
                active: multiPopupContainer.needsScroll
                sourceComponent: ScrollBarEntry {
                    flickable: multiFlickable
                    width: Enums.comboBoxMetrics.scrollBarWidth
                }
            }
        }
    }
}
