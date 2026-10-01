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
    property real outwardEdgePosition: 0
    property double lastRelativeScrollTimestamp: 0

    // ==================== Public Methods 公开方法 ====================
    function reset() {
        revokedBoundary = 0
        outwardBoundary = 0
        outwardEdgePosition = 0
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

    function beginOutwardLeg(boundary, edge) {
        outwardBoundary = boundary
        outwardEdgePosition = edge
    }

    function constrainOutwardValue(value) {
        var outward = verticalAxis
            ? scrollHelper._isOutwardBounceV : scrollHelper._isOutwardBounceH
        if (!outward) return value
        var minimum = verticalAxis ? scrollHelper._minY : scrollHelper._minX
        var maximum = verticalAxis ? scrollHelper._maxY : scrollHelper._maxX
        return scrollHelper._clamp(
            value,
            minimum - scrollHelper._maxOvershoot,
            maximum + scrollHelper._maxOvershoot
        )
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
        return scrollHelper.target.boundsBehavior !== Flickable.StopAtBounds
    }

    // True when this frame belongs to the guard instead of the publisher: either
    // the view clamped the axis back inside its bounds, or the whole outward
    // window elapsed without a frame and the catch-up peak must not be published.
    // 本帧归门闸而非发布者时为真：视图已把轴夹回合法区间，或整段外移窗口无帧、
    // 补算峰值不得发布。
    function consumesFrame(current, lastPublished, minimum, maximum,
                           overshot, outward, lastFrameTimestamp) {
        if (overshot && isRevoked(current, lastPublished, minimum, maximum)) {
            if (allowsOvershoot() && outward
                    && isAtOutwardBoundary(current, minimum, maximum)) {
                rebaseOutwardFrame(current, minimum, maximum, true)
            } else {
                interruptOutwardLeg(current, !allowsOvershoot())
            }
            return true
        }
        if (outward && lastFrameTimestamp > 0
                && Date.now() - lastFrameTimestamp >= Enums.duration.fast) {
            interruptOutwardLeg(lastPublished, false)
            return true
        }
        return false
    }

    function isAtOutwardBoundary(current, minimum, maximum) {
        var boundary = outwardBoundary < 0 ? minimum : maximum
        return Math.abs(current - boundary) <= Enums.scroll.revocation_epsilon
    }

    // A supported view may re-anchor an outward leg when its bounds move. Preserve
    // the requested overshoot relative to the new edge and cap it to the configured limit.
    // 允许越界的视图移动边界时可重锚外移腿；相对新边缘保留原越界意图并限制在配置上限内。
    // The axis is always re-anchored on the live animation value: a view that writes
    // the outward edge back is restoring its own position, not rejecting our
    // overshoot, and adopting that edge would restart the leg from zero every layout
    // pass. See _rebaseLiveOutwardLeg.
    // 轴一律重锚到实时动画值：把外移边缘写回来的视图只是在恢复自身位置，并不是拒绝我们的
    // 超出；采纳该边缘会让外移腿每次布局都从零重启。详见 _rebaseLiveOutwardLeg。
    function rebaseOutwardFrame(current, minimum, maximum, force) {
        var edge = outwardBoundary < 0 ? minimum : maximum
        if (outwardBoundary === 0 || (!force && edge === outwardEdgePosition)) return
        var driver = verticalAxis
            ? scrollHelper.verticalFrameDriver : scrollHelper.horizontalFrameDriver
        var previousTarget = driver._toValue
        var previousOvershoot = Math.max(
            0, outwardBoundary * (previousTarget - outwardEdgePosition)
        )
        var nextTarget = edge + outwardBoundary
            * Math.min(previousOvershoot, scrollHelper._maxOvershoot)
        outwardEdgePosition = edge
        _rebaseLiveOutwardLeg(nextTarget)
    }

    // Re-anchor the axis on the live animation value rather than on the value the
    // view wrote. A re-measuring view only restores its own position; the excursion
    // is still in flight, so adopting the view's edge restarts the leg from zero on
    // every layout pass and the bounce never develops (measured 7px of a requested
    // 72px on a real chat list). Re-publishing the live value in this same turn keeps
    // the view's write from rendering, and the leg keeps its progress.
    // 把轴重锚到实时动画值，而不是视图写入的值。重测中的视图只是在恢复自身位置，位移仍在进行；
    // 采纳视图的边缘值会让外移腿每次布局都从零重启，回弹永远长不出来（真实聊天列表实测只有
    // 请求 72px 中的 7px）。在同一轮内重新发布实时值可让视图的写入不被渲染，外移腿保住进度。
    function _rebaseLiveOutwardLeg(nextTarget) {
        var driver = verticalAxis
            ? scrollHelper.verticalFrameDriver : scrollHelper.horizontalFrameDriver
        var minimum = verticalAxis ? scrollHelper._minY : scrollHelper._minX
        var maximum = verticalAxis ? scrollHelper._maxY : scrollHelper._maxX
        var live = scrollHelper._clamp(
            verticalAxis ? scrollHelper._smoothY : scrollHelper._smoothX,
            minimum - scrollHelper._maxOvershoot,
            maximum + scrollHelper._maxOvershoot
        )
        // Rebase publication follows the same pixel and visual-layer rules as a frame.
        // 重锚发布必须遵循与逐帧发布相同的像素对齐和视觉位移层规则。
        var published = scrollHelper._publishedPosition(live, minimum, maximum)
        var contentPosition = scrollHelper._visualOvershootEnabled
            ? scrollHelper._clamp(published, minimum, maximum) : published
        if (verticalAxis) {
            scrollHelper._discardingStaleFrameV = true
            scrollHelper._lastPublishedY = contentPosition
        } else {
            scrollHelper._discardingStaleFrameH = true
            scrollHelper._lastPublishedX = contentPosition
        }
        if (scrollHelper.target) {
            if (verticalAxis && scrollHelper.target.contentY !== contentPosition)
                scrollHelper.target.contentY = contentPosition
            else if (!verticalAxis && scrollHelper.target.contentX !== contentPosition)
                scrollHelper.target.contentX = contentPosition
        }
        if (verticalAxis) scrollHelper._discardingStaleFrameV = false
        else scrollHelper._discardingStaleFrameH = false
        // Only re-aim when the edge actually moved; otherwise the running animation
        // is already heading for the right target and must not be restarted.
        // 仅当边缘真的移动时才重新瞄准；否则进行中的动画已朝正确目标前进，不得重启。
        if (driver._toValue !== nextTarget) driver.moveTo(nextTarget)
    }

    function rebaseReturnFrame(current, minimum, maximum, returnEdge) {
        var position = scrollHelper._clamp(
            current,
            minimum - scrollHelper._maxOvershoot,
            maximum + scrollHelper._maxOvershoot
        )
        _applyPositionRebase(position, returnEdge)
    }

    function _applyPositionRebase(position, nextTarget) {
        var driver = verticalAxis
            ? scrollHelper.verticalFrameDriver : scrollHelper.horizontalFrameDriver
        if (verticalAxis) {
            scrollHelper._discardingStaleFrameV = true
            scrollHelper._lastPublishedY = position
        } else {
            scrollHelper._discardingStaleFrameH = true
            scrollHelper._lastPublishedX = position
        }
        driver.setImmediate(position)
        if (scrollHelper.target) {
            if (verticalAxis && scrollHelper.target.contentY !== position)
                scrollHelper.target.contentY = position
            else if (!verticalAxis && scrollHelper.target.contentX !== position)
                scrollHelper.target.contentX = position
        }
        if (verticalAxis) scrollHelper._discardingStaleFrameV = false
        else scrollHelper._discardingStaleFrameH = false
        driver.moveTo(nextTarget)
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
