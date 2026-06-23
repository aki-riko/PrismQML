// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "../data"

// Watermark - Pure QtQuick implementation 水印组件
// Transparent overlay, repeat pattern 透明覆盖重复图案
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string text: "Watermark"
    property real fontSize: Enums.typography.body
    property real opacity_: Enums.opacityLevel.watermark
    property real rotation_: _internal.defaultRotation
    property int gapX: _internal.defaultGapX
    property int gapY: _internal.defaultGapY
    property color textColor: Enums.textColor.tertiary

    default property alias content: contentItem.data

    // ==================== Internal 内部常量 ====================
    QtObject {
        id: _internal
        // Watermark layout constants 水印布局常量
        readonly property real defaultRotation: -22  // Fluent Design standard angle 标准倾斜角度
        readonly property int defaultGapX: 120       // Horizontal gap 水平间距
        readonly property int defaultGapY: 100       // Vertical gap 垂直间距
        readonly property int extraCols: 2           // Extra columns for coverage 额外列数确保覆盖
        readonly property int extraRows: 2           // Extra rows for coverage 额外行数确保覆盖
    }

    // ==================== Content 内容区域 ====================
    Item {
        id: contentItem
        anchors.fill: parent
    }

    // ==================== Watermark Layer 水印层 ====================
    Item {
        anchors.fill: parent
        clip: true
        z: Enums.zIndex.popup

        Repeater {
            id: watermarkRepeater
            model: {
                var cols = Math.ceil(control.width / control.gapX) + _internal.extraCols
                var rows = Math.ceil(control.height / control.gapY) + _internal.extraRows
                return cols * rows
            }

            Label {
                id: watermarkText
                property int cols: Math.ceil(control.width / control.gapX) + _internal.extraCols
                property int col: index % cols
                property int row: Math.floor(index / cols)

                x: col * control.gapX - control.gapX / _internal.extraCols + (row % _internal.extraRows === 0 ? 0 : control.gapX / _internal.extraCols)
                y: row * control.gapY - control.gapY / _internal.extraRows

                type: Enums.label.type_caption
                text: control.text
                font.pixelSize: control.fontSize
                font.weight: Font.Light
                color: control.textColor
                opacity: control.opacity_
                rotation: control.rotation_
                transformOrigin: Item.Center
            }
        }
    }
}
