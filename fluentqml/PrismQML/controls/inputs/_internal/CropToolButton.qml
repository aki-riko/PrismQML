// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../feedback"

// CropToolButton - Tool button for ImageCropperDialog 图像裁剪器工具按钮
// Extracted from ImageCropperDialog for modularity 从ImageCropperDialog提取以模块化
Rectangle {
    id: cropToolBtn
    
    // ==================== Props 属性 ====================
    property string icon: ""
    property string tip: ""
    property bool highlight: false
    
    signal clicked()
    
    width: Enums.imageCropperDialogMetrics.toolButtonSize
    height: Enums.imageCropperDialogMetrics.toolButtonSize
    radius: Enums.radius.xlarge + Enums.spacing.xs
    color: highlight 
        ? Enums.accentColor 
        : (ma.containsMouse ? Enums.stateColor.whiteOverlay : Enums.transparent)
    
    Icon { 
        anchors.centerIn: parent
        icon: cropToolBtn.icon
        iconSize: Enums.imageCropperDialogMetrics.toolButtonIconSize
        color: Enums.textColor.primary 
    }
    
    MouseArea {
        id: ma
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: cropToolBtn.clicked()
        onContainsMouseChanged: {
            if (containsMouse && cropToolBtn.tip !== "") {
                tipTimer.start()
            } else {
                tipTimer.stop()
                tooltip.hide()
            }
        }
    }
    
    Timer {
        id: tipTimer
        interval: 0
        onTriggered: tooltip.show()
    }
    
    ToolTip {
        id: tooltip
        text: cropToolBtn.tip
        x: (cropToolBtn.width - width) / 2
        y: -height - Enums.imageCropperDialogMetrics.toolTipOffset
    }
}
