// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../menus"
import "../../utils"
import "../../icons"
import "../../containers/ScrollBar"
import "../../containers/Separator"

// ButtonDropdown - Dropdown menu and split button features 下拉菜单功能
// Internal module for Button Button内部模块
Item {
    id: dropdownFeature
    
    // ==================== Required Props 必需属性 ====================
    required property bool isToolButton
    required property int feature
    required property var menuItems
    required property bool controlEnabled
    required property bool loading
    required property real parentRadius
    required property string fontFamily
    required property int fontSize
    required property color textColor  // Parent button text color 父按钮文字颜色
    
    // ==================== Public Props 公开属性 ====================
    // Expose menu open state for arrow animation 暴露菜单打开状态供箭头动画使用
    readonly property bool isMenuOpen: dropDownMenu.isOpen
    // Expose hover states for parent button color calculation 暴露悬浮状态供父按钮颜色计算
    readonly property bool mainHovered: splitMainMouse.containsMouse
    readonly property bool mainPressed: splitMainMouse.pressed
    readonly property bool dropHovered: splitDropMouse.containsMouse
    readonly property bool dropPressed: splitDropMouse.pressed
    
    // ==================== Signals 信号 ====================
    signal menuItemClicked(int index, string text)
    signal mainButtonClicked()
    
    // ==================== Style Helper 样式辅助 ====================
    property int parentStyle: 0
    
    // Check if style uses accent foreground (white text/icon) 检查是否使用强调前景色（白色文字/图标）
    readonly property bool _useAccentForeground: parentStyle === Enums.button.style_primary ||
                                                  parentStyle === Enums.button.style_filled ||
                                                  parentStyle === Enums.button.style_gradient
    
    // Split button hover/pressed colors based on parent style Split按钮悬浮/按下颜色
    // For accent styles (primary/filled/gradient): use semi-transparent white 强调样式用半透明白
    // For other styles: use transparent button colors 其他样式用透明按钮颜色
    readonly property color _splitHoverColor: _useAccentForeground 
        ? (Enums.isDark ? "#4dffffff" : "#33ffffff")
        : Enums.stateColor.transparentHover
    readonly property color _splitPressedColor: _useAccentForeground 
        ? (Enums.isDark ? "#33ffffff" : "#26ffffff")
        : Enums.stateColor.transparentPressed
    readonly property color _splitTransparent: _useAccentForeground
        ? Enums.stateColor.whiteTransparent
        : Enums.stateColor.controlBgTransparent
    
    // Arrow color based on parent style 箭头颜色
    readonly property color _arrowColor: {
        if (!dropdownFeature.controlEnabled) return Enums.stateColor.indicatorActive
        if (_useAccentForeground) return Enums.accentForeground
        return Enums.textColor.secondary
    }
    
    // Separator line color 分隔线颜色
    readonly property color _separatorColor: _useAccentForeground
        ? Enums.stateColor.onAccentOverlay
        : Enums.stateColor.separator

    // ==================== Public Methods 公开方法 ====================
    // Calculate max content width from menu items (imperative, avoid binding loop)
    // 根据菜单项计算最大内容宽度（命令式调用，避免绑定循环）
    function _calcContentWidth() {
        var maxW = 0
        // Total horizontal padding: contentContainer margins(xs*2) + itemBg margins(xs*2) + text margins(l*2)
        // 总水平内边距：内容容器边距(xs*2) + 项背景边距(xs*2) + 文本边距(l*2)
        var itemPadding = Enums.spacing.l * 2 + Enums.spacing.xs * 4
        // Check if any item has icon 检查是否有图标项
        var hasIcon = false
        for (var i = 0; i < menuItems.length; i++) {
            var item = menuItems[i]
            if (typeof item === "object" && item.icon && item.icon !== "") {
                hasIcon = true
                break
            }
        }
        // Add icon space if any item has icon 有图标时加上图标占位空间
        var iconSpace = hasIcon ? (Enums.iconSize.m + Enums.spacing.m) : 0
        for (var j = 0; j < menuItems.length; j++) {
            var mi = menuItems[j]
            var text = typeof mi === "object" ? (mi.text || mi) : (mi || "")
            if (text === "-") continue  // Skip separator 跳过分隔线
            textMeasure.text = text
            maxW = Math.max(maxW, textMeasure.advanceWidth + itemPadding + iconSpace)
        }
        return Math.ceil(maxW)
    }

    function openMenu() {
        if (menuItems.length > 0) {
            var contentW = _calcContentWidth()
            // Split mode: use content width only; Dropdown mode: max(content, button width)
            // Split模式：仅用内容宽度；Dropdown模式：取内容宽度和按钮宽度的最大值
            if (feature === Enums.button.feature_split) {
                dropDownMenu.popupWidth = contentW
            } else {
                dropDownMenu.popupWidth = Math.max(contentW, parent.width)
            }
            dropDownMenu.openAtControl(parent)
        }
    }

    // ==================== Split Main Button Hover Area 主按钮悬浮区域 ====================
    Rectangle {
        id: splitMainArea
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.right: splitLine.left
        anchors.margins: Enums.spacing.micro
        radius: dropdownFeature.parentRadius > 0 ? dropdownFeature.parentRadius - 1 : Enums.radius.small - 1
        color: splitMainMouse.pressed ? dropdownFeature._splitPressedColor :
               (splitMainMouse.containsMouse ? dropdownFeature._splitHoverColor : dropdownFeature._splitTransparent)
        visible: feature === Enums.button.feature_split
        
        Behavior on color {
            ColorAnimation { duration: Enums.duration.fast }
        }
    }
    
    // ==================== Split Separator Line 分离线 ====================
    Separator {
        id: splitLine
        type: Enums.separator.vertical
        anchors.right: splitDropArea.left
        anchors.verticalCenter: parent.verticalCenter
        lineLength: parent.height - Enums.spacing.l
        lineColor: dropdownFeature._separatorColor
        visible: feature === Enums.button.feature_split
    }
    
    // ==================== Split Dropdown Area 下拉区域 ====================
    Rectangle {
        id: splitDropArea
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.margins: Enums.spacing.micro
        width: Enums.spacing.xxxl
        radius: dropdownFeature.parentRadius > 0 ? dropdownFeature.parentRadius - 1 : Enums.radius.small - 1
        color: splitDropMouse.pressed ? dropdownFeature._splitPressedColor :
               (splitDropMouse.containsMouse ? dropdownFeature._splitHoverColor : dropdownFeature._splitTransparent)
        visible: feature === Enums.button.feature_split
        
        Behavior on color {
            ColorAnimation { duration: Enums.duration.fast }
        }
        
        ChevronIcon {
            id: splitArrow
            animated: true
            isOpen: dropDownMenu.isOpen
            color: dropdownFeature._arrowColor
            anchors.centerIn: parent
        }
        
        MouseArea {
            id: splitDropMouse
            anchors.fill: parent
            hoverEnabled: true
            enabled: dropdownFeature.controlEnabled && !dropdownFeature.loading
            onClicked: dropdownFeature.openMenu()
        }
    }
    
    // ==================== Split Main Button Interaction 主按钮交互 ====================
    MouseArea {
        id: splitMainMouse
        anchors.fill: splitMainArea
        hoverEnabled: true
        enabled: dropdownFeature.controlEnabled && !dropdownFeature.loading && feature === Enums.button.feature_split
        visible: feature === Enums.button.feature_split
        onClicked: dropdownFeature.mainButtonClicked()
    }
    
    // ==================== Content Width Measurement 内容宽度测量 ====================
    // TextMetrics to measure menu item text width 用TextMetrics测量菜单项文本宽度
    TextMetrics {
        id: textMeasure
        font.family: fontFamily || Enums.fontFamily
        font.pixelSize: fontSize > 0 ? fontSize : Enums.typography.body
    }

    // ==================== Dropdown Menu 下拉菜单 ====================
    PopupWindowCore {
        id: dropDownMenu
        // Set reference width for center alignment 设置参考宽度用于居中对齐
        referenceControlWidth: parent.width
        
        // Calculate content height 计算内容高度
        readonly property int _contentHeight: {
            var h = Enums.comboBoxMetrics.popupPadding
            for (var i = 0; i < dropdownFeature.menuItems.length; i++) {
                var item = dropdownFeature.menuItems[i]
                var text = typeof item === "object" ? (item.text || item) : (item || "")
                h += (text === "-") ? Enums.controlSize.menuSeparatorHeight : Enums.comboBoxMetrics.itemHeight
            }
            return h
        }
        readonly property bool _needsScroll: _contentHeight > Enums.comboBoxMetrics.popupMaxHeight
        
        popupHeight: Math.min(_contentHeight, Enums.comboBoxMetrics.popupMaxHeight)
        closeOnClickOutside: true
        
        Flickable {
            id: menuFlickable
            anchors.fill: parent
            anchors.rightMargin: dropDownMenu._needsScroll ? Enums.comboBoxMetrics.scrollBarRightMargin : 0
            contentWidth: width
            contentHeight: menuColumn.height
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            interactive: false  // Disable native scroll, use smooth scroll 禁用原生滚动，使用平滑滚动
            
            // Smooth scroll 平滑滚动
            PopupSmoothScroll { flickable: menuFlickable; enabled: dropDownMenu._needsScroll }
            
            Column {
                id: menuColumn
                width: parent.width
                
                Repeater {
                    model: dropdownFeature.menuItems
                    
                    MenuDelegate {
                        width: menuColumn.width
                        text: typeof modelData === "object" ? (modelData.text || modelData) : (modelData || "")
                        icon: typeof modelData === "object" ? (modelData.icon || "") : ""
                        isSeparator: text === "-"
                        onClicked: {
                            dropdownFeature.menuItemClicked(index, text)
                            dropDownMenu.close()
                        }
                    }
                }
            }
        }
        
        // Scrollbar 滚动条
        Loader {
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.margins: Enums.spacing.xxs
            width: Enums.comboBoxMetrics.scrollBarWidth
            active: dropDownMenu._needsScroll
            sourceComponent: ScrollBarEntry {
                flickable: menuFlickable
                width: Enums.comboBoxMetrics.scrollBarWidth
            }
        }
    }
}
