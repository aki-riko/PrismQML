// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// Backdrop - Windows 11 system backdrop constants 系统背板常量
// Values mirror the DWM DWMSBT_* enumeration so QML and Python share one
// numbering. 取值与 DWM 的 DWMSBT_* 枚举一致，使 QML 与 Python 共用一套编号。
QtObject {
    // DWM backdrop type values (for internal use) DWM背景类型值（内部使用）
    readonly property int none: 1      // DWMSBT_NONE
    readonly property int mica: 2      // DWMSBT_MAINWINDOW (Mica)
    readonly property int acrylic: 3   // DWMSBT_TRANSIENTWINDOW (Acrylic)
    readonly property int mica_alt: 4  // DWMSBT_TABBEDWINDOW (Mica Alt)

    // Original on/off aliases kept unchanged for existing consumers.
    // 原有开关别名保持原样，供既有消费者继续使用。
    readonly property int _dwm_none: 1   // DWMSBT_NONE
    readonly property int _dwm_mica: 2   // DWMSBT_MAINWINDOW (Mica)
}
