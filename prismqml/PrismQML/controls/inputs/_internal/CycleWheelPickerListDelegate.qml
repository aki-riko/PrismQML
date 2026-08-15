// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../data/Label"

// CycleWheelPickerListDelegate - Linear wheel item 线性滚轮项目委托
// Keeps ListView visual binding outside CycleWheelPicker orchestration.
// 将 ListView 视觉绑定移出 CycleWheelPicker 编排入口。
Item {
    id: delegate

    // ==================== Required Props 必需属性 ====================
    required property var wheelControl
    required property var modelData
    required property int index

    // ==================== Internal Props 内部属性 ====================
    property bool isCurrent: index === ListView.view.currentIndex
    property real distanceFromCenter: {
        var center = wheelControl.height / 2
        var itemCenter = y - ListView.view.contentY + height / 2
        return wheelControl._distanceFromCenter(center, itemCenter)
    }

    // ==================== Size 尺寸 ====================
    width: ListView.view.width
    height: wheelControl._safeItemHeight

    // ==================== Content 内容 ====================
    // Item stays transparent so the popup highlight remains visible.
    // 保持 Item 透明，避免遮挡弹窗选中高亮。
    Label {
        anchors.centerIn: parent
        type: Enums.label.type_body
        text: String(modelData)
        font.pixelSize: delegate.isCurrent
            ? Enums.typography.subtitle : Enums.typography.body
        font.weight: delegate.isCurrent ? Font.Medium : Font.Normal
        horizontalAlignment: delegate.wheelControl.textAlignment
        verticalAlignment: Text.AlignVCenter
        color: delegate.isCurrent
            ? Enums.textColor.primary : Enums.stateColor.textMedium
        opacity: delegate.isCurrent
            ? 1 : Math.max(0.3, 1 - delegate.distanceFromCenter * 0.6)
    }

    MouseArea {
        anchors.fill: parent
        onClicked: ListView.view.currentIndex = index
    }
}
