// NavigationPanelShadow - Expanded navigation panel edge shadow 展开导航面板边缘阴影
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

import QtQuick
import QtQuick.Effects
import ".."

// Casts the pane elevation onto the content area while the pane is expanded.
// Include the rounded corner cutouts, then mask away the pane interior. A
// rectangular clip at the right edge leaves bright wedges beside the curves.
// 阴影包含圆角外侧的凹入区域，再遮掉面板内部；沿最右边直线裁剪会在圆弧旁露出亮角。
Item {
    id: root

    // ==================== Required Props 必需属性 ====================
    required property var panel   // Panel that owns the shadow 拥有阴影的面板
    required property bool active // Expanded state that raises the pane 让面板浮起的展开状态

    // ==================== Readonly State 只读状态 ====================
    readonly property real _paneWidth: root.panel ? root.panel.width : 0
    readonly property real _paneRadius: Enums.surfaceRadius(Enums.radius.large)
    readonly property real _shadowBlur: Enums.shadow.level8.blur

    // ==================== Size 尺寸 ====================
    objectName: "navigationPanelShadow"
    anchors.left: parent.left
    anchors.leftMargin: Math.max(0, root._paneWidth - root._paneRadius)
    anchors.top: parent.top
    anchors.bottom: parent.bottom
    // Only allocate the narrow band containing the curved edge and its shadow.
    // 只为包含圆弧边缘及阴影的窄条分配纹理，避免整窗离屏绘制。
    width: root._paneRadius + root._shadowBlur + Enums.shadow.level8.offset
    clip: true
    // Fade in step with the pane width so neither end of the transition pops.
    // 与面板宽度同步淡入淡出，避免过渡两端出现跳变。
    opacity: root.active ? Enums.opacityLevel.visible : Enums.opacityLevel.invisible
    visible: opacity > Enums.opacityLevel.invisible
             && Enums.usesSoftElevation && !Enums.isNeumorphism
    layer.enabled: visible
    layer.effect: MultiEffect {
        maskEnabled: true
        maskInverted: true
        maskThresholdMin: Enums.mask.thresholdMin
        maskSpreadAtMin: Enums.mask.spreadFull
        maskSource: ShaderEffectSource {
            hideSource: true
            live: true
            smooth: true
            sourceItem: Item {
                width: root.width
                height: root.height

                Rectangle {
                    x: shadowSource.x
                    width: root._paneWidth
                    height: parent.height
                    topLeftRadius: Enums.radius.none
                    bottomLeftRadius: Enums.radius.none
                    topRightRadius: root._paneRadius
                    bottomRightRadius: root._paneRadius
                    antialiasing: true
                    color: Enums.textColor.primary
                }
            }
        }
    }

    // ==================== Content 内容 ====================
    // Match the visible pane; extending above/below it creates a square slab.
    // 轮廓与可见面板一致；上下外扩会让阴影变成无圆角的底板。
    Item {
        id: shadowSource

        objectName: "navigationPanelShadowSource"
        x: -root.x
        width: root._paneWidth
        height: parent.height
    }

    RectangularShadow {
        anchors.fill: shadowSource
        radius: root._paneRadius
        color: Enums.shadow.level8.color
        blur: Enums.shadow.level8.blur
        offset.x: Enums.shadow.level8.offset
        offset.y: 0
    }

    Behavior on opacity {
        NumberAnimation {
            duration: Enums.duration.medium
            easing.type: Easing.OutCubic
        }
    }
}
