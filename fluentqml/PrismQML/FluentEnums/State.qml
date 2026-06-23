// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// State - State component type enums 状态组件类型枚举
QtObject {
    readonly property int type_result: 0       // 结果状态（ResultState）
    readonly property int type_no_data: 1      // 无数据（EmptyDataState）
    readonly property int type_no_internet: 2  // 无网络（OfflineState）
}
