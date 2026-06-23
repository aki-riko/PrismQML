// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../data/Label"

// OfflineState - Pure QtQuick implementation 无网络状态纯QtQuick实现
// Display network disconnected state with retry button 显示断网状态带重试
Item {
    id: control
    
    property string title: ""  // Title text 标题文本
    property string retryText: ""  // Retry button text 重试按钮文本
    property int imageWidth: 128
    property int imageHeight: 128
    
    signal retried()
    
    implicitWidth: 300
    implicitHeight: contentColumn.height
    
    Column {
        id: contentColumn
        anchors.centerIn: parent
        spacing: Enums.spacing.xl
        
        // Image/Icon 图片图标
        Item {
            anchors.horizontalCenter: parent.horizontalCenter
            width: control.imageWidth
            height: control.imageHeight
            
            Icon {
                anchors.centerIn: parent
                iconSize: Math.min(control.imageWidth, control.imageHeight) * 0.6
                color: Enums.textColor.tertiary
                icon: Enums.icon.wi_fi_off
            }
        }
        
        // Title text 标题文本
        Label {
            type: Enums.label.type_subtitle
            anchors.horizontalCenter: parent.horizontalCenter
            text: control.title || "No Internet Connection"
            color: Enums.textColor.tertiary
            horizontalAlignment: Text.AlignHCenter
        }
        
        // Retry button 重试按钮
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            width: retryTextItem.width + 32
            height: 32
            radius: Enums.radius.small
            color: retryArea.pressed ? Qt.darker(Enums.accentColor, 1.1) : (retryArea.containsMouse ? Qt.lighter(Enums.accentColor, 1.1) : Enums.accentColor)
            
            Label {
                id: retryTextItem
                type: Enums.label.type_body
                anchors.centerIn: parent
                text: control.retryText || "Retry"
                color: "white"
            }
            
            MouseArea {
                id: retryArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: control.retried()
            }
        }
    }
}
