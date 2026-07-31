// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

// PaintedRow - Centralized rendering row control (Phase 4 / 100B optimization) 集中绘制行控件
//
// Purpose: collapse a large ListView delegate subtree into one Canvas and one paint call.
// 用途：将庞大的 ListView 委托子树收敛为一个 Canvas 和一次绘制。
//
// Usage example 接入示例：
//   PaintedRow {
//       columns: [{key:"date", text:"时间", width: 120, align:"left"},
//                 {key:"income", text:"收入", width: 0.2, align:"right"}]
//       rowData: ({date:"2026-05-26", income:"+9999"})
//       rowIndex: index
//       rowHeight: 40
//       extraDraw: function(ctx, columns, data, w, h) { /* 画自定义图标 */ }
//   }
//
// Limits 限制：
// - Canvas software rendering targets smooth 1080p; 4K may need QQuickPaintedItem. Canvas 软件渲染适合 1080p，4K 可升级到 QQuickPaintedItem。
// - Cell-level hover/click is unavailable; use a normal delegate when needed. 不提供单元格级 hover/click，需要时使用普通委托。
// - Rich text/SVG needs extraDraw because the context cannot draw it directly. 富文本/SVG 需通过 extraDraw 补充。
import QtQuick
import "../../.."

Item {
    id: root

    // ==================== Public Props 公开属性 ====================
    property var columns: []      // [{key, text, width, align}]
    property var rowData: ({})    // model row 数据 (含每个 column.key 的 value)
    property int rowIndex: 0
    property int rowHeight: 36
    // Custom drawing runs after standard cell text. 自定义绘制在标准单元格文本之后调用。
    // function(ctx: CanvasRenderingContext2D, columns, rowData, width, height): void
    property var extraDraw: null
    // Font and color configuration aligned with Enums 字体与颜色配置默认对齐 Enums
    property int fontPointSize: 12
    property color textColor: Enums.foregroundColor
    property color textColorSubtle: Enums.secondaryForeground

    // ==================== Readonly State 只读状态 ====================
    readonly property var _safeColumns:
        columns === null || columns === undefined ? []
        : (typeof columns.length === "number" ? columns : [])

    // ==================== Signals 信号 ====================
    signal cellHovered(int colIdx, int rowIdx)

    // ==================== Public Methods 公开方法 ====================
    // Request an immediate repaint 主动请求重绘
    function refreshNow() { canvas.requestPaint() }

    // ==================== Size 尺寸 ====================
    implicitHeight: rowHeight
    // Repaint on data, geometry, theme, callback, or font changes. 数据、几何、主题、回调或字体变化时重绘。
    onRowDataChanged: canvas.requestPaint()
    onColumnsChanged: canvas.requestPaint()
    onWidthChanged: canvas.requestPaint()
    onHeightChanged: canvas.requestPaint()
    onTextColorChanged: canvas.requestPaint()
    onTextColorSubtleChanged: canvas.requestPaint()
    onFontPointSizeChanged: canvas.requestPaint()
    onExtraDrawChanged: canvas.requestPaint()

    // ==================== Content 内容 ====================
    Canvas {
        id: canvas
        readonly property string fontSpec: root.fontPointSize + "pt " + Enums.canvasFontFamily
        anchors.fill: parent
        renderStrategy: Canvas.Cooperative
        renderTarget: Canvas.FramebufferObject  // GL acceleration with Image fallback GL 加速，不支持时回退到 Image
        onFontSpecChanged: requestPaint()

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.textBaseline = "middle"
            ctx.font = canvas.fontSpec
            ctx.fillStyle = root.textColor
            var columns = root._safeColumns
            var publicColumns = root.columns
            var publicRowData = root.rowData
            var rowData = publicRowData || {}
            var rowWidth = root.width
            var rowHeight = root.height
            var extraDraw = root.extraDraw
            var x = 0
            var y = rowHeight / 2
            for (var i = 0; i < columns.length; i++) {
                var col = columns[i] || {}
                var w = col.width || 0.15
                if (w < 1) w = w * rowWidth
                var key = col.key
                var val = rowData[key]
                var text = (val === null || val === undefined) ? "" : String(val)
                var align = col.align || "left"
                ctx.save()
                // Clip the cell rectangle to prevent text overflow 裁剪单元格以防文本溢出
                ctx.beginPath()
                ctx.rect(x + 8, 0, w - 16, rowHeight)
                ctx.clip()
                if (align === "right") {
                    ctx.textAlign = "right"
                    ctx.fillText(text, x + w - 8, y)
                } else if (align === "center") {
                    ctx.textAlign = "center"
                    ctx.fillText(text, x + w / 2, y)
                } else {
                    ctx.textAlign = "left"
                    ctx.fillText(text, x + 8, y)
                }
                ctx.restore()
                x += w
            }
            // Draw business-specific additions 绘制业务自定义内容
            if (extraDraw) {
                try {
                    extraDraw.call(root, ctx, publicColumns, publicRowData, rowWidth, rowHeight)
                } catch (e) {
                    console.warn("[PaintedRow] extraDraw error:", e)
                }
            }
        }
    }

    // Lightweight hover hit testing emits only; it does not draw a background. 轻量 hover 命中检测只发信号，不绘制背景。
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton  // Let the parent ListView delegate handle clicks 由上层 ListView 委托处理点击
        onPositionChanged: function(mouse) {
            var columns = root._safeColumns
            var rowWidth = root.width
            var rowIndex = root.rowIndex
            var x = 0
            for (var i = 0; i < columns.length; i++) {
                var col = columns[i] || {}
                var w = col.width || 0.15
                if (w < 1) w = w * rowWidth
                if (mouse.x >= x && mouse.x < x + w) {
                    root.cellHovered(i, rowIndex)
                    return
                }
                x += w
            }
        }
        onExited: root.cellHovered(-1, -1)
    }
}
