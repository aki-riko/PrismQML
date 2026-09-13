// PopupSkinContext - Popup-local appearance context bridge 弹层局部外观上下文桥
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../../SkinResolver.js" as SkinResolver

// PopupSkinContext - Resolves popup appearance before its surface leaves the
// originating visual tree. 弹层表面离开来源视觉树前解析其外观上下文。
QtObject {
    id: state

    // ==================== Required Props 必需属性 ====================
    required property Item host

    // ==================== Public Props 公开属性 ====================
    property var skinContext: null
    readonly property var targetSkinContext:
        (skinContext || !host || !host.targetControl)
        ? null : host.targetControl.effectiveSkinContext
    readonly property var nearestSkinContext:
        (skinContext || targetSkinContext)
        ? null : SkinResolver.nearestContext(host ? host.parent : null)
    readonly property var effectiveSkinContext:
        skinContext || targetSkinContext || nearestSkinContext || Enums

}
