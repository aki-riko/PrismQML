// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import ".."
import "../effects"

// WindowIcon - Reusable window icon component 可复用的窗口图标组件
// Supports both themed and colored icons 支持主题图标和彩色图标
// Uses Python QSvgRenderer for high-quality SVG rendering 使用Python QSvgRenderer实现高质量SVG渲染
Item {
    id: root
    
    // ==================== Props 属性 ====================
    property string source: ""  // Icon source path 图标源路径
    property bool colored: false  // Whether icon is colored (skip theme overlay) 图标是否为彩色（跳过主题覆盖）
    
    // ==================== Size 尺寸 ====================
    width: Enums.window.titleIconSize
    height: Enums.window.titleIconSize
    
    visible: source !== ""
    
    // DPI 感知：物理像素 = 逻辑像素 × devicePixelRatio
    readonly property real _dpr: Screen.devicePixelRatio || 1.0
    readonly property int _physicalSize: Math.ceil(Enums.window.titleIconSize * _dpr)
    
    // Check if source is SVG 检查是否为SVG文件
    readonly property bool _isSvg: source.toLowerCase().endsWith(".svg")
    
    // Convert source to svg provider URL (only for SVG files) 将SVG源路径转换为svg提供器URL
    readonly property string _svgSource: {
        if (source === "" || !_isSvg) return ""
        // Normalize Windows backslashes to forward slashes 将Windows反斜杠转换为正斜杠
        let normalizedSource = source.replace(/\\/g, "/")
        // Convert qrc:/xxx to image://svg/qrc:/xxx
        if (normalizedSource.startsWith("qrc:/") || normalizedSource.startsWith(":/")) {
            return "image://svg/" + normalizedSource
        }
        // For file:// URLs, extract path 对于file://URL，提取路径
        if (normalizedSource.startsWith("file:///")) {
            return "image://svg/" + normalizedSource.substring(8)
        }
        return "image://svg/" + normalizedSource
    }
    
    // Direct source for non-SVG images (PNG, etc.) 非SVG图片直接使用源路径
    readonly property string _directSource: {
        if (source === "" || _isSvg) return ""
        // Normalize Windows backslashes to forward slashes 将Windows反斜杠转换为正斜杠
        let normalizedSource = source.replace(/\\/g, "/")
        // qrc paths work directly qrc路径直接使用
        if (normalizedSource.startsWith("qrc:/") || normalizedSource.startsWith(":/")) {
            return normalizedSource.startsWith(":/") ? "qrc" + normalizedSource : normalizedSource
        }
        // file:// URLs work directly file://URL直接使用
        if (normalizedSource.startsWith("file:///")) {
            return normalizedSource
        }
        // Local file paths need file:/// prefix 本地文件路径需要file:///前缀
        return "file:///" + normalizedSource
    }
    
    // ==================== SVG Icon Image SVG图标图像 ====================
    Image {
        id: svgImage
        anchors.fill: parent
        source: root._svgSource
        visible: root._isSvg
        fillMode: Image.PreserveAspectFit
        // Render at high resolution for crisp SVG display 高分辨率渲染以获得清晰的SVG显示
        sourceSize: Qt.size(Enums.window.iconRenderSize, Enums.window.iconRenderSize)
        cache: true
        smooth: true
        mipmap: true
        
        // Apply color overlay for theme-aware icons 应用颜色叠加实现主题感知
        layer.enabled: !root.colored
        layer.effect: ColorOverlay {
            color: Enums.textColor.primary
        }
    }
    
    // ==================== Non-SVG Icon Image (PNG, etc.) 非SVG图标图像 ====================
    Image {
        id: directImage
        anchors.fill: parent
        source: root._directSource
        visible: !root._isSvg && root.source !== ""
        fillMode: Image.PreserveAspectFit
        // sourceSize 精确匹配物理像素，Qt CPU 侧高质量重采样
        // 避免 GPU bilinear 大比例缩放导致模糊
        sourceSize: Qt.size(root._physicalSize, root._physicalSize)
        cache: true
        smooth: true
        mipmap: true
        // PNG icons are typically colored, no overlay PNG图标通常是彩色的，不需要叠加
    }
}
