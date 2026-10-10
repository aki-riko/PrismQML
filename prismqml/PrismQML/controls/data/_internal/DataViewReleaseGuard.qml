// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import QtQuick  // After library import: unprefixed native types stay unshadowed 置于库import后:去前缀后保原生类型不被库覆盖

// DataViewReleaseGuard - Hides rows released after a cancelled exit transition
// 数据视图退场兜底 - 隐藏退场过渡被取消后释放的行
//
// A follow-up model change cancels the exit transition, and Qt then releases the row without
// resetting its opacity, so the row keeps showing at a partial opacity. This guard re-checks
// after the exit transition should have finished and hides every row the view no longer owns.
// 后续模型变化会取消退场过渡，Qt 释放该行时不会重置 opacity，该行会以半透明状态继续显示。
// 本兜底在退场过渡应已结束之后复查，并隐藏视图已不再持有的行。
QtObject {
    id: guard

    // ==================== Required Props 必需属性 ====================
    required property var view

    // ==================== Public Props 公开属性 ====================
    // Keep the guard inert while the owning view has its transitions disabled.
    // 拥有者关闭过渡动画时兜底保持惰性。
    property bool active: true

    // ==================== Internal Methods 内部方法 ====================
    function hideReleasedRows() {
        var layer = view.contentItem
        if (!layer) return
        var liveItems = []
        for (var liveIndex = 0; liveIndex < view.count; ++liveIndex) {
            var liveItem = view.itemAtIndex(liveIndex)
            if (liveItem) liveItems.push(liveItem)
        }
        var children = layer.children
        for (var childIndex = 0; childIndex < children.length; ++childIndex) {
            var child = children[childIndex]
            if (liveItems.indexOf(child) >= 0) continue
            if (child.opacity > 0) child.opacity = 0
        }
    }

    // ==================== Content 内容 ====================
    property Timer releaseTimer: Timer {
        interval: Enums.duration.exit + Enums.duration.fast
        onTriggered: guard.hideReleasedRows()
    }

    property Connections countWatcher: Connections {
        target: guard.view

        function onCountChanged() {
            if (guard.active) guard.releaseTimer.restart()
        }
    }
}
