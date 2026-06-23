// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// Card - Card type enums 卡片类型枚举
QtObject {
    readonly property int type_default: 0    // DefaultCard - no hover effect 默认卡片(无悬停反馈)
    readonly property int type_hover: 1      // HoverCard - hover color change 悬停变色卡片
    readonly property int type_elevated: 2   // ElevatedCard - hover float up 悬浮卡片上浮
    readonly property int type_header: 3     // HeaderCard - with title header 带标题卡片
    readonly property int type_setting: 4    // SettingCard - setting item card 设置项卡片
    readonly property int type_expander: 5   // Expander - expandable card 可展开卡片
}
