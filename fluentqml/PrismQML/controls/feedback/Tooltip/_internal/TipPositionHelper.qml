// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."

// TipPositionHelper - Position calculation for TipPopup 提示弹出位置计算
QtObject {
    id: helper
    
    // ==================== Required Props 必需属性 ====================
    // ✅ 2026-05-15: target 从 Item 放宽为 var,允许传 QQuickWindow / QWindow
    // 等鸭子类型对象(只要具备 mapToGlobal / width / height 即可)
    required property var target
    required property int tipType
    required property int animationType
    required property int anchorPosition
    required property int viewWidth
    required property int viewHeight
    
    // ==================== Constants 常量 ====================
    readonly property int slideOffset: 8
    readonly property int tailSize: 8
    readonly property int gap: 4
    
    // ==================== Type Checks 类型检查 ====================
    readonly property bool isFlyout: tipType === Enums.tip.type_flyout
    readonly property bool isTeachingTip: tipType === Enums.tip.type_teaching_tip
    
    // ==================== Arrow Direction 箭头方向 ====================
    readonly property bool isTop: isTeachingTip && (
        anchorPosition === Enums.teachingTip.anchor_top || 
        anchorPosition === Enums.teachingTip.anchor_top_left ||
        anchorPosition === Enums.teachingTip.anchor_top_right)
    readonly property bool isBottom: isTeachingTip && (
        anchorPosition === Enums.teachingTip.anchor_bottom ||
        anchorPosition === Enums.teachingTip.anchor_bottom_left ||
        anchorPosition === Enums.teachingTip.anchor_bottom_right)
    readonly property bool isLeft: isTeachingTip && (
        anchorPosition === Enums.teachingTip.anchor_left ||
        anchorPosition === Enums.teachingTip.anchor_left_top ||
        anchorPosition === Enums.teachingTip.anchor_left_bottom)
    readonly property bool isRight: isTeachingTip && (
        anchorPosition === Enums.teachingTip.anchor_right ||
        anchorPosition === Enums.teachingTip.anchor_right_top ||
        anchorPosition === Enums.teachingTip.anchor_right_bottom)
    readonly property bool hasArrow: isTop || isBottom || isLeft || isRight
    
    // ==================== Position Calculation 位置计算 ====================
    function calculatePosition() {
        if (!target) return { x: 0, y: 0 }
        
        var targetPos = target.mapToGlobal(0, 0)
        var w = viewWidth
        var h = viewHeight
        var arrowSpace = isTeachingTip ? (tailSize + 4) : gap
        
        if (isFlyout) {
            switch (animationType) {
                case Enums.flyout.pullUp:
                    return { x: targetPos.x + target.width / 2 - w / 2, y: targetPos.y - h - gap }
                case Enums.flyout.dropDown:
                    return { x: targetPos.x + target.width / 2 - w / 2, y: targetPos.y + target.height + gap }
                case Enums.flyout.slideLeft:
                    return { x: targetPos.x - w - gap, y: targetPos.y + target.height / 2 - h / 2 }
                case Enums.flyout.slideRight:
                    return { x: targetPos.x + target.width + gap, y: targetPos.y + target.height / 2 - h / 2 }
                default:
                    return { x: targetPos.x + target.width / 2 - w / 2, y: targetPos.y - h - gap }
            }
        } else {
            switch (anchorPosition) {
                case Enums.teachingTip.anchor_bottom:
                case Enums.teachingTip.anchor_bottom_left:
                case Enums.teachingTip.anchor_bottom_right:
                    return { x: targetPos.x + target.width / 2 - w / 2, y: targetPos.y - h - arrowSpace }
                case Enums.teachingTip.anchor_top:
                case Enums.teachingTip.anchor_top_left:
                case Enums.teachingTip.anchor_top_right:
                    return { x: targetPos.x + target.width / 2 - w / 2, y: targetPos.y + target.height + arrowSpace }
                case Enums.teachingTip.anchor_left:
                case Enums.teachingTip.anchor_left_top:
                case Enums.teachingTip.anchor_left_bottom:
                    return { x: targetPos.x + target.width + arrowSpace, y: targetPos.y + target.height / 2 - h / 2 }
                case Enums.teachingTip.anchor_right:
                case Enums.teachingTip.anchor_right_top:
                case Enums.teachingTip.anchor_right_bottom:
                    return { x: targetPos.x - w - arrowSpace, y: targetPos.y + target.height / 2 - h / 2 }
                default:
                    return { x: targetPos.x + target.width / 2 - w / 2, y: targetPos.y - h - arrowSpace }
            }
        }
    }
    
    function getStartPosition(endPos) {
        if (isFlyout) {
            switch (animationType) {
                case Enums.flyout.pullUp:
                    return { x: endPos.x, y: endPos.y + slideOffset }
                case Enums.flyout.dropDown:
                    return { x: endPos.x, y: endPos.y - slideOffset }
                case Enums.flyout.slideLeft:
                    return { x: endPos.x + slideOffset, y: endPos.y }
                case Enums.flyout.slideRight:
                    return { x: endPos.x - slideOffset, y: endPos.y }
                default:
                    return endPos
            }
        }
        // TeachingTip animation based on tail position 根据箭头方向设置动画
        if (isTeachingTip) {
            if (isBottom) return { x: endPos.x, y: endPos.y + slideOffset }
            if (isTop) return { x: endPos.x, y: endPos.y - slideOffset }
            if (isLeft) return { x: endPos.x + slideOffset, y: endPos.y }
            if (isRight) return { x: endPos.x - slideOffset, y: endPos.y }
        }
        return endPos
    }
    
    function calculateArrowPosition(mainPos) {
        var arrowW = (isLeft || isRight) ? (tailSize + 28) : 44
        var arrowH = (isTop || isBottom) ? (tailSize + 28) : 44
        var offset = 3
        
        if (isBottom) {
            return { x: mainPos.x + viewWidth / 2 - arrowW / 2, y: mainPos.y + viewHeight - arrowH / 2 + offset }
        } else if (isTop) {
            return { x: mainPos.x + viewWidth / 2 - arrowW / 2, y: mainPos.y - arrowH / 2 - offset }
        } else if (isLeft) {
            return { x: mainPos.x - arrowW / 2 - offset, y: mainPos.y + viewHeight / 2 - arrowH / 2 }
        } else if (isRight) {
            return { x: mainPos.x + viewWidth - arrowW / 2 + offset, y: mainPos.y + viewHeight / 2 - arrowH / 2 }
        }
        return { x: mainPos.x, y: mainPos.y }
    }
    
    function isHorizontalAnimation() {
        if (isFlyout) {
            return animationType === Enums.flyout.slideLeft ||
                   animationType === Enums.flyout.slideRight
        }
        // TeachingTip horizontal animation for left/right tail 左右箭头使用水平动画
        return isLeft || isRight
    }
}
