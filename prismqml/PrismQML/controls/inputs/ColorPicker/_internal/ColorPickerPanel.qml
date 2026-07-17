// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// ColorPickerPanel - Hue/Saturation selection panel 色相/饱和度选择面板
// Layout: Horizontal hue (0-360), vertical saturation (full to white) 布局：水平色相（0-360），垂直饱和度（全色到白色）
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property real hue: Enums.colorPickerMetrics.dialogHueDefault  // Normalized hue mapped to 0-360 degrees 映射到 0-360 度的归一化色相
    property real saturation: Enums.colorPickerMetrics.dialogSaturationDefault  // Full at top, white at bottom 顶部全色，底部白色
    property real brightness: Enums.colorPickerMetrics.dialogBrightnessDefault  // Brightness adjustment 亮度调整

    // ==================== Signals 信号 ====================
    signal colorChanged(real h, real s)

    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.colorPickerMetrics.dialogPanelSize
    implicitHeight: Enums.colorPickerMetrics.panelDefaultHeight

    // Repaint when brightness changes 亮度变化时重绘
    onBrightnessChanged: canvas.requestPaint()

    // ==================== Content 内容 ====================
    // Hue/saturation canvas 色相/饱和度画布
    Canvas {
        id: canvas
        anchors.fill: parent

        onPaint: {
            var ctx = getContext("2d")
            var w = width, h = height

            // Draw hue gradient horizontally 水平绘制色相渐变
            for (var x = Enums.opacityLevel.invisible; x < w; x++) {
                var hueValue = x / w
                // Vertical gradient from saturated color to white 垂直渐变由饱和色过渡到白色
                var gradient = ctx.createLinearGradient(x, Enums.opacityLevel.invisible, x, h)
                gradient.addColorStop(Enums.opacityLevel.invisible, Qt.hsva(hueValue, Enums.opacityLevel.visible, control.brightness, Enums.opacityLevel.visible).toString())
                gradient.addColorStop(Enums.opacityLevel.visible, Qt.hsva(hueValue, Enums.opacityLevel.invisible, control.brightness, Enums.opacityLevel.visible).toString())
                ctx.fillStyle = gradient
                ctx.fillRect(x, Enums.opacityLevel.invisible, Enums.colorPickerMetrics.panelCanvasColumnWidth, h)
            }
        }

        Component.onCompleted: requestPaint()
    }

    // Selection circle 选择圆圈
    Rectangle {
        id: selector
        width: Enums.spacing.xl
        height: Enums.spacing.xl
        radius: width / 2
        color: Enums.transparent
        border.width: Enums.border.normal
        border.color: {
            // Use contrasting border color 使用对比边框色
            var lum = control.brightness * (Enums.opacityLevel.visible - control.saturation * Enums.colorPickerMetrics.panelSelectorLuminanceFactor)
            return lum > Enums.colorPickerMetrics.panelSelectorLuminanceThreshold
                ? Enums.colorPickerGradient.lightnessDark
                : Enums.colorPickerGradient.lightnessLight
        }

        x: Math.max(Enums.opacityLevel.invisible, Math.min(parent.width - width, control.hue * parent.width - width / 2))
        y: Math.max(Enums.opacityLevel.invisible, Math.min(parent.height - height, (Enums.opacityLevel.visible - control.saturation) * parent.height - height / 2))

        Behavior on x { NumberAnimation { duration: Enums.duration.fast } }
        Behavior on y { NumberAnimation { duration: Enums.duration.fast } }
    }

    // Interaction 交互
    MouseArea {
        function updateColor(mouse) {
            control.hue = Math.max(Enums.opacityLevel.invisible, Math.min(Enums.opacityLevel.visible, mouse.x / width))
            control.saturation = Math.max(Enums.opacityLevel.invisible, Math.min(Enums.opacityLevel.visible, Enums.opacityLevel.visible - mouse.y / height))
            control.colorChanged(control.hue, control.saturation)
        }

        anchors.fill: parent
        enabled: control.enabled
        preventStealing: true

        onPressed: (mouse) => updateColor(mouse)
        onPositionChanged: (mouse) => { if (pressed) updateColor(mouse) }
    }

    // Border 边框
    Rectangle {
        anchors.fill: parent
        color: Enums.transparent
        radius: Enums.isPrismDesign ? Enums.prismDesign.radiusCard : Enums.radius.large
        border.width: Enums.border.thin
        border.color: Enums.stateColor.border
    }
}
