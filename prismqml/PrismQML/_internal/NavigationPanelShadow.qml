// NavigationPanelShadow - Expanded navigation panel edge shadow 展开导航面板边缘阴影
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

import QtQuick
import QtQuick.Effects
import ".."

// Casts the pane elevation onto the content area while the pane is expanded.
// The pane is flush with the window edges, so only its outer edge can carry a
// shadow: this layer starts at the pane edge and clips away everything inside
// the pane, keeping the pane surface clean even when Mica makes it translucent.
// 面板展开时把高度投影到内容区。面板与窗口边缘齐平，因此只有外缘能承载阴影：
// 本层从面板边缘开始并裁掉面板内部的一切，使面板表面即使因云母而半透明也保持干净。
Item {
    id: root

    // ==================== Required Props 必需属性 ====================
    required property var panel   // Panel that owns the shadow 拥有阴影的面板
    required property bool active // Expanded state that raises the pane 让面板浮起的展开状态

    // ==================== Readonly State 只读状态 ====================
    readonly property real _paneWidth: root.panel ? root.panel.width : 0
    readonly property real _shadowBlur: Enums.shadow.level8.blur

    // ==================== Size 尺寸 ====================
    objectName: "navigationPanelShadow"
    anchors.left: parent.left
    anchors.leftMargin: root._paneWidth
    anchors.top: parent.top
    anchors.right: parent.right
    anchors.bottom: parent.bottom
    // Clip boundary follows the animated pane edge. 裁剪边界跟随动画中的面板边缘。
    clip: true
    // Fade in step with the pane width so neither end of the transition pops.
    // 与面板宽度同步淡入淡出，避免过渡两端出现跳变。
    opacity: root.active ? Enums.opacityLevel.visible : Enums.opacityLevel.invisible
    visible: opacity > Enums.opacityLevel.invisible
             && Enums.usesSoftElevation && !Enums.isNeumorphism

    // ==================== Content 内容 ====================
    // Panel silhouette; the clip above discards everything inside the pane.
    // 面板轮廓；上方的裁剪会丢弃面板内部的一切。
    Item {
        id: shadowSource

        objectName: "navigationPanelShadowSource"
        x: -root._paneWidth
        y: -root._shadowBlur
        width: root._paneWidth
        height: parent.height + root._shadowBlur * 2
    }

    RectangularShadow {
        anchors.fill: shadowSource
        // Extend the source beyond the clipped top/bottom so only the outer
        // vertical seam contributes shadow pixels; no rounded corner lobe can
        // protrude into the title/content junction.
        // 阴影源上下越过裁剪层，使这里只产生外侧垂直接缝的阴影像素；
        // 不再让圆角阴影在标题栏/内容接缝处形成突出的暗块。
        radius: Enums.radius.none
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
