// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../Card"
import "../../icons"

// IconCardDelegate - Icon card for GridScrollArea 图标卡片代理
// Usage: GridScrollArea { delegate: IconCardDelegate {} }
Card {
    id: card
    cardType: Enums.card.type_elevated
    borderRadius: Enums.radius.large
    width: 100
    height: 88
    clickEnabled: true
    
    Column {
        anchors.centerIn: parent
        spacing: Enums.spacing.m
        
        Icon {
            anchors.horizontalCenter: parent.horizontalCenter
            iconSize: Enums.iconSize.xl
            color: Enums.textColor.primary
            icon: modelData
        }
        
        Text {
            id: textLabel
            anchors.horizontalCenter: parent.horizontalCenter
            text: modelData
            font.pixelSize: Enums.typography.caption
            font.family: Enums.fontFamily
            color: Enums.textColor.secondary
            width: 90
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideMiddle
        }
    }

}
