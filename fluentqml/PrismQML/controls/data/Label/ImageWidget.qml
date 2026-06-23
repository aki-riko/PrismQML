// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../.."
import "../../icons"

// ImageWidget - High-resolution image component with rounded corners 高清图片组件（支持圆角裁剪）
// Supports 4K/8K/16K images with HiDPI optimization 支持超高清图片和高DPI优化
// Renamed from Image to avoid conflict with QtQuick.Image 从 Image 重命名以避免与 QtQuick.Image 冲突
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property string source: ""
    property int radius: Enums.radius.small
    property int fillMode: Image.PreserveAspectCrop  // Fill mode 填充模式
    property bool loading: sourceImage.status === Image.Loading
    property bool error: sourceImage.status === Image.Error
    property bool ready: sourceImage.status === Image.Ready
    
    // HiDPI support 高DPI支持
    property bool hiDpiEnabled: true  // Enable HiDPI scaling 启用高DPI缩放
    property real maxSourceSize: 16384  // Max source size (16K) 最大源尺寸
    
    // Original image info 原始图片信息
    readonly property int sourceWidth: sourceImage.sourceSize.width
    readonly property int sourceHeight: sourceImage.sourceSize.height
    
    signal clicked()
    property color accentColor: Enums.accentColor

    // ==================== Public Methods 公共方法 ====================
    // Set scaled contents (for compatibility) 设置缩放内容
    function setScaledContents(scaled) {
        fillMode = scaled ? Image.Stretch : Image.PreserveAspectFit
    }

    implicitWidth: 100
    implicitHeight: 100
    
    // ==================== Placeholder 占位符 ====================
    Rectangle {
        anchors.fill: parent
        radius: control.radius
        color: Enums.stateColor.controlBgHover
        visible: loading || error || source === ""
        
        Icon {
            anchors.centerIn: parent
            iconSize: Math.min(parent.width, parent.height) * 0.3
            color: Enums.stateColor.dropBorderHover
            icon: error ? "DismissCircle" : (loading ? "ArrowSync" : "Camera")
        }
    }
    
    // ==================== Rounded Image Container 圆角图片容器 ====================
    Item {
        id: imageContainer
        anchors.fill: parent
        visible: sourceImage.status === Image.Ready
        
        Image {
            id: sourceImage
            anchors.fill: parent
            source: control.source
            asynchronous: true
            cache: true
            mipmap: true
            smooth: true
            fillMode: control.fillMode
        }
        
        layer.enabled: control.radius > 0
        layer.smooth: true
        layer.samples: 8
        layer.effect: MultiEffect {
            maskEnabled: true
            maskThresholdMin: 0.5
            maskSpreadAtMin: 1.0
            maskSource: ShaderEffectSource {
                sourceItem: Rectangle {
                    width: imageContainer.width
                    height: imageContainer.height
                    radius: control.radius
                    antialiasing: true
                }
                smooth: true
            }
        }
    }
    
    // ==================== Interaction 交互 ====================
    MouseArea {
        anchors.fill: parent
        onClicked: control.clicked()
    }
}
