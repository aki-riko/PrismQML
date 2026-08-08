// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import QtQuick
import QtQuick.Window

// PopupNativeWindow - Lazy native surface for PopupWindowCore 弹层核心的延迟原生窗口
Window {
    id: nativePopupWindow

    // ==================== Required Props 必需属性 ====================
    required property Item popupControl

    width: popupControl._outerWidth
    height: popupControl._outerHeight
    visible: false
    flags: Qt.ToolTip | Qt.FramelessWindowHint | Qt.NoFluentShadowWindowHint
    color: Enums.transparent
    onVisibleChanged: {
        if (visible && popupControl.stealFocus) keyHandler.forceActiveFocus()
    }

    // Auto close on focus lost 失焦自动关闭
    onActiveFocusItemChanged: {
        if (!activeFocusItem
                && popupControl.isOpen
                && popupControl.closeOnClickOutside) {
            Qt.callLater(function() {
                if (!nativePopupWindow.activeFocusItem && popupControl.isOpen) {
                    popupControl.close()
                }
            })
        }
    }

    Item {
        id: keyHandler

        anchors.fill: parent
        focus: popupControl.stealFocus
        Keys.onEscapePressed: function(event) {
            if (!popupControl.isOpen || !popupControl.closeOnClickOutside) return
            popupControl.close()
            event.accepted = true
        }
    }
}
