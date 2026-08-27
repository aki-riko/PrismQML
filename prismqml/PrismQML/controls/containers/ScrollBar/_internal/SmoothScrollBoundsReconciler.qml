// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// SmoothScrollBoundsReconciler - Realigns one axis after its bounds moved
// SmoothScrollBoundsReconciler - 边界移动后重新对齐单轴
// ListView/GridView may change origin and content size while delegates are
// recycled, so the animated value and the target must return to the legal range.
// ListView/GridView 复用 delegate 时可能改变 origin 与内容尺寸，动画值与目标必须回到合法区间。
QtObject {
    id: reconciler

    // ==================== Required Props 必需属性 ====================
    required property var scrollHelper

    // ==================== Public Methods 公开方法 ====================
    function reconcile(verticalAxis) {
        var owner = scrollHelper
        if (!owner.target) return
        var minimum = verticalAxis ? owner._minY : owner._minX
        var maximum = verticalAxis ? owner._maxY : owner._maxX
        var driver = verticalAxis
            ? owner.verticalFrameDriver : owner.horizontalFrameDriver
        var boundaryTarget = verticalAxis
            ? owner._boundaryTargetV : owner._boundaryTargetH
        var overshot = verticalAxis ? owner._isOvershotV : owner._isOvershotH
        var currentTarget = verticalAxis ? owner._targetY : owner._targetX
        var currentSmooth = verticalAxis ? owner._smoothY : owner._smoothX

        // Idle axis simply adopts the view's own clamped position.
        // 空闲轴直接接管视图自身的夹紧位置。
        if (boundaryTarget === 0 && !driver.running && !overshot) {
            var adopted = owner._clamp(
                verticalAxis ? owner.target.contentY : owner.target.contentX,
                minimum, maximum
            )
            if (adopted === currentTarget && adopted === currentSmooth) return
            owner._syncing = true
            _setTarget(verticalAxis, adopted)
            driver.moveTo(adopted)
            owner._syncing = false
            return
        }

        // An outward bounce is deliberately out of bounds. Only re-aim its return
        // target at the current boundary; clamping the live value here would be a
        // second correction path fighting the bounce.
        // 外移回弹是有意越界，此处仅把回弹目标重新对准当前边界；夹紧实时值会形成与回弹对抗的第二条校正路径。
        var guard = verticalAxis
            ? owner.verticalOvershootGuard : owner.horizontalOvershootGuard
        if (verticalAxis ? owner._isOutwardBounceV : owner._isOutwardBounceH) {
            _setTarget(verticalAxis, guard.outwardBoundary < 0 ? minimum : maximum)
            return
        }

        var nextTarget = boundaryTarget < 0
            ? minimum
            : (boundaryTarget > 0
                ? maximum : owner._clamp(currentTarget, minimum, maximum))
        var nextSmooth = owner._clamp(currentSmooth, minimum, maximum)
        if (nextTarget === currentTarget && nextSmooth === currentSmooth) return
        if (verticalAxis) {
            owner._isOvershotV = false
            owner._isOutwardBounceV = false
        } else {
            owner._isOvershotH = false
            owner._isOutwardBounceH = false
        }
        owner._stopBounceTimer(verticalAxis)
        _setTarget(verticalAxis, nextTarget)
        if (nextSmooth !== currentSmooth) {
            owner._syncing = true
            driver.moveTo(nextSmooth)
            owner._syncing = false
        }
        var settledTarget = verticalAxis ? owner._targetY : owner._targetX
        if ((verticalAxis ? owner._smoothY : owner._smoothX) !== settledTarget) {
            driver.moveTo(settledTarget)
        }
    }

    // ==================== Internal Methods 内部方法 ====================
    function _setTarget(verticalAxis, value) {
        if (verticalAxis) scrollHelper._targetY = value
        else scrollHelper._targetX = value
    }

    objectName: "smoothScrollBoundsReconciler"
}
