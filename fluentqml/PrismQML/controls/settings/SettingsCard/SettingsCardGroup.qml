// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../data"

// SettingsCardGroup - Setting card group container 设置卡片分组容器
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property string title: ""
    property int spacing: Enums.spacing.xxs  // Card spacing 卡片间距
    
    // ==================== Content 内容 ====================
    default property alias cards: cardColumn.data
    
    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.controlSize.cardWidth
    implicitHeight: titleLabel.height + Enums.spacing.l + cardColumn.height

    // ==================== Public Methods 公开方法 ====================
    function addCard(card) {
        card.parent = cardColumn
        // Auto-set card width to parent container width 自动设置卡片宽度为父容器宽度
        card.width = Qt.binding(function() { return cardColumn.width })
    }

    function removeCard(card) {
        card.parent = null
    }

    function clearCards() {
        for (var i = cardColumn.children.length - 1; i >= 0; i--) {
            cardColumn.children[i].destroy()
        }
    }

    // ==================== Title 标题 ====================
    Label {
        id: titleLabel
        type: Enums.label.type_body_strong
        text: control.title
        font.pixelSize: Enums.typography.titleLarge
        visible: control.title !== ""
    }
    
    // ==================== Card Container 卡片容器 ====================
    Column {
        id: cardColumn
        anchors.top: titleLabel.visible ? titleLabel.bottom : parent.top
        anchors.topMargin: titleLabel.visible ? Enums.spacing.l : 0
        anchors.left: parent.left
        anchors.right: parent.right
        spacing: control.spacing
    }
}
