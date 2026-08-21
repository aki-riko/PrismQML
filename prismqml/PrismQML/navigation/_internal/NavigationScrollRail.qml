// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "../../controls/containers/ScrollBar"

// NavigationScrollRail - hover-revealed overlay rail for a sidebar viewport
// 悬停显形的侧边栏浮层滚动轨
//
// 与边缘渐隐互补: 渐隐说"还有更多", 轨道说"还有多少、你在哪"。
// Complements the edge fade: the fade says "there is more", the rail says
// "how much more, and where you are".
//
// 轨道是浮层 —— 它绝不能进入布局, 否则会挤压导航项宽度。因此本组件锚在视口
// 之上、与视口同级, 且不声明任何会被父级布局读取的 implicit 尺寸。
// The rail is an overlay: it must never enter layout, or it would squeeze the
// nav items. So it anchors over the viewport as a sibling and declares no
// implicit size that a parent layout could pick up.
Item {
    id: rail

    // ==================== Required Props 必需属性 ====================
    required property Flickable flickable

    // ==================== Public Props 公开属性 ====================
    property bool active: true
    // 悬停整个侧边栏即显形, 而非只悬停轨道本身 —— 否则用户得先找到一条看不见的
    // 细线才能让它出现。Reveal on hovering the whole sidebar, not just the rail;
    // otherwise the user must find an invisible line to make it appear.
    property bool hostHovered: false

    // ==================== Readonly State 只读状态 ====================
    readonly property bool scrollable:
        rail.flickable.contentHeight > rail.flickable.height
    readonly property bool shown:
        rail.active && rail.scrollable && (rail.hostHovered || rail._settling)

    // ==================== Internal Props 内部属性 ====================
    // 滚动刚发生后短暂显形, 让纯滚轮操作也能看到位置反馈。
    // Briefly shown after a scroll, so wheel-only use still gets position feedback.
    property bool _settling: false

    // ==================== Size 尺寸 ====================
    // 只覆盖视口, 不覆盖底部固定项 Covers the viewport only, not the fixed items
    anchors.top: rail.flickable.top
    anchors.bottom: rail.flickable.bottom
    anchors.right: rail.flickable.right
    anchors.rightMargin: Enums.navigationRail.inset
    width: Enums.navigationRail.thickness
    visible: rail.active && rail.scrollable
    opacity: rail.shown
        ? Enums.navigationRail.activeOpacity
        : Enums.navigationRail.idleOpacity

    Behavior on opacity {
        NumberAnimation {
            duration: rail.shown
                ? Enums.navigationRail.revealDuration
                : Enums.navigationRail.hideDuration
            easing.type: Easing.OutCubic
        }
    }

    // ==================== Content 内容 ====================
    ScrollBar {
        id: bar
        objectName: "navigationScrollRailBar"
        anchors.fill: parent
        target: rail.flickable
        barWidth: Enums.navigationRail.thickness
    }

    // 静止一段时间后退隐 Retreat once scrolling has settled
    Timer {
        id: idleTimer
        objectName: "navigationScrollRailIdleTimer"
        interval: Enums.navigationRail.idleDelay
        onTriggered: rail._settling = false
    }

    Connections {
        function onContentYChanged() {
            if (!rail.active || !rail.scrollable) return
            rail._settling = true
            idleTimer.restart()
        }

        target: rail.flickable
    }
}
