// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

// PaintedRow - Centralized rendering row control (Phase 4 / 100B optimization)
//
// 用途: ListView delegate 子树过大时(10+ QObject/行)快速滚动卡,本控件
//   把整行收敛到 1 个 Canvas + 1 次 paint,极大减少 QObject 创建销毁开销。
//
// 接入示例:
//   PaintedRow {
//       columns: [{key:"date", text:"时间", width: 120, align:"left"},
//                 {key:"income", text:"收入", width: 0.2, align:"right"}]
//       rowData: ({date:"2026-05-26", income:"+9999"})
//       rowIndex: index
//       rowHeight: 40
//       extraDraw: function(ctx, columns, data, w, h) { /* 画自定义图标 */ }
//   }
//
// 限制:
// - Canvas 软件渲染,1080p 下可流畅 60fps;4k 屏会感受到糊化,需要升级到 QQuickPaintedItem
// - 单 cell hover/click 失效;只能整行选中。需要 cell 级交互的场景用普通 delegate
// - 富文本/SVG 无法在 ctx 直接画;extraDraw 可填补
import QtQuick
import "../.."

Item {
    id: root

    // ==================== Public Props 公开属性 ====================
    property var columns: []      // [{key, text, width, align}]
    property var rowData: ({})    // model row 数据 (含每个 column.key 的 value)
    property int rowIndex: 0
    property int rowHeight: 36
    // 自定义补充绘制 (icon / 进度条 / 等), 在标准 cell text 后调用
    // function(ctx: CanvasRenderingContext2D, columns, rowData, width, height): void
    property var extraDraw: null
    // 字体/颜色配置 (默认与 Enums 对齐)
    property string fontFamily: "Microsoft YaHei UI"
    property int fontPointSize: 12
    property color textColor: Enums.foregroundColor
    property color textColorSubtle: Enums.foregroundColorSubtle

    // ==================== Signals 信号 ====================
    signal cellHovered(int colIdx, int rowIdx)

    // ==================== Public Methods 公共方法 ====================
    // 主动重绘
    function refreshNow() { canvas.requestPaint() }

    implicitHeight: rowHeight

    Canvas {
        id: canvas
        anchors.fill: parent
        renderStrategy: Canvas.Cooperative
        renderTarget: Canvas.FramebufferObject  // GL 加速 (Qt 选择性支持,不支持时退到 Image)

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.textBaseline = "middle"
            ctx.font = root.fontPointSize + "pt '" + root.fontFamily + "'"
            ctx.fillStyle = root.textColor
            var x = 0
            var y = root.height / 2
            for (var i = 0; i < root.columns.length; i++) {
                var col = root.columns[i]
                var w = col.width || 0.15
                if (w < 1) w = w * root.width
                var key = col.key
                var val = root.rowData[key]
                var text = (val === null || val === undefined) ? "" : String(val)
                var align = col.align || "left"
                ctx.save()
                // clip cell rect 防止文本溢出
                ctx.beginPath()
                ctx.rect(x + 8, 0, w - 16, root.height)
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
            // 业务自定义补充绘制
            if (root.extraDraw) {
                try {
                    root.extraDraw(ctx, root.columns, root.rowData, root.width, root.height)
                } catch (e) {
                    console.warn("[PaintedRow] extraDraw error:", e)
                }
            }
        }
    }

    // 数据变更触发重绘
    onRowDataChanged: canvas.requestPaint()
    onColumnsChanged: canvas.requestPaint()
    onWidthChanged: canvas.requestPaint()
    onHeightChanged: canvas.requestPaint()
    // 自检 review 修复: 主题切换 / 业务运行时换 extraDraw / 字体改 都要触发重绘
    onTextColorChanged: canvas.requestPaint()
    onTextColorSubtleChanged: canvas.requestPaint()
    onFontFamilyChanged: canvas.requestPaint()
    onFontPointSizeChanged: canvas.requestPaint()
    onExtraDrawChanged: canvas.requestPaint()

    // hover 命中检测 (轻量,只 emit 信号,不画背景)
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton  // 让上层 ListView delegate 处理点击
        onPositionChanged: function(mouse) {
            var x = 0
            for (var i = 0; i < root.columns.length; i++) {
                var w = root.columns[i].width || 0.15
                if (w < 1) w = w * root.width
                if (mouse.x >= x && mouse.x < x + w) {
                    root.cellHovered(i, root.rowIndex)
                    return
                }
                x += w
            }
        }
        onExited: root.cellHovered(-1, -1)
    }
}
