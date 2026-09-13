// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../../SkinResolver.js" as SkinResolver

// OverlayDialogSkinContext - Preserves dialog skin across reparenting 对话框重挂载时保持局部皮肤
QtObject {
    id: context

    // ==================== Required Props 必需属性 ====================
    required property var host

    // ==================== Public Props 公开属性 ====================
    property var skinContext: null

    // ==================== Internal Props 内部属性 ====================
    property var capturedSkinContext: null

    // ==================== Readonly State 只读状态 ====================
    readonly property var nearestSkinContext:
        (skinContext || capturedSkinContext)
        ? null : SkinResolver.nearestContext(host.parent)
    readonly property var effectiveSkinContext:
        skinContext || capturedSkinContext || nearestSkinContext || Enums
    readonly property var prismSkinScopeContext:
        skinContext || capturedSkinContext || null
    readonly property var skin: effectiveSkinContext
}
