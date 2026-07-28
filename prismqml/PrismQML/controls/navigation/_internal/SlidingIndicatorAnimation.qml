// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// SlidingIndicatorAnimation - Shared sliding-indicator animation engine 统一滑动指示器动画引擎
// Uses independent lead and trail edges for sticky stretch 使用独立前缘和后缘实现粘滞拉伸
// The leading edge arrives quickly while the trailing edge follows slowly 前缘快速到位，后缘缓慢跟随
// Their distance stretches and contracts with direction-aware motion 两边距离随方向自适应地拉伸和收回
// The main axis stretches while the cross axis follows quickly 主轴执行拉伸，副轴快速跟随
// Used by navigation and segmented controls 用于导航控件与分段控件
Item {
    id: root

    // ==================== Public Props 公开属性 ====================
    // 主轴方向: Qt.Vertical → Y/Height 为主轴; Qt.Horizontal → X/Width 为主轴
    property int orientation: Qt.Vertical

    // 动画模式: "stretch"(橡皮筋粘滞) / "spring"(弹簧) / "instant"(无动画)
    property string mode: "stretch"

    // 橡皮筋时长: 前缘(快) / 后缘(慢), 差值越大粘滞越明显
    property int leadDuration: Enums.duration.medium   // 200ms
    property int trailDuration: Enums.duration.dialog   // 400ms

    // 是否正在动画 (引用各 Animation 的 running, Behavior 本身无可靠 running)
    readonly property bool running: nearAnim.running || farAnim.running
                                    || crossPosAnim.running || crossLenAnim.running
                                    || springPosAnim.running || springLenAnim.running

    // ==================== Internal Props 内部属性 ====================
    readonly property bool _isH: orientation === Qt.Horizontal

    // 立即定位守卫: 为真时所有 Behavior 禁用 (setGeometry 真正无动画)
    property bool _immediate: false

    // 主轴两条边 (橡皮筋驱动): near = 小坐标边(左/上), far = 大坐标边(右/下)
    property real _near: 0
    property real _far: 0
    // 副轴 (固定边, 快速跟随): cross 位置 + 长度
    property real _crossPos: 0
    property real _crossLen: 0
    // spring 模式专用 (整体平移 + 长度弹簧)
    property real _springPos: 0
    property real _springLen: 0
    property real _targetNear: 0
    property real _targetFar: 0

    // ==================== Readonly State 只读状态 ====================
    readonly property real _mainPos: mode === "spring" ? _springPos : Math.min(_near, _far)
    readonly property real _mainLen: mode === "spring" ? _springLen : Math.abs(_far - _near)

    readonly property real indicatorX: _isH ? _mainPos : _crossPos
    readonly property real indicatorY: _isH ? _crossPos : _mainPos
    readonly property real indicatorWidth: _isH ? _mainLen : _crossLen
    readonly property real indicatorHeight: _isH ? _crossLen : _mainLen

    // ==================== Signals 信号 ====================
    signal finished()

    // ==================== Internal Methods 内部方法 ====================
    // 把 rect 拆成 主轴(pos,len) + 副轴(pos,len)
    function _mainOf(rect) { return _isH ? { p: rect.x, l: rect.width } : { p: rect.y, l: rect.height } }
    function _crossOf(rect) { return _isH ? { p: rect.y, l: rect.height } : { p: rect.x, l: rect.width } }

    // Reject incomplete or non-finite geometry before it reaches QML real properties.
    // 在不完整或非有限几何进入 QML real 属性前拒绝它。
    function _isFiniteRect(rect) {
        return rect !== null && rect !== undefined
                && typeof rect.x === "number" && isFinite(rect.x)
                && typeof rect.y === "number" && isFinite(rect.y)
                && typeof rect.width === "number" && isFinite(rect.width)
                && typeof rect.height === "number" && isFinite(rect.height)
    }

    // ==================== Public Methods 公开方法 ====================
    // 直接设几何, 无动画
    function setGeometry(rect) {
        if (!_isFiniteRect(rect)) return false
        nearAnim.stop(); farAnim.stop()
        _immediate = true   // 禁用所有 Behavior, 保证瞬间定位
        var m = _mainOf(rect), c = _crossOf(rect)
        _crossPos = c.p; _crossLen = c.l
        _near = m.p; _far = m.p + m.l
        _springPos = m.p; _springLen = m.l
        _immediate = false
        return true
    }

    // 从 startRect 动画到 endRect
    function animateTo(startRect, endRect) {
        if (!_isFiniteRect(startRect) || !_isFiniteRect(endRect)) return false
        var ms = _mainOf(startRect), me = _mainOf(endRect)
        var ce = _crossOf(endRect)

        if (mode === "instant") {
            nearAnim.stop(); farAnim.stop()
            _immediate = true
            _crossPos = ce.p; _crossLen = ce.l
            _near = me.p; _far = me.p + me.l
            _springPos = me.p; _springLen = me.l
            _immediate = false
            root.finished()
            return true
        }

        // 副轴快速跟随 (位置/长度差异由 Behavior 平滑)
        _crossPos = ce.p
        _crossLen = ce.l

        if (mode === "spring") {
            // 弹簧: 直接赋目标值, Behavior 内 SpringAnimation 驱动
            _springPos = me.p
            _springLen = me.l
            // near/far 同步, 保证 mode 切换无跳变 (immediate 避免触发橡皮筋路径)
            _immediate = true
            _near = me.p; _far = me.p + me.l
            _immediate = false
            return true
        }

        // Stretch mode 橡皮筋模式
        nearAnim.stop(); farAnim.stop()

        var startNear = ms.p, startFar = ms.p + ms.l
        var endNear = me.p, endFar = me.p + me.l

        // 朝运动方向: forward = 向大坐标移动 (下/右)
        var forward = endNear >= startNear

        // 瞬置到起点 (无动画), 再由 nearAnim/farAnim 驱动到终点
        _immediate = true
        _near = startNear
        _far = startFar
        _immediate = false

        _targetNear = endNear
        _targetFar = endFar

        if (forward) {
            // far(下/右边) 是前缘, 先到; near(上/左边) 后随
            farAnim.duration = leadDuration
            nearAnim.duration = trailDuration
        } else {
            // near(上/左边) 是前缘, 先到; far(下/右边) 后随
            nearAnim.duration = leadDuration
            farAnim.duration = trailDuration
        }

        nearAnim.start()
        farAnim.start()
        return true
    }

    function stopAnimation() {
        nearAnim.stop(); farAnim.stop()
    }

    // ==================== Content 内容 ====================
    // Independent stretch-edge animations 橡皮筋两条边独立动画
    NumberAnimation {
        id: nearAnim
        target: root; property: "_near"
        to: root._targetNear
        easing.type: Easing.OutCubic
        onStopped: if (!farAnim.running) root.finished()
    }
    NumberAnimation {
        id: farAnim
        target: root; property: "_far"
        to: root._targetFar
        easing.type: Easing.OutCubic
        onStopped: if (!nearAnim.running) root.finished()
    }

    // Fast cross-axis following 副轴快速跟随
    Behavior on _crossPos {
        enabled: root.mode !== "instant" && !root._immediate
        NumberAnimation { id: crossPosAnim; duration: Enums.duration.medium; easing.type: Easing.OutCubic }
    }
    Behavior on _crossLen {
        enabled: root.mode !== "instant" && !root._immediate
        NumberAnimation { id: crossLenAnim; duration: Enums.duration.medium; easing.type: Easing.OutCubic }
    }

    // Spring physics 弹簧物理
    Behavior on _springPos {
        enabled: root.mode === "spring" && !root._immediate
        SpringAnimation { id: springPosAnim; spring: 3; damping: 0.35; mass: 1; epsilon: 0.5 }
    }
    Behavior on _springLen {
        enabled: root.mode === "spring" && !root._immediate
        SpringAnimation { id: springLenAnim; spring: 3; damping: 0.35; mass: 1; epsilon: 0.5 }
    }
}
