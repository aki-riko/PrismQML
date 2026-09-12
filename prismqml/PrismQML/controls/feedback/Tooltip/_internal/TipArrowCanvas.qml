// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// TipArrowCanvas - Paints the TeachingTip arrow triangle 绘制教学提示的箭头三角形
//
// Kept out of TipPopup so the popup entry stays an orchestration file. The triangle
// reuses the popup surface's fill and border contract on its two exposed sides.
// 从 TipPopup 抽出来,让弹层入口只做编排。三角形在两条外露斜边上复用主表面的填充与
// 描边合同。
Canvas {
    id: arrowCanvas

    // ==================== Required Props 必需属性 ====================
    // Arrow geometry owner 箭头几何来源
    required property var positionHelper
    // Popup owning the surface colors 持有表面配色的弹层
    required property var popupControl

    // ==================== Public Methods 公开方法 ====================
    function requestArrowPaint() { requestPaint() }

    // ==================== Content 内容 ====================
    onPaint: {
        var ctx = getContext("2d")
        ctx.reset()
        var bgColor = popupControl._tipBackground
        var borderColor = popupControl._tipBorderColor
        var w = width, h = height, inset = 2

        // Draw filled triangle 绘制填充三角形
        ctx.beginPath()
        if (positionHelper.isBottom) {
            ctx.moveTo(inset, inset)
            ctx.lineTo(w/2, h - inset)
            ctx.lineTo(w - inset, inset)
        } else if (positionHelper.isTop) {
            ctx.moveTo(inset, h - inset)
            ctx.lineTo(w/2, inset)
            ctx.lineTo(w - inset, h - inset)
        } else if (positionHelper.isLeft) {
            ctx.moveTo(w - inset, inset)
            ctx.lineTo(inset, h/2)
            ctx.lineTo(w - inset, h - inset)
        } else if (positionHelper.isRight) {
            ctx.moveTo(inset, inset)
            ctx.lineTo(w - inset, h/2)
            ctx.lineTo(inset, h - inset)
        }
        ctx.closePath()
        ctx.fillStyle = bgColor
        ctx.fill()

        // Draw the same border contract as the popup surface on the two exposed sides.
        // 箭头仅在两条外露斜边复用主表面的描边合同。
        if (popupControl._tipBorderWidth > Enums.border.none) {
            ctx.beginPath()
            ctx.strokeStyle = borderColor
            ctx.lineWidth = popupControl._tipBorderWidth
            if (positionHelper.isBottom) {
                ctx.moveTo(inset, inset)
                ctx.lineTo(w/2, h - inset)
                ctx.lineTo(w - inset, inset)
            } else if (positionHelper.isTop) {
                ctx.moveTo(inset, h - inset)
                ctx.lineTo(w/2, inset)
                ctx.lineTo(w - inset, h - inset)
            } else if (positionHelper.isLeft) {
                ctx.moveTo(w - inset, inset)
                ctx.lineTo(inset, h/2)
                ctx.lineTo(w - inset, h - inset)
            } else if (positionHelper.isRight) {
                ctx.moveTo(inset, inset)
                ctx.lineTo(w - inset, h/2)
                ctx.lineTo(inset, h - inset)
            }
            ctx.stroke()
        }
    }
}
