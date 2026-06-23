// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import ".."
import "../controls/data/Label"

// LoadingOverlay - Reusable loading spinner overlay 可复用的加载动画覆盖层
// Extracted from Window*/WindowsBar/WindowsFilled 从三个窗口组件中提取
Rectangle {
    id: root
    
    required property bool loading
    property string text: Translator.tr("loading")
    property color backgroundColor: Enums.backgroundColor

    color: backgroundColor
    visible: loading
    z: Enums.zIndex.popup
    
    Column {
        anchors.centerIn: parent
        spacing: Enums.spacing.xl
        
        Item {
            width: Enums.controlSize.navBarHeight
            height: Enums.controlSize.navBarHeight
            anchors.horizontalCenter: parent.horizontalCenter
            
            RotationAnimator on rotation {
                from: 0; to: 360
                duration: Enums.duration.scroll
                loops: Animation.Infinite
                running: root.loading
            }
            
            Canvas {
                anchors.fill: parent
                onPaint: {
                    var ctx = getContext("2d")
                    ctx.clearRect(0, 0, width, height)
                    var centerX = width / 2, centerY = height / 2
                    var sw = Enums.controlSize.progressStrokeWidth
                    var r = Math.min(centerX, centerY) - sw / 2
                    ctx.strokeStyle = Enums.accentColor
                    ctx.lineWidth = sw
                    ctx.lineCap = "round"
                    ctx.beginPath()
                    ctx.arc(centerX, centerY, r, -Math.PI / 2, 0, false)
                    ctx.stroke()
                }
                Component.onCompleted: requestPaint()
            }
        }
        
        Label {
            type: Enums.label.type_body
            text: root.text
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }
}
