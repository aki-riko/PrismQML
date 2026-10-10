// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// WindowsCoreMirroring - Window-level RTL mirroring 窗口级 RTL 镜像
// Right-to-left scripts mirror the whole window: Qt propagates the attached
// property to every child, so surfaces do not each hand-roll a mirrored layout.
// Left-to-right resolves to false and leaves the historical geometry untouched.
// 从右到左的文字会镜像整个窗口：Qt 会把附加属性传播到所有子项，因此各表面无需
// 各自手写镜像布局。从左到右解析为 false，既有几何完全不变。
//
// The host declares this and binds both properties; keeping the mirroring in one
// owner is what keeps WindowsCore inside its size gate.
// 宿主声明本对象并绑定两个属性；镜像逻辑单独归属使 WindowsCore 保持在体积门禁内。
QtObject {
    id: mirroring

    // ==================== Required Props 必需属性 ====================
    required property Item host
    // Language-derived direction, resolved once by the shared enum entry point.
    // 由语言派生的文字方向，由共享枚举入口解析一次。
    required property bool rightToLeft

    // ==================== Public Props 公开属性 ====================
    // A binding rather than a one-shot assignment, so switching the language at
    // runtime re-mirrors the window.
    // 使用绑定而非一次性赋值，因此运行时切换语言会重新镜像窗口。
    property bool enabled: rightToLeft
    onEnabledChanged: mirroring.host.LayoutMirroring.enabled = mirroring.enabled
    Component.onCompleted: mirroring.host.LayoutMirroring.enabled = mirroring.enabled
}
