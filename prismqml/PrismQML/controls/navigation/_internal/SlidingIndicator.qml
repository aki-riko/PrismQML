// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// SlidingIndicator - Shared sliding indicator public base 统一滑动指示器公开基类
// Uses SlidingIndicatorAnimation with sticky stretch by default 默认使用带粘滞拉伸的SlidingIndicatorAnimation
// Exposes setGeometry, startAnimation, and moveToItem 对外提供setGeometry、startAnimation和moveToItem
// Used by navigation controls and segmented selectors 用于导航控件和分段选择器
Item {
    id: root

    // ==================== Public Props 公开属性 ====================
    // Main-axis orientation 主轴方向
    property int orientation: Qt.Vertical

    // Animation mode: stretch, spring, or instant 动画模式：拉伸、弹簧或立即切换
    property string mode: "stretch"

    // Default indicator size; callers constrain the fixed edge 默认指示器尺寸，固定边由调用方约束
    property int indicatorWidth: orientation === Qt.Horizontal
        ? Enums.controlSize.navIndicatorHeight
        : Enums.controlSize.topNavIndicatorHeight
    property int indicatorHeight: orientation === Qt.Horizontal
        ? Enums.controlSize.topNavIndicatorHeight
        : Enums.controlSize.navIndicatorHeight

    // Corner radius 圆角
    property real radius: Enums.radius.micro

    // Theme-aware colors 主题感知颜色
    property color indicatorColor: Enums.accentColor
    property color lightColor: Enums.accentColor
    property color darkColor: Enums.accentColor

    // Disable animation to force instant mode 禁用动画时强制使用立即切换模式
    property bool animationEnabled: true

    // Current animation state 当前动画状态
    readonly property bool running: animation.running

    // ==================== Internal Props 内部属性 ====================
    property bool _initialized: false
    readonly property string _effectiveMode: animationEnabled ? mode : "instant"

    // ==================== Signals 信号 ====================
    signal animationFinished()

    // ==================== Public Methods 公开方法 ====================
    // Animate from startRect to endRect; useCrossFade is reserved 从startRect动画到endRect，useCrossFade为保留参数
    function startAnimation(startRect, endRect, useCrossFade) {
        if (!animationEnabled) {
            setGeometry(endRect)
            return
        }
        _initialized = true
        animation.animateTo(startRect, endRect)
    }

    function stopAnimation() {
        animation.stopAnimation()
    }

    // Set geometry directly without animation 直接设置几何且不播放动画
    function setGeometry(rect) {
        _initialized = true
        animation.setGeometry(rect)
    }

    // Return the current indicator rectangle 获取当前指示器矩形
    function getIndicatorRect() {
        return Qt.rect(indicator.x, indicator.y, indicator.width, indicator.height)
    }

    // Move to a target item 便捷移动到目标项
    // targetItem and prevItem provide x, y, width, and height 目标项和前项提供几何属性
    function _rectForItem(item) {
        if (orientation === Qt.Horizontal) {
            // Center the horizontal indicator at the bottom 水平指示器在底部居中
            return Qt.rect(
                item.x + (item.width - indicatorWidth) / 2,
                item.y + item.height - indicatorHeight,
                indicatorWidth, indicatorHeight)
        }
        // Center the vertical indicator on the left 垂直指示器在左侧居中
        return Qt.rect(
            item.x,
            item.y + (item.height - indicatorHeight) / 2,
            indicatorWidth, indicatorHeight)
    }

    function moveToItem(targetItem, prevItem) {
        if (!targetItem) return
        var endRect = _rectForItem(targetItem)
        if (prevItem && _initialized && animationEnabled) {
            startAnimation(_rectForItem(prevItem), endRect)
        } else {
            setGeometry(endRect)
        }
    }

    // ==================== Content 内容 ====================
    Rectangle {
        id: indicator
        x: animation.indicatorX
        y: animation.indicatorY
        width: animation.indicatorWidth
        height: animation.indicatorHeight
        radius: root.radius
        color: root.indicatorColor
        visible: root._initialized
        antialiasing: true

        Binding {
            target: indicator
            property: "color"
            value: Enums.isDark ? root.darkColor : root.lightColor
            when: root.lightColor !== root.darkColor
        }
    }

    // Animation engine 动画引擎
    SlidingIndicatorAnimation {
        id: animation
        orientation: root.orientation
        mode: root._effectiveMode
        onFinished: root.animationFinished()
    }
}
