// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import QtQuick.Window  // Keep native Window after the library import. 库导入后保留原生 Window 名称。

// WindowAnimationHelper - Window presentation management 窗口呈现管理
//
// Design principle: present startup content as a complete surface.
// 设计原则：启动内容以完整表面直接呈现。
// Leave taskbar, Win+D, and Alt+Space transitions to Qt and DWM.
// 任务栏、Win+D 与 Alt+Space 过渡交给 Qt 和 DWM，避免冲突闪烁。
//
// - startup: present immediately after the first complete frame.
//   启动阶段在首个完整帧后直接呈现。
// - minimize: delegate directly to Qt and DWM. 最小化直接交给 Qt 与 DWM。
// - maximize / restore: request WM_SYSCOMMAND so DWM keeps native transitions.
//   最大化与还原请求 WM_SYSCOMMAND，以保留 DWM 原生过渡。
Item {
    id: helper

    // ==================== Required Props 必需属性 ====================
    required property Window targetWindow

    // ==================== Internal Props 内部属性 ====================
    property real animScale: 0.95
    property real animOpacity: 0

    // Expose startup animation state to the native presentation gate.
    // 向原生首帧门槛暴露启动动画状态。
    readonly property bool showAnimationRunning: showAnim.running

    // ==================== Public Methods 公开方法 ====================
    function startShow() {
        showAnim.stop()
        // Present the window as a complete surface so Splash handoff has no blank gap.
        // 直接呈现完整窗口表面，避免与 Splash 交接时出现短暂空白。
        if (!targetWindow) return
        targetWindow.opacity = 1
        animScale = 1
        animOpacity = 1
    }

    function restoreVisibleState() {
        showAnim.stop()
        if (targetWindow) {
            targetWindow.opacity = 1
        }
        animScale = 1
        animOpacity = 1
    }

    // Minimize directly and let DWM own the transition. 直接最小化并由 DWM 接管过渡。
    function animatedMinimize() {
        if (!targetWindow) return
        targetWindow.showMinimized()
    }

    // Request the native maximize transition, then fall back to Qt.
    // 请求原生最大化过渡，失败时回退 Qt。
    function animatedMaximize() {
        if (!targetWindow) return
        if (typeof NativeWindow !== "undefined" && NativeWindow &&
                typeof NativeWindow.requestMaximize === "function" &&
                NativeWindow.requestMaximize(targetWindow) === true) return
        targetWindow.showMaximized()
    }

    // Request the native restore transition, then fall back to Qt.
    // 请求原生还原过渡，失败时回退 Qt。
    function animatedRestore() {
        if (!targetWindow) return
        if (typeof NativeWindow !== "undefined" && NativeWindow &&
                typeof NativeWindow.requestRestore === "function" &&
                NativeWindow.requestRestore(targetWindow) === true) return
        targetWindow.showNormal()
    }

    anchors.fill: parent
    z: Enums.zIndex.overlay

    // ==================== Content 内容 ====================
    // Show animation. 显示动画。
    ParallelAnimation {
        id: showAnim
        NumberAnimation { target: targetWindow; property: "opacity"; to: 1; duration: Enums.duration.medium; easing.type: Easing.OutCubic }
        NumberAnimation { target: helper; property: "animScale"; to: 1; duration: Enums.duration.medium; easing.type: Easing.OutCubic }
        NumberAnimation { target: helper; property: "animOpacity"; to: 1; duration: Enums.duration.medium; easing.type: Easing.OutCubic }
    }

}
