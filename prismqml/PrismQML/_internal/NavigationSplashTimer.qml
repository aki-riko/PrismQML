// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."

// NavigationSplashTimer - Shared timeout and minimum-visibility timer
// NavigationSplashTimer - 欢迎页超时与最短可见时长复用计时器
Timer {
    id: splashTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    // ==================== Internal Props 内部属性 ====================
    property bool _minimumVisiblePhase: false
    property int _minimumVisibleInterval: Enums.duration.splashMinimumVisible
    property var _onTimeout: null

    interval: _minimumVisiblePhase
              ? _minimumVisibleInterval : Enums.duration.splashTimeout
    onTriggered: {
        if (_minimumVisiblePhase) host._scheduleSplashDismiss()
        else if (_onTimeout) _onTimeout()
    }
}
