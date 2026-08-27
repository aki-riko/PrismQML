// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// SmoothScrollOvershootGuard - Owns one axis' outward-leg interruption state
// SmoothScrollOvershootGuard - 持有单轴外移腿中断状态
// A view clamps an out-of-bounds contentX/Y whenever its own bounds change while
// the axis is overshooting. The guard adopts that clamp instead of fighting it,
// and keeps the same boundary from relaunching an outward leg during the same
// continuous input burst.
// 轴向超出期间视图自身边界变化会夹掉越界 contentX/Y。门闸接管该夹紧而非与之对抗，
// 并禁止同一边界在同一连续输入串中再次外移。
QtObject {
    id: guard

    // ==================== Required Props 必需属性 ====================
    required property var scrollHelper
    required property bool verticalAxis

    // ==================== Internal Props 内部属性 ====================
    // Boundary whose overshoot the view already clamped away 视图已夹掉超出的边界
    // -1=start, 0=none, 1=end
    property int revokedBoundary: 0
    // Boundary the in-flight outward bounce belongs to 进行中外移回弹所属边界
    property int outwardBoundary: 0
    property double lastRelativeScrollTimestamp: 0

    // ==================== Public Methods 公开方法 ====================
    function reset() {
        revokedBoundary = 0
    }

    // True when someone else moved the view back inside its own bounds.
    // 当他人把视图移回自身合法区间时为真。
    function isRevoked(current, lastPublished, minimum, maximum) {
        var epsilon = Enums.scroll.revocation_epsilon
        if (Math.abs(current - lastPublished) <= epsilon) return false
        return current >= minimum - epsilon && current <= maximum + epsilon
    }

    // The guard covers one continuous input burst, so an idle gap re-arms overshoot.
    // 门闸只覆盖一次连续输入串，空闲间隙后重新武装超出。
    function noteRelativeScroll() {
        var now = Date.now()
        if (revokedBoundary !== 0
                && now - lastRelativeScrollTimestamp > Enums.scroll.input_burst_gap) {
            revokedBoundary = 0
        }
        lastRelativeScrollTimestamp = now
    }

    function blocksBoundary(atStartBoundary) {
        return revokedBoundary === (atStartBoundary ? -1 : 1)
    }

    // True when this frame belongs to the guard instead of the publisher: either
    // the view clamped the axis back inside its bounds, or the whole outward
    // window elapsed without a frame and the catch-up peak must not be published.
    // 本帧归门闸而非发布者时为真：视图已把轴夹回合法区间，或整段外移窗口无帧、
    // 补算峰值不得发布。
    function consumesFrame(current, lastPublished, minimum, maximum,
                           overshot, outward, lastFrameTimestamp) {
        if (overshot && isRevoked(current, lastPublished, minimum, maximum)) {
            interruptOutwardLeg(current, true)
            return true
        }
        if (outward && lastFrameTimestamp > 0
                && Date.now() - lastFrameTimestamp >= Enums.duration.fast) {
            interruptOutwardLeg(lastPublished, false)
            return true
        }
        return false
    }

    // Cut the outward leg short at position, then run the normal return from
    // there. 在 position 处截断外移腿，并从该处执行正常回弹。
    function interruptOutwardLeg(position, markRevoked) {
        if (markRevoked) revokedBoundary = outwardBoundary
        var driver = verticalAxis
            ? scrollHelper.verticalFrameDriver : scrollHelper.horizontalFrameDriver
        if (verticalAxis) scrollHelper._discardingStaleFrameV = true
        else scrollHelper._discardingStaleFrameH = true
        scrollHelper._stopBounceTimer(verticalAxis)
        scrollHelper._syncing = true
        driver.moveTo(position)
        scrollHelper._syncing = false
        if (verticalAxis) {
            scrollHelper._lastPublishedY = position
            scrollHelper._discardingStaleFrameV = false
            scrollHelper._bounceBackV()
        } else {
            scrollHelper._lastPublishedX = position
            scrollHelper._discardingStaleFrameH = false
            scrollHelper._bounceBackH()
        }
    }

    objectName: verticalAxis
        ? "smoothScrollVerticalOvershootGuard"
        : "smoothScrollHorizontalOvershootGuard"
}
