// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."

// Icon - Unified icon component 统一图标组件
// Usage: icon: Enums.icon.chevron_up 使用枚举方式
// Also supports: text/emoji, image path (png/svg/qrc) 也支持文本/emoji和图片路径
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property string icon: ""           // Icon name / text / emoji / image path 图标名/文本/emoji/图片路径
    property bool themeAware: true     // Icon color follows theme 图标颜色跟随主题
    
    // Base path for fluent icons 图标基础路径
    readonly property string _fluentBasePath: Qt.resolvedUrl("fluent/")
    
    // Check if icon is a Icon name (PascalCase or special cases like iOS*) 检查是否为图标名称
    // 含下划线: 大量图标名带下划线(如 Multiplier1_2x), 正则须含 _ 否则被当文本 fallback
    readonly property bool _isIconName: icon !== "" && /^[a-zA-Z][a-zA-Z0-9_]*$/.test(icon) && icon.length > 1
    
    // Check if icon is an image path 检查是否为图片路径
    readonly property bool _isImagePath: icon !== "" && (
        icon.startsWith("qrc:") || 
        icon.startsWith("file:") || 
        icon.startsWith("http") ||
        icon.endsWith(".png") || 
        icon.endsWith(".jpg") || 
        icon.endsWith(".jpeg") || 
        icon.endsWith(".svg") ||
        icon.startsWith("/") ||
        icon.match(/^[a-zA-Z]:/)  // Windows absolute path
    )
    
    // Compute actual source 计算实际source
    readonly property string _resolvedSource: {
        if (_isIconName) {
            return _fluentBasePath + icon + ".svg"
        }
        if (_isImagePath) {
            return icon
        }
        return ""
    }
    
    // Icon size 图标尺寸
    property int iconSize: Enums.iconSize.m
    property alias size: control.iconSize
    
    // Icon color 图标颜色
    property color color: Enums.textColor.primary
    property color iconColor: color
    
    // ==================== Readonly State 只读状态 ====================
    readonly property bool isTextIcon: icon !== "" && !_isIconName && !_isImagePath
    readonly property bool isImageIcon: _resolvedSource !== ""
    readonly property bool isSvgIcon: _resolvedSource.toLowerCase().endsWith(".svg")
    // Check for avatar icon (non-svg images require circular clipping, no color overlay) 是否为头像图标（非 svg 的图片需要圆形裁剪，不应用颜色叠加）

    readonly property bool isAvatarIcon: isImageIcon && !isSvgIcon && (
        _resolvedSource.endsWith(".png") || _resolvedSource.endsWith(".jpg") || _resolvedSource.endsWith(".jpeg")
    )

    // ==================== Public Methods 公开方法 ====================
    // Set icon 设置图标
    function setIcon(iconName) {
        icon = iconName
    }

    // Set icon size 设置图标尺寸
    function setIconSize(size) {
        iconSize = size
    }

    // Set color 设置颜色
    function setColor(c) {
        color = c
    }

    function clear() { icon = "" }
    function hasIcon() { return icon !== "" }

    // ==================== Size 尺寸 ====================
    implicitWidth: iconSize
    implicitHeight: iconSize
    width: iconSize
    height: iconSize
    
    // ==================== Content 内容 ====================
    // Load only the active icon renderer 仅加载当前图标渲染器
    Loader {
        readonly property Item iconControl: control

        anchors.fill: parent
        active: control.icon !== ""
        sourceComponent: control.isTextIcon
            ? IconRendererResources.textIconComponent
            : control.isAvatarIcon
                ? IconRendererResources.avatarIconComponent
                : control.isImageIcon
                    ? IconRendererResources.imageIconComponent
                    : null
    }
}
