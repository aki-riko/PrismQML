// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../utils"
import "../../../effects"

// Badge - Unified badge component 统一徽章组件
// Supports: count, text, icon, dot modes 支持：计数、文本、图标、点模式
// Use Enums.statusLevel.xxx for level 使用 Enums.statusLevel.xxx 作为级别
Rectangle {
    id: control
    
    // ==================== Required Props 必需属性 ====================
    // Level: Enums.statusLevel.info/success/warning/error/attention
    property int level: Enums.statusLevel.error
    
    // ==================== Public Props 公开属性 ====================
    property int count: 0              // Count mode 计数模式
    property int maxCount: 99          // Max count before showing "99+" 最大计数
    property string text: ""           // Text mode 文本模式
    property string icon: ""           // Icon mode 图标模式
    property bool dot: false           // Dot mode 点模式
    property bool showZero: false      // Show badge when count is 0 计数为0时是否显示

    // Host anchoring 宿主锚定
    // Inert until a target is supplied: with `target: null` the badge keeps its
    // own declarative geometry exactly as before.
    // 未提供 target 前完全不生效: target 为 null 时徽章保持原有声明式几何, 行为不变。
    property Item target: null         // Host item to anchor onto 锚定的宿主控件
    property int anchorPosition: Enums.position.top_right  // Anchored corner 锚定角
    property real anchorOffset: Enums.spacing.xs           // Outward offset 向外偏移

    // ==================== Readonly State 只读状态 ====================
    // Anchor geometry, resolved in the badge's own parent space
    // 锚定几何, 在徽章自身父级坐标系内解析
    readonly property point _anchorOrigin: control.target
        ? control._originInParentSpace(control.target, control.parent)
        : Qt.point(0, 0)
    readonly property real _anchorRight: _anchorOrigin.x
        + (control.target ? control.target.width : 0)
    readonly property real _anchorBottom: _anchorOrigin.y
        + (control.target ? control.target.height : 0)
    readonly property bool _anchorLeftSide:
        anchorPosition === Enums.position.top_left
        || anchorPosition === Enums.position.bottom_left
    readonly property bool _anchorTopSide:
        anchorPosition === Enums.position.top_left
        || anchorPosition === Enums.position.top_right
    readonly property real _anchoredX: _anchorLeftSide
        ? _anchorOrigin.x - anchorOffset
        : _anchorRight - width + anchorOffset
    readonly property real _anchoredY: _anchorTopSide
        ? _anchorOrigin.y - anchorOffset
        : _anchorBottom - height + anchorOffset

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
    
    // Text color on semantic/accent fill 语义/强调填充上的文字色
    readonly property color _contentColor: Enums.accentForeground
    readonly property real _badgeBorderWidth: Enums.isNeobrutalism
                                               ? Enums.border.medium
                                               : (Enums.isVintageTicket
                                                  ? Enums.ticket.borderWidth : 0)
    readonly property color _badgeBorderColor: Enums.hasOutlinedSurfaces
                                                ? Enums.borderColor : Enums.transparent

    // ==================== Internal Methods 内部方法 ====================
    // Resolve a target origin inside the badge's parent space while keeping the
    // binding reactive; mapToItem() alone would not create dependencies.
    // 在徽章父级空间内解析 target 原点并保持绑定响应; 仅用 mapToItem 不会建立依赖。
    // The badge's parent must be the target itself or one of its ancestors.
    // 徽章的父级必须是 target 本身或它的某个祖先。
    function _originInParentSpace(item, space) {
        if (!item || item === space) return Qt.point(0, 0)
        var parentOrigin = _originInParentSpace(item.parent, space)
        return Qt.point(parentOrigin.x + item.x, parentOrigin.y + item.y)
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: _effectiveDot ? Enums.spacing.s : Math.max(Enums.controlSize.checkboxOuter, contentItem.implicitWidth + Enums.spacing.m)
    implicitHeight: _effectiveDot ? Enums.spacing.s : Enums.controlSize.checkboxOuter
    radius: height / 2
    visible: _visible

    // Color 颜色
    // 语义色由 getColorByLevel 在 neo 下自动返回高饱和值; 黑边为 neo 结构差异
    color: Enums.statusLevel.getColorByLevel(level)
    // Outlined skins keep a visible ink edge; Neo stays on its compact medium width.
    // 描边皮肤保留可见油墨边；Neo 小徽章继续使用紧凑 medium 宽度。
    border.width: control._badgeBorderWidth
    border.color: control._badgeBorderColor

    NeumorphicShadow {
        target: control
        visible: Enums.isNeumorphism
        z: control.z - 1
    }
    
    // ==================== Content 内容 ====================
    // A badge is a static annotation; its accessible name is the count or text a
    // sighted user reads, so screen readers announce the same value.
    // 徽标是静态标注；可访问名称即用户看到的计数或文本，使读屏器播报同一数值。
    A11ySurface {
        target: control
        role: Enums.accessibility.role_statictext
        name: control.text !== "" ? control.text : String(control.count)
    }

    // Host anchoring binds only while a target exists, so a badge without a
    // target never overrides its own x/y.
    // 宿主锚定仅在存在 target 时绑定, 没有 target 的徽章永远不会覆盖自身 x/y。
    Binding {
        target: control
        property: "x"
        when: control.target !== null
        value: control._anchoredX
    }

    Binding {
        target: control
        property: "y"
        when: control.target !== null
        value: control._anchoredY
    }

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
            font.pixelSize: Enums.typography.captionCompact
            font.weight: Font.Medium
            color: control._contentColor
            visible: control._showText || control._showCount
        }
    }
    
}
