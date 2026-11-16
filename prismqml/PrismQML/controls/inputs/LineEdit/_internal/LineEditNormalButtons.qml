// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../buttons"

// LineEditNormalButtons - Embedded button components for LineEditNormal 普通输入框内嵌按钮组件
// Each button is a full ButtonCore (about 1ms to create, measured), so the host only
// loads one while it is shown. 每个按钮都是完整 ButtonCore（实测创建约 1ms），宿主只在显示时加载。
Item {
    id: buttons

    // ==================== Required Props 必需属性 ====================
    required property var host

    // ==================== Public Props 公开属性 ====================
    property alias clearButtonComponent: clearButtonComponent
    property alias actionButtonComponent: actionButtonComponent

    // ==================== Size 尺寸 ====================
    width: 0
    height: 0
    visible: false

    // ==================== Content 内容 ====================
    // Clear button (transparent, never steals input focus) 清除按钮（透明，不抢输入焦点）
    Component {
        id: clearButtonComponent

        Button {
            objectName: "closeBtn"
            style: Enums.button.style_transparent
            icon: Enums.icon.dismiss
            width: Enums.controlSize.lineEditClearButtonSize
            height: Enums.controlSize.lineEditClearButtonSize
            radius: width / 2
            iconSize: Enums.controlSize.checkboxInner
            focusOnPress: false  // Never steal focus from the input 不抢输入框焦点
            onClicked: {
                buttons.host.textInput.text = ""
                buttons.host.cleared()
            }
        }
    }

    // Action button for password and search 密码与搜索操作按钮
    Component {
        id: actionButtonComponent

        InputActionButton {
            // Its parent is the Loader; size against the input instead.
            // 父对象是 Loader；改按所在输入框计算尺寸。
            sizingParent: buttons.host
            collapsed: buttons.host._isCollapsedSearch
            collapsedSize: buttons.host.collapsedWidth
            fillParentHeight: buttons.host._isSearch
            icon: buttons.host._isPassword
                ? (buttons.host.showPassword ? Enums.icon.eye_off : Enums.icon.eye)
                : Enums.icon.search
            onClicked: {
                if (buttons.host._isPassword) {
                    buttons.host.showPassword = !buttons.host.showPassword
                } else if (buttons.host._isSearch) {
                    if (buttons.host._isCollapsedSearch) {
                        buttons.host.textInput.forceActiveFocus()
                    } else {
                        buttons.host.searched(buttons.host.textInput.text)
                    }
                }
            }
        }
    }
}
