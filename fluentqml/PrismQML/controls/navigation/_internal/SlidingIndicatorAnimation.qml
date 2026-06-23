// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."

// SlidingIndicatorAnimation - 滑动指示器动画引擎 (统一基类内核)
// 独立"橡皮筋"粘滞算法 (非 Pivot 两段式 SequentialAnimation):
//   指示器拆为前缘(lead)/后缘(trail)两条边, 各跑一个 NumberAnimation。
//   朝运动方向的前缘用短时长先到位, 背向的后缘用长时长慢追。
//   中间 长度=|lead-trail| 被自然拉大再收回 → 橡皮筋粘滞, 方向自适应。
// 主轴 (orientation 决定) 走橡皮筋; 副轴 (固定边) 用快速跟随。
// 用于: NavigationBar / NavigationView / Pivot / SegmentedControl / ToggleNavigationBar
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

    // ==================== Signals 信号 ====================
    signal finished()

    // ==================== Internal Geometry 内部几何 ====================
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

    // ==================== Output Geometry 输出几何 ====================
    readonly property real _mainPos: mode === "spring" ? _springPos : Math.min(_near, _far)
    readonly property real _mainLen: mode === "spring" ? _springLen : Math.abs(_far - _near)

    readonly property real indicatorX: _isH ? _mainPos : _crossPos
    readonly property real indicatorY: _isH ? _crossPos : _mainPos
    readonly property real indicatorWidth: _isH ? _mainLen : _crossLen
    readonly property real indicatorHeight: _isH ? _crossLen : _mainLen

    // ==================== Helpers 几何拆分 ====================
    // 把 rect 拆成 主轴(pos,len) + 副轴(pos,len)
    function _mainOf(rect) { return _isH ? { p: rect.x, l: rect.width } : { p: rect.y, l: rect.height } }
    function _crossOf(rect) { return _isH ? { p: rect.y, l: rect.height } : { p: rect.x, l: rect.width } }

    // ==================== Public Methods 公开方法 ====================
    // 直接设几何, 无动画
    function setGeometry(rect) {
        nearAnim.stop(); farAnim.stop()
        _immediate = true   // 禁用所有 Behavior, 保证瞬间定位
        var m = _mainOf(rect), c = _crossOf(rect)
        _crossPos = c.p; _crossLen = c.l
        _near = m.p; _far = m.p + m.l
        _springPos = m.p; _springLen = m.l
        _immediate = false
    }

    // 从 startRect 动画到 endRect
    function animateTo(startRect, endRect) {
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
            return
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
            return
        }

        // ===== stretch 橡皮筋 =====
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

        nearAnim.from = startNear; nearAnim.to = endNear
        farAnim.from = startFar; farAnim.to = endFar

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
    }

    function stopAnimation() {
        nearAnim.stop(); farAnim.stop()
    }

    // ==================== stretch: 两条边独立动画 ====================
    NumberAnimation {
        id: nearAnim
        target: root; property: "_near"
        easing.type: Easing.OutCubic
        onStopped: if (!farAnim.running) root.finished()
    }
    NumberAnimation {
        id: farAnim
        target: root; property: "_far"
        easing.type: Easing.OutCubic
        onStopped: if (!nearAnim.running) root.finished()
    }

    // ==================== 副轴: 快速跟随 ====================
    Behavior on _crossPos {
        enabled: root.mode !== "instant" && !root._immediate
        NumberAnimation { id: crossPosAnim; duration: Enums.duration.medium; easing.type: Easing.OutCubic }
    }
    Behavior on _crossLen {
        enabled: root.mode !== "instant" && !root._immediate
        NumberAnimation { id: crossLenAnim; duration: Enums.duration.medium; easing.type: Easing.OutCubic }
    }

    // ==================== spring: 弹簧物理 ====================
    Behavior on _springPos {
        enabled: root.mode === "spring" && !root._immediate
        SpringAnimation { id: springPosAnim; spring: 3; damping: 0.35; mass: 1; epsilon: 0.5 }
    }
    Behavior on _springLen {
        enabled: root.mode === "spring" && !root._immediate
        SpringAnimation { id: springLenAnim; spring: 3; damping: 0.35; mass: 1; epsilon: 0.5 }
    }
}
