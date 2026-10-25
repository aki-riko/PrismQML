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
    // Calibrated against the real DWM window shadow measured on a presenting desktop over a
    // white backdrop (screen grab, per-physical-pixel luminance, median of three samples per
    // edge, repeated on two window sizes): DWM's band is asymmetric because its shadow is
    // offset downwards — the left/right (side) edges peak at ~11.4% darkening (255 -> 226)
    // and fade out over ~33 logical px, the top edge at ~5%, and the bottom edge at ~21.6%
    // (255 -> 200) over ~40 logical px. An outside drawer shows exactly one outward band on
    // the side it is anchored to, so the side measurement is the parity target: a 0.50 black
    // silhouette put the panel edge at 21.2% (54/255 measured on the real effect) — the DWM
    // *bottom* figure on a *side* edge, which is the heavy band users reported. The pushout
    // per unit colour alpha measured on the real effect is ~42% (0.50 -> 21.2%), so 0.27
    // lands the panel edge at ~11.4%, equal to the DWM side band; blur stays 24 because it
    // only decides how wide the band reads and the follower reserve has to cover that fade.
    // Offset stays 0 because a window shadow is centred, unlike the popup elevation levels.
    // 窗口外阴影: 用于替代外侧抽屉 HWND 的原生 DWM 阴影。标定依据是真实上屏桌面上量得的
    // DWM 窗口阴影 (白背板, 抓屏后逐物理像素取亮度, 每边三个采样点取中位数, 两种窗口尺寸
    // 各复验一次): DWM 阴影向下偏移, 因此并不对称 —— 左/右边(侧边)峰值约 11.4% 暗化
    // (255 -> 226), 约 33 逻辑像素内衰减完; 上边约 5%; 下边约 21.6% (255 -> 200), 衰减
    // 跨度约 40 逻辑像素。外侧抽屉只在它所贴的那一侧露出一条外阴影, 因此以"侧边"实测值作为
    // 对齐目标: 轮廓取 0.50 黑时真实效果测得面板边缘 21.2% (54/255) —— 等于把 DWM 的
    // *下边* 浓度用在 *侧边* 上, 即用户报告的浓重像带。实测每单位颜色 alpha 的推高量约
    // 42% (0.50 -> 21.2%), 故 0.27 把面板边缘落在约 11.4%, 与 DWM 侧边一致; blur 仍保持
    // 24, 因为它只决定像带读起来的宽度, 而附属窗口留白必须覆盖该衰减。偏移保持 0:
    // 窗口阴影居中, 与弹层高度等级不同。
    readonly property QtObject windowOutside: QtObject {
        readonly property real offset: 0
        readonly property real blur: shadow.isTicket ? 0 : 24
        readonly property color color: shadow.isTicket ? Qt.rgba(0, 0, 0, 0) : Qt.rgba(0, 0, 0, 0.27 * shadow._alphaMultiplier)
    }
}
