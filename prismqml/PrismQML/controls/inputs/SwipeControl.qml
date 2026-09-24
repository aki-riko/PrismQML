// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "_internal" as InputInternal

// SwipeControl - Swipe-to-reveal row actions 滑动露出行操作
//
// 内容横向拖拽露出两侧操作按钮: 拖过一半松手吸附到展开位, 否则收回; 点操作发
// actionTriggered(key, side) 并收回; 展开状态下点击内容也会收回.
// 鼠标与触摸走同一个 DragHandler, 因此桌面端同样可用.
//
// 用法 / Usage:
//   Fluent.SwipeControl {
//       leftActions: [{ key: "flag", text: "Flag", icon: <path>,
//                       level: Enums.statusLevel.info }]
//       rightActions: [{ key: "delete", text: "Delete", icon: <path>,
//                        level: Enums.statusLevel.error }]
//       onActionTriggered: (key, side) => runAction(key, side)
//
//       Rectangle { ... }   // 内容用默认属性传入
//   }
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    // Row content goes through the default property 行内容走默认属性
    default property alias content: contentHost.data
    // [{ key, text, icon, level, enabled }] 每项一个操作按钮
    property var leftActions: []
    property var rightActions: []
    // Width of one revealed action 单个露出操作的宽度
    property int actionWidth: Enums.controlSize.swipeActionWidth
    property bool interactionEnabled: true

    // ==================== Internal Props 内部属性 ====================
    // Content displacement: positive reveals left actions, negative right ones
    // 内容位移: 正值露出左侧操作, 负值露出右侧
    property real _offset: 0
    property bool _dragging: false
    readonly property var _safeLeft: control._actionList(leftActions)
    readonly property var _safeRight: control._actionList(rightActions)
    readonly property real _leftWidth: _safeLeft.length * actionWidth
    readonly property real _rightWidth: _safeRight.length * actionWidth

    // ==================== Readonly State 只读状态 ====================
    readonly property string openSide: _offset > 0 ? "left"
                                     : (_offset < 0 ? "right" : "")
    readonly property bool isOpen: openSide !== ""
    readonly property bool canSwipe: interactionEnabled
        && (_leftWidth > 0 || _rightWidth > 0)

    // ==================== Signals 信号 ====================
    signal actionTriggered(string key, string side)

    // ==================== Public Methods 公开方法 ====================
    // Reveal one side ("left"/"right"), or close with "" / null
    // 展开指定一侧 ("left"/"right"), 传空则收回
    function open(side) {
        if (side === "left") _offset = _leftWidth
        else if (side === "right") _offset = -_rightWidth
        else _offset = 0
    }
    function close() { _offset = 0 }
    // Stable key for an action entry 取操作项的稳定 key
    function actionKey(action) {
        if (!action) return ""
        if (action.key !== undefined) return String(action.key)
        return action.text !== undefined ? String(action.text) : ""
    }

    // ==================== Internal Methods 内部方法 ====================
    // Only real action entries are accepted, so a null model never crashes the row
    // 只接受真正的操作项, 空模型不会让行崩掉
    function _actionList(source) {
        if (source === null || source === undefined) return []
        return typeof source.length === "number" ? source : []
    }
    // Snap to the nearest rest position 吸附到最近的静止位
    function _settle() {
        if (_offset > _leftWidth / 2) _offset = _leftWidth
        else if (_offset < -_rightWidth / 2) _offset = -_rightWidth
        else _offset = 0
    }
    // Close first so the host sees a settled row, then report the action
    // 先收回再派发, 宿主响应时行已收敛
    function _trigger(action, side) {
        var key = control.actionKey(action)
        control.close()
        control.actionTriggered(key, side)
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: contentHost.childrenRect.width
    implicitHeight: contentHost.childrenRect.height
    clip: true

    // ==================== Content 内容 ====================
    // Content sits behind the edge actions 内容位于两侧操作的下层
    Row {
        id: leftRow
        objectName: "swipeLeftActions"
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        spacing: Enums.spacing.none

        Repeater {
            model: control._safeLeft

            InputInternal.SwipeActionButton {
                host: control
                side: "left"
            }
        }
    }

    Row {
        id: rightRow
        objectName: "swipeRightActions"
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        spacing: Enums.spacing.none

        Repeater {
            model: control._safeRight

            InputInternal.SwipeActionButton {
                host: control
                side: "right"
            }
        }
    }

    Item {
        id: contentHost
        objectName: "swipeContent"
        x: control._offset
        width: control.width
        height: control.height

        // Follow the finger while dragging, glide on release
        // 拖拽时跟手, 松手后平滑归位
        Behavior on x {
            enabled: !control._dragging
            NumberAnimation {
                duration: Enums.duration.fast
                easing.type: Easing.OutCubic
            }
        }

        DragHandler {
            id: swipeDrag
            target: null
            enabled: control.canSwipe
            xAxis.enabled: true
            yAxis.enabled: false
            dragThreshold: 8

            onActiveChanged: {
                control._dragging = active
                if (!active) control._settle()
            }
            onActiveTranslationChanged: {
                if (!active) return
                control._offset = Math.max(
                    -control._rightWidth,
                    Math.min(control._leftWidth, activeTranslation.x))
            }
        }

        // Tapping the content while a row is open closes it again
        // 展开状态下点击内容把它收回
        TapHandler {
            enabled: control.isOpen
            onTapped: control.close()
        }
    }
}
