// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

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
    
    signal actionClicked()
    
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
    
    implicitWidth: Enums.controlSize.resultStateWidth  // Fixed result width 固定结果宽度
    implicitHeight: contentCol.implicitHeight
    
    Column {
        id: contentCol
        anchors.centerIn: parent
        spacing: Enums.spacing.xl
        
        // Icon 图标
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            width: Enums.controlSize.resultStateIconSize; height: Enums.controlSize.resultStateIconSize; radius: width / 2  // Fixed icon container 固定图标容器(圆形)
            color: Enums.stateColor.accentSubtle
            
            Icon {
                anchors.centerIn: parent
                iconSize: Enums.controlSize.flyoutIconSize
                color: stateColor
                icon: stateIconName
            }
            
            RotationAnimation on rotation {
                running: state === "loading"
                from: 0; to: 360
                duration: Enums.duration.dialog * 3.75
                loops: Animation.Infinite
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
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            width: actionBtnText.implicitWidth + 32
            height: Enums.controlSize.inputHeightLarge - 4
            radius: Enums.radius.small
            color: actionArea.containsMouse ? Qt.lighter(Enums.accentColor, 1.1) : Enums.accentColor
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
