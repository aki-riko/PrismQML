// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../data/Label"

// EmptyDataState - Pure QtQuick implementation 空状态组件纯QtQuick实现
// Display empty data or no result state 显示空数据或无结果
Item {
    id: control
    
    property string image: ""  // Image path or emoji 图片路径或emoji
    property string title: Translator.tr("no_data")  // No data 暂无数据
    property int imageWidth: 128
    property int imageHeight: 128
    
    implicitWidth: 300
    implicitHeight: contentColumn.height
    
    Column {
        id: contentColumn
        anchors.centerIn: parent
        spacing: Enums.spacing.xl
        
        // Image/Icon 图片/图标
        Item {
            anchors.horizontalCenter: parent.horizontalCenter
            width: control.imageWidth
            height: control.imageHeight
            
            // If image path 如果是图片路径
            Image {
                anchors.fill: parent
                source: control.image.indexOf("/") >= 0 || control.image.indexOf(".") >= 0 ? control.image : ""
                fillMode: Image.PreserveAspectFit
                visible: source !== ""
            }
            
            // If emoji or text 如果是emoji或文字
            Icon {
                anchors.centerIn: parent
                iconSize: Math.min(control.imageWidth, control.imageHeight) * 0.6
                visible: control.image.indexOf("/") < 0 && control.image.indexOf(".") < 0 || control.image === ""
                icon: control.image.indexOf("/") < 0 && control.image.indexOf(".") < 0 && control.image !== "" ? control.image : "MailInboxDismiss"
            }
        }
        
        // Title text 标题文本
        Label {
            type: Enums.label.type_subtitle
            anchors.horizontalCenter: parent.horizontalCenter
            text: control.title
            color: Enums.textColor.tertiary
            horizontalAlignment: Text.AlignHCenter
        }
    }
    
}
