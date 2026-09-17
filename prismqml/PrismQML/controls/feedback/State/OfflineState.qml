// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

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

    readonly property string _defaultTitle: {
        Translator._v
        return Translator.tr("no_internet")
    }
    readonly property string _defaultRetryText: {
        Translator._v
        return Translator.tr("retry")
    }
    // Touch has no hover preview: on touch the hover treatment follows the press
    // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
    readonly property bool _touchActive: Touch.feedback(retryArea.containsMouse,
                                                       retryArea.pressed)
    
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
            text: control.title || control._defaultTitle
            color: Enums.textColor.tertiary
            horizontalAlignment: Text.AlignHCenter
        }
        
        // Retry button 重试按钮
        ShadowedRectangle {
            id: retrySurface

            objectName: "offlineStateActionSurface"
            anchors.horizontalCenter: parent.horizontalCenter
            width: retryTextItem.width + 32
            // Interactive target: raised to the touch minimum off desktop
            // 交互目标尺寸: 非桌面端抬到触摸下限
            height: Touch.target(32)
            radius: Enums.surfaceRadius(Enums.radius.small)
            color: retryArea.pressed ? Enums.accentColorDark : (_touchActive ? Enums.accentColorLight : Enums.accentColor)
            border.width: Enums.surfaceBorderWidth(Enums.border.none)
            shadowVisible: Enums.isNeumorphism
            neumorphicPressed: retryArea.pressed
            
            Label {
                id: retryTextItem
                type: Enums.label.type_body
                anchors.centerIn: parent
                text: control.retryText || control._defaultRetryText
                color: Enums.accentForeground
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
