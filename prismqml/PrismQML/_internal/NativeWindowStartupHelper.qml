// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import ".."

// NativeWindowStartupHelper - Optional native startup transaction 可选原生启动事务
Item {
    id: root

    // ==================== Required Props 必需属性 ====================
    required property Window targetWindow
    required property Item animationHelper
    required property bool useNativeShadow

    // ==================== Internal Props 内部属性 ====================
    property bool retryAttempted: false
    property bool readyPublished: false
    property bool showAnimationStarted: false
    property int showAnimationStartCount: 0

    // ==================== Public Methods 公开方法 ====================
    function start() {
        delayTimer.start()
    }

    // ==================== Internal Methods 内部方法 ====================
    function _ensureStartupVisible() {
        if (showAnimationStarted) return
        showAnimationStarted = true
        showAnimationStartCount += 1
        targetWindow.profileTime("animHelper.startShow start")
        animationHelper.startShow()
        targetWindow.profileTime("animHelper.startShow done")
    }
    function _callNativeHook() {
        var nativeHookSucceeded = false
        try {
            if (useNativeShadow && typeof ShadowManager !== "undefined" && ShadowManager) {
                targetWindow.profileTime("ShadowManager.enableShadowForWindow start")
                ShadowManager.enableShadowForWindow(targetWindow)
                targetWindow.profileTime("ShadowManager.enableShadowForWindow done")
            }
            if (typeof NativeWindow !== "undefined" && NativeWindow &&
                    typeof NativeWindow.finalizeAttach === "function") {
                targetWindow.profileTime("NativeWindow.finalizeAttach start")
                nativeHookSucceeded =
                    NativeWindow.finalizeAttach(targetWindow) === true
                targetWindow.profileTime("NativeWindow.finalizeAttach done")
            } else {
                console.warn("NativeWindow.finalizeAttach is unavailable; native effects disabled")
            }
        } catch (error) {
            console.warn("NativeWindow.finalizeAttach raised; native effects disabled:", error)
        }
        return nativeHookSucceeded
    }

    function _publishNativeHookResult(nativeHookSucceeded) {
        if (nativeHookSucceeded) {
            if (!readyPublished) {
                readyPublished = true
                targetWindow.profileTime("nativeHookReady emit start")
                targetWindow.nativeHookReady()
                targetWindow.profileTime("nativeHookReady emit done")
            }
            return
        }

        console.warn("NativeWindow.finalizeAttach failed; native effects disabled")
        if (!retryAttempted) {
            retryAttempted = true
            delayTimer.start()
        }
    }
    function _attemptNativeHook() {
        var nativeHookSucceeded = _callNativeHook()
        targetWindow._dwmInitializationDone = true
        targetWindow.profileTime("DWM initialization attempt marked done")
        // Visibility must complete even when optional native enhancement fails.
        // 即使可选原生增强失败，窗口显示也必须继续。
        _ensureStartupVisible()
        _publishNativeHookResult(nativeHookSucceeded)
    }

    visible: false

    Timer {
        id: delayTimer
        interval: Enums.duration.instant
        onTriggered: root._attemptNativeHook()
    }
}
