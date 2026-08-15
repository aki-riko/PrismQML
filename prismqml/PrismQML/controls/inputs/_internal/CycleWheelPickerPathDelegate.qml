// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../data/Label"

// CycleWheelPickerPathDelegate - Cyclic wheel item 循环滚轮项目委托
// Keeps PathView visual binding outside CycleWheelPicker orchestration.
// 将 PathView 视觉绑定移出 CycleWheelPicker 编排入口。
Item {
    id: delegate

    // ==================== Required Props 必需属性 ====================
    required property var wheelControl
    required property var modelData

    // ==================== Internal Props 内部属性 ====================
    property real distanceFromCenter: {
        var center = wheelControl.height / 2
        var itemCenter = y + height / 2
        return wheelControl._distanceFromCenter(center, itemCenter)
    }

    // ==================== Size 尺寸 ====================
    width: wheelControl.width
    height: wheelControl._safeItemHeight
    x: -width / 2

    // ==================== Content 内容 ====================
    // Item stays transparent so the popup highlight remains visible.
    // 保持 Item 透明，避免遮挡弹窗选中高亮。
    Label {
        anchors.centerIn: parent
        type: Enums.label.type_body
        text: String(modelData)
        font.pixelSize: PathView.isCurrentItem
            ? Enums.typography.subtitle : Enums.typography.body
        font.weight: PathView.isCurrentItem ? Font.Medium : Font.Normal
        horizontalAlignment: delegate.wheelControl.textAlignment
        verticalAlignment: Text.AlignVCenter
        color: PathView.isCurrentItem
            ? Enums.textColor.primary : Enums.stateColor.textMedium
        opacity: PathView.isCurrentItem
            ? 1 : Math.max(0.3, 1 - delegate.distanceFromCenter * 0.6)
    }
}
