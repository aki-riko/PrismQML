// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// FocusVisual - Fluent keyboard focus ring 键盘焦点视觉环
// Draw a Fluent double ring so keyboard users can always see where focus sits.
// It resolves its own visibility from the item it outlines, so adopting it is one
// declaration and never a hand-written focus binding.
// 自行从被描边的项目解析可见性，因此采用它只需一行声明，不必手写焦点绑定。
//
// The ring is created lazily: while the item has no keyboard focus the visual
// tree holds a single inactive Loader, so default appearances and object counts
// stay unchanged.
// 焦点环惰性创建：项目没有键盘焦点时视觉树里只有一个未激活的 Loader，
// 因此默认外观与对象计数保持不变。
//
// Usage 使用方式:
//   FocusVisual { anchors.fill: parent; radius: Enums.radius.small }
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    // Corner radius of the ring; follow the surface it outlines. 环的圆角, 跟随被描边表面。
    property real radius: Enums.radius.small
    // Gap between the ring and the surface edge. 环与表面边缘之间的间隔。
    property int inset: 1
    // Inner stroke colour; defaults to the foreground so it reads on both themes.
    // 内圈颜色; 默认取前景色, 因此在两种主题下都可读。
    property color innerColor: Enums.foregroundColor
    // Outer stroke colour; defaults to the surface so the ring separates from it.
    // 外圈颜色; 默认取表面色, 使环与表面分离。
    property color outerColor: Enums.cardColor
    // Item whose keyboard focus the ring tracks. Defaults to the parent.
    // 环所跟踪键盘焦点的项目，默认为父级。
    property Item focusSource: parent
    // Mouse focus must not raise the ring: Fluent only reveals keyboard focus.
    // 鼠标焦点不显示焦点环：Fluent 只揭示键盘焦点。
    property bool keyboardOnly: true
    // Ring thickness reuses the existing border tokens so the ring matches every
    // other stroke in the design system instead of inventing parallel metrics.
    // 环的粗细复用既有描边令牌，使焦点环与设计系统其余描边一致，而非另造一套度量。
    readonly property real innerWidth: Enums.border.normal
    readonly property real outerWidth: Enums.border.thin
    // Total width the ring occupies inside its bounds. 环在其边界内占用的总宽度。
    readonly property real ringExtent: innerWidth + outerWidth

    // ==================== Readonly State 只读状态 ====================
    readonly property bool keyboardFocused: focusSource !== null
        && focusSource !== undefined
        && focusSource.activeFocus === true
        && (!keyboardOnly || focusSource.focusReason !== Qt.MouseFocusReason)
    // The loaded ring, or null while the item has no keyboard focus. Consumers
    // and tests read this instead of walking the visual tree.
    // 已加载的焦点环；项目无键盘焦点时为 null。消费者与测试读它，而不是遍历视觉树。
    readonly property Item ringItem: ringLoader.item

    // ==================== Size 尺寸 ====================
    // Never take part in layout sizing; the consumer anchors or binds this.
    // 不参与布局尺寸计算, 由消费者锚定或绑定。
    width: parent ? parent.width : 0
    height: parent ? parent.height : 0
    // Pointer events belong to the control underneath. 指针事件属于下层控件。
    enabled: false

    // ==================== Content 内容 ====================
    Loader {
        id: ringLoader
        anchors.fill: parent
        active: control.keyboardFocused
        sourceComponent: ringComponent
    }

    Component {
        id: ringComponent

        Item {
            // Outer stroke sits flush with the surface edge. 外圈贴合表面边缘。
            Rectangle {
                anchors.fill: parent
                radius: Math.max(0, control.radius)
                color: Enums.transparent
                border.color: control.outerColor
                border.width: control.outerWidth
                antialiasing: true
            }

            // Inner stroke is inset so the two strokes never overlap.
            // 内圈内缩, 两圈不重叠。
            Rectangle {
                anchors.fill: parent
                anchors.margins: control.inset + control.outerWidth
                radius: Math.max(0, control.radius - control.inset - control.outerWidth)
                color: Enums.transparent
                border.color: control.innerColor
                border.width: control.innerWidth
                antialiasing: true
            }
        }
    }
}
