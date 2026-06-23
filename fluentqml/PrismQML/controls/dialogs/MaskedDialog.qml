// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../.."
import "../../effects"

// MaskedDialog - Dialog with a translucent mask layer 带半透明遮罩层的对话框
//
// Architecture: Fill parent window, place dialogBody in center 架构：填满父窗口，中心放置 dialogBody
// 半透明遮罩铺满父窗口 + 居中主体带柔和投影 + 打开/关闭淡入淡出过渡,具体视觉参数见下方实现

OverlayDialogCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    // Dialog body content 对话框主体内容
    default property alias bodyContent: dialogBody.data

    // Dialog body reference 对话框主体引用
    readonly property alias body: dialogBody

    // ==================== Override Methods 重写方法 ====================
    // Override open to reset dialogBody position 重写open以重置 dialogBody 位置
    function open() {
        // Save original parent 保存原始父组件
        if (!_originalParent) {
            _originalParent = control.parent
        }

        // Determine overlay target 确定覆盖目标
        var target = _resolveOverlayTarget()
        if (target && target !== control.parent) {
            control.parent = target
        }

        // Reset position 重置位置
        dialogBody.anchors.centerIn = Qt.binding(function() { return control })
        _isOpen = true
    }

    // ==================== Shadow Layer 阴影层 ====================
    // Shadow: soft drop shadow under the dialog body 主体下方柔和投影
    // Fluent: 模糊阴影; neo: 硬阴影
    RectangularShadow {
        anchors.fill: dialogBody
        radius: Enums.radius.dialog
        color: Enums.stateColor.maskMedium
        blur: Enums.shadow.level16.blur
        offset: Qt.vector2d(0, Enums.shadow.level16.offset)
        visible: !Enums.isNeobrutalism
    }

    NeoShadow {
        target: dialogBody
        visible: Enums.isNeobrutalism
        radius: Enums.radius.dialog
        z: dialogBody.z - 1
    }

    // ==================== Dialog Body 对话框主体 ====================
    Rectangle {
        id: dialogBody
        objectName: "dialogBody"
        anchors.centerIn: parent

        // Default size, will be overridden by child 默认尺寸，由子类覆盖
        width: Enums.controlSize.dialogDefaultWidth
        height: Enums.controlSize.dialogDefaultHeight

        radius: Enums.radius.dialog

        // neo: 白面+黑边; Fluent: dialogColors
        color: Enums.isNeobrutalism ? Enums.dialogColor : Enums.dialogColors.containerBg

        border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth : Enums.border.thin
        border.color: Enums.isNeobrutalism ? Enums.neo.borderColor : Enums.dialogColors.border
        
        // Clip children to rounded corners 裁剪子元素以适应圆角
        clip: true
        
        // Animation 动画
        scale: control._isOpen ? 1 : 0.95
        opacity: control._isOpen ? 1 : 0
        
        Behavior on scale {
            NumberAnimation {
                duration: control._isClosing ? Enums.duration.fast : Enums.duration.medium
                easing.type: control._isClosing ? Easing.Linear : Easing.InSine
            }
        }
        Behavior on opacity {
            NumberAnimation {
                duration: control._isClosing ? Enums.duration.fast : Enums.duration.medium
                easing.type: control._isClosing ? Easing.Linear : Easing.InSine
                onRunningChanged: {
                    if (!running && control._isClosing) {
                        control._isClosing = false
                        control.closed()
                    }
                }
            }
        }
        
        // Drag handler 拖拽处理
        MouseArea {
            anchors.fill: parent
            enabled: control.draggable
            drag.target: control.draggable ? dialogBody : null

            property point dragStart

            onPressed: (mouse) => {
                if (control.draggable) {
                    // Unbind anchors 解除锚点绑定
                    dialogBody.anchors.centerIn = undefined
                    dragStart = Qt.point(mouse.x, mouse.y)
                }
            }

            onPositionChanged: (mouse) => {
                if (pressed && control.draggable) {
                    var newX = dialogBody.x + mouse.x - dragStart.x
                    var newY = dialogBody.y + mouse.y - dragStart.y
                    // Clamp to parent bounds 限制在父组件范围内
                    dialogBody.x = Math.max(0, Math.min(newX, control.width - dialogBody.width))
                    dialogBody.y = Math.max(0, Math.min(newY, control.height - dialogBody.height))
                }
            }
        }
    }
}
