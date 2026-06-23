// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import ".."
import "../controls/icons"

// PipsPager - Pure QtQuick implementation 点状分页器纯QtQuick实现
// Page indicator 分页指示器
Item {
    id: control
    
    // Public props 公开属性
    property int pageCount: 5
    property int currentIndex: 0
    property int visiblePipCount: 5  // Max visible pips 最多显示点数
    property int orientation: Qt.Horizontal
    property color accentColor: Enums.accentColor  // Active pip color 选中点颜色
    
    // Signals 信号
    signal pageClicked(int index)
    
    // Internal state 内部状态
    readonly property bool isHorizontal: orientation === Qt.Horizontal
    
    // Size 尺寸
    implicitWidth: isHorizontal ? (pipsRow.implicitWidth + Enums.spacing.navBarHeight) : Enums.controlSize.emptyStateButtonHeight
    implicitHeight: isHorizontal ? Enums.controlSize.emptyStateButtonHeight : (pipsColumn.implicitHeight + Enums.spacing.navBarHeight)
    
    // Prev button 上一页按钮
    Rectangle {
        id: prevBtn
        anchors.left: control.isHorizontal ? parent.left : undefined
        anchors.top: control.isHorizontal ? undefined : parent.top
        anchors.verticalCenter: control.isHorizontal ? parent.verticalCenter : undefined
        anchors.horizontalCenter: control.isHorizontal ? undefined : parent.horizontalCenter
        width: Enums.iconSize.xl
        height: Enums.iconSize.xl
        radius: Enums.radius.small
        color: prevArea.containsMouse ? Enums.stateColor.controlBgHover : Enums.transparent
        visible: control.currentIndex > 0
        
        Icon {
            anchors.centerIn: parent
            iconSize: Enums.iconSize.micro
            color: Enums.textColor.tertiary
            icon: control.isHorizontal ? Enums.icon.chevron_left : Enums.icon.chevron_up
        }
        
        MouseArea {
            id: prevArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: {
                if (control.currentIndex > 0) {
                    control.currentIndex--
                    control.pageClicked(control.currentIndex)
                }
            }
        }
    }
    
    // Pips indicator (horizontal) 点状指示器水平
    Row {
        id: pipsRow
        anchors.centerIn: parent
        spacing: Enums.spacing.m
        visible: control.isHorizontal
        
        Repeater {
            model: Math.min(control.pageCount, control.visiblePipCount)
            
            Rectangle {
                width: index === control.currentIndex % control.visiblePipCount ? 16 : 8
                height: 8
                radius: Enums.radius.small
                color: index === control.currentIndex % control.visiblePipCount 
                    ? control.accentColor 
                    : (Enums.stateColor.dropBorderHover)
                
                Behavior on width { NumberAnimation { duration: Enums.duration.normal } }
                
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        control.currentIndex = index
                        control.pageClicked(index)
                    }
                }
            }
        }
    }
    
    // Pips indicator (vertical) 点状指示器垂直
    Column {
        id: pipsColumn
        anchors.centerIn: parent
        spacing: Enums.spacing.m
        visible: !control.isHorizontal
        
        Repeater {
            model: Math.min(control.pageCount, control.visiblePipCount)
            
            Rectangle {
                width: 8
                height: index === control.currentIndex % control.visiblePipCount ? 16 : 8
                radius: Enums.radius.small
                color: index === control.currentIndex % control.visiblePipCount 
                    ? control.accentColor 
                    : (Enums.stateColor.dropBorderHover)
                
                Behavior on height { NumberAnimation { duration: Enums.duration.normal } }
                
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        control.currentIndex = index
                        control.pageClicked(index)
                    }
                }
            }
        }
    }
    
    // Next button 下一页按钮
    Rectangle {
        id: nextBtn
        anchors.right: control.isHorizontal ? parent.right : undefined
        anchors.bottom: control.isHorizontal ? undefined : parent.bottom
        anchors.verticalCenter: control.isHorizontal ? parent.verticalCenter : undefined
        anchors.horizontalCenter: control.isHorizontal ? undefined : parent.horizontalCenter
        width: Enums.iconSize.xl
        height: Enums.iconSize.xl
        radius: Enums.radius.small
        color: nextArea.containsMouse ? Enums.stateColor.controlBgHover : Enums.transparent
        visible: control.currentIndex < control.pageCount - 1
        
        Icon {
            anchors.centerIn: parent
            iconSize: Enums.iconSize.micro
            color: Enums.textColor.tertiary
            icon: control.isHorizontal ? Enums.icon.chevron_right : Enums.icon.chevron_down
        }
        
        MouseArea {
            id: nextArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: {
                if (control.currentIndex < control.pageCount - 1) {
                    control.currentIndex++
                    control.pageClicked(control.currentIndex)
                }
            }
        }
    }
}
