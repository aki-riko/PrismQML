// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../utils"

// ButtonA11ySurface - Accessible metadata for ButtonCore 按钮核心的无障碍元数据
// Keeps the metadata contract beside the other Button helpers so ButtonCore itself
// only declares one line and stays inside its architecture size gate.
// 让元数据契约与 Button 的其它 helper 同处，使 ButtonCore 只声明一行并保持在
// 架构体积门禁内。
Item {
    id: surface

    // ==================== Required Props 必需属性 ====================
    required property var buttonControl

    // ==================== Readonly State 只读状态 ====================
    // Only the toggle feature carries state; every other style is a plain button.
    // 仅切换特性带状态；其余样式都是普通按钮。
    readonly property bool _isToggle:
        surface.buttonControl !== null
        && surface.buttonControl !== undefined
        && surface.buttonControl.feature === surface.buttonControl._skin.button.feature_toggle
    readonly property string _label:
        surface.buttonControl !== null && surface.buttonControl !== undefined
            && surface.buttonControl.text !== ""
            ? surface.buttonControl.text
            : (surface.buttonControl ? surface.buttonControl.toolTipText : "")

    // ==================== Size 尺寸 ====================
    // Non-visual: the inner surface owns the metadata, this wrapper owns nothing.
    // 非可视：内层 surface 承载元数据，本包装不承载任何内容。
    width: 0
    height: 0
    enabled: false
    visible: false

    // ==================== Content 内容 ====================
    A11ySurface {
        target: surface.buttonControl
        role: surface._isToggle
              ? Enums.accessibility.role_checkbox
              : Enums.accessibility.role_button
        name: surface._label
        checkable: surface._isToggle ? 1 : 0
        checked: surface.buttonControl ? surface.buttonControl.checked : false
    }
}
