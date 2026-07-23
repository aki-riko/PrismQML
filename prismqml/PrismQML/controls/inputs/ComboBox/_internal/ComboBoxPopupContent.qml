// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../../.."
import "../../../containers"
import "../../../containers/ScrollBar"
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// ComboBoxPopupContent - Default popup content for ComboBox ComboBox默认弹出内容
// Extracted from ComboBoxCore for modularity 从ComboBoxCore提取以模块化
Item {
    id: popupContainer

    // ==================== Public Props 公开属性 ====================
    property var control: null  // Parent ComboBox control 父ComboBox控件

    // ==================== Readonly State 只读状态 ====================
    // Check if scrollbar needed 检查是否需要滚动条
    readonly property int _maxItems: (control && control.maxVisibleItems > 0)
        ? control.maxVisibleItems
        : Enums.comboBoxMetrics.popupDefaultMaxItems
    readonly property var _safeControlModel: {
        var value = control && control._safeModel !== undefined
                    ? control._safeModel : (control ? control.model : [])
        return value && typeof value.length === "number" ? value : []
    }
    readonly property bool needsScroll: _safeControlModel.length > _maxItems

    // ==================== Size 尺寸 ====================
    width: parent ? parent.width : (control ? control.width : 100)
    height: parent ? parent.height : Enums.comboBoxMetrics.popupDefaultHeight

    // ==================== Content 内容 ====================
    ListView {
        id: popupListView
        property var parentControl: popupContainer.control

        anchors.fill: parent
        anchors.rightMargin: popupContainer.needsScroll ? Enums.comboBoxMetrics.scrollBarRightMargin : 0
        model: popupContainer._safeControlModel
        delegate: popupContainer.control ? popupContainer.control.popupDelegate : null
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        interactive: false  // Disable native scroll, use smooth scroll 禁用原生滚动，使用平滑滚动

        // Smooth scroll 平滑滚动
        PopupSmoothScroll { flickable: popupListView; enabled: popupContainer.needsScroll }
    }

    // Scrollbar 滚动条
    Loader {
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.margins: Enums.spacing.xxs
        width: Enums.comboBoxMetrics.scrollBarWidth
        active: popupContainer.needsScroll
        sourceComponent: ScrollBarEntry {
            flickable: popupListView
            width: Enums.comboBoxMetrics.scrollBarWidth
        }
    }
}
