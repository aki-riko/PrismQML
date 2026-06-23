// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../../effects"
import "../../buttons"
import "../../icons"

// ImageCropperPanel - Image cropper with toolbar 图片裁剪面板（含工具栏）
// Used by ImageCropper Dialog/Overlay modes 供ImageCropper的Dialog/Overlay模式使用
Item {
    id: panel
    
    // ==================== Required Props 必需属性 ====================
    required property url source
    required property int cropShape
    required property rect cropRect
    
    // ==================== Signals 信号 ====================
    signal cropRectUpdated(rect newRect)
    signal confirmClicked()
    signal cancelClicked()

    // ==================== Public Methods 公开方法 ====================
    function initDefaultCropRect() {
        content.initDefaultCropRect()
    }

    // ==================== Content 内容区 ====================
    ImageCropperContent {
        id: content
        anchors.fill: parent
        anchors.bottomMargin: Enums.imageCropperDialogMetrics.containerBottomMargin
        source: panel.source
        cropShape: panel.cropShape
        cropRect: panel.cropRect
        onCropRectUpdated: (newRect) => panel.cropRectUpdated(newRect)
    }
    
    // ==================== Toolbar 工具栏 ====================
    ShadowedRectangle {
        id: toolbar
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: Enums.imageCropperDialogMetrics.bottomToolbarBottomMargin
        width: toolRow.width + Enums.imageCropperDialogMetrics.bottomToolbarWidthPadding
        height: Enums.imageCropperDialogMetrics.bottomToolbarHeight
        radius: height / 2
        color: Enums.cardColor
        border.width: Enums.border.thin
        border.color: Enums.stateColor.cardBorder
        shadowLevel: Enums.shadow.level4
        
        Row {
            id: toolRow
            anchors.centerIn: parent
            spacing: Enums.spacing.xs
            
            Button {
                icon: Enums.icon.dismiss
                style: Enums.button.style_transparent
                shape: Enums.button.shape_pill
                onClicked: panel.cancelClicked()
            }
            Button {
                icon: Enums.icon.arrow_rotate_clockwise
                style: Enums.button.style_transparent
                shape: Enums.button.shape_pill
                onClicked: content.imageRotation = (content.imageRotation + 90) % 360
            }
            Button {
                icon: Enums.icon.flip_horizontal
                style: Enums.button.style_transparent
                shape: Enums.button.shape_pill
                onClicked: content.imageMirror = !content.imageMirror
            }
            Button {
                icon: Enums.icon.checkmark
                style: Enums.button.style_primary
                shape: Enums.button.shape_pill
                onClicked: panel.confirmClicked()
            }
        }
    }
}
