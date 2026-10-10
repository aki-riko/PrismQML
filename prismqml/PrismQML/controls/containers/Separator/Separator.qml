// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import "../../.."
import ".."
import "../../utils"

// Separator - Unified separator component 统一分隔线组件
// Usage: Separator { type: Enums.separator.horizontal }
Widget {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property int type: 0  // 0=horizontal, 1=vertical
    property real lineWidth: effectiveSkinContext.border.thin
    property real lineLength: 0  // 0=auto fill, >0=fixed length  0=自动填充，>0=固定长度
    property color lineColor: effectiveSkinContext.stateColor.divider  // Line color, defaults to divider, overridable 线条颜色,默认 divider, 可覆盖

    // ==================== Readonly State 只读状态 ====================
    readonly property bool isHorizontal: type === 0
    readonly property bool autoFill: lineLength <= 0

    // ==================== Size 尺寸 ====================
    // 水平分隔线：宽度填充或固定，高度为线宽
    // 垂直分隔线：宽度为线宽，高度填充或固定
    contentWidth: isHorizontal ? (autoFill ? 100 : lineLength) : lineWidth
    contentHeight: isHorizontal ? lineWidth : (autoFill ? 100 : lineLength)

    // Layout fill support 布局填充支持（仅autoFill时生效）
    Layout.fillWidth: isHorizontal && autoFill
    Layout.fillHeight: !isHorizontal && autoFill
    Layout.preferredHeight: isHorizontal ? lineWidth : (autoFill ? -1 : lineLength)
    Layout.preferredWidth: isHorizontal ? (autoFill ? -1 : lineLength) : lineWidth

    // ==================== Content 内容 ====================
    Rectangle {
        anchors.fill: parent
        color: control.lineColor
    }

    // A divider is pure decoration: it carries no text and no interaction, so it is
    // removed from the accessibility tree instead of being given a role. The role
    // stays required by the A11ySurface contract and is passed as none.
    // 分隔线是纯装饰：既无文本也无交互，因此从无障碍树移除而不是赋予角色。
    // A11ySurface 契约要求 role，故传入 none。
    A11ySurface {
        target: control
        role: Enums.accessibility.role_none
        ignored: true
    }

}
