// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

// ChartViewportTransition - Viewport transform planning 视窗变换规划
.pragma library

function visualRange(renderStart, renderEnd, scaleValue, offsetRatio) {
    var renderSpan = renderEnd - renderStart
    var safeScale = scaleValue > 0 ? scaleValue : 1
    var visualSpan = renderSpan / safeScale
    var visualStart = renderStart - renderSpan * offsetRatio / safeScale
    return {
        start: visualStart,
        end: visualStart + visualSpan,
        span: visualSpan
    }
}

function plan(renderStart, renderEnd, scaleValue, offsetRatio,
              targetStart, targetEnd, epsilon) {
    var current = visualRange(renderStart, renderEnd, scaleValue, offsetRatio)
    var renderSpan = renderEnd - renderStart
    var targetSpan = targetEnd - targetStart
    if (renderSpan <= epsilon || current.span <= epsilon || targetSpan <= epsilon) {
        return { animate: false }
    }
    if (Math.abs(targetStart - current.start) <= epsilon &&
            Math.abs(targetEnd - current.end) <= epsilon) {
        return { animate: false }
    }

    var targetInsideRender = targetStart >= renderStart - epsilon &&
                             targetEnd <= renderEnd + epsilon
    var zoomingIn = targetSpan < current.span - epsilon && targetInsideRender
    if (zoomingIn) {
        return {
            animate: true,
            replaceData: false,
            scaleFrom: scaleValue,
            offsetFrom: offsetRatio,
            scaleTo: renderSpan / targetSpan,
            offsetTo: (renderStart - targetStart) / targetSpan,
            commitAfter: true
        }
    }

    return {
        animate: true,
        replaceData: true,
        scaleFrom: targetSpan / current.span,
        offsetFrom: (targetStart - current.start) / current.span,
        scaleTo: 1,
        offsetTo: 0,
        commitAfter: false
    }
}
