// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// FocusVisual - Fluent focus ring Fluent 焦点视觉环
// Draw a Fluent double ring around an item that owns active focus.
// It resolves its own visibility from the item it outlines, so adopting it is one
// declaration and never a hand-written focus binding.
// 自行从被描边的项目解析可见性，因此采用它只需一行声明，不必手写焦点绑定。
//
// The ring is created lazily: while the item has no active focus the visual
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
    // Inner stroke follows the active theme accent like other focus indicators.
    // 内圈跟随当前主题强调色，与其他焦点提示保持一致。
    property color innerColor: Enums.accentColor
    // Outer stroke uses the theme foreground to keep a clear contrast outline.
    // 外圈使用主题前景色，维持清晰的高对比轮廓。
    property color outerColor: Enums.foregroundColor
    // Item whose active focus the ring tracks. Defaults to the parent.
    // 环所跟踪 activeFocus 的项目，默认为父级。
    property Item focusSource: parent
    // Ring thickness reuses the existing border tokens so the ring matches every
    // other stroke in the design system instead of inventing parallel metrics.
    // 环的粗细复用既有描边令牌，使焦点环与设计系统其余描边一致，而非另造一套度量。
    readonly property real innerWidth: Enums.border.normal
    readonly property real outerWidth: Enums.border.thin
    // Total width the ring occupies inside its bounds. 环在其边界内占用的总宽度。
    readonly property real ringExtent: innerWidth + outerWidth

    // ==================== Readonly State 只读状态 ====================
    // The ring follows the focus state owned by the source item. Input modality
    // is intentionally left to the focus owner because QQuickItem does not
    // expose a reliable focus-reason property.
    // 焦点环跟随宿主项目已有的焦点状态；输入方式交由宿主决定，因为 QQuickItem
    // 没有可靠的焦点原因属性可供组件读取。
    readonly property bool focused: focusSource !== null
        && focusSource !== undefined
        && focusSource.activeFocus === true
    // The loaded ring, or null while the item has no active focus. Consumers
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
        active: control.focused
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
