// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

.pragma library

// BottomSheetGesture - Pure drag math for BottomSheet 底部弹层拖拽纯计算
// Library scope cannot see QML ids, so every input is passed in.
// library 作用域取不到 QML id，所有输入都显式传入。

// Height change while dragging, split into growth above the detent and slide below it.
// 拖拽中的高度变化，拆成停靠高度之上的伸长与之下的下滑。
function dragState(startHeight, translationY, detentHeight, maxHeight, resistance) {
    var height = startHeight - translationY
    if (height > maxHeight) {
        height = maxHeight + (height - maxHeight) * resistance
    }
    if (height >= detentHeight) {
        return { upExtension: height - detentHeight, downOffset: 0 }
    }
    return { upExtension: 0, downOffset: Math.min(detentHeight, detentHeight - height) }
}

// Duration that makes the curve start at the finger's speed, so the panel neither
// stalls nor jumps at release. delta > 0 means the shown height still has to shrink.
// When an exact match would exceed maxMs, pick whichever start is closer to the finger:
// the curve capped at maxMs (starts a little faster) or the default motion from rest.
// Returns 0 for the default motion, also when the finger moved away from the goal.
// 让曲线以手指松开时的速度起步的时长，松手时面板不顿也不窜。delta > 0 表示显示高度
// 还要缩小。精确匹配会超过 maxMs 时，在"按 maxMs 截断的曲线（起步略快）"与"从静止
// 起步的默认动效"中取起步速度更接近手指的一个。返回 0 表示默认动效，手指背离目标时也是。
function releaseDuration(delta, velocityY, curve, minMs, maxMs) {
    if (maxMs <= 0 || delta * velocityY <= 0) return 0
    var startSlope = curve[1] / curve[0]
    var speed = Math.abs(velocityY)
    var ms = startSlope * Math.abs(delta) / speed * 1000
    if (ms <= maxMs) return Math.max(minMs, Math.round(ms))
    var cappedStartSpeed = startSlope * Math.abs(delta) / maxMs * 1000
    return cappedStartSpeed - speed < speed ? maxMs : 0
}

// Release decision: returns closeTarget, or the detent to settle on.
// 松手判定：返回 closeTarget，或应停靠的 detent。
function releaseTarget(p) {
    var dismiss = p.dismissRatio * p.detentHeight
    var fastDown = p.velocityY > p.velocityThreshold && p.translationY > 0
    var fastUp = p.velocityY < -p.velocityThreshold && p.translationY < 0
    if (p.detent === p.detentLarge) {
        if (p.translationY >= p.largeHeight - p.mediumHeight + dismiss) return p.closeTarget
        if (p.translationY > dismiss || fastDown) return p.detentMedium
        return p.detentLarge
    }
    if (p.translationY > dismiss || fastDown) return p.closeTarget
    if (p.allowLargeDetent && (-p.translationY > dismiss || fastUp)) return p.detentLarge
    return p.detentMedium
}
