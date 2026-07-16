// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "../data"

// QRCode - QR code component 二维码组件
// Uses Python backend qrcode library to generate real QR codes 使用 Python 后端 qrcode 库生成真实二维码
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string content: "" // QR code content 二维码内容
    property int size: Enums.controlSize.qrcodeSize // Target size in pixels 目标像素尺寸
    property color foregroundColor: Enums.textColor.primary // Dark modules 深色模块
    property color backgroundColor: Enums.cardColor // Light modules 浅色模块
    property string errorLevel: "M" // Error correction L/M/Q/H 纠错级别

    // ==================== Readonly State 只读状态 ====================
    readonly property bool isAvailable: typeof QRCodeGenerator !== "undefined" && QRCodeGenerator !== null && QRCodeGenerator.available
    readonly property bool imageReady: qrImage.status === Image.Ready
    readonly property string imageSource: {
        if (!isAvailable || content === "" || typeof QRCodeGenerator === "undefined" || QRCodeGenerator === null)
            return ""
        return QRCodeGenerator.getImageSource(
            content,
            size,
            foregroundColor.toString(),
            backgroundColor.toString(),
            errorLevel
        )
    }
    readonly property int _qrPlaceholderRadius: Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.small
    readonly property color _qrBorderColor: Enums.stateColor.border
    readonly property color _qrHintColor: Enums.textColor.secondary

    // ==================== Public Methods 公开方法 ====================
    function getContent() { return content }

    // ==================== Size 尺寸 ====================
    implicitWidth: size
    implicitHeight: size

    // ==================== Content 内容 ====================
    // Placeholder/error state 占位/错误状态
    Rectangle {
        anchors.fill: parent
        color: control.backgroundColor
        radius: control._qrPlaceholderRadius
        border.width: Enums.border.thin
        border.color: control._qrBorderColor

        Column {
            anchors.centerIn: parent
            spacing: Enums.spacing.s

            // Placeholder icon 占位图标
            Label {
                anchors.horizontalCenter: parent.horizontalCenter
                type: Enums.label.type_display
                text: "📷"
                font.pixelSize: Enums.typography.display
            }

            // Hint text 提示文字
            Label {
                anchors.horizontalCenter: parent.horizontalCenter
                type: Enums.label.type_caption
                text: control.content === "" ? "无内容" : (control.imageSource === "" ? "参数无效" : "加载中...")
                color: control._qrHintColor
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }

    // QR code image 二维码图片
    Image {
        id: qrImage

        anchors.fill: parent
        visible: control.imageSource !== ""
        smooth: false
        fillMode: Image.PreserveAspectFit
        source: control.imageSource
        sourceSize: Qt.size(control.size, control.size)
    }
}
