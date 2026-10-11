// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import "_internal"
import "_internal/AppBarDisplayStateResolver.js" as AppBarDisplayStateResolver

// AppBarButton - WinUI AppBar command button 应用栏命令按钮
// The shell reuses ButtonCore for its surface, hover/press animation, toggle
// semantics and tooltip; this file owns the AppBar label layout, the
// Sticky/Compact/Expanded state machine and the dropdown command menu.
// 外壳复用 ButtonCore 的表面、悬浮/按压动画、切换语义与提示；本文件负责应用栏
// 标签排布、固定/紧凑/展开状态机与下拉命令菜单。
Button {
    id: control

    // ==================== Public Props 公开属性 ====================
    // Label placement 标签位置: style_text_under (default) / style_text_beside / style_icon_only
    property int labelPosition: Enums.commandBar.style_text_under
    // Display state 显示状态: appBar_inherit (default) / appBar_sticky / appBar_compact / appBar_expanded
    property int displayState: Enums.commandBar.appBar_inherit
    property bool checkable: false  // Toggle semantics 切换语义
    property bool menuOpen: false  // Menu open state, written by the owned popup 菜单开合状态, 由自身弹层写入

    // ==================== Internal Props 内部属性 ====================
    // A button forwards its host's state instead of publishing one. 按钮只转发宿主状态, 自身不作为宿主。
    readonly property bool _isAppBarDisplayStateHost: false
    readonly property int _padding: Enums.spacing.xs
    readonly property int _compactHeight: Enums.controlSize.commandBarButtonSize
    readonly property int _largeHeight: Enums.controlSize.commandBarButtonSize * 2
    readonly property bool _stacked: labelPosition === Enums.commandBar.style_text_under

    // ==================== Readonly State 只读状态 ====================
    readonly property int resolvedDisplayState: displayState === Enums.commandBar.appBar_inherit
        ? AppBarDisplayStateResolver.resolve(control, Enums) : displayState
    readonly property bool appBarSticky: resolvedDisplayState === Enums.commandBar.appBar_sticky
    readonly property bool appBarCompact: resolvedDisplayState === Enums.commandBar.appBar_compact
    readonly property bool appBarExpanded: resolvedDisplayState === Enums.commandBar.appBar_expanded
    readonly property string appBarStateName: appBarSticky ? "sticky"
        : (appBarCompact ? "compact" : "expanded")
    // Sticky keeps labels visible even when the host bar collapses. 固定态在宿主折叠时仍保留标签。
    readonly property bool labelVisible: labelPosition !== Enums.commandBar.style_icon_only
        && !appBarCompact
    readonly property bool _hasLabel: labelVisible && text !== ""
    readonly property bool menuEnabled: _safeMenuItems.length > 0
    readonly property int _targetHeight: _stacked && labelVisible ? _largeHeight : _compactHeight

    // ==================== Public Methods 公开方法 ====================
    function setDisplayState(state) { displayState = state }

    // Walk the WinUI AppBar display-state cycle 按 WinUI 应用栏显示状态循环切换
    function cycleDisplayState() {
        var next = appBarSticky ? Enums.commandBar.appBar_compact
            : (appBarCompact ? Enums.commandBar.appBar_expanded
                : Enums.commandBar.appBar_sticky)
        displayState = next
        return next
    }

    function openMenu() { if (menuEnabled) menuPopup.openAtControl(control) }

    function closeMenu() { menuPopup.close() }

    // Menu entries accept strings and {text, icon, enabled, separator} objects.
    // 菜单项接受字符串与 {text, icon, enabled, separator} 对象。
    function menuText(item) {
        if (item === null || item === undefined) return ""
        return typeof item === "object" ? (item.text || "") : String(item)
    }

    function menuIcon(item) {
        if (item === null || item === undefined || typeof item !== "object") return ""
        return item.icon || ""
    }

    // ==================== Internal Methods 内部方法 ====================
    // Keyboard activation mirrors the pointer path: toggle first, then the same
    // clicked() handler opens the command menu. 键盘激活与指针路径一致: 先切换,
    // 再由同一个 clicked() 处理器打开命令菜单。
    function _activate() {
        if (!enabled) return
        if (checkable) toggle()
        clicked()
    }

    function _handleClick() {
        if (menuEnabled && !checkable) openMenu()
    }

    // ==================== Size 尺寸 ====================
    contentWidth: Math.max(
        labelVisible && _stacked ? Enums.controlSize.buttonMinWidth : _compactHeight,
        contentSlot.implicitWidth + _padding * 2)
    contentHeight: _targetHeight
    iconSize: _stacked ? Enums.iconSize.xl : Enums.iconSize.m
    feature: checkable ? Enums.button.feature_toggle : Enums.button.feature_none
    hasCustomContent: true
    style: Enums.button.style_transparent
    activeFocusOnTab: true
    // Icon-only buttons keep the label reachable through the shared tooltip.
    // 仅图标按钮通过共享提示保留标签可读性。
    toolTipText: _hasLabel ? "" : text
    // This handler owns onClicked instead of ButtonCore's hyperlink navigation:
    // an AppBar command opens its own menu, it is not a hyperlink surface.
    // 本处理器取代 ButtonCore 的超链接导航: 应用栏命令打开自身菜单, 不是超链接面。
    onClicked: control._handleClick()
    Keys.onReturnPressed: control._activate()
    Keys.onEnterPressed: control._activate()
    Keys.onSpacePressed: control._activate()

    // ==================== Content 内容 ====================
    Item {
        id: contentSlot

        anchors.centerIn: parent
        implicitWidth: control._stacked ? stackedContent.implicitWidth
            : inlineContent.implicitWidth
        implicitHeight: control._stacked ? stackedContent.implicitHeight
            : inlineContent.implicitHeight

        // Icon above label 图标在上, 标签在下
        Column {
            id: stackedContent

            spacing: Enums.spacing.micro
            visible: control._stacked

            Icon {
                anchors.horizontalCenter: parent.horizontalCenter
                iconSize: control.iconSize
                color: control._styleTextColor
                icon: control.icon
                visible: control.icon !== ""
            }

            Label {
                anchors.horizontalCenter: parent.horizontalCenter
                type: Enums.label.type_caption
                text: control.text
                customTextColor: control._styleTextColor
                visible: control._hasLabel
            }
        }

        // Icon beside label 图标在侧, 标签随行
        Row {
            id: inlineContent

            spacing: Enums.spacing.xs
            visible: !control._stacked

            Icon {
                anchors.verticalCenter: parent.verticalCenter
                iconSize: control.iconSize
                color: control._styleTextColor
                icon: control.icon
                visible: control.icon !== ""
            }

            Label {
                anchors.verticalCenter: parent.verticalCenter
                type: Enums.label.type_body_small
                text: control.text
                customTextColor: control._styleTextColor
                visible: control._hasLabel
            }

            Icon {
                id: menuIndicator

                anchors.verticalCenter: parent.verticalCenter
                iconSize: Enums.iconSize.xs
                color: control._styleTextColor
                icon: Enums.icon.chevron_down
                visible: control.menuEnabled && control.showDropdownIndicator
            }
        }
    }

    // Command menu: PopupWindowCore-based native top-level window 命令菜单: 基于 PopupWindowCore 的原生顶层窗口
    ContextMenu {
        id: menuPopup

        objectName: "appBarButtonMenu"
        autoBindRightClick: false
        onIsOpenChanged: control.menuOpen = isOpen

        Repeater {
            model: control._safeMenuItems

            Action {
                objectName: "appBarButtonMenuAction_" + index
                text: control.menuText(modelData)
                icon: control.menuIcon(modelData)
                enabled: !modelData || modelData.enabled !== false
                visible: !modelData || !modelData.separator
                onTriggered: {
                    control.menuItemClicked(index, control.menuText(modelData))
                    control.closeMenu()
                }
            }
        }
    }
}
