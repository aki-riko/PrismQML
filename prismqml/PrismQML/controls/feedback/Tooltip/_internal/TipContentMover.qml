// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// TipContentMover - Moves caller content into the native tip surface 把调用方内容搬进原生提示弹层
//
// Caller content is collected by the TipPopup's `default property alias` into a
// staging Item, so the staging area — not the popup itself — owns it visually.
// A TipPopup is an invisible Item and the content has to be rendered by the native
// surface, so the staged children are reparented into that surface once it exists.
// Assigning a QQmlListProperty across windows does not move any object, which is why
// this has to be an explicit reparent.
//
// 调用方内容由 TipPopup 的 `default property alias` 收进暂存 Item,因此它的视觉父对象是
// 暂存区而不是弹层本身。TipPopup 是不可见的 Item,内容必须由原生弹层来渲染,所以在这个
// 弹层就绪后把暂存区里的子项重新挂进去。跨窗口直接赋值 QQmlListProperty 不会搬运任何
// 对象,因此必须显式 reparent。
QtObject {
    id: mover

    // ==================== Required Props 必需属性 ====================
    // Staging Item holding the caller-supplied declarative children
    // 存放调用方声明式子项的暂存 Item
    required property var staging
    // The native surface holding the content host, or null before it exists
    // 承载内容宿主的原生弹层,未创建时为 null
    required property var surface

    // ==================== Public Methods 公开方法 ====================
    // Move every staged child into the surface content host. Safe to call
    // repeatedly: already-moved children are no longer staged.
    // 把暂存区里的子项全部搬进弹层内容宿主。可重复调用:已搬走的子项不再留在暂存区。
    function moveContent() {
        var host = surface ? surface.customContentHost : null
        if (!host) return
        var staged = staging.children
        for (var i = staged.length - 1; i >= 0; --i) {
            staged[i].parent = host
        }
    }
}
