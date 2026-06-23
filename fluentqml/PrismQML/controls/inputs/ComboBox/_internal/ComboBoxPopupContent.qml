// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import "../../../.."
import "../../../containers"
import "../../../containers/ScrollBar"
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// ComboBoxPopupContent - Default popup content for ComboBox ComboBox默认弹出内容
// Extracted from ComboBoxCore for modularity 从ComboBoxCore提取以模块化
Item {
    id: popupContainer
    
    // ==================== Props 属性 ====================
    property var control: null  // Parent ComboBox control 父ComboBox控件
    
    width: parent ? parent.width : (control ? control.width : 100)
    height: parent ? parent.height : Enums.comboBoxMetrics.popupDefaultHeight
    
    // Check if scrollbar needed 检查是否需要滚动条
    readonly property int _maxItems: (control && control.maxVisibleItems > 0)
        ? control.maxVisibleItems 
        : Enums.comboBoxMetrics.popupDefaultMaxItems
    readonly property bool needsScroll: control ? control.model.length > _maxItems : false
    
    ListView {
        id: popupListView
        anchors.fill: parent
        anchors.rightMargin: popupContainer.needsScroll ? Enums.comboBoxMetrics.scrollBarRightMargin : 0
        model: popupContainer.control ? popupContainer.control.model : []
        delegate: popupContainer.control ? popupContainer.control.popupDelegate : null
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        interactive: false  // Disable native scroll, use smooth scroll 禁用原生滚动，使用平滑滚动
        
        property var parentControl: popupContainer.control
        
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
