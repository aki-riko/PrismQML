// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../containers"
import "../../icons"

// HintIcon - Icon with built-in hover tooltip 自带 hover ToolTip 的图标
//
// 场景: 配置面板里"标签后面跟一个 ⓘ 图标,鼠标 hover 显说明"
// 解决: Icon 不继承 Widget,没自带 toolTipText 行为;
//       Button 占按钮高度 + 有 hover 背景, 不适合纯展示。
//       HintIcon 继承 Widget 拿到 toolTipText, 内嵌 Icon 显图标,
//       不可点击, 大小跟图标本身一致。
//
// Usage:
//   HintIcon { toolTipText: "说明文字" }                   // 默认 Info 图标
//   HintIcon { icon: "Question"; toolTipText: "..." }       // 换图标
//   HintIcon { iconSize: 16; toolTipText: "..." }            // 改大小
Widget {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string icon: "Info"                         // 图标名,等同 Icon.icon
    property int iconSize: 14                             // 图标渲染大小
    property color color: Enums.textColor.tertiary // 图标颜色,默认次要文本色

    // ==================== Size 尺寸 ====================
    // contentWidth/Height = 图标尺寸,不占额外空间。Widget 基类会让最终
    // implicitWidth/Height = contentWidth/Height + padding (默认 0)。
    contentWidth: iconSize
    contentHeight: iconSize

    // Show explanatory hints faster than buttons 说明性提示比按钮更快显示
    toolTipShowDelay: 100
    // Open beside the icon so the label remains unobstructed 默认在图标右侧展开，避免遮挡标签
    toolTipPosition: Enums.position.right

    // ==================== Content 内容 ====================
    Icon {
        anchors.centerIn: parent
        icon: control.icon
        iconSize: control.iconSize
        color: control.color
        themeAware: false   // 颜色由外层 control.color 主导,不再跟主题二次变换
    }
}
