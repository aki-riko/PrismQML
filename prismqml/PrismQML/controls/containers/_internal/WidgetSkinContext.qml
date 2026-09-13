// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../../SkinResolver.js" as SkinResolver

// WidgetSkinContext - Resolves the nearest widget skin scope 控件局部皮肤范围解析器
QtObject {
    id: context

    // ==================== Required Props 必需属性 ====================
    required property var host

    // ==================== Public Props 公开属性 ====================
    property var skinContext: null

    // ==================== Readonly State 只读状态 ====================
    readonly property var nearestSkinContext: skinContext
        ? null : SkinResolver.nearestContext(host.parent)
    readonly property var effectiveSkinContext:
        skinContext || nearestSkinContext || Enums
    readonly property var prismSkinScopeContext: skinContext || null
}
