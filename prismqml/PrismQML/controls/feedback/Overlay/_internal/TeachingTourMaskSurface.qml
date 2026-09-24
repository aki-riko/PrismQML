// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Shapes
import "../../../.."

// TeachingTourMaskSurface - Spotlight scrim built without any masking 无遮罩聚光蒙层
// layer.effect masking is a silent no-op in Qt 6.11 (see the OpacityMask docs and
// tests/tooling/test_opacity_mask_contract.py) and one ShapePath only fills its last
// subpath, so the scrim is four bands around the hole plus four rounded corner patches.
// Qt 6.11 下 layer.effect 遮罩静默失效(见 OpacityMask 文档与
// tests/tooling/test_opacity_mask_contract.py), 且一个 ShapePath 只填充最后一个子路径,
// 因此蒙层由"孔四周四条带 + 四个圆角补块"构成。
Item {
    id: maskSurface

    // ==================== Required Props 必需属性 ====================
    required property var host

    // ==================== Size 尺寸 ====================
    objectName: "teachingTourMaskSurface"
    anchors.fill: parent

    // ==================== Content 内容 ====================
    Rectangle {
        objectName: "teachingTourMaskScrim"
        anchors.fill: parent
        color: maskSurface.host.maskColor
        visible: !maskSurface.host._targetAvailable
    }

    Rectangle {
        x: 0
        y: 0
        width: maskSurface.width
        height: maskSurface.host._holeTop
        color: maskSurface.host.maskColor
        visible: maskSurface.host._targetAvailable
    }

    Rectangle {
        x: 0
        y: maskSurface.host._holeBottom
        width: maskSurface.width
        height: maskSurface.height - maskSurface.host._holeBottom
        color: maskSurface.host.maskColor
        visible: maskSurface.host._targetAvailable
    }

    Rectangle {
        x: 0
        y: maskSurface.host._holeTop
        width: maskSurface.host._holeLeft
        height: maskSurface.host._holeBottom - maskSurface.host._holeTop
        color: maskSurface.host.maskColor
        visible: maskSurface.host._targetAvailable
    }

    Rectangle {
        x: maskSurface.host._holeRight
        y: maskSurface.host._holeTop
        width: maskSurface.width - maskSurface.host._holeRight
        height: maskSurface.host._holeBottom - maskSurface.host._holeTop
        color: maskSurface.host.maskColor
        visible: maskSurface.host._targetAvailable
    }

    Shape {
        objectName: "teachingTourMaskCorners"
        anchors.fill: parent
        antialiasing: true
        // Curve renderer is what actually antialiases Shape geometry here;
        // the default geometry renderer leaves the arcs stepped.
        // 圆角弧线真正获得抗锯齿靠曲线渲染器; 默认几何渲染器会让弧边出现阶梯。
        preferredRendererType: Shape.CurveRenderer
        visible: maskSurface.host._targetAvailable

        ShapePath {
            fillColor: maskSurface.host.maskColor
            strokeColor: Enums.transparent
            strokeWidth: 0
            PathMove { x: maskSurface.host._holeLeft; y: maskSurface.host._holeTop }
            PathLine {
                x: maskSurface.host._holeLeft
                y: maskSurface.host._holeTop + maskSurface.host._currentHighlightRadius
            }
            PathArc {
                x: maskSurface.host._holeLeft + maskSurface.host._currentHighlightRadius
                y: maskSurface.host._holeTop
                radiusX: maskSurface.host._currentHighlightRadius
                radiusY: maskSurface.host._currentHighlightRadius
                direction: PathArc.Clockwise
            }
            PathLine { x: maskSurface.host._holeLeft; y: maskSurface.host._holeTop }
        }

        ShapePath {
            fillColor: maskSurface.host.maskColor
            strokeColor: Enums.transparent
            strokeWidth: 0
            PathMove { x: maskSurface.host._holeRight; y: maskSurface.host._holeTop }
            PathLine {
                x: maskSurface.host._holeRight - maskSurface.host._currentHighlightRadius
                y: maskSurface.host._holeTop
            }
            PathArc {
                x: maskSurface.host._holeRight
                y: maskSurface.host._holeTop + maskSurface.host._currentHighlightRadius
                radiusX: maskSurface.host._currentHighlightRadius
                radiusY: maskSurface.host._currentHighlightRadius
                direction: PathArc.Clockwise
            }
            PathLine { x: maskSurface.host._holeRight; y: maskSurface.host._holeTop }
        }

        ShapePath {
            fillColor: maskSurface.host.maskColor
            strokeColor: Enums.transparent
            strokeWidth: 0
            PathMove { x: maskSurface.host._holeRight; y: maskSurface.host._holeBottom }
            PathLine {
                x: maskSurface.host._holeRight
                y: maskSurface.host._holeBottom - maskSurface.host._currentHighlightRadius
            }
            PathArc {
                x: maskSurface.host._holeRight - maskSurface.host._currentHighlightRadius
                y: maskSurface.host._holeBottom
                radiusX: maskSurface.host._currentHighlightRadius
                radiusY: maskSurface.host._currentHighlightRadius
                direction: PathArc.Clockwise
            }
            PathLine { x: maskSurface.host._holeRight; y: maskSurface.host._holeBottom }
        }

        ShapePath {
            fillColor: maskSurface.host.maskColor
            strokeColor: Enums.transparent
            strokeWidth: 0
            PathMove { x: maskSurface.host._holeLeft; y: maskSurface.host._holeBottom }
            PathLine {
                x: maskSurface.host._holeLeft + maskSurface.host._currentHighlightRadius
                y: maskSurface.host._holeBottom
            }
            PathArc {
                x: maskSurface.host._holeLeft
                y: maskSurface.host._holeBottom - maskSurface.host._currentHighlightRadius
                radiusX: maskSurface.host._currentHighlightRadius
                radiusY: maskSurface.host._currentHighlightRadius
                direction: PathArc.Clockwise
            }
            PathLine { x: maskSurface.host._holeLeft; y: maskSurface.host._holeBottom }
        }
    }
}
