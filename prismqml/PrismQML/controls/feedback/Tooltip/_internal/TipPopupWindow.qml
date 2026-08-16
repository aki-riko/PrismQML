// TipPopupWindow - Main native tip surface 主提示原生窗口表面
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import "../../../.."
import "../../../buttons"
import "../../../data/Label"

// TipPopupWindow - Owns the main popup visual tree 承载主弹层视觉树
Window {
    id: popupWindow

    // ==================== Required Props 必需属性 ====================
    required property var popupControl
    required property var positionHelper

    flags: Qt.ToolTip | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint
    color: Enums.transparent
    width: positionHelper.viewWidth
    height: positionHelper.viewHeight
    x: popupControl._animX
    y: popupControl._animY
    opacity: 0

    // Focus detection for click outside close 焦点检测实现点击外部关闭
    onActiveFocusItemChanged: {
        if (!activeFocusItem && popupControl._isOpen && popupControl.modal) {
            Qt.callLater(function() {
                if (!popupWindow.activeFocusItem && popupControl._isOpen) {
                    popupControl.close()
                }
            })
        }
    }

    // ==================== Content 内容 ====================
    Rectangle {
        id: contentRect

        objectName: "tipPopupSurface"
        anchors.fill: parent
        radius: popupControl._tipRadius
        color: popupControl._tipBackground
        border.width: popupControl._tipBorderWidth
        border.color: popupControl._tipBorderColor

        Column {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: actionRow.visible ? actionRow.top : parent.bottom
            anchors.topMargin: Enums.spacing.l
            anchors.leftMargin: Enums.spacing.l
            anchors.rightMargin: popupControl.closable ? 32 : Enums.spacing.l
            anchors.bottomMargin: actionRow.visible ? Enums.spacing.s : Enums.spacing.l
            spacing: Enums.spacing.xs

            Label {
                type: Enums.label.type_body_strong
                text: popupControl.title
                visible: text !== ""
            }

            Label {
                type: Enums.label.type_caption
                text: popupControl.content
                color: Enums.textColor.secondary
                wrapMode: Text.Wrap
                width: parent.width
                visible: text !== ""
            }
        }

        // Create action controls only for tips that expose actions.
        // 仅为带操作的提示创建操作控件。
        Loader {
            id: actionRow

            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.rightMargin: Enums.spacing.l
            anchors.bottomMargin: Enums.spacing.l
            active: popupControl._hasActions
            visible: active
            sourceComponent: Row {
                spacing: Enums.spacing.m

                Button {
                    objectName: "tipSecondaryActionButton"
                    text: popupControl.secondaryButtonText
                    visible: text !== ""
                    onClicked: popupControl._triggerSecondaryAction()
                }

                Button {
                    objectName: "tipPrimaryActionButton"
                    style: Enums.button.style_primary
                    text: popupControl.primaryButtonText
                    visible: text !== ""
                    onClicked: popupControl._triggerPrimaryAction()
                }
            }
        }

        CloseButton {
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.topMargin: Enums.spacing.xs
            anchors.rightMargin: Enums.spacing.xs
            visible: popupControl.closable
            onClicked: popupControl.close()
        }
    }
}
