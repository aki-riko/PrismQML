// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../controls/feedback/SplashScreen"

// NavigationDefaultSplash - Default navigation startup visual 导航窗口默认启动视觉
SplashScreen {
    required property var hostWindow

    iconSource: hostWindow.splashIcon !== "" ? hostWindow.splashIcon : hostWindow.windowIcon
    title: hostWindow.splashTitle !== "" ? hostWindow.splashTitle : hostWindow.windowTitle
    subtitle: hostWindow.splashSubtitle
    revealDuration: hostWindow.splashRevealDuration
}
