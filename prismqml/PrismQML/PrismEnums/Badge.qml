// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// Badge - Badge type enums 徽章类型枚举
QtObject {
    readonly property int type_dot: 0
    readonly property int type_number: 1
    readonly property int type_icon: 2

    // Person picture 人物头像
    readonly property real personPictureInitialsScale: 0.4        // Single initial scale 单首字母比例
    readonly property real personPictureMultiInitialsScale: 0.32  // Multi-initial scale 多首字母比例
    readonly property int personPictureInitialsLength: 2          // Max rendered initials 最多渲染的首字母数
}
