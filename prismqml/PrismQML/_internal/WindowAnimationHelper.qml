// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import QtQuick.Window  // Keep native Window after the library import. 库导入后保留原生 Window 名称。

// WindowAnimationHelper - Window animation management 窗口动画管理
//
// Design principle: keep custom transitions to startup and explicit close.
// 设计原则：自定义过渡仅用于启动与显式关闭。
// Leave taskbar, Win+D, and Alt+Space transitions to Qt and DWM.
// 任务栏、Win+D 与 Alt+Space 过渡交给 Qt 和 DWM，避免冲突闪烁。
//
// - showAnim / closeAnim: retain startup and close transitions. 保留启动和关闭过渡。
// - minimize / maximize / restore: delegate directly to Qt and DWM. 最小化、最大化和还原直接交给 Qt 与 DWM。
Item {
    id: helper

    // ==================== Required Props 必需属性 ====================
    required property Window targetWindow
    required property var onCloseCallback

    // ==================== Internal Props 内部属性 ====================
    property real animScale: 0.95
    property real animOpacity: 0

    // ==================== Public Methods 公开方法 ====================
    function startShow() {
        if (closeAnimLoader.item) closeAnimLoader.item.stop()
        showAnim.stop()
        if (!targetWindow || targetWindow.opacity < 0.99) {
            animScale = 0.95
            animOpacity = 0
        }
        showAnim.start()
    }

    function restoreVisibleState() {
        if (closeAnimLoader.item) closeAnimLoader.item.stop()
        showAnim.stop()
        if (targetWindow) {
            targetWindow.opacity = 1
        }
        animScale = 1
        animOpacity = 1
    }

    function animatedClose() {
        if (!targetWindow) return
        showAnim.stop()
        prewarmCloseAnimation()
        if (!closeAnimLoader.item) return
        closeAnimLoader.item.stop()
        closeAnimLoader.item.start()
    }

    function prewarmCloseAnimation() { closeAnimLoader.active = true }

    // Minimize directly and let DWM own the transition. 直接最小化并由 DWM 接管过渡。
    function animatedMinimize() {
        if (!targetWindow) return
        targetWindow.showMinimized()
    }

    // Maximize directly and let DWM own the transition. 直接最大化并由 DWM 接管过渡。
    function animatedMaximize() {
        if (!targetWindow) return
        targetWindow.showMaximized()
    }

    // Restore directly through Qt. 直接通过 Qt 还原窗口。
    function animatedRestore() {
        if (!targetWindow) return
        targetWindow.showNormal()
    }

    // ==================== Content 内容 ====================
    // Show animation. 显示动画。
    ParallelAnimation {
        id: showAnim
        NumberAnimation { target: targetWindow; property: "opacity"; to: 1; duration: Enums.duration.medium; easing.type: Easing.OutCubic }
        NumberAnimation { target: helper; property: "animScale"; to: 1; duration: Enums.duration.medium; easing.type: Easing.OutCubic }
        NumberAnimation { target: helper; property: "animOpacity"; to: 1; duration: Enums.duration.medium; easing.type: Easing.OutCubic }
    }

    // Close animation. 关闭动画。
    Loader {
        id: closeAnimLoader
        active: false
        sourceComponent: SequentialAnimation {
            ParallelAnimation {
                NumberAnimation { target: targetWindow; property: "opacity"; to: 0; duration: Enums.duration.normal; easing.type: Easing.InCubic }
                NumberAnimation { target: helper; property: "animScale"; to: 0.95; duration: Enums.duration.normal; easing.type: Easing.InCubic }
                NumberAnimation { target: helper; property: "animOpacity"; to: 0; duration: Enums.duration.normal; easing.type: Easing.InCubic }
            }
            ScriptAction { script: onCloseCallback() }
        }
    }

}
