// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "_internal" as LayoutInternal

// Viewbox - Uniform content scaling 内容等比缩放适配
// Fluent Viewbox parity 对齐 Fluent Viewbox
// Qt image fill modes map onto Fluent Stretch 1:1 Qt 图像填充模式与 Fluent Stretch 一一对应:
//   Image.Pad = None, Image.Stretch = Fill,
//   Image.PreserveAspectFit = Uniform, Image.PreserveAspectCrop = UniformToFill
// Content must report a natural size (explicit width / height or implicit size);
// anchored-fill content creates a sizing loop. 内容必须报告自然尺寸（显式宽高或隐式尺寸），
// 使用 anchors.fill 的内容会形成尺寸循环。
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    // Stretch mode 拉伸模式
    property int stretch: Image.PreserveAspectFit
    // Clip the scaled content 裁剪缩放后的内容
    property bool clipContent: false

    // Content 内容
    default property alias content: contentHolder.content

    // ==================== Readonly State 只读状态 ====================
    readonly property real naturalWidth: viewboxContent.naturalWidth
    readonly property real naturalHeight: viewboxContent.naturalHeight
    readonly property real scaleX: viewboxContent.scaleX
    readonly property real scaleY: viewboxContent.scaleY

    // ==================== Size 尺寸 ====================
    implicitWidth: naturalWidth
    implicitHeight: naturalHeight

    // ==================== Content 内容 ====================
    // Content holder keeps the entry free of the visual tree 内容持有者让入口不承载视觉树
    QtObject {
        id: contentHolder
        default property list<QtObject> content
    }

    LayoutInternal.ViewboxContent {
        id: viewboxContent
        objectName: "viewboxSurface"
        anchors.fill: parent
        host: control
        content: contentHolder.content
    }
}
