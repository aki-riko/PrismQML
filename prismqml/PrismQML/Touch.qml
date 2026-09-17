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
//
// 约定 (维护者决策):
//   - 触摸端**不显示任何 tooltip**: Qt 会把触摸按压合成为 hover 且松手不派发 leave,
//     提示弹出后没有任何事件能清掉它。提示入口由 TooltipCore.show() 与
//     WidgetToolTipSupport 的悬浮计时器统一关闭, 两处 Slider 提示 Loader 在触摸端不创建。
//     TooltipCore.qml 已接近其行数门禁上限, 因此守卫写成 `= !Touch.isTouch` 的赋值形式
//     而不是新增分支; 改动时不要为了可读性把行数顶破架构门禁。
//   - 触摸端不常显遮罩类附属内容: 需要反馈的视觉用 feedback(), 只有真正的入口控件
//     (滚动轨/翻页箭头/关闭按钮) 才用 reveal()。
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
    //
    // 触摸端恒为 true: 悬停才出现的附属控件(滚动轨/翻页箭头/关闭按钮/更换遮罩)若在
    // 触摸端继续隐藏就没有入口。调用方需自行确认该附属控件常显是安全的。
    // Always true on touch: hover-only affordances (scroll rail, nav arrows, close
    // button, change overlay) would otherwise be unreachable.
    function reveal(hovered) {
        return touch.isTouch || hovered === true
    }

    // Raise an interactive metric to the touch minimum 把交互度量抬到触摸下限
    function target(desktopSize) {
        return Math.max(desktopSize, touch.minTargetSize)
    }

    // 备注: feedback() 可以安全地嵌套/重复施加 —— 触摸端 f(f(h,p),p) = f(p,p) = p,
    // 桌面端两端都等于 h。因此"父组件先映射、子委托再映射"的链路(Toggle→指示器、
    // ListWidget→ListWidgetItem、ComboBoxCore→ComboBoxCoreContent)无需去重。
    // Note: nested/duplicated feedback() is idempotent in both modes.
}
