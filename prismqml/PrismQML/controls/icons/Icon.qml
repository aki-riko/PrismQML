// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import QtQuick.Effects
import "../../effects"

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
    readonly property bool _isIconName: icon !== "" && /^[a-zA-Z][a-zA-Z0-9]*$/.test(icon) && icon.length > 1
    
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
    
    // ==================== Computed Props 计算属性 ====================
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
    
    // ==================== Text Icon 文本图标 ====================
    Text {
        anchors.centerIn: parent
        text: control.icon
        font.pixelSize: control.iconSize
        font.family: Enums.fontFamily
        color: control.color
        visible: control.isTextIcon
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
    
    // ==================== Image Icon 图片图标（非SVG非头像，应用颜色叠加）====================
    Image {
        anchors.centerIn: parent
        width: control.iconSize
        height: control.iconSize
        source: control.isImageIcon && !control.isSvgIcon && !control.isAvatarIcon ? control._resolvedSource : ""
        visible: control.isImageIcon && !control.isSvgIcon && !control.isAvatarIcon
        fillMode: Image.PreserveAspectFit
        smooth: true
        mipmap: true
        asynchronous: true
        
        layer.enabled: true
        layer.effect: ColorOverlay { color: control.color }
    }
    
    // ==================== Avatar Icon 头像图标（圆形裁剪，不应用颜色叠加）====================
    Item {
        id: avatarContainer
        anchors.centerIn: parent
        width: control.iconSize
        height: control.iconSize
        visible: control.isAvatarIcon
        
        Image {
            anchors.fill: parent
            source: control.isAvatarIcon ? control._resolvedSource : ""
            fillMode: Image.PreserveAspectCrop
            smooth: true
            mipmap: true
            asynchronous: true
            
            layer.enabled: true
            layer.smooth: true
            layer.effect: MultiEffect {
                maskEnabled: true
                maskThresholdMin: 0.5
                maskSpreadAtMin: 1.0
                maskSource: ShaderEffectSource {
                    sourceItem: Rectangle {
                        width: avatarContainer.width
                        height: avatarContainer.height
                        radius: width / 2
                        antialiasing: true
                    }
                }
            }
        }
    }
    
    // ==================== SVG Icon SVG图标 ====================
    Image {
        anchors.centerIn: parent
        width: control.iconSize
        height: control.iconSize
        source: control.isSvgIcon ? control._resolvedSource : ""
        visible: control.isSvgIcon
        fillMode: Image.PreserveAspectFit
        smooth: true
        sourceSize: Qt.size(control.iconSize * 2, control.iconSize * 2)
        
        layer.enabled: true
        layer.effect: ColorOverlay { color: control.color }
    }
}
