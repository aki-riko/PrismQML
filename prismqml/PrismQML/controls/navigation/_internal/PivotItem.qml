// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../buttons"

// PivotItem - Pivot delegate 透视导航项委托
// Content-sized cell: horizontal packs the cells in a row, vertical stacks them.
// 按内容定宽的单元: 横向并排, 纵向堆叠。
Item {
    id: pivotItem

    // ==================== Required Props 必需属性 ====================
    required property var host
    required property int index
    required property var modelData

    // ==================== Internal Props 内部属性 ====================
    property bool selected: index === host.currentIndex
    property string itemText: typeof modelData === "string" ? modelData : (modelData && modelData.text !== undefined ? modelData.text : "")
    property string itemIcon: modelData && modelData.icon !== undefined ? modelData.icon : ""
    property string key: modelData && modelData.key !== undefined ? modelData.key : (itemText !== "" ? itemText : itemIcon)
    property bool hasIcon: itemIcon !== ""
    property bool hasText: itemText !== ""

    // ==================== Size 尺寸 ====================
    width: pivotBtn.implicitWidth
    // Vertical cells take a fixed row height so the control's implicit height
    // never depends on the control's own height.
    // 纵向单元取固定行高, 使控件隐式高度不依赖控件自身高度。
    height: pivotItem.host.vertical
        ? Enums.controlSize.inputHeight
        : pivotItem.host.height

    // ==================== Content 内容 ====================
    Button {
        id: pivotBtn
        anchors.fill: parent
        style: Enums.button.style_transparent
        flat: true
        text: pivotItem.itemText
        icon: pivotItem.itemIcon
        iconSize: pivotItem.host.iconSize

        onClicked: {
            if (index !== pivotItem.host.currentIndex) {
                pivotItem.host.setCurrentIndex(index)
                pivotItem.host.itemClicked(index, true)
            }
        }
    }
}
