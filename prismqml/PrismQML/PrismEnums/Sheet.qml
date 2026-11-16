// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// Sheet - Bottom sheet detent enums and stacking geometry 底部弹层停靠枚举与叠层几何
QtObject {
    // ==================== Detents 停靠高度 ====================
    readonly property int detent_medium: 0  // About half of the host height 约宿主一半高度
    readonly property int detent_large: 1   // Fully expanded 完全展开

    // ==================== Geometry 几何 ====================
    readonly property real mediumRatio: 0.5    // Medium detent height / host height 中档高度占宿主比例
    readonly property int topInset: 48         // Large detent gap above the sheet 完全展开时顶部留白
    readonly property int maxWidth: 640        // Centered width cap on wide hosts 宽宿主居中限宽
    readonly property int grabberHeight: 24    // Grabber hit area height 手柄可点击区域高度
    readonly property int grabberBarWidth: 36  // Grabber pill width 手柄胶囊宽度
    readonly property int grabberBarHeight: 5  // Grabber pill height 手柄胶囊高度

    // ==================== Stacking 叠层 ====================
    readonly property int stackPeek: 12           // Covered sheet edge shown above the next one 被覆盖层露出的顶边
    readonly property real stackScaleStep: 0.05   // Scale lost per covered level 每被覆盖一层缩小的比例
    readonly property int maxVisibleDepth: 3      // Deeper sheets fade out 更深的层淡出
    readonly property real stackZStep: 0.01       // z gap between stacked sheets, stays below the next zIndex level 叠层 z 间隔，不越过下一 zIndex 级
    readonly property real stackDimOpacity: 0.5   // Covered sheet dim layer opacity 被覆盖层压暗不透明度
}
