// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../utils"

// ToggleA11ySurface - Accessible metadata for Toggle 切换控件的无障碍元数据
// The unified toggle presents as a check box, radio button or switch depending on
// controlType, so the accessible role follows that same decision. Kept in
// _internal so Toggle.qml only declares one line and stays inside its size gate.
// 统一切换控件按 controlType 呈现为复选框/单选按钮/开关，无障碍角色沿用同一判定。
// 放在 _internal 使 Toggle.qml 只声明一行并保持在体积门禁内。
Item {
    id: surface

    // ==================== Required Props 必需属性 ====================
    required property var toggleControl

    // ==================== Size 尺寸 ====================
    // Non-visual: the inner surface owns the metadata, this wrapper owns nothing.
    // 非可视：内层 surface 承载元数据，本包装不承载任何内容。
    width: 0
    height: 0
    enabled: false
    visible: false

    // ==================== Content 内容 ====================
    A11ySurface {
        target: surface.toggleControl
        // Radio and switch win over the checkbox default; the order mirrors how
        // Toggle resolves its own visual type.
        // 单选与开关优先于复选框默认值；顺序与 Toggle 解析自身视觉类型的顺序一致。
        role: surface.toggleControl._isRadio
              ? Enums.accessibility.role_radiobutton
              : (surface.toggleControl._isSwitch
                 ? Enums.accessibility.role_switch
                 : Enums.accessibility.role_checkbox)
        name: surface.toggleControl.text
        description: surface.toggleControl.checked
                     ? surface.toggleControl.textOn
                     : surface.toggleControl.textOff
        checkable: 1
        checked: surface.toggleControl.checked
    }
}
