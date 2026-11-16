// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../../effects"

// ButtonNeumorphicShadow - Button face neumorphic shadow, loaded by URL 按钮面新拟态阴影，按 URL 加载
// Loaded through Loader.source rather than an inline Component: an inline block would
// add a resident QQmlComponent to every button. The host is read from the Loader.
// 通过 Loader.source 加载而非内联 Component：内联块会给每个按钮常驻一个 QQmlComponent。
// 宿主从 Loader 读取。
NeumorphicShadow {
    id: shadow

    // ==================== Readonly State 只读状态 ====================
    readonly property var _surfaceHost: parent ? parent.surfaceHost : null

    target: _surfaceHost ? _surfaceHost.background : null
    inset: _surfaceHost ? _surfaceHost.buttonControl.pressed : false
    pressed: _surfaceHost ? _surfaceHost.buttonControl.pressed : false
}
