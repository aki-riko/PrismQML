// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// StackedDirectPages - Direct child page container 直接子页面容器
// Owns the direct-child page parent and its first-frame geometry initialization.
// 负责直接子页面父级及首帧几何初始化，保持入口只做状态编排。
Item {
    id: stackLayout

    // ==================== Required Props 必需属性 ====================
    required property Item host

    // ==================== Size 尺寸 ====================
    objectName: "stackLayout"
    anchors.fill: parent
    visible: !host._useSourceMode

    // ==================== Content 内容 ====================
    Component.onCompleted: {
        host.profileTime("stackLayout Component.onCompleted start children=" + children.length)
        for (let i = 0; i < children.length; i++) {
            let child = children[i]
            child.width = Qt.binding(function() { return stackLayout.width })
            child.height = Qt.binding(function() { return stackLayout.height })
            child.x = 0
            child.y = 0
            child.visible = (i === host._displayIndex)
            child.opacity = (i === host._displayIndex) ? 1 : 0
            child.scale = 1
            child.transformOrigin = Item.Center
        }
        host.profileTime("stackLayout Component.onCompleted done")
    }
}
