// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// Backdrop - Windows 11 Mica effect constants 云母效果常量
// Simplified to on/off only 简化为开关模式
QtObject {
    // DWM backdrop type values (for internal use) DWM背景类型值（内部使用）
    readonly property int _dwm_none: 1   // DWMSBT_NONE
    readonly property int _dwm_mica: 2   // DWMSBT_MAINWINDOW (Mica)
}
