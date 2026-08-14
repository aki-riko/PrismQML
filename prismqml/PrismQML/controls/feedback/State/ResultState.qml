// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../data/Label"

// ResultState - 结果状态页（支持主题）
Item {
    id: control
    
    property string state: "success"  // success, error, warning, empty, loading
    property string title: ""
    property string description: ""
    property string actionText: ""
    
    readonly property color stateColor: Enums.statusLevel.getColor(state)
    
    readonly property string stateIconName: {
        switch (state) {
            case "success": return "Checkmark"
            case "error": return "Dismiss"
            case "warning": return "Warning"
            case "empty": return "MailInboxDismiss"
            case "loading": return "ArrowSync"
            default: return "Info"
        }
    }

    signal actionClicked()
    
    implicitWidth: Enums.controlSize.resultStateWidth  // Fixed result width 固定结果宽度
    implicitHeight: contentCol.implicitHeight
    
    Column {
        id: contentCol
        anchors.centerIn: parent
        spacing: Enums.spacing.xl
        
        // Icon 图标
        Item {
            anchors.horizontalCenter: parent.horizontalCenter
            width: Enums.controlSize.resultStateIconSize
            height: Enums.controlSize.resultStateIconSize

            // Standard loading ring 标准加载环
            ProgressRing {
                anchors.fill: parent
                visible: state === "loading"
                indeterminate: visible
                color: stateColor
            }
            
            // Result icon container 结果图标容器
            Rectangle {
                anchors.fill: parent
                radius: width / 2
                color: Enums.stateColor.accentSubtle
                visible: state !== "loading"

                Icon {
                    anchors.centerIn: parent
                    iconSize: Enums.controlSize.flyoutIconSize
                    color: stateColor
                    icon: stateIconName
                }
            }
        }
        
        // Title 标题
        Label {
            type: Enums.label.type_subtitle
            anchors.horizontalCenter: parent.horizontalCenter
            text: title
            visible: text !== ""
        }
        
        // Description 描述
        Label {
            type: Enums.label.type_body
            anchors.horizontalCenter: parent.horizontalCenter
            text: description
            color: Enums.textColor.tertiary
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            width: Math.min(implicitWidth, 280)
            visible: text !== ""
        }
        
        // Action button 操作按钮
        ShadowedRectangle {
            id: actionSurface

            objectName: "resultStateActionSurface"
            anchors.horizontalCenter: parent.horizontalCenter
            width: actionBtnText.implicitWidth + 32
            height: Enums.controlSize.inputHeightLarge - 4
            radius: Enums.surfaceRadius(Enums.radius.small)
            color: actionArea.pressed ? Enums.accentColorDark : (actionArea.containsMouse ? Enums.accentColorLight : Enums.accentColor)
            border.width: Enums.surfaceBorderWidth(Enums.border.none)
            shadowVisible: Enums.isNeumorphism
            neumorphicPressed: actionArea.pressed
            visible: actionText !== ""
            
            Label {
                id: actionBtnText
                type: Enums.label.type_body
                anchors.centerIn: parent
                text: actionText
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
