// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// MetricsShadow - Shadow elevation metrics 阴影层级度量
QtObject {
    id: shadow

    // ==================== Required Props 必需属性 ====================
    required property bool isDark
    required property bool isTicket

    // ==================== Internal Props 内部属性 ====================
    readonly property real _alphaMultiplier: isDark ? 1.5 : 1.0
    readonly property real baseScale: 1.0 // MultiEffect neutral shadow scale MultiEffect 中性阴影缩放

    // ==================== Internal Methods 内部方法 ====================
    // Apply shadow to MultiEffect for non-RectangularShadow scenarios
    // 在不支持 RectangularShadow 的场景中将阴影应用到 MultiEffect。
    function applyLevel2(target) { target.verticalOffset = level2.offset; target.blur = level2.blurNormalized; target.samples = level2.samples; target.color = level2.color }
    function applyLevel4(target) { target.verticalOffset = level4.offset; target.blur = level4.blurNormalized; target.samples = level4.samples; target.color = level4.color }
    function applyLevel8(target) { target.verticalOffset = level8.offset; target.blur = level8.blurNormalized; target.samples = level8.samples; target.color = level8.color }
    function applyLevel16(target) { target.verticalOffset = level16.offset; target.blur = level16.blurNormalized; target.samples = level16.samples; target.color = level16.color }
    function applyLevel28(target) { target.verticalOffset = level28.offset; target.blur = level28.blurNormalized; target.samples = level28.samples; target.color = level28.color }

    // ==================== Content 内容 ====================
    // Level 2: Slight elevation 轻微悬浮
    // Usage: Card, SimpleCard, HeaderCard, button hover state
    // Visual: Barely floating, almost touching surface
    readonly property QtObject level2: QtObject {
        readonly property real offset: shadow.isTicket ? 0 : 1
        readonly property real blur: shadow.isTicket ? 0 : 4
        readonly property int samples: shadow.isTicket ? 1 : 13
        readonly property color color: shadow.isTicket ? Qt.rgba(0, 0, 0, 0) : Qt.rgba(0, 0, 0, 0.08 * shadow._alphaMultiplier)
        readonly property real blurNormalized: shadow.isTicket ? 0 : 0.1
    }

    // Level 4: Standard elevation 标准悬浮
    // Usage: ElevatedCard, ComboBox dropdown, InfoBar, Toast
    // Visual: Clearly floating, layered appearance
    readonly property QtObject level4: QtObject {
        readonly property real offset: shadow.isTicket ? 0 : 2
        readonly property real blur: shadow.isTicket ? 0 : 8
        readonly property int samples: shadow.isTicket ? 1 : 17
        readonly property color color: shadow.isTicket ? Qt.rgba(0, 0, 0, 0) : Qt.rgba(0, 0, 0, 0.12 * shadow._alphaMultiplier)
        readonly property real blurNormalized: shadow.isTicket ? 0 : 0.15
    }

    // Level 8: Medium elevation 中等悬浮
    // Usage: Menu, ContextMenu, Tooltip, Flyout, TeachingTip
    // Visual: Significantly floating, temporary overlay
    readonly property QtObject level8: QtObject {
        readonly property real offset: shadow.isTicket ? 0 : 4
        readonly property real blur: shadow.isTicket ? 0 : 16
        readonly property int samples: shadow.isTicket ? 1 : 21
        readonly property color color: shadow.isTicket ? Qt.rgba(0, 0, 0, 0) : Qt.rgba(0, 0, 0, 0.14 * shadow._alphaMultiplier)
        readonly property real blurNormalized: shadow.isTicket ? 0 : 0.25
    }

    // Level 16: High elevation 高悬浮
    // Usage: Dialog, MessageBox, Modal windows
    // Visual: Highly floating, focus emphasis
    readonly property QtObject level16: QtObject {
        readonly property real offset: shadow.isTicket ? 0 : 8
        readonly property real blur: shadow.isTicket ? 0 : 32
        readonly property int samples: shadow.isTicket ? 1 : 25
        readonly property color color: shadow.isTicket ? Qt.rgba(0, 0, 0, 0) : Qt.rgba(0, 0, 0, 0.18 * shadow._alphaMultiplier)
        readonly property real blurNormalized: shadow.isTicket ? 0 : 0.4
    }

    // Level 28: Highest elevation 最高悬浮
    // Usage: Main window shadow, standalone popup windows
    // Visual: Maximum shadow, window level
    readonly property QtObject level28: QtObject {
        readonly property real offset: shadow.isTicket ? 0 : 12
        readonly property real blur: shadow.isTicket ? 0 : 48
        readonly property int samples: shadow.isTicket ? 1 : 29
        readonly property color color: shadow.isTicket ? Qt.rgba(0, 0, 0, 0) : Qt.rgba(0, 0, 0, 0.22 * shadow._alphaMultiplier)
        readonly property real blurNormalized: shadow.isTicket ? 0 : 0.5
    }

    // Splash icon MultiEffect shadow 启动画面图标 MultiEffect 阴影
    readonly property QtObject splashIcon: QtObject {
        readonly property real blurNormalized: 0.8
        readonly property real offset: 6
    }

    // Window outward shadow: replaces the native DWM shadow on an outside drawer HWND.
    // Measured on the real effect with 0.50 black: the panel edge lands at ~21% darkening for
    // every blur, and the fade settles at about 0.8x the blur (40 -> 32px, 24 -> 19px,
    // 16 -> 13px). Blur therefore decides how wide the shadow reads and the follower reserve
    // has to cover that fade, or the band is cut off on the HWND edge. Offset stays 0 because
    // a window shadow is centred, unlike the popup elevation levels.
    // 窗口外阴影: 用于替代外侧抽屉 HWND 的原生 DWM 阴影。真实效果实测(0.50 黑): 面板边缘在
    // 任何 blur 下都落在约 21% 暗化 —— 即 DWM 量级 —— 衰减跨度约为 blur 的 0.8 倍
    // (40 -> 32px, 24 -> 19px, 16 -> 13px)。因此 blur 决定阴影的观感宽度, 而附属窗口留白
    // 必须覆盖该衰减, 否则像带会被 HWND 边界切断。偏移保持 0: 窗口阴影居中, 与弹层不同。
    readonly property QtObject windowOutside: QtObject {
        readonly property real offset: 0
        readonly property real blur: shadow.isTicket ? 0 : 24
        readonly property color color: shadow.isTicket ? Qt.rgba(0, 0, 0, 0) : Qt.rgba(0, 0, 0, 0.50 * shadow._alphaMultiplier)
    }
}
