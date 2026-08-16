// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// SmoothScrollBoundsReconcileTimer - Reconcile one scroll axis after bounds changes
// SmoothScrollBoundsReconcileTimer - 边界变化后校准一个滚动轴
Timer {
    id: reconcileTimer

    // ==================== Required Props 必需属性 ====================
    required property var scrollHelper
    required property bool verticalAxis

    objectName: verticalAxis
        ? "smoothScrollVerticalReconcileTimer"
        : "smoothScrollHorizontalReconcileTimer"
    interval: Enums.duration.instant
    repeat: false
    onTriggered: {
        if (verticalAxis) scrollHelper._reconcileVerticalBounds()
        else scrollHelper._reconcileHorizontalBounds()
    }
}
