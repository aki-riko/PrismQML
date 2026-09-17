// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

pragma Singleton
import QtQuick

// Touch - Touch platform capability resolver 触摸平台能力解析
//
// 宿主 (C++ prism) 注入 PlatformInfo 上下文属性; Python 宿主与桌面 C++ 宿主提供
// 非触摸语义, 此时本单例全部返回桌面默认值.
// The host (C++ prism) injects the PlatformInfo context property; the Python host
// and the desktop C++ host stay non-touch, which keeps every value at its desktop
// default here.
//
// 桌面不变式 (铁律): 非触摸平台 minTargetSize 恒为 0, 因此
// `Math.max(<桌面度量>, Touch.minTargetSize) === <桌面度量>`, 布局与视觉零变化.
// Desktop invariant: minTargetSize is always 0 off touch, so
// `Math.max(<desktop metric>, Touch.minTargetSize) === <desktop metric>`.
//
// 用法:
//   height: Math.max(Enums.searchMetrics.resultItemHeight, Touch.minTargetSize)
//   readonly property bool _active: Touch.feedback(hovered, pressed)
//   color: Touch.feedback(hovered, pressed) ? Enums.stateColor.hover : Enums.transparent
//   visible: Touch.reveal(hovered)   // hover 才揭示的附属控件, 触摸端常显
QtObject {
    id: touch

    // ==================== Readonly State 只读状态 ====================
    // Defensive read: the Python host has no PlatformInfo context property 防御式读取
    readonly property bool _hasPlatformInfo:
        typeof PlatformInfo !== "undefined" && PlatformInfo !== null

    readonly property bool isTouch: _hasPlatformInfo && PlatformInfo.isTouch === true
    readonly property bool isMobile: _hasPlatformInfo && PlatformInfo.isMobile === true
    readonly property bool isCompact: _hasPlatformInfo && PlatformInfo.isCompact === true

    // Material 48dp minimum interactive target; 0 means "leave desktop metrics alone"
    // Material 48dp 最小可点目标; 0 表示不抬高桌面度量
    readonly property int minTargetSize: {
        if (!isTouch) return 0
        if (_hasPlatformInfo && PlatformInfo.touchTargetSize > 0) {
            return Math.max(48, PlatformInfo.touchTargetSize)
        }
        return 48
    }

    // ==================== Public Methods 公开方法 ====================
    // Hover-equivalent visual feedback 等价于 hover 的视觉反馈
    //
    // 桌面: 完全等于 hovered, 现有行为零变化.
    // 触摸: Qt 会把触摸按压合成为 hover 且松手后不派发 leave, 直接采信 hovered 会留下
    //       残留高亮; 因此触摸端改由按压驱动 —— 既清掉残留, 又让"只有 hover 反馈"的
    //       控件在按压期间真正给出反馈.
    // Desktop: identical to hovered. Touch: Qt synthesizes hover from touch and never
    // sends a leave on release, so hover-driven visuals would stick; drive them from
    // the press instead.
    function feedback(hovered, pressed) {
        if (touch.isTouch) return pressed === true
        return hovered === true
    }

    // Hover-revealed affordances must stay reachable on touch 触摸端 hover 揭示的控件需常显
    function reveal(hovered) {
        return touch.isTouch || hovered === true
    }

    // Raise an interactive metric to the touch minimum 把交互度量抬到触摸下限
    function target(desktopSize) {
        return Math.max(desktopSize, touch.minTargetSize)
    }
}
