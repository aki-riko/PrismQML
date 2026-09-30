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

    // True when the view declares it accepts going out of bounds. Such a target
    // re-measures its own content (async delegates, recycled rows) and writes the axis
    // back inside the bounds to keep its position; treating that write as a rejection
    // permanently cancels the bounce for the rest of the input burst.
    // 视图声明允许越界时返回真。这类目标会自行重测内容（异步委托、回收行）并把轴写回
    // 合法区间以维持位置；把该写入当成拒绝，会在整个输入串内永久取消回弹。
    function allowsOvershoot() {
        if (!scrollHelper.target
                || scrollHelper.target.boundsBehavior === undefined) return false
        return (scrollHelper.target.boundsBehavior & Flickable.DragAndOvershootBounds)
            === Flickable.DragAndOvershootBounds
    }

    // True when this frame belongs to the guard instead of the publisher: either
    // the view clamped the axis back inside its bounds, or the whole outward
    // window elapsed without a frame and the catch-up peak must not be published.
    // 本帧归门闸而非发布者时为真：视图已把轴夹回合法区间，或整段外移窗口无帧、
    // 补算峰值不得发布。
    function consumesFrame(current, lastPublished, minimum, maximum,
                           overshot, outward, lastFrameTimestamp) {
        if (overshot && isRevoked(current, lastPublished, minimum, maximum)) {
            if (allowsOvershoot()) adoptOvershootFrame(current)
            else interruptOutwardLeg(current, true)
            return true
        }
        if (outward && lastFrameTimestamp > 0
                && Date.now() - lastFrameTimestamp >= Enums.duration.fast) {
            interruptOutwardLeg(lastPublished, false)
            return true
        }
        return false
    }

    // A view that supports overshoot is not rejecting our excursion by re-laying out;
    // it is only keeping its own position. Take its write as this frame's value, keep
    // the boundary armed for the burst, and let the next frame publish the excursion
    // again. A view that stops at bounds keeps the strict revoke above.
    // 支持越界的视图重新布局并不是在拒绝我们的位移，只是在维持自身位置。把它的写入当成本帧
    // 取值，本输入串内继续保持边界武装，下一帧重新发布该位移。禁止越界的视图仍走上面的严格撤销。
    function adoptOvershootFrame(current) {
        if (verticalAxis) {
            scrollHelper._lastPublishedY = current
            scrollHelper._lastBounceFrameTimestampV = Date.now()
        } else {
            scrollHelper._lastPublishedX = current
            scrollHelper._lastBounceFrameTimestampH = Date.now()
        }
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
