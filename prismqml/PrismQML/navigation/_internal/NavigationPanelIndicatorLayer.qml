// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "../../controls/navigation/_internal"

// NavigationPanelIndicatorLayer - Clipped navigation indicator surface 导航指示器裁剪层
Item {
    id: indicatorLayer

    // ==================== Required Props 必需属性 ====================
    required property var host

    // ==================== Readonly State 只读状态 ====================
    readonly property bool running: indicator.running

    // ==================== Internal Methods 内部方法 ====================
    function setGeometry(rect) {
        indicator.setGeometry(rect)
    }

    function startAnimation(startRect, endRect) {
        if (indicator.startAnimation) {
            indicator.startAnimation(startRect, endRect)
        } else {
            indicator.setGeometry(endRect)
        }
    }

    function stopAnimation() {
        indicator.stopAnimation()
    }

    // ==================== Content 内容 ====================
    anchors.top: parent.top
    anchors.left: parent.left
    anchors.right: parent.right
    height: (host._currentKey !== "" || indicator.running)
            ? host.height
            : host.indicatorClipBottom
    clip: true
    // Keep high Z while animating, otherwise backward anim gets covered by bottom items.
    // 动画进行中保持高 Z，否则反向动画启动时会被底部项遮住。
    z: (host._currentKey !== "" || indicator.running)
        ? (Enums.zIndex.controlsAbove + 1)
        : (Enums.zIndex.controls - 1)

    SlidingIndicator {
        id: indicator
        x: host.indicatorX
        orientation: Qt.Vertical
        mode: "stretch"
        indicatorWidth: host.indicatorWidth
        indicatorHeight: host.indicatorHeight
        radius: Enums.radius.micro
        animationEnabled: host.indicatorAnimationEnabled
        // Outlined skins use the selected paper block instead of a second accent strip.
        // 描边皮肤使用选中纸面块，不再叠加第二条强调指示线。
        visible: !Enums.hasOutlinedSurfaces && host._indicatorVisible
        // Track the selected item's scroll fade; the indicator sits outside the viewport.
        // 跟随选中项的滚动渐隐；指示器在视口之外。
        opacity: host.indicatorOpacity
    }
}
