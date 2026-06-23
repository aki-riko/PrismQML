// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../icons"

// ImageCropperContent - Core cropping logic 核心裁剪逻辑
// Extracted from ImageCropperDialog 从ImageCropperDialog提取
Item {
    id: content
    
    // ==================== Required Props 必需属性 ====================
    required property url source
    required property int cropShape
    required property rect cropRect
    
    // ==================== Signals 信号 ====================
    signal cropRectUpdated(rect newRect)
    
    // ==================== Internal Props 内部属性 ====================
    readonly property real _imgX: cropImage.displayX
    readonly property real _imgY: cropImage.displayY
    readonly property real _imgW: cropImage.displayWidth
    readonly property real _imgH: cropImage.displayHeight
    readonly property real _maxSize: Math.min(_imgW, _imgH)
    readonly property bool _isCircle: cropShape === Enums.imageCropper.shape_circle
    
    // Image rotation/mirror for toolbar control 图片旋转/镜像供工具栏控制
    property alias imageRotation: cropImage.rotation
    property alias imageMirror: cropImage.mirror

    // ==================== Public Methods 公开方法 ====================
    function initDefaultCropRect() {
        content.cropRectUpdated(Qt.rect(
            Enums.imageCropperDialogMetrics.cropRectDefaultX,
            Enums.imageCropperDialogMetrics.cropRectDefaultY,
            Enums.imageCropperDialogMetrics.cropRectDefaultW,
            Enums.imageCropperDialogMetrics.cropRectDefaultH
        ))
    }

    // ==================== Image 图片 ====================
    Image {
        id: cropImage
        anchors.fill: parent
        source: content.source
        fillMode: Image.PreserveAspectFit
        
        // Calculate actual image display rect 计算实际图片显示区域
        readonly property real imgRatio: sourceSize.width > 0 ? sourceSize.width / sourceSize.height : 1
        readonly property real containerRatio: width > 0 ? width / height : 1
        readonly property real displayWidth: imgRatio > containerRatio ? width : height * imgRatio
        readonly property real displayHeight: imgRatio > containerRatio ? width / imgRatio : height
        readonly property real displayX: (width - displayWidth) / 2
        readonly property real displayY: (height - displayHeight) / 2
    }
    
    // ==================== Circle Mask 圆形遮罩 ====================
    Canvas {
        id: circleMaskCanvas
        x: content._imgX
        y: content._imgY
        width: content._imgW
        height: content._imgH
        visible: content._isCircle
        
        readonly property color maskColor: Enums.stateColor.cropperMask
        onMaskColorChanged: requestPaint()
        
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.clearRect(0, 0, width, height)
            
            ctx.save()
            ctx.fillStyle = maskColor
            ctx.fillRect(0, 0, width, height)
            
            ctx.globalCompositeOperation = "destination-out"
            ctx.fillStyle = "white"
            ctx.beginPath()
            // Convert cropArea position to canvas local coordinates 转换裁剪区域位置到画布本地坐标
            var cx = cropArea.x - content._imgX + cropArea.width / 2
            var cy = cropArea.y - content._imgY + cropArea.height / 2
            var r = Math.min(cropArea.width, cropArea.height) / 2
            ctx.arc(cx, cy, r, 0, Math.PI * 2)
            ctx.fill()
            ctx.restore()
        }
        
        Connections {
            target: cropArea
            function onXChanged() { circleMaskCanvas.requestPaint() }
            function onYChanged() { circleMaskCanvas.requestPaint() }
            function onWidthChanged() { circleMaskCanvas.requestPaint() }
            function onHeightChanged() { circleMaskCanvas.requestPaint() }
        }
        
        Component.onCompleted: requestPaint()
    }

    // ==================== Rectangle Mask 矩形遮罩 ====================
    Item {
        x: content._imgX
        y: content._imgY
        width: content._imgW
        height: content._imgH
        visible: !content._isCircle
        
        // Convert cropArea to local coordinates 转换裁剪区域到本地坐标
        readonly property real localCropX: cropArea.x - content._imgX
        readonly property real localCropY: cropArea.y - content._imgY
        readonly property real localCropW: cropArea.width
        readonly property real localCropH: cropArea.height
        
        Rectangle {
            anchors { top: parent.top; left: parent.left; right: parent.right }
            height: parent.localCropY
            color: Enums.stateColor.cropperMask
        }
        Rectangle {
            anchors { bottom: parent.bottom; left: parent.left; right: parent.right }
            height: parent.height - parent.localCropY - parent.localCropH
            color: Enums.stateColor.cropperMask
        }
        Rectangle {
            y: parent.localCropY
            width: parent.localCropX
            height: parent.localCropH
            color: Enums.stateColor.cropperMask
        }
        Rectangle {
            x: parent.localCropX + parent.localCropW
            y: parent.localCropY
            width: parent.width - parent.localCropX - parent.localCropW
            height: parent.localCropH
            color: Enums.stateColor.cropperMask
        }
    }
    
    // ==================== Crop Area 裁剪区域 ====================
    Item {
        id: cropArea
        
        x: content._imgX + content.cropRect.x * content._imgW
        y: content._imgY + content.cropRect.y * content._imgH
        width: content._isCircle ? (content.cropRect.width * content._maxSize) : (content.cropRect.width * content._imgW)
        height: content._isCircle ? (content.cropRect.width * content._maxSize) : (content.cropRect.height * content._imgH)
        
        // Border 边框
        Rectangle {
            anchors.fill: parent
            color: Enums.transparent
            border.width: Enums.imageCropperDialogMetrics.cropBorderWidth
            border.color: Enums.stateColor.cropperLine
            radius: content._isCircle ? width / 2 : 0
        }
        
        // Drag to move 拖拽移动
        MouseArea {
            anchors.fill: parent
            anchors.margins: Enums.imageCropperDialogMetrics.cropMoveMargin
            cursorShape: Qt.SizeAllCursor
            
            property real startRectX
            property real startRectY
            property real pressGlobalX
            property real pressGlobalY
            
            onPressed: (mouse) => {
                var globalPos = mapToItem(content, mouse.x, mouse.y)
                pressGlobalX = globalPos.x
                pressGlobalY = globalPos.y
                startRectX = content.cropRect.x
                startRectY = content.cropRect.y
            }
            
            onPositionChanged: (mouse) => {
                if (pressed) {
                    var globalPos = mapToItem(content, mouse.x, mouse.y)
                    var imgW = content._imgW, imgH = content._imgH
                    var dx = (globalPos.x - pressGlobalX) / imgW
                    var dy = (globalPos.y - pressGlobalY) / imgH
                    
                    var w = content.cropRect.width
                    var h = content.cropRect.height
                    var pixelW = content._isCircle ? (w * content._maxSize) : (w * imgW)
                    var pixelH = content._isCircle ? (w * content._maxSize) : (h * imgH)
                    
                    var newX = Math.max(0, Math.min(1 - pixelW / imgW, startRectX + dx))
                    var newY = Math.max(0, Math.min(1 - pixelH / imgH, startRectY + dy))
                    
                    content.cropRectUpdated(Qt.rect(newX, newY, w, h))
                }
            }

            onWheel: (wheel) => {
                var scaleFactor = wheel.angleDelta.y > 0 ? Enums.imageCropperDialogMetrics.wheelZoomIn : Enums.imageCropperDialogMetrics.wheelZoomOut
                var minSize = Enums.imageCropperDialogMetrics.minCropSize
                var imgX = content._imgX, imgY = content._imgY
                var imgW = content._imgW, imgH = content._imgH
                var maxSize = content._maxSize
                
                var cx = cropArea.x + cropArea.width / 2
                var cy = cropArea.y + cropArea.height / 2
                var newW, newH, newRectW, newRectH
                
                if (content._isCircle) {
                    var newS = cropArea.width * scaleFactor
                    newS = Math.max(minSize, Math.min(newS, maxSize))
                    newW = newH = newS
                    newRectW = newRectH = newS / maxSize
                } else {
                    newW = Math.max(minSize, Math.min(cropArea.width * scaleFactor, imgW))
                    newH = Math.max(minSize, Math.min(cropArea.height * scaleFactor, imgH))
                    newRectW = newW / imgW
                    newRectH = newH / imgH
                }
                
                var newX = cx - newW / 2
                var newY = cy - newH / 2
                newX = Math.max(imgX, Math.min(imgX + imgW - newW, newX))
                newY = Math.max(imgY, Math.min(imgY + imgH - newH, newY))
                
                content.cropRectUpdated(Qt.rect((newX - imgX) / imgW, (newY - imgY) / imgH, newRectW, newRectH))
            }
        }
        
        // ==================== Corner Handles 四角手柄 ====================
        Repeater {
            model: Enums.imageCropperDialogMetrics.handleCount
            
            Rectangle {
                id: handle
                width: Enums.imageCropperDialogMetrics.handleSize
                height: Enums.imageCropperDialogMetrics.handleSize
                radius: Enums.imageCropperDialogMetrics.handleRadius
                color: Enums.stateColor.cropperLine
                
                x: (index % 2 === 0) ? -Enums.imageCropperDialogMetrics.handleOffset : cropArea.width - Enums.imageCropperDialogMetrics.handleOffset
                y: (index < 2) ? -Enums.imageCropperDialogMetrics.handleOffset : cropArea.height - Enums.imageCropperDialogMetrics.handleOffset
                
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: Enums.imageCropperDialogMetrics.handleOuterMargin
                    radius: width / 2
                    color: Enums.stateColor.cropperMask
                    z: Enums.zIndex.background
                }
                
                MouseArea {
                    anchors.fill: parent
                    anchors.margins: Enums.imageCropperDialogMetrics.handleHitMargin
                    cursorShape: (index === 0 || index === 3) ? Qt.SizeFDiagCursor : Qt.SizeBDiagCursor
                    
                    property point pp
                    property real sx
                    property real sy
                    property real sw
                    property real sh
                    
                    onPressed: {
                        pp = mapToItem(content, mouseX, mouseY)
                        sx = cropArea.x; sy = cropArea.y
                        sw = cropArea.width; sh = cropArea.height
                    }

                    onPositionChanged: {
                        if (!pressed) return
                        
                        var c = mapToItem(content, mouseX, mouseY)
                        var dx = c.x - pp.x, dy = c.y - pp.y
                        var m = Enums.imageCropperDialogMetrics.minCropSize
                        var imgX = content._imgX, imgY = content._imgY
                        var imgW = content._imgW, imgH = content._imgH
                        var maxSize = content._maxSize
                        var boundRight = imgX + imgW, boundBottom = imgY + imgH
                        
                        var newX = sx, newY = sy, newW = sw, newH = sh
                        
                        if (content._isCircle) {
                            var delta = Math.max(Math.abs(dx), Math.abs(dy)) * ((dx + dy) > 0 ? 1 : -1)
                            if (index === 0) {
                                newX = Math.max(imgX, sx + delta)
                                newY = Math.max(imgY, sy + delta)
                                var nS = Math.min(sw - (newX - sx), maxSize)
                                if (nS >= m && newX + nS <= boundRight && newY + nS <= boundBottom) { newW = newH = nS }
                                else { newX = sx; newY = sy }
                            } else if (index === 1) {
                                newY = Math.max(imgY, sy - delta)
                                var nS1 = Math.min(sw + delta, maxSize, boundRight - sx, boundBottom - newY)
                                if (nS1 >= m && newY >= imgY && sx + nS1 <= boundRight && newY + nS1 <= boundBottom) { newW = newH = nS1 }
                                else { newY = sy }
                            } else if (index === 2) {
                                newX = Math.max(imgX, sx - delta)
                                var nS2 = Math.min(sw + delta, maxSize, boundRight - newX, boundBottom - sy)
                                if (nS2 >= m && newX >= imgX && newX + nS2 <= boundRight && sy + nS2 <= boundBottom) { newW = newH = nS2 }
                                else { newX = sx }
                            } else {
                                var nS3 = Math.min(sw + delta, maxSize, boundRight - sx, boundBottom - sy)
                                if (nS3 >= m) { newW = newH = nS3 }
                            }
                            content.cropRectUpdated(Qt.rect((newX - imgX) / imgW, (newY - imgY) / imgH, newW / maxSize, newW / maxSize))
                        } else {
                            if (index === 0) {
                                newX = Math.max(imgX, sx + dx); newY = Math.max(imgY, sy + dy)
                                newW = sw - (newX - sx); newH = sh - (newY - sy)
                                if (newW < m || newH < m) { newX = sx; newY = sy; newW = sw; newH = sh }
                            } else if (index === 1) {
                                newY = Math.max(imgY, sy + dy)
                                newW = Math.min(boundRight - sx, sw + dx); newH = sh - (newY - sy)
                                if (newW < m || newH < m) { newY = sy; newW = sw; newH = sh }
                            } else if (index === 2) {
                                newX = Math.max(imgX, sx + dx)
                                newW = sw - (newX - sx); newH = Math.min(boundBottom - sy, sh + dy)
                                if (newW < m || newH < m) { newX = sx; newW = sw; newH = sh }
                            } else {
                                newW = Math.min(boundRight - sx, sw + dx)
                                newH = Math.min(boundBottom - sy, sh + dy)
                                if (newW < m || newH < m) { newW = sw; newH = sh }
                            }
                            content.cropRectUpdated(Qt.rect((newX - imgX) / imgW, (newY - imgY) / imgH, newW / imgW, newH / imgH))
                        }
                    }
                }
            }
        }
    }
}
