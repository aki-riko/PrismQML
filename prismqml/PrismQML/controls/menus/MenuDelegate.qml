// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "../../SkinResolver.js" as SkinResolver
import "../icons"
import "../data"
import "../containers"

// MenuDelegate - Unified menu item delegate 统一菜单项委托
// Used by ComboBox, ButtonDropdown, Menu 用于ComboBox、下拉按钮、菜单
Item {
    id: delegateRoot
    
    // ==================== Public Props 公开属性 ====================
    property var skinContext: null
    property string text: ""
    property string icon: ""
    property bool selected: false
    property bool isSeparator: false
    property bool itemEnabled: true
    readonly property var effectiveSkinContext:
        skinContext || _nearestSkinContext || Enums
    readonly property var _skin: effectiveSkinContext
    readonly property int _itemRadius: _skin.radius.small
    readonly property color _itemHoverColor: _skin.stateColor.menuItemHover
    readonly property color _itemPressedColor: _skin.stateColor.menuItemPressed
    readonly property color _itemTextColor: delegateRoot.itemEnabled ? _skin.textColor.primary : _skin.textColor.disabled

    // ==================== Internal Props 内部属性 ====================
    readonly property var _nearestSkinContext: skinContext
        ? null : SkinResolver.nearestContext(parent)
    // Touch has no hover preview: on touch the hover treatment follows the press
    // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
    readonly property bool _touchActive: Touch.feedback(delegateMouseArea.containsMouse, delegateMouseArea.pressed)
    
    // ==================== Signals 信号 ====================
    signal clicked()
    signal pressed()

    // ==================== Size 尺寸 ====================
    width: parent ? parent.width : _skin.comboBoxMetrics.defaultWidth
    height: isSeparator ? _skin.controlSize.menuSeparatorHeight : _skin.comboBoxMetrics.itemHeight

    // ==================== Content 内容 ====================
    // Separator 分隔线
    Separator {
        skinContext: delegateRoot.effectiveSkinContext
        anchors.centerIn: parent
        width: parent.width - _skin.spacing.m * 2
        visible: delegateRoot.isSeparator
    }
    
    // Item background 项目背景
    Rectangle {
        id: itemBg
        anchors.fill: parent
        anchors.leftMargin: _skin.spacing.xs
        anchors.rightMargin: _skin.spacing.xs
        anchors.topMargin: _skin.spacing.xxs
        anchors.bottomMargin: _skin.spacing.xxs
        radius: delegateRoot._itemRadius
        visible: !delegateRoot.isSeparator
        
        color: {
            if (!delegateRoot.itemEnabled) return _skin.transparent
            if (delegateMouseArea.pressed) return delegateRoot._itemPressedColor
            if (delegateRoot.selected) return delegateRoot._itemPressedColor
            if (delegateRoot._touchActive) return delegateRoot._itemHoverColor
            return _skin.transparent
        }
        
        // Selection indicator 选中指示器
        Rectangle {
            anchors.left: parent.left
            anchors.leftMargin: _skin.spacing.xxs
            anchors.verticalCenter: parent.verticalCenter
            width: _skin.controlSize.topNavIndicatorHeight
            height: _skin.spacing.xl
            radius: _skin.radius.micro
            color: _skin.accentColor
            visible: delegateRoot.selected
        }
        
        // Item icon 项目图标
        Icon {
            id: itemIcon
            anchors.left: parent.left
            anchors.leftMargin: _skin.spacing.l
            anchors.verticalCenter: parent.verticalCenter
            iconSize: _skin.iconSize.m
            icon: delegateRoot.icon
            color: delegateRoot._itemTextColor
            visible: delegateRoot.icon !== ""
        }
        
        // Item text 项目文本
        Label {
            skinContext: delegateRoot.effectiveSkinContext
            anchors.left: parent.left
            // Shift text right when icon is present 有图标时文本右移
            anchors.leftMargin: delegateRoot.icon !== "" ? (_skin.spacing.l + _skin.iconSize.m + _skin.spacing.m) : _skin.spacing.l
            anchors.right: parent.right
            anchors.rightMargin: _skin.spacing.l
            anchors.verticalCenter: parent.verticalCenter
            type: _skin.label.type_body
            text: delegateRoot.text
            color: delegateRoot._itemTextColor
            wrapMode: Text.NoWrap  // Override body default WordWrap 覆盖body默认的自动换行
            maximumLineCount: 1    // Single line only 仅单行
            elide: Text.ElideRight
        }
    }
    
    // Interaction 交互
    MouseArea {
        id: delegateMouseArea
        anchors.fill: parent
        hoverEnabled: true
        enabled: !delegateRoot.isSeparator && delegateRoot.itemEnabled
        onPressed: delegateRoot.pressed()
        onClicked: delegateRoot.clicked()
    }

}
