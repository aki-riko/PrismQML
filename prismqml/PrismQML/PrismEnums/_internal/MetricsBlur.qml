// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// MetricsBlur - Blur radius metrics 模糊半径度量
// Static data only; kept in _internal so Metrics.qml stays inside its size gate.
// 仅静态数据; 放在 _internal 以保证 Metrics.qml 留在体积门禁内。
QtObject {
    id: blur

    // ==================== Public Props 公开属性 ====================
    readonly property real acrylic: 30 // Acrylic effect blur 亚克力效果模糊
    readonly property real background: 64 // Background blur 背景模糊
    readonly property real light: 16 // Light blur 轻度模糊
}
