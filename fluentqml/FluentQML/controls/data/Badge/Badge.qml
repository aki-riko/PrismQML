// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"

// Badge - Unified badge component 统一徽章组件
// Supports: count, text, icon, dot modes 支持：计数、文本、图标、点模式
// Use Enums.statusLevel.xxx for level 使用 Enums.statusLevel.xxx 作为级别
Rectangle {
    id: control
    
    // ==================== Required Props 必需属性 ====================
    // Level: Enums.statusLevel.info/success/warning/error/attention
    property int level: Enums.statusLevel.error
    
    // ==================== Content Props 内容属性 ====================
    property int count: 0              // Count mode 计数模式
    property int maxCount: 99          // Max count before showing "99+" 最大计数
    property string text: ""           // Text mode 文本模式
    property string icon: ""           // Icon mode 图标模式
    property bool dot: false           // Dot mode 点模式
    property bool showZero: false      // Show badge when count is 0 计数为0时是否显示
    
    // ==================== Internal State 内部状态 ====================
    // Check if has explicit content 检查是否有显式内容
    readonly property bool _hasContent: icon !== "" || text !== "" || count > 0 || showZero
    
    // Effective dot: only when explicitly opted-in via `dot` prop. 仅显式 dot:true 才是点模式
    // 注意: count=0 且未设 showZero 时应整体隐藏(对齐 Ant/Element Badge 语义),
    // 不再退化成无意义的无数字红点。
    readonly property bool _effectiveDot: dot
    
    // Default icon only for explicit icon prop 仅显式设置icon时使用
    readonly property string _defaultIcon: icon
    
    readonly property bool _showIcon: _defaultIcon !== "" && !_effectiveDot
    readonly property bool _showText: text !== "" && !_showIcon && !_effectiveDot
    readonly property bool _showCount: !_showText && !_showIcon && !_effectiveDot && (count > 0 || (count === 0 && showZero))
    readonly property bool _visible: _effectiveDot || _showIcon || _showText || _showCount
    
    // Text color: always white 文字颜色：统一白色
    readonly property color _contentColor: Enums.accentForeground

    // ==================== Size 尺寸 ====================
    implicitWidth: _effectiveDot ? Enums.spacing.s : Math.max(Enums.controlSize.checkboxOuter, contentItem.implicitWidth + Enums.spacing.m)
    implicitHeight: _effectiveDot ? Enums.spacing.s : Enums.controlSize.checkboxOuter
    radius: height / 2
    visible: _visible

    // ==================== Color 颜色 ====================
    // 语义色由 getColorByLevel 在 neo 下自动返回高饱和值; 黑边为 neo 结构差异
    color: Enums.statusLevel.getColorByLevel(level)
    // neo: 黑细粗边(徽章小, 用 medium 不用 thick)
    border.width: Enums.isNeobrutalism ? Enums.border.medium : 0
    border.color: Enums.isNeobrutalism ? Enums.neo.borderColor : Enums.transparent
    
    // ==================== Content 内容 ====================
    Item {
        id: contentItem
        anchors.centerIn: parent
        implicitWidth: _showIcon ? iconItem.width : contentText.implicitWidth
        implicitHeight: _showIcon ? iconItem.height : contentText.implicitHeight
        visible: !control._effectiveDot
        
        // Icon 图标
        Icon {
            id: iconItem
            anchors.centerIn: parent
            icon: control._defaultIcon
            iconSize: Enums.iconSize.xs
            color: control._contentColor
            visible: control._showIcon
        }
        
        // Text or Count 文字或计数
        Text {
            id: contentText
            anchors.centerIn: parent
            text: {
                if (control._showText) return control.text
                if (control._showCount) return control.count > control.maxCount ? control.maxCount + "+" : String(control.count)
                return ""
            }
            font.family: Enums.fontFamily
            font.pixelSize: Enums.typography.caption - 1
            font.weight: Font.Medium
            color: control._contentColor
            visible: control._showText || control._showCount
        }
    }
    
}
