// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import "../../.."

// DataWidgetFooter - Data widget count footer 数据组件计数底栏
Rectangle {
    id: footer

    // ==================== Required Props 必需属性 ====================
    required property var dataControl

    Layout.fillWidth: true
    height: Enums.controlSize.inputHeightCompact
    color: dataControl.headerColor
    radius: dataControl._effectiveBorderRadius
    visible: dataControl.showFooter && dataControl.itemCount > 0
    opacity: visible ? 1 : 0

    Behavior on opacity {
        enabled: dataControl.animated
        NumberAnimation {
            duration: Enums.duration.normal
            easing.type: Easing.OutCubic
        }
    }

    // Top half fill 顶部半圆填充
    Rectangle {
        anchors.top: parent.top
        width: parent.width
        height: parent.height / 2
        color: parent.color
    }

    Label {
        anchors.centerIn: parent
        type: Enums.label.type_caption
        text: dataControl.footerText
              ? dataControl.footerText.replace("{count}", dataControl.itemCount)
              : Enums.trCount("total_items", dataControl.itemCount)
        font.pixelSize: Enums.typography.captionCompact
        color: dataControl.secondaryColor
    }
}
