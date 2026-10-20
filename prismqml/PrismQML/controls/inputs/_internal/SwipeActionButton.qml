// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"
import "../../data"
import "../../utils/_internal/ContrastInk.js" as ContrastInk

// SwipeActionButton - One revealed swipe action 滑动露出的单个操作
// Bound behaviour: the Repeater's index/modelData are injected into the required
// properties, because a delegate living in another file has no modelData scope of
// its own. 绑定行为: 委托位于另一个文件时没有 modelData 作用域, 因此由 Repeater 注入
// 到 required 属性里。
pragma ComponentBehavior: Bound
Item {
    id: button

    // ==================== Required Props 必需属性 ====================
    required property var host
    required property string side
    required property int index
    required property var modelData

    // ==================== Readonly State 只读状态 ====================
    readonly property bool enabledAction: !modelData || modelData.enabled !== false
    readonly property string label: modelData && modelData.text !== undefined
        ? String(modelData.text) : ""
    readonly property string iconName: modelData && modelData.icon !== undefined
        ? String(modelData.icon) : ""
    readonly property color tint: Enums.statusLevel.getColorByLevel(
        modelData && modelData.level !== undefined
            ? Number(modelData.level) : Enums.statusLevel.info)
    // Semantic tokens brighten to pastels on dark, so the content ink follows the
    // tint it is drawn on instead of assuming white always survives.
    // 语义 token 在深色下提亮为粉彩色，故内容墨色跟随实际底色，而非假定白字总能存活。
    readonly property color tintInk: ContrastInk.onFill(
        tint, Enums.accentForeground, Enums.onLightFill, 4.5)
    // Touch has no hover preview: the hover treatment follows the press there
    // 触摸没有 hover 预览: 触摸端 hover 视觉跟随按压
    readonly property bool _touchActive: Touch.feedback(hoverHandler.hovered,
                                                        tapHandler.pressed)

    // ==================== Size 尺寸 ====================
    width: host.actionWidth
    height: parent ? parent.height : 0
    opacity: enabledAction ? Enums.opacityLevel.visible
                           : Enums.opacityLevel.disabled

    // ==================== Content 内容 ====================
    Rectangle {
        anchors.fill: parent
        color: button.tint
        opacity: button._touchActive ? Enums.opacityLevel.strong
                                     : Enums.opacityLevel.visible
    }

    Column {
        anchors.centerIn: parent
        spacing: Enums.spacing.xxs

        Icon {
            anchors.horizontalCenter: parent.horizontalCenter
            icon: button.iconName
            iconSize: Enums.iconSize.m
            color: button.tintInk
            visible: button.iconName !== ""
        }

        Label {
            anchors.horizontalCenter: parent.horizontalCenter
            type: Enums.label.type_caption
            text: button.label
            color: button.tintInk
            visible: button.label !== ""
        }
    }

    HoverHandler {
        id: hoverHandler
        cursorShape: Qt.PointingHandCursor
        enabled: button.enabledAction
    }

    TapHandler {
        id: tapHandler
        enabled: button.enabledAction
        onTapped: button.host._trigger(button.modelData, button.side)
    }
}
