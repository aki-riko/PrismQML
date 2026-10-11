// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "."

// RadioMenuFlyoutItem - Single-choice menu row 菜单内单选行
// Rows without an explicit radioGroup share the "default" group and stay mutually exclusive.
// 未显式指定 radioGroup 的行共享 "default" 组并保持互斥。
Action {
    id: control

    // ==================== Public Props 公开属性 ====================
    radioGroup: "default"
    exclusive: true
}
