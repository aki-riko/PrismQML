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
