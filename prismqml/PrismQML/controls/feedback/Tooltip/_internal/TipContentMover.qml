// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// TipContentMover - Moves caller content into the native tip surface 把调用方内容搬进原生提示弹层
//
// Declarative children of a TipPopup end up parented to the TipPopup itself, not to
// a nested container: `default property alias x: inner.data` does not reparent them
// (verified against Card and SettingsCardGroup too). A TipPopup is an invisible Item,
// so leaving them there renders nothing. They therefore have to be reparented into
// the native window, and assigning a QQmlListProperty across windows does not move
// any object — hence this explicit mover.
//
// TipPopup 的声明式子项实际会挂在 TipPopup 自身而不是嵌套容器里:`default property
// alias x: inner.data` 不会搬运它们(对 Card / SettingsCardGroup 实测同样如此)。而
// TipPopup 是不可见的 Item,留在原处等于什么都不显示,必须重新挂到原生窗口里;跨窗口
// 直接赋值 QQmlListProperty 又不会搬运任何对象,所以由本组件显式搬运。
//
// Internal children are recognised by objectName: everything else that is still
// parented to the control counts as caller content. Adding a new *visual* internal
// child means registering its objectName here, and the architecture contract test
// fails otherwise.
// 内部子项按 objectName 识别:其余仍挂在 control 下的都算调用方内容。新增"可视"内部
// 子项必须在这里登记 objectName,否则架构合同测试会失败。
QtObject {
    id: mover

    // ==================== Required Props 必需属性 ====================
    // The TipPopup that owns the declarative children 承载声明式子项的 TipPopup
    required property var control
    // The native surface holding the content host, or null before it exists
    // 承载内容宿主的原生弹层,未创建时为 null
    required property var surface

    // ==================== Internal Props 内部属性 ====================
    // Visual internal children that must stay parented to the control.
    // 必须留在 control 名下的可视内部子项。
    readonly property var internalNames: [
        "tipPopupWindowLoader",
        "tipArrowWindowLoader",
        "tipPositionTracker"
    ]

    // ==================== Public Methods 公开方法 ====================
    // Move every caller-supplied child into the surface content host. Safe to call
    // repeatedly: already-moved children no longer report the control as parent.
    // 把所有调用方子项搬进弹层内容宿主。可重复调用:已搬走的子项不再以 control 为父。
    function moveContent() {
        var host = surface ? surface.customContentHost : null
        if (!host) return
        var children = control.children
        for (var i = children.length - 1; i >= 0; --i) {
            var child = children[i]
            if (internalNames.indexOf(child.objectName) >= 0) continue
            if (child.parent !== control) continue
            child.parent = host
        }
    }
}
