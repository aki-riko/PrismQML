// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."

// SlidingIndicator - 统一滑动指示器 (公开基类)
// 内核为 SlidingIndicatorAnimation, 默认 stretch 橡皮筋粘滞。
// 对外保留历史 NavigationIndicator 调用: setGeometry / startAnimation / moveToItem。
// 用于: NavigationBar / NavigationView / Pivot / SegmentedControl / ToggleNavigationBar
Item {
    id: root

    // ==================== Public Props 公开属性 ====================
    // 主轴方向
    property int orientation: Qt.Vertical

    // 动画模式: "stretch"(橡皮筋粘滞) / "spring"(弹簧) / "instant"
    property string mode: "stretch"

    // 指示器尺寸 (固定边由调用方约束, 这里给默认)
    property int indicatorWidth: orientation === Qt.Horizontal
        ? Enums.controlSize.navIndicatorHeight
        : Enums.controlSize.topNavIndicatorHeight
    property int indicatorHeight: orientation === Qt.Horizontal
        ? Enums.controlSize.topNavIndicatorHeight
        : Enums.controlSize.navIndicatorHeight

    // 圆角
    property real radius: Enums.radius.micro

    // 颜色 (随主题)
    property color indicatorColor: Enums.accentColor
    property color lightColor: Enums.accentColor
    property color darkColor: Enums.accentColor

    // 是否启用动画 (false → mode 退化为 instant)
    property bool animationEnabled: true

    // 当前动画状态
    readonly property bool running: animation.running

    // ==================== Signals 信号 ====================
    signal animationFinished()

    // ==================== Internal 内部 ====================
    property bool _initialized: false
    readonly property string _effectiveMode: animationEnabled ? mode : "instant"

    // ==================== Public Methods 公开方法 ====================
    // 从 startRect 动画到 endRect (第三参 useCrossFade 保留占位, 当前不使用)
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

    // 直接设几何, 无动画
    function setGeometry(rect) {
        _initialized = true
        animation.setGeometry(rect)
    }

    // 获取当前矩形
    function getIndicatorRect() {
        return Qt.rect(indicator.x, indicator.y, indicator.width, indicator.height)
    }

    // ==================== Convenience 便捷: 移动到目标项 ====================
    // targetItem / prevItem: 带 x,y,width,height 的 Item
    function _rectForItem(item) {
        if (orientation === Qt.Horizontal) {
            // 水平: 指示器在底部居中
            return Qt.rect(
                item.x + (item.width - indicatorWidth) / 2,
                item.y + item.height - indicatorHeight,
                indicatorWidth, indicatorHeight)
        }
        // 垂直: 指示器在左侧居中
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

    // ==================== Indicator Rectangle 指示器矩形 ====================
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

    // ==================== Animation Engine 动画引擎 ====================
    SlidingIndicatorAnimation {
        id: animation
        orientation: root.orientation
        mode: root._effectiveMode
        onFinished: root.animationFinished()
    }
}
