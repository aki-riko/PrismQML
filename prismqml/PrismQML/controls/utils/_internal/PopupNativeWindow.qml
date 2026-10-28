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
    // A surface that leaves focus with its owner must also stay out of window
    // activation: otherwise the platform activates it on the first click inside it,
    // the owner window goes inactive, the owner's input loses activeFocus, and the
    // owner's focus-loss guard dismisses the very popup being clicked. Declaring the
    // window non-focusable keeps the owner authoritative for the whole interaction.
    // Qt.ToolTip is itself a window type, so the non-focusable hint can only be added
    // alongside it — never with another type flag such as Qt.Window.
    // 把焦点留给宿主的表面也必须不参与窗口激活：否则平台在首次点入时激活该窗口，
    // 宿主窗口转为非激活、宿主输入框失去 activeFocus，宿主的失焦守卫就会驳回正在被
    // 点击的这个弹层。声明窗口不可聚焦可让宿主在整个交互期间保持权威。
    // Qt.ToolTip 本身已是窗口类型，因此不可聚焦只能作为附加标志追加，绝不能再叠加
    // Qt.Window 之类的类型标志。
    flags: Qt.ToolTip | Qt.FramelessWindowHint | Qt.NoFluentShadowWindowHint
        | (popupControl.stealFocus ? 0 : Qt.WindowDoesNotAcceptFocus)
    color: popupControl.effectiveSkinContext.transparent
    onVisibleChanged: {
        if (visible && popupControl.stealFocus) keyHandler.forceActiveFocus()
        if (!visible) popupControl._handleSurfaceClosed()
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
