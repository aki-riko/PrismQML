// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../data"

// EmptyState - 空状态（支持主题）
Item {
    id: control
    
    property string icon: Enums.icon.mail_inbox_dismiss
    property string title: { Translator._v; return Translator.tr("no_data") }
    property string description: ""
    property string actionText: ""
    
    signal actionClicked()
    
    implicitWidth: 300
    implicitHeight: contentCol.implicitHeight
    
    Column {
        id: contentCol
        anchors.centerIn: parent
        spacing: Enums.spacing.l
        
        // Icon (using Icon component) 图标（使用Icon组件）
        Icon {
            iconSize: Enums.iconSize.display
            anchors.horizontalCenter: parent.horizontalCenter
            opacity: Enums.opacityLevel.disabled
            icon: control.icon
        }
        
        Label {
            anchors.horizontalCenter: parent.horizontalCenter
            text: title
            type: Enums.label.type_subtitle
            color: Enums.textColor.strong
        }
        
        Label {
            anchors.horizontalCenter: parent.horizontalCenter
            text: description
            type: Enums.label.type_caption
            color: Enums.stateColor.textMedium
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            width: Math.min(implicitWidth, 260)
            visible: text !== ""
        }
        
        ShadowedRectangle {
            id: actionSurface

            objectName: "emptyStateActionSurface"
            anchors.horizontalCenter: parent.horizontalCenter
            width: actionBtnText.implicitWidth + 24
            height: 32
            radius: Enums.surfaceRadius(Enums.radius.small)
            color: actionArea.pressed ? Enums.accentColorDark : (actionArea.containsMouse ? Enums.accentColorLight : Enums.accentColor)
            border.width: Enums.surfaceBorderWidth(Enums.border.none)
            shadowVisible: Enums.isNeumorphism
            neumorphicPressed: actionArea.pressed
            visible: actionText !== ""
            
            Label {
                id: actionBtnText
                anchors.centerIn: parent
                text: actionText
                type: Enums.label.type_caption
                color: Enums.accentForeground
            }
            
            MouseArea {
                id: actionArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: actionClicked()
            }
        }
    }
}
