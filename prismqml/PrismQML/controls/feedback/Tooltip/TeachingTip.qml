// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."

// TeachingTip - Teaching tip component (based on TipPopup) 教学提示组件
// Teaching tip with arrow, supports 13 arrow positions 带箭头的教学提示，支持 13 种箭头位置

TipPopup {
    id: control
    tipType: Enums.tip.type_teaching_tip
    duration: Enums.duration.toast  // TeachingTip default 3s auto-close 默认3秒自动关闭
    
    // TeachingTip specific properties TeachingTip特有属性
    // anchorPosition is defined in TipPopup 已在TipPopup中定义
    // Supports: anchor_top / anchor_bottom / anchor_left / anchor_right / anchor_top_left / anchor_top_right / ... 支持: anchor_top / anchor_bottom / anchor_left / anchor_right / anchor_top_left / anchor_top_right / ...

}
