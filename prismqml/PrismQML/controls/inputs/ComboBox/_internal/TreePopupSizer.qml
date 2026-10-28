// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../../.."
import QtQuick  // After library import: unprefixed native types stay unshadowed 置于库import后:去前缀后保原生类型不被库覆盖

// TreePopupSizer - Content-driven popup height for tree dropdowns 树形下拉的弹层高度
// Single owner of "how tall should the tree popup be and how does it get there".
// ComboBoxTree and ComboBoxMultiTree differ only in their rows, so the height math,
// the growth animation and the native-window follow-up live here once.
// 树形下拉「弹层该多高、怎么长过去」的唯一归属。单树与多选树只在行内容上不同,
// 因此高度算法、生长动画与原生窗口跟随只在这里实现一次。
QtObject {
    id: sizer

    // ==================== Required Props 必需属性 ====================
    required property var host  // ComboBoxCore subclass 下拉控件

    // ==================== Public Props 公开属性 ====================
    property int itemCount: 0
    property bool searchEnabled: true
    property real animatedContentHeight: 0

    // ==================== Readonly State 只读状态 ====================
    readonly property bool running: heightAnimation ? heightAnimation.running : false

    // ==================== Public Methods 公开方法 ====================
    /// 按当前行数重算目标高度：展开/收窄时开始/打断高度动画。
    function update() {
        var searchHeight = searchEnabled ? Enums.comboBoxMetrics.searchBoxHeight : 0
        var targetHeight = Math.min(
            itemCount * Enums.comboBoxMetrics.itemHeight + searchHeight,
            Math.max(0, Enums.comboBoxMetrics.treePopupHeight
                - 2 * host._popup.contentPadding))
        heightAnimation.stop()
        if (!host.isOpen || animatedContentHeight === targetHeight) {
            animatedContentHeight = targetHeight
            return
        }
        heightAnimation.from = animatedContentHeight
        heightAnimation.to = targetHeight
        heightAnimation.start()
    }

    /// 高度变化后让原生弹层窗口跟着长/缩，并按屏幕可用区夹紧位置。
    /// 高度动画逐帧触发，所以这里必须是廉价的几何同步，不能重建表面。
    function syncOpenGeometry() {
        host._popup.stabilizeInteraction()
        host._popup._clipHeight = host._popup.popupHeight
        var popupWindow = host._popup._popupWindow
        if (!popupWindow) return
        popupWindow.width = host._popup._outerWidth
        popupWindow.height = host._popup._outerHeight
        host._popup._applyTrackedPosition(host.mapToGlobal(0, 0))
        var bounds = host._popup._screenBoundsAt(popupWindow.x, popupWindow.y, host)
        if (!bounds) return
        popupWindow.x = Math.max(
            bounds.left,
            Math.min(popupWindow.x, bounds.right - host._popup._outerWidth)
        )
        popupWindow.y = Math.max(
            bounds.top,
            Math.min(popupWindow.y, bounds.bottom - host._popup._outerHeight)
        )
    }

    // ==================== Content 内容 ====================
    onAnimatedContentHeightChanged: {
        host._popup.implicitContentHeight = Math.round(animatedContentHeight)
        if (host.isOpen) syncOpenGeometry()
    }

    // QtObject 没有 default property，动画只能作为属性持有
    property NumberAnimation heightAnimation: NumberAnimation {
        target: sizer
        property: "animatedContentHeight"
        duration: Enums.duration.fast
        easing.type: Easing.OutCubic
    }
}
