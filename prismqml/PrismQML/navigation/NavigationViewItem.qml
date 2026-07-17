// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import ".."
import "../effects"
import "../controls/data/Label"

// NavigationViewItem - Expandable navigation item 展开式导航项
// Horizontal layout: icon+text, supports compact mode 水平布局
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property string text: ""
    property string icon: ""
    property bool selected: false
    property bool compact: false  // Compact mode (icon only) 紧凑模式
    property bool selectable: true  // Whether item can be selected 是否可选中
    
    // ==================== Readonly State 只读状态 ====================
    readonly property bool hovered: mouseArea.containsMouse
    readonly property bool pressed: mouseArea.pressed
    readonly property color accentColor: Enums.accentColor
    readonly property int _navItemRadius: Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.card
    readonly property color _navItemBackground: {
        if (control.selected) return Enums.stateColor.navSelected
        if (control.pressed || control.hovered) return control.hovered ? Enums.stateColor.hover : Enums.stateColor.pressed
        return Enums.transparent
    }
    readonly property int _navItemBorderWidth: Enums.isPrismDesign && control.selected ? Enums.prismDesign.borderWidth : 0
    readonly property color _navItemBorderColor: Enums.isPrismDesign ? Enums.prismDesign.primaryDark : Enums.transparent
    readonly property color _navItemContentColor: control.selected ? control.accentColor : Enums.textColor.primary

    // ==================== Signals 信号 ====================
    signal clicked()
    
    // ==================== Size 尺寸 ====================
    implicitWidth: parent ? parent.width : Enums.controlSize.navPanelExpandWidth
    implicitHeight: Enums.controlSize.navItemHeight
    clip: true  // Clip overflow content, hide text in compact mode 裁剪超出内容，紧凑模式下隐藏文本
    
    // ==================== Content 内容 ====================
    // Background 背景
    Rectangle {
        id: bg
        anchors.fill: parent
        radius: control._navItemRadius
        
        color: control._navItemBackground
        border.width: control._navItemBorderWidth
        border.color: control._navItemBorderColor
        
        // Prism glass rail rim Prism玻璃导航边缘
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: Enums.prismDesign.borderWidth
            color: Enums.prismDesign.glassRimLight
            visible: Enums.isPrismDesign && (control.selected || control.hovered)
        }

        Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: Enums.prismDesign.focusBorderWidth
            radius: width / 2
            color: Enums.prismDesign.spectralEdge
            opacity: control.selected ? 0.9 : 0.35
            visible: Enums.isPrismDesign && (control.selected || control.hovered)

            Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
        }

        // No animation to avoid flicker 无动画避免闪烁
    }
    
    // Selection indicator managed by NavigationView 选中指示条由 NavigationView 管理
    // Removed: indicator is now managed by NavigationView with slide animation 已移除：指示条现在由NavigationView统一管理，支持滑动动画
    
    // Content (horizontal layout) 内容（水平布局）
    // Icon position: center in visible area in compact mode 图标位置：紧凑模式下需要在可见区域内居中
    // Visible area width = navPanelCompactWidth - navPanelPaddingH * 2 = 48 - 4*2 = 40px
    // Icon center = (40 - 20) / 2 = 10px
    Row {
        // Icon type check 图标判断
        readonly property bool isPathIcon: control.icon.length > 0 && 
            (control.icon.startsWith("file:") || control.icon.startsWith("qrc:") || 
             control.icon.endsWith(".svg") || control.icon.endsWith(".png") ||
             control.icon.endsWith(".jpg") || control.icon.endsWith(".jpeg"))

        // Check if avatar image (non-svg images need circular clipping) 是否为头像图片（非svg的图片需要圆形裁剪）
        readonly property bool isAvatarIcon: isPathIcon && !control.icon.endsWith(".svg")

        anchors.left: parent.left
        anchors.leftMargin: (Enums.controlSize.navPanelCompactWidth - Enums.controlSize.navPanelPaddingH * 2 - Enums.iconSize.xl) / 2
        anchors.verticalCenter: parent.verticalCenter
        spacing: Enums.spacing.l
        
        // SVG icon (apply color overlay) SVG图标（应用颜色叠加）
        Image {
            anchors.verticalCenter: parent.verticalCenter
            width: Enums.iconSize.xl
            height: Enums.iconSize.xl
            source: parent.isPathIcon && !parent.isAvatarIcon ? control.icon : ""
            visible: parent.isPathIcon && !parent.isAvatarIcon
            fillMode: Image.PreserveAspectFit
            
            // High quality scaling 高质量缩放 SVG
            sourceSize: Qt.size(width * Screen.devicePixelRatio, height * Screen.devicePixelRatio)
            smooth: true
            antialiasing: true
            
            // Apply color overlay for theme-aware icons 应用颜色叠加实现主题感知
            layer.enabled: true
            layer.effect: ColorOverlay {
                color: control._navItemContentColor
            }
        }
        
        // Avatar image (circular clipping, no color overlay) 头像图片（圆形裁剪，不应用颜色叠加）
        Item {
            id: avatarContainer
            anchors.verticalCenter: parent.verticalCenter
            width: Enums.iconSize.xl
            height: Enums.iconSize.xl
            visible: parent.isAvatarIcon
            
            Image {
                anchors.fill: parent
                source: avatarContainer.visible ? control.icon : ""
                fillMode: Image.PreserveAspectCrop
                // High quality scaling 高质量缩放
                sourceSize: Qt.size(width * Screen.devicePixelRatio, height * Screen.devicePixelRatio)
                smooth: true
                antialiasing: true
                
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
        
        // Emoji/text icon Emoji/文字图标
        Label {
            type: Enums.label.type_subtitle
            anchors.verticalCenter: parent.verticalCenter
            text: control.icon
            visible: !parent.isPathIcon && control.icon !== ""
            color: control._navItemContentColor
            
            Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
        }
        
        // Text (hidden in compact mode) 文字（紧凑模式下隐藏）
        Label {
            type: Enums.label.type_body_small
            anchors.verticalCenter: parent.verticalCenter
            text: control.text
            visible: !control.compact
        }
    }
    
    // Mouse interaction 鼠标交互
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        enabled: control.enabled
        hoverEnabled: true
        onClicked: control.clicked()
    }
}
