// NavigationPanelBackground - Navigation panel visual background 导航面板视觉背景
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

import QtQuick
import "../.."

// Keeps background layers below navigation content 将背景层保持在导航内容下方
Item {
    id: backgroundLayer

    // ==================== Required Props 必需属性 ====================
    required property var panel

    // ==================== Internal Props 内部属性 ====================
    readonly property var control: panel

    anchors.fill: parent
    z: -2

    // Layer A: opaque background with right-side rounded corners 层A：右侧圆角不透明背景
    Canvas {
        id: bgCanvas

        readonly property color _backgroundColor: control.backgroundColor
        readonly property real _paintRadius: control._cornerRadius

        function _scheduleBgRepaint() {
            Qt.callLater(bgCanvas.requestPaint)
        }

        anchors.fill: parent
        z: 0  // Lowest layer within the background surface 背景层内部的最低层

        onPaint: {
            var ctx = getContext("2d")
            var w = width, h = height, r = control._cornerRadius
            var topOffset = control.titleBarHeight  // Top-right corner starts below title bar 右上圆角从标题栏下方开始
            ctx.clearRect(0, 0, w, h)

            // Fill background 填充背景
            ctx.fillStyle = _backgroundColor.toString()
            ctx.beginPath()
            ctx.moveTo(0, 0)
            ctx.lineTo(w, 0)  // Top edge (no corner, extends into title bar) 顶边（无圆角，延伸到标题栏）
            ctx.lineTo(w, topOffset)  // Right edge above title bar 标题栏上方的右边
            ctx.lineTo(w - r, topOffset)  // Move to top-right corner start 移动到右上圆角起点
            ctx.arcTo(w, topOffset, w, topOffset + r, r)  // Top-right corner below title bar 标题栏下方的右上圆角
            ctx.lineTo(w, h - r)
            ctx.arcTo(w, h, w - r, h, r)  // Bottom-right corner 右下圆角
            ctx.lineTo(0, h)
            ctx.closePath()
            ctx.fill()
        }

        // Repaint when size or color changes (debounced via Qt.callLater)
        // 尺寸或颜色变化时防抖重绘 — Qt.callLater 自动合并同一事件循环中的多次调用,
        // 不绑死 60fps 帧时长, 跟随事件循环节拍刷新一次
        onWidthChanged: _scheduleBgRepaint()
        onHeightChanged: _scheduleBgRepaint()
        on_BackgroundColorChanged: requestPaint()
        on_PaintRadiusChanged: requestPaint()
    }

    TicketPaper {
        anchors.fill: parent
        patternOriginX: control.paperOriginX
        patternOriginY: control.paperOriginY
        visible: control.ticketPaperEnabled && Enums.isVintageTicket
        z: 1
    }

    // Layer B: Acrylic blurred background 层B：亚克力模糊背景
    Rectangle {
        id: acrylicLayer

        // Acrylic tint color: pure white/dark gray; keeps Mica tint 亚克力着色：纯白/深灰，保留云母色调
        readonly property color acrylicTintColor: Enums.stateColor.acrylicTintColor

        anchors.fill: parent
        visible: Enums.usesSoftElevation && control.acrylicEnabled && control.acrylicImageSource !== ""
        z: 1  // Below all content 在所有内容下方
        radius: control._cornerRadius
        clip: true
        color: Enums.transparent

        // Acrylic surface: the blurred capture plus the tint that keeps the Mica
        // tone. The panel silhouette is square along the window edge and rounded
        // on the right, so the blur is painted through that clip path: a plain
        // Image keeps its square corners where the panel is rounded, and those
        // corners read as a second, square-cornered layer sticking out of the
        // panel.
        // 亚克力面: 模糊截图 + 保留云母色调的着色。面板轮廓贴窗口一侧为直角、右侧为
        // 圆角, 因此模糊图必须按该轮廓裁剪绘制: 直接用 Image 会在面板圆角处留下方角,
        // 那块方角看起来就是面板外侧多出来的一层"没有圆角"的层。
        //
        // The capture covers the panel inside the window while this layer starts
        // one title bar higher, so the image is drawn at that offset with its own
        // height. Filling the whole layer instead stretched the blur by
        // height/(height-titleBarHeight) and lifted it by one title bar, which
        // ghosted a second, offset copy of the panel behind the real content.
        // 截图取的是窗口内的面板区域, 而本层比窗口高出一个标题栏, 因此图像按该偏移
        // 下移并使用自身高度绘制。铺满整层会把模糊图纵向拉伸 height/(height-titleBarHeight)
        // 倍并整体上移一个标题栏, 在真实内容后面多出一层错位的重影。
        Canvas {
            id: acrylicSurface

            readonly property string _source: control.acrylicImageSource
            readonly property real _paintRadius: control._cornerRadius
            readonly property real _topOffset: control.titleBarHeight
            // Bounded retry budget for the asynchronous capture load: 16ms per
            // attempt, about three seconds in total, after which the panel stays
            // unblurred until the source changes.
            // 异步截图加载的有界重试预算: 每次 16ms, 共约三秒; 之后面板保持无模糊,
            // 直到图源变化。
            readonly property int _maxRetries: 180
            property int _retries: 0

            function _scheduleRepaint() {
                Qt.callLater(acrylicSurface.requestPaint)
            }

            function _loadSource() {
                if (_source !== "" && !isImageLoaded(_source)) loadImage(_source)
            }

            function _tintStyle() {
                var tint = acrylicLayer.acrylicTintColor
                return "rgba(" + Math.round(tint.r * 255) + "," +
                    Math.round(tint.g * 255) + "," + Math.round(tint.b * 255) +
                    "," + tint.a + ")"
            }

            anchors.fill: parent

            onPaint: {
                var ctx = getContext("2d")
                var w = width, h = height, r = _paintRadius
                var topOffset = _topOffset
                ctx.clearRect(0, 0, w, h)
                // A canvas loads images by URL asynchronously, so the first
                // paints run before the capture is ready. Keep re-asking until
                // the canvas reports it loaded: a single retry is not enough on
                // a slower machine and leaves the panel with no acrylic at all.
                // Canvas 按 URL 异步加载图像, 前几帧必然早于截图就绪。这里持续重试到
                // 画布报告已加载为止: 只重试一次在较慢的机器上会直接留下没有亚克力的
                // 面板。
                if (_source === "" || h <= topOffset) {
                    acrylicRetryTimer.stop()
                    return
                }
                if (!isImageLoaded(_source)) {
                    _loadSource()
                    if (!acrylicRetryTimer.running && _retries < _maxRetries) {
                        acrylicRetryTimer.start()
                    }
                    return
                }
                acrylicRetryTimer.stop()
                _retries = 0
                ctx.save()
                ctx.beginPath()
                ctx.moveTo(0, 0)
                ctx.lineTo(w, 0)
                ctx.lineTo(w, topOffset)
                ctx.lineTo(w - r, topOffset)
                ctx.arcTo(w, topOffset, w, topOffset + r, r)
                ctx.lineTo(w, h - r)
                ctx.arcTo(w, h, w - r, h, r)
                ctx.lineTo(0, h)
                ctx.closePath()
                ctx.clip()
                ctx.drawImage(_source, 0, topOffset, w, h - topOffset)
                ctx.fillStyle = _tintStyle()
                ctx.fill()
                ctx.restore()
            }

            Component.onCompleted: _loadSource()
            onWidthChanged: _scheduleRepaint()
            onHeightChanged: _scheduleRepaint()
            on_SourceChanged: {
                _retries = 0
                _loadSource()
                _scheduleRepaint()
            }
            on_PaintRadiusChanged: _scheduleRepaint()
            on_TopOffsetChanged: _scheduleRepaint()

            // Bounded retry loop for the first paint before the capture is
            // decoded. It stops as soon as a paint finds the image loaded.
            // 截图解码完成前首帧的有界重试循环; 一旦某次绘制发现图像已加载就停止。
            Timer {
                id: acrylicRetryTimer

                interval: 16
                repeat: true
                onTriggered: {
                    acrylicSurface._retries += 1
                    if (acrylicSurface._retries >= acrylicSurface._maxRetries) {
                        stop()
                        console.warn(
                            "Acrylic capture never loaded:", acrylicSurface._source)
                        return
                    }
                    acrylicSurface.requestPaint()
                }
            }

            // Loader for the capture: it only exists to warm the engine's image
            // cache and to request a repaint once the acrylic image is ready.
            // 截图的加载器: 只负责预热引擎图像缓存, 并在亚克力图就绪后再请求一次重绘。
            Image {
                id: acrylicSource

                visible: false
                source: acrylicSurface._source
                cache: false  // Disable cache for dynamic updates 禁用缓存以支持动态更新
                onStatusChanged: {
                    if (status === Image.Ready) acrylicSurface.requestPaint()
                }
            }
        }
    }


}
