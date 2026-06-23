// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import ".."
import QtQuick.Window  // 置于库import后:原生Window名归库后不被覆盖

// WindowAnimationHelper - Window animation management 窗口动画管理
//
// 设计原则: 只在用户主动点击 caption button 的路径上播伪动画。
// 任务栏 / Win+D / Alt+Space 等系统行为走 Qt 默认 (不拦截 visibility),
// 否则会与 DWM 冲突造成"闪一下"。
//
// - showAnim / closeAnim: 启动 / 关闭, 一直保留
// - minimizeAnim: 仅由 animatedMinimize() 触发, 走完动画再 showMinimized()
// - maximizePulseAnim: 仅由 animatedMaximize() / animatedRestore() 触发,
//   播完 scale 回弹再实际改尺寸
Item {
    id: helper

    // ==================== Required Props 必需属性 ====================
    required property Window targetWindow
    required property var onCloseCallback

    // ==================== Animation State 动画状态 ====================
    property real animScale: 0.95
    property real animOpacity: 0

    // ==================== Public Methods 公开方法 ====================
    function startShow() {
        animScale = 0.95
        animOpacity = 0
        showAnim.start()
    }

    function animatedClose() { closeAnim.start() }

    /// 用户点最小化按钮: 直接 showMinimized,DWM 接管动画
    /// (NativeWindowHook v2 给 hwnd 加回了 WS_CAPTION,DWM 会做缩到任务栏的动画)
    function animatedMinimize() {
        if (!targetWindow) return
        targetWindow.showMinimized()
    }

    /// 内部别名,直接走 DWM
    function animatedMinimizeWithForward() {
        if (!targetWindow) return
        targetWindow.showMinimized()
    }

    /// 用户点最大化按钮: 直接 showMaximized,DWM 接管动画
    function animatedMaximize() {
        if (!targetWindow) return
        targetWindow.showMaximized()
    }

    /// 用户点还原按钮: 直接 showNormal
    function animatedRestore() {
        if (!targetWindow) return
        targetWindow.showNormal()
    }

    /// 任务栏 / Win+D 等系统触发的 visibility 变化: 不拦截, 不播伪动画。
    /// 让 Qt 走默认路径, 避免与 DWM 冲突造成的闪烁。
    function handleVisibilityChange(newVis) {
        return false
    }

    // ==================== Show Animation 显示动画 ====================
    ParallelAnimation {
        id: showAnim
        NumberAnimation { target: targetWindow; property: "opacity"; to: 1; duration: Enums.duration.medium; easing.type: Easing.OutCubic }
        NumberAnimation { target: helper; property: "animScale"; to: 1; duration: Enums.duration.medium; easing.type: Easing.OutCubic }
        NumberAnimation { target: helper; property: "animOpacity"; to: 1; duration: Enums.duration.medium; easing.type: Easing.OutCubic }
    }

    // ==================== Close Animation 关闭动画 ====================
    SequentialAnimation {
        id: closeAnim
        ParallelAnimation {
            NumberAnimation { target: targetWindow; property: "opacity"; to: 0; duration: Enums.duration.normal; easing.type: Easing.InCubic }
            NumberAnimation { target: helper; property: "animScale"; to: 0.95; duration: Enums.duration.normal; easing.type: Easing.InCubic }
            NumberAnimation { target: helper; property: "animOpacity"; to: 0; duration: Enums.duration.normal; easing.type: Easing.InCubic }
        }
        ScriptAction { script: onCloseCallback() }
    }

    // ==================== Minimize / Maximize / Restore ====================
    // 不再做伪动画。NativeWindowHook v2 给 hwnd 加回 WS_CAPTION 后,
    // DWM 会接管 minimize / maximize / restore 的原生动画。
    // animatedMinimize / animatedMaximize / animatedRestore 直接走 Qt API,
    // 由 DWM 自己渲染动画。
}
