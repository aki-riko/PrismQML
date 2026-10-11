// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// FocusVisual - Fluent focus ring Fluent 焦点视觉环
// Draw one theme-accent outline around an item that owns active focus.
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
    // Focus outline follows the active theme accent. 焦点轮廓跟随当前主题强调色。
    property color ringColor: Enums.accentColor
    // Item whose active focus the ring tracks. Defaults to the parent.
    // 环所跟踪 activeFocus 的项目，默认为父级。
    property Item focusSource: parent
    // Reuse the shared border width token. 复用全局描边粗细令牌。
    readonly property real ringWidth: Enums.border.normal

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
            Rectangle {
                anchors.fill: parent
                radius: Math.max(0, control.radius)
                color: Enums.transparent
                border.color: control.ringColor
                border.width: control.ringWidth
                antialiasing: true
            }
        }
    }
}
