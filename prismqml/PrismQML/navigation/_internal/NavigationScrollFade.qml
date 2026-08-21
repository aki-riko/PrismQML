// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."

// NavigationScrollFade - Edge fade hint for scrollable navigation panels 可滚动导航面板的边缘渐隐提示
// Ramps each item's real opacity near whichever edge still has overflow, so the
// hint survives Mica/transparent backgrounds that defeat colored overlays.
// 按实际 opacity 对仍有溢出的那一端做斜坡，因此在遮盖层失效的 Mica/透明背景下依然可见。
QtObject {
    id: fade

    // ==================== Required Props 必需属性 ====================
    required property Flickable flickable

    // ==================== Public Props 公开属性 ====================
    property bool active: true
    // Item height the band is measured in; hosts pass their delegate height.
    // 渐隐带以此项高为单位度量；宿主传入自身委托高度。
    property real itemHeight: Enums.controlSize.navItemHeight
    // Scrollable-item count; hosts bind their top Repeater's count so
    // selectionOpacity() re-evaluates once the Repeater is populated.
    // 可滚动项数量; 宿主绑定顶部 Repeater 的 count, 使 selectionOpacity() 在
    // Repeater 填充后重新求值。
    property int itemCount: 0

    // ==================== Readonly State 只读状态 ====================
    readonly property bool scrollable:
        fade.flickable.contentHeight > fade.flickable.height
    // Band must span several items, otherwise the per-item ramp collapses into
    // a single step and reads as a hard cut rather than a fade.
    // 渐隐带必须跨多项，否则逐项斜坡退化为单一档位，看起来是硬切而非渐隐。
    readonly property real band: fade.itemHeight * Enums.navigationFade.bandItems
    readonly property bool fadeTop: fade.active && fade.scrollable && !fade.atTop
    readonly property bool fadeBottom:
        fade.active && fade.scrollable && !fade.atBottom
    readonly property bool atTop: fade.flickable.contentY <= fade.flickable.originY
    readonly property bool atBottom:
        fade.flickable.contentY
        >= fade.flickable.originY
           + Math.max(0, fade.flickable.contentHeight - fade.flickable.height)

    // ==================== Public Methods 公开方法 ====================
    // Opacity for an item spanning [itemY, itemY + itemH) in content coordinates.
    // 内容坐标中占据 [itemY, itemY + itemH) 的项应有的透明度。
    function opacityAt(itemY, itemH) {
        var full = Enums.navigationFade.maxOpacity
        if (!fade.active || !fade.scrollable || fade.band <= 0) return full

        // Ramp on the item centre so entering and leaving items mirror each other.
        // 按项中心取斜坡，使进入与离开的项互为镜像。
        var centre = itemY + itemH / 2 - fade.flickable.contentY
        var factor = full
        if (fade.fadeTop && centre < fade.band) {
            factor = Math.min(factor, Math.max(0, centre) / fade.band)
        }
        var bottomRoom = fade.flickable.height - centre
        if (fade.fadeBottom && bottomRoom < fade.band) {
            factor = Math.min(factor, Math.max(0, bottomRoom) / fade.band)
        }

        var floor = Enums.navigationFade.minOpacity
        return Math.max(floor, Math.min(full, factor))
    }

    // Opacity for an item, resolved from the item itself. 直接由项自身解析透明度。
    function opacityForItem(item) {
        if (!item) return Enums.navigationFade.maxOpacity
        return fade.opacityAt(item.y, item.height)
    }

    // Opacity for the selected item, used to keep an indicator that lives outside
    // the viewport in lockstep with the item it marks.
    // 选中项的透明度; 用于让视口之外的指示器与其所标记的项锁步渐隐。
    function selectionOpacity(item, eligible) {
        // 无条件先读填充与布局信号: itemAt() 是命令式取值, 不登记依赖。若宿主在
        // Repeater 尚空时求值一次, 其绑定会永久锁死在满值。
        // Read population/layout signals unconditionally; itemAt() registers no
        // dependency, so an early empty-Repeater pass would latch the binding.
        var ready = fade.itemCount > 0 && fade.flickable.contentHeight > 0
        if (!ready || !eligible) return Enums.navigationFade.maxOpacity
        return fade.opacityForItem(item)
    }
}
