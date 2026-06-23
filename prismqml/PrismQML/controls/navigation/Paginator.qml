// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "../icons"
import "../buttons"
import "../data"

// Paginator - Fluent Design style pagination 分页器
// Features: sliding animation when page changes, hover effects, accent color highlight
Item {
    id: root
    
    // ==================== Public Props 公开属性 ====================
    property int currentPage: 1
    property int totalPages: 10
    property int visiblePages: 5
    property color accentColor: Enums.accentColor
    property bool showPrevNext: true
    
    signal pageChanged(int page)
    
    // ==================== Private Props 私有属性 ====================
    readonly property real _buttonSize: Enums.controlSize.buttonHeight
    readonly property real _spacing: Enums.spacing.xxs
    readonly property real _itemWidth: _buttonSize + _spacing
    
    // ==================== Size 尺寸 ====================
    implicitWidth: pagerRow.implicitWidth
    implicitHeight: _buttonSize

    Row {
        id: pagerRow
        anchors.centerIn: parent
        spacing: _spacing
        
        // ==================== Previous Button 上一页按钮 ====================
        Button {
            visible: root.showPrevNext
            style: Enums.button.style_transparent
            icon: Enums.icon.chevron_left
            iconSize: Enums.iconSize.xs
            implicitWidth: root._buttonSize
            implicitHeight: root._buttonSize
            flat: true
            enabled: root.currentPage > 1
            onClicked: {
                root.currentPage--
                root.pageChanged(root.currentPage)
            }
        }
        
        // ==================== Page Numbers Viewport 页码视口 ====================
        Item {
            id: viewport
            width: root.visiblePages * root._buttonSize + (root.visiblePages - 1) * root._spacing
            height: root._buttonSize
            clip: true
            
            // Inner container with all pages 包含所有页码的内部容器
            Item {
                id: innerContainer
                width: root.totalPages * root._itemWidth
                height: root._buttonSize
                
                // Slide to show current page centered 滑动使当前页居中
                x: -_targetX
                
                property real _targetX: {
                    var centerIndex = Math.floor(root.visiblePages / 2)
                    var pageIndex = root.currentPage - 1
                    var maxOffset = root.totalPages - root.visiblePages
                    var offset = Math.max(0, Math.min(maxOffset, pageIndex - centerIndex))
                    return offset * root._itemWidth
                }
                
                Behavior on x {
                    NumberAnimation {
                        duration: Enums.duration.medium
                        easing.type: Easing.OutCubic
                    }
                }

                // Sliding indicator 滑动指示器
                Rectangle {
                    id: indicator
                    width: root._buttonSize
                    height: root._buttonSize
                    radius: Enums.radius.small
                    color: root.accentColor
                    
                    x: (root.currentPage - 1) * root._itemWidth
                    
                    Behavior on x {
                        NumberAnimation {
                            duration: Enums.duration.medium
                            easing.type: Easing.OutCubic
                        }
                    }
                }
                
                // Page number buttons 页码按钮
                Row {
                    id: pageRow
                    spacing: root._spacing
                    
                    Repeater {
                        id: pageRepeater
                        model: root.totalPages
                        
                        delegate: Item {
                            id: pageDelegate
                            required property int index
                            
                            property int pageNum: index + 1
                            property bool isCurrentPage: pageNum === root.currentPage
                            
                            width: root._buttonSize
                            height: root._buttonSize
                            
                            // Hover background 悬停背景
                            Rectangle {
                                anchors.fill: parent
                                radius: Enums.radius.small
                                color: pageMouseArea.containsMouse && !pageDelegate.isCurrentPage 
                                       ? Enums.stateColor.hover : "transparent"
                                Behavior on color {
                                    ColorAnimation { duration: Enums.duration.fast }
                                }
                            }
                            
                            // Page number text 页码文字
                            Label {
                                anchors.centerIn: parent
                                type: Enums.label.type_body
                                text: pageDelegate.pageNum.toString()
                                color: pageDelegate.isCurrentPage 
                                       ? Enums.accentForeground 
                                       : Enums.foregroundColor
                                Behavior on color {
                                    ColorAnimation { duration: Enums.duration.fast }
                                }
                            }
                            
                            MouseArea {
                                id: pageMouseArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    root.currentPage = pageDelegate.pageNum
                                    root.pageChanged(pageDelegate.pageNum)
                                }
                            }
                        }
                    }
                }
            }
        }

        // ==================== Next Button 下一页按钮 ====================
        Button {
            visible: root.showPrevNext
            style: Enums.button.style_transparent
            icon: Enums.icon.chevron_right
            iconSize: Enums.iconSize.xs
            implicitWidth: root._buttonSize
            implicitHeight: root._buttonSize
            flat: true
            enabled: root.currentPage < root.totalPages
            onClicked: {
                root.currentPage++
                root.pageChanged(root.currentPage)
            }
        }
    }
}
