// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../buttons/Button"

// ColorPickerTrigger - Dropdown trigger button 下拉触发按钮
// Uses ButtonCore with feature_dropdown 使用ButtonCore的dropdown功能
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property color selectedColor: Enums.colorPickerDefaults.defaultColor
    property bool isOpen: false
    property var menu: null
    
    // ==================== Signals 信号 ====================
    signal clicked()
    signal menuAboutToOpen()
    
    // ==================== Size 尺寸 ====================
    implicitWidth: btn.implicitWidth
    implicitHeight: btn.implicitHeight
    
    // ==================== Content 内容 ====================
    ButtonCore {
        id: btn
        anchors.fill: parent
        feature: Enums.button.feature_dropdown
        contentAlignment: Enums.button.align_center
        enabled: control.enabled
        menu: control.menu
        dropdownOpen: control.isOpen  // Sync arrow animation with popup state 同步箭头动画与弹窗状态
        onClicked: control.clicked()
        onMenuAboutToOpen: control.menuAboutToOpen()
        
        // Custom content: color preview 自定义内容：颜色预览
        // Note: customContentContainer is Item without size, need anchors 注意：customContentContainer是无尺寸Item，需要锚点
        Rectangle {
            anchors.centerIn: parent
            width: Enums.spacing.xxl
            height: Enums.spacing.xxl
            radius: Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.small
            color: control.selectedColor
            border.width: Enums.border.thin
            border.color: Enums.stateColor.inputBorderStrong
        }
    }
}
