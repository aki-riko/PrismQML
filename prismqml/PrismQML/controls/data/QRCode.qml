// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "../data"

// QRCode - QR code component 二维码组件
// Uses Python backend qrcode library to generate real QR codes 使用 Python 后端 qrcode 库生成真实二维码
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property string content: ""           // 二维码内容
    property int size: 150                // 目标尺寸（像素）
    property color foregroundColor: Enums.textColor.primary  // 前景色（黑色模块）
    property color backgroundColor: Enums.cardColor          // 背景色
    property string errorLevel: "M"       // 错误纠正级别: L(7%) / M(15%) / Q(25%) / H(30%)
    
    // ==================== Internal 内部属性 ====================
    readonly property bool isAvailable: typeof QRCodeGenerator !== "undefined" && QRCodeGenerator !== null && QRCodeGenerator.available

    // ==================== Public Methods 公共方法 ====================
    function getContent() { return content }

    implicitWidth: size
    implicitHeight: size
    
    // QR code image 二维码图片
    Image {
        id: qrImage
        anchors.fill: parent
        visible: control.isAvailable && control.content !== ""
        smooth: true
        fillMode: Image.PreserveAspectFit
        
        source: {
            if (!control.isAvailable || control.content === "" || typeof QRCodeGenerator === "undefined" || QRCodeGenerator === null) return ""
            return QRCodeGenerator.getImageSource(
                control.content,
                control.size,
                control.foregroundColor.toString(),
                control.backgroundColor.toString(),
                control.errorLevel
            )
        }
    }
    
    // Placeholder/error state 占位/错误状态
    Rectangle {
        anchors.fill: parent
        visible: !qrImage.visible
        color: control.backgroundColor
        radius: Enums.radius.small
        border.width: Enums.border.thin
        border.color: Enums.stateColor.border
        
        Column {
            anchors.centerIn: parent
            spacing: Enums.spacing.s
            
            // Placeholder icon 占位图标
            Label {
                anchors.horizontalCenter: parent.horizontalCenter
                type: Enums.label.type_display
                text: "📷"
                font.pixelSize: control.size * 0.2
            }
            
            // Hint text 提示文字
            Label {
                anchors.horizontalCenter: parent.horizontalCenter
                type: Enums.label.type_caption
                text: control.content === "" ? "无内容" : "加载中..."
                color: Enums.textColor.secondary
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }
}
