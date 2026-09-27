// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../icons"
import "../../../data"

// CascadeItemDelegate - One row inside a cascade ComboBox popup 级联下拉框单行
// Owner nodes with children open a sibling panel instead of selecting, so the row
// carries a trailing arrow and reports a submenu request. Visual language matches
// MenuDelegate so a cascade panel never reads as a different surface.
// 含子节点的行打开同级面板而不是选中，因此行尾带箭头并上报子菜单请求。
// 视觉沿用 MenuDelegate 语言，使级联面板不会看起来像另一种弹层。
Item {
    id: delegateRoot

    // ==================== Public Props 公开属性 ====================
    property string text: ""
    property string icon: ""                 // Icon name, empty hides it 图标名，空则不显示
    property bool selected: false            // Mirror of the owning panel selection 所属面板选中态
    property int itemIndex: -1               // Row index inside the owning panel 所属面板行下标
    property bool hasChildren: false         // Owns a submenu 拥有子菜单
    property bool itemEnabled: true          // Disabled rows stay visible but inert 禁用行仍占位但不可交互
    readonly property bool hasSubmenu: delegateRoot.hasChildren

    // ==================== Internal Props 内部属性 ====================
    readonly property color _itemHoverColor: Enums.stateColor.menuItemHover
    readonly property color _itemPressedColor: Enums.stateColor.menuItemPressed
    readonly property color _itemTextColor: delegateRoot.itemEnabled
        ? Enums.textColor.primary : Enums.textColor.disabled

    // ==================== Readonly State 只读状态 ====================
    readonly property bool hovered: delegateMouseArea.containsMouse
    // Touch has no hover preview: on touch the hover treatment follows the press
    // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
    readonly property bool _touchActive: Touch.feedback(hovered, delegateMouseArea.pressed)

    // ==================== Signals 信号 ====================
    signal pressed()
    signal clicked()
    signal hoverChanged()                    // Row hover edge for the panel timer 面板定时器用悬停边沿
    signal submenuRequested()                // Arrow activation 箭头激活

    // ==================== Internal Methods 内部方法 ====================
    // Stabilize the nearest popup before the press/release hit test begins.
    // 在按下/释放命中测试开始前稳定最近的弹层。
    function _stabilizePopupAncestor() {
        var ancestor = delegateRoot.parent
        while (ancestor) {
            var popupHost = ancestor._interactionHost
            if (popupHost && popupHost._isPopupWindowCore === true
                    && typeof popupHost.stabilizeInteraction === "function") {
                popupHost.stabilizeInteraction()
                return
            }
            ancestor = ancestor.parent
        }
    }

    // ==================== Size 尺寸 ====================
    width: parent ? parent.width : Enums.comboBoxMetrics.defaultWidth
    height: Enums.comboBoxMetrics.itemHeight

    // ==================== Content 内容 ====================
    // Item background 项目背景
    Rectangle {
        id: itemBg
        anchors.fill: parent
        anchors.leftMargin: Enums.spacing.xs
        anchors.rightMargin: Enums.spacing.xs
        anchors.topMargin: Enums.spacing.xxs
        anchors.bottomMargin: Enums.spacing.xxs
        radius: Enums.radius.small
        color: {
            if (!delegateRoot.itemEnabled) return Enums.transparent
            if (delegateMouseArea.pressed) return delegateRoot._itemPressedColor
            if (delegateRoot.selected) return delegateRoot._itemPressedColor
            if (delegateRoot._touchActive) return delegateRoot._itemHoverColor
            return Enums.transparent
        }

        // Selection indicator 选中指示器
        Rectangle {
            anchors.left: parent.left
            anchors.leftMargin: Enums.spacing.xxs
            anchors.verticalCenter: parent.verticalCenter
            width: Enums.controlSize.topNavIndicatorHeight
            height: Enums.spacing.xl
            radius: Enums.radius.micro
            color: Enums.accentColor
            visible: delegateRoot.selected
        }

        // Item icon 项目图标
        Icon {
            id: itemIcon
            anchors.left: parent.left
            anchors.leftMargin: Enums.spacing.l
            anchors.verticalCenter: parent.verticalCenter
            iconSize: Enums.iconSize.m
            icon: delegateRoot.icon
            color: delegateRoot._itemTextColor
            visible: delegateRoot.icon !== ""
        }

        // Item text 项目文本
        Label {
            anchors.left: parent.left
            anchors.leftMargin: delegateRoot.icon !== ""
                ? (Enums.spacing.l + Enums.iconSize.m + Enums.spacing.m)
                : Enums.spacing.l
            anchors.right: submenuArrow.left
            anchors.rightMargin: Enums.spacing.s
            anchors.verticalCenter: parent.verticalCenter
            type: Enums.label.type_body
            text: delegateRoot.text
            color: delegateRoot._itemTextColor
            wrapMode: Text.NoWrap  // Override body default WordWrap 覆盖body默认的自动换行
            maximumLineCount: 1    // Single line only 仅单行
            elide: Text.ElideRight
        }

        // Submenu arrow 子菜单箭头
        Icon {
            id: submenuArrow
            anchors.right: parent.right
            anchors.rightMargin: Enums.spacing.l
            anchors.verticalCenter: parent.verticalCenter
            iconSize: Enums.iconSize.xs
            icon: Enums.icon.chevron_right
            color: delegateRoot.itemEnabled
                ? Enums.textColor.secondary : Enums.textColor.disabled
            visible: delegateRoot.hasChildren
        }
    }

    // Interaction 交互
    MouseArea {
        id: delegateMouseArea
        anchors.fill: parent
        hoverEnabled: true
        enabled: delegateRoot.itemEnabled
        cursorShape: Qt.ArrowCursor
        onPressed: {
            delegateRoot._stabilizePopupAncestor()
            delegateRoot.pressed()
        }
        onContainsMouseChanged: delegateRoot.hoverChanged()
        onClicked: {
            if (delegateRoot.hasChildren) {
                delegateRoot.submenuRequested()
                return
            }
            delegateRoot.clicked()
        }
    }
}
