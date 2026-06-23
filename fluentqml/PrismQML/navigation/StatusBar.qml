// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import ".."
import "../controls/data/Label"

// StatusBar - Pure QtQuick implementation 状态栏纯QtQuick实现
// Display status info at window bottom 显示窗口底部状态信息
Rectangle {
    id: control
    
    // Public props 公开属性
    property string message: ""
    property var leftItems: []  // Left items 左侧项
    property var rightItems: [] // Right items 右侧项
    
    // Size 尺寸
    implicitWidth: parent ? parent.width : 400
    implicitHeight: Enums.controlSize.statusBarHeight
    
    color: Enums.surfaceColor
    
    // Top separator 顶部分隔线
    Separator {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        lineColor: Enums.stateColor.inputBorder
    }
    
    // Left content 左侧内容
    Row {
        anchors.left: parent.left
        anchors.leftMargin: Enums.spacing.m
        anchors.verticalCenter: parent.verticalCenter
        spacing: Enums.spacing.xl
        
        // Message text 消息文本
        Label {
            type: Enums.label.type_caption
            text: control.message
            color: Enums.textColor.secondary
            visible: control.message !== ""
        }
        
        // Left custom items 左侧自定义项
        Repeater {
            model: control.leftItems
            
            Label {
                type: Enums.label.type_caption
                text: modelData.text || modelData
                color: Enums.textColor.secondary
            }
        }
    }
    
    // Right content 右侧内容
    Row {
        anchors.right: parent.right
        anchors.rightMargin: Enums.spacing.m
        anchors.verticalCenter: parent.verticalCenter
        spacing: Enums.spacing.xl
        
        Repeater {
            model: control.rightItems
            
            Label {
                type: Enums.label.type_caption
                text: modelData.text || modelData
                color: Enums.textColor.secondary
            }
        }
    }
}
