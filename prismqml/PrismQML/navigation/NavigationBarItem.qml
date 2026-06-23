// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import ".."
import "../effects"
import "../controls/data/Label"

// NavigationBarItem - Fluent Design navigation bar item 导航栏项
// 64x60px, vertical layout (icon top, text bottom), icon slide animation 垂直布局（图标在上，文字在下），图标滑动动画
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property string text: ""
    property string icon: ""
    property string selectedIcon: ""
    property bool selected: false
    property bool selectable: true
    
    signal clicked()
    
    // ==================== Internal State 内部状态 ====================
    readonly property bool hovered: mouseArea.containsMouse
    readonly property bool pressed: mouseArea.pressed
    readonly property color accentColor: Enums.accentColor
    
    // Icon offset animation 图标偏移动画
    property real iconOffset: 0
    
    
    // ==================== Size (64x60) 尺寸 ====================
    implicitWidth: Enums.controlSize.navBarItemWidth
    implicitHeight: Enums.controlSize.navBarItemHeight
    
    // ==================== Background 背景 ====================
    Rectangle {
        id: bg
        anchors.fill: parent
        anchors.leftMargin: Enums.spacing.xxs
        anchors.rightMargin: Enums.spacing.xxs
        anchors.topMargin: Enums.spacing.xxs
        anchors.bottomMargin: Enums.spacing.xxs
        radius: Enums.isNeobrutalism ? Enums.neo.radius : Enums.radius.small

        color: {
            if (control.selected) {
                // neo: 选中=橙实心块; Fluent: 淡色高亮
                if (Enums.isNeobrutalism) return Enums.neo.primary
                return Enums.stateColor.navSelected
            }
            if (control.pressed || control.hovered) {
                // Use stateColor constants 使用stateColor常量
                return control.hovered ? Enums.stateColor.hover : Enums.stateColor.pressed
            }
            return Enums.transparent
        }

        // neo: 选中态加黑边
        border.width: Enums.isNeobrutalism && control.selected ? Enums.neo.borderWidth : 0
        border.color: Enums.isNeobrutalism ? Enums.neo.borderColor : Enums.transparent

        // No animation to avoid flicker 无动画避免闪烁
    }
    
    // Indicator managed by NavigationBar 指示条由NavigationBar管理
    
    // ==================== Icon Area 图标区域 ====================
    Item {
        id: iconContainer
        anchors.horizontalCenter: parent.horizontalCenter
        y: Enums.spacing.l + Enums.spacing.micro + control.iconOffset
        width: Enums.iconSize.xl
        height: Enums.iconSize.xl
        
        // Check icon type 判断图标类型
        readonly property bool isPathIcon: control.icon.length > 0 && 
            (control.icon.startsWith("file:") || control.icon.startsWith("qrc:") || 
             control.icon.endsWith(".svg") || control.icon.endsWith(".png") ||
             control.icon.endsWith(".jpg") || control.icon.endsWith(".jpeg"))
        
        // Check if avatar image (non-svg images need circular clipping) 是否为头像图片（非svg的图片需要圆形裁剪）
        readonly property bool isAvatarIcon: isPathIcon && !control.icon.endsWith(".svg")
        
        // SVG icon (apply color overlay) SVG图标（应用颜色叠加）
        Image {
            id: svgIcon
            anchors.fill: parent
            source: iconContainer.isPathIcon && !iconContainer.isAvatarIcon ? 
                (control.selected && control.selectedIcon ? control.selectedIcon : control.icon) : ""
            visible: iconContainer.isPathIcon && !iconContainer.isAvatarIcon
            fillMode: Image.PreserveAspectFit
            opacity: (control.pressed || !control.hovered) && !control.selected ? Enums.opacityLevel.secondary : 1
            
            // High quality scaling 高质量缩放 SVG
            sourceSize: Qt.size(width * Screen.devicePixelRatio, height * Screen.devicePixelRatio)
            smooth: true
            antialiasing: true
            
            // Apply color overlay for theme-aware icons 应用颜色叠加实现主题感知
            layer.enabled: true
            layer.effect: ColorOverlay {
                color: control.selected ? (Enums.isNeobrutalism ? Enums.neo.primaryForeground : control.accentColor) : Enums.textColor.primary
            }
            
            Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
        }
        
        // Avatar image (circular clipping, no color overlay) 头像图片（圆形裁剪，不应用颜色叠加）
        Item {
            id: avatarContainer
            anchors.fill: parent
            visible: iconContainer.isAvatarIcon
            
            Image {
                id: avatarImage
                anchors.fill: parent
                source: iconContainer.isAvatarIcon ? 
                    (control.selected && control.selectedIcon ? control.selectedIcon : control.icon) : ""
                fillMode: Image.PreserveAspectCrop
                // High quality scaling 高质量缩放
                sourceSize: Qt.size(width * Screen.devicePixelRatio, height * Screen.devicePixelRatio)
                smooth: true
                antialiasing: true
                opacity: (control.pressed || !control.hovered) && !control.selected ? Enums.opacityLevel.secondary : 1
                
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
                
                Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
            }
        }
        
        // Emoji/text icon Emoji/文字图标
        Label {
            type: Enums.label.type_title
            anchors.centerIn: parent
            text: control.selected && control.selectedIcon ? control.selectedIcon : control.icon
            visible: !iconContainer.isPathIcon && control.icon !== ""
            color: control.selected ? (Enums.isNeobrutalism ? Enums.neo.primaryForeground : control.accentColor) : Enums.textColor.primary
            opacity: (control.pressed || !control.hovered) && !control.selected ? Enums.opacityLevel.secondary : 1
            
            Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
            Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
        }
    }
    
    // ==================== Text 文字 ====================
    Label {
        id: label
        type: Enums.label.type_caption
        anchors.horizontalCenter: parent.horizontalCenter
        y: Enums.controlSize.topNavItemHeight - Enums.spacing.xxs
        text: control.text
        font.pixelSize: Enums.typography.caption - 1
        horizontalAlignment: Text.AlignHCenter
        
        color: control.selected ? (Enums.isNeobrutalism ? Enums.neo.primaryForeground : control.accentColor) : Enums.textColor.primary

        Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
    }
    
    // ==================== Mouse Interaction 鼠标交互 ====================
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        enabled: control.enabled
        hoverEnabled: true
                onClicked: control.clicked()
    }
    
}
