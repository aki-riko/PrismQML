// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "_internal" as ScrollBarInternal

// SmoothScrollHelper - Reusable smooth scroll logic 可复用平滑滚动逻辑
// Usage 用法:
//   SmoothScrollHelper { target: listView; handleWheel: true }  // Auto handle wheel 自动处理滚轮
//   SmoothScrollHelper { target: listView }  // Manual: scrollHelper.scrollBy(...) 手动调用
Item {
    id: helper
    
    // ==================== Required Props 必需属性 ====================
    required property Flickable target  // Target view (ListView/GridView/Flickable) 目标视图

    // ==================== Public Props 公开属性 ====================
    property int orientation: Qt.Vertical  // Qt.Vertical or Qt.Horizontal 滚动方向
    property int duration: Enums.duration.scroll
    property real step: Enums.spacing.xxxl * 3  // Scroll step per wheel tick 每次滚轮滚动距离
    property int easing: Easing.OutQuart
    property bool bounceEnabled: true  // Enable overshoot bounce 启用边界回弹
    property bool handleWheel: false  // Auto handle mouse wheel 自动处理鼠标滚轮
    // ==================== Internal Props 内部属性 ====================
    // Timeline enables the visual overshoot layer; other Flickables keep native overshoot.
    // Timeline 启用视觉超出位移层；其他 Flickable 保持原生超出路径。
    property bool _visualOvershootEnabled: false
    // Vertical state 垂直状态
    property real _targetY: 0
    property real _smoothY: 0
    property bool _isOvershotV: false
    property bool _isOutwardBounceV: false
    property bool _discardingStaleFrameV: false
    property real _lastPublishedY: 0
    property double _lastBounceFrameTimestampV: 0
    property int _boundaryTargetV: 0  // -1=start, 0=absolute, 1=end
    
    // Horizontal state 水平状态
    property real _targetX: 0
    property real _smoothX: 0
    property bool _isOvershotH: false
    property bool _isOutwardBounceH: false
    property bool _discardingStaleFrameH: false
    property real _lastPublishedX: 0
    property double _lastBounceFrameTimestampH: 0
    property int _boundaryTargetH: 0  // -1=start, 0=absolute, 1=end
    property QtObject _bounceTimerV: null
    property QtObject _bounceTimerH: null
    property real _devicePixelRatio: 1.0

    // The guards and the reconciler reach the drivers through scrollHelper, and an
    // id is not visible outside this component, so each child is also exposed as a
    // property here. 门闸与校正器经 scrollHelper 访问驱动器，而 id 在组件外不可见，
    // 故每个子对象在此另以属性暴露。
    readonly property QtObject verticalFrameDriver: verticalFrameDriverObject
    readonly property QtObject horizontalFrameDriver: horizontalFrameDriverObject
    readonly property QtObject verticalOvershootGuard: verticalOvershootGuardObject
    readonly property QtObject horizontalOvershootGuard: horizontalOvershootGuardObject
    readonly property QtObject boundsReconciler: boundsReconcilerObject
    // _syncing = true 时禁用动画, 让 ScrollBar 拖拽场景下 contentX/Y 立即跟随 handle,
    // 不被 Behavior 平滑过渡反向拖拽.
    property bool _syncing: false

    // ==================== Readonly State 只读状态 ====================
    readonly property real targetPos: _isVertical ? _targetY : _targetX
    readonly property real smoothPos: _isVertical ? _smoothY : _smoothX
    readonly property real minScroll: _isVertical ? _minY : _minX
    readonly property real maxScroll: _isVertical ? _maxY : _maxX
    readonly property bool isOvershot: _isVertical ? _isOvershotV : _isOvershotH
    readonly property real _visualOvershootOffset: !_visualOvershootEnabled ? 0
        : (_isVertical
            ? _visualOvershootFor(_smoothY, _minY, _maxY)
            : _visualOvershootFor(_smoothX, _minX, _maxX))
    readonly property bool _isVertical: orientation === Qt.Vertical
    readonly property real _minY: target ? target.originY : 0
    readonly property real _minX: target ? target.originX : 0
    readonly property real _maxY: _minY + Math.max(0, target.contentHeight - target.height)
    readonly property real _maxX: _minX + Math.max(0, target.contentWidth - target.width)
    readonly property real _maxOvershoot: Enums.spacing.scrollOvershoot

    // ==================== Public Methods 公开方法 ====================
    // Scroll to absolute position 滚动到绝对位置
    function scrollTo(pos) {
        _refreshDevicePixelRatio()
        if (_isVertical) {
            _boundaryTargetV = 0
            _scrollToY(pos)
        } else {
            _boundaryTargetH = 0
            _scrollToX(pos)
        }
    }
    // Scroll by delta 相对滚动
    function scrollBy(delta) {
        _refreshDevicePixelRatio()
        if (_isVertical) {
            _boundaryTargetV = 0
            _scrollByY(delta)
        } else {
            _boundaryTargetH = 0
            _scrollByX(delta)
        }
    }
    // Scroll to top/left 滚动到顶部/左侧
    function scrollToStart() {
        _refreshDevicePixelRatio()
        if (_isVertical) {
            _boundaryTargetV = -1
            _scrollToY(_minY)
        } else {
            _boundaryTargetH = -1
            _scrollToX(_minX)
        }
    }
    // Scroll to bottom/right 滚动到底部/右侧
    function scrollToEnd() {
        _refreshDevicePixelRatio()
        if (_isVertical) {
            _boundaryTargetV = 1
            _scrollToY(_maxY)
        } else {
            _boundaryTargetH = 1
            _scrollToX(_maxX)
        }
    }
    // Sync position (call after drag) 同步位置（拖拽后调用）
    function syncPosition() {
        _refreshDevicePixelRatio()
        _syncing = true
        if (_isVertical) {
            _stopBounceTimer(true)
            _isOutwardBounceV = false
            _boundaryTargetV = 0
            _targetY = target.contentY
            verticalFrameDriver.moveTo(target.contentY)
        } else {
            _stopBounceTimer(false)
            _isOutwardBounceH = false
            _boundaryTargetH = 0
            _targetX = target.contentX
            horizontalFrameDriver.moveTo(target.contentX)
        }
        _syncing = false
    }
    // ==================== Internal Methods 内部方法 ====================
    function _clamp(value, minimum, maximum) {
        return Math.max(minimum, Math.min(maximum, value))
    }

    function _setSmoothPosition(verticalAxis, value) {
        if (verticalAxis) _smoothY = value
        else _smoothX = value
    }
    function _onFrameDriverSettled(verticalAxis) {
        if (verticalAxis && !_isOutwardBounceV && _isOvershotV && _smoothY === _targetY) _isOvershotV = false
        else if (!verticalAxis && !_isOutwardBounceH && _isOvershotH && _smoothX === _targetX) _isOvershotH = false
    }
    function _refreshDevicePixelRatio() {
        if (typeof WindowHelper === "undefined" || !WindowHelper
                || typeof WindowHelper.devicePixelRatioAt !== "function") {
            _devicePixelRatio = 1.0
            return
        }
        var globalCenter = target.mapToGlobal(target.width / 2, target.height / 2)
        var ratio = WindowHelper.devicePixelRatioAt(
            Math.round(globalCenter.x), Math.round(globalCenter.y)
        )
        _devicePixelRatio = ratio > 0 ? ratio : 1.0
    }

    function _alignToPhysicalPixel(value) {
        return Math.round(value * _devicePixelRatio) / _devicePixelRatio
    }

    function _publishedPosition(value, minimum, maximum) {
        // Preserve exact legal boundaries for Flickable end-state semantics.
        // 保留精确合法边界，避免破坏 Flickable 的起止状态语义。
        if (Math.abs(value - minimum) < Enums.scroll.boundary_epsilon) return minimum
        if (Math.abs(value - maximum) < Enums.scroll.boundary_epsilon) return maximum
        return _alignToPhysicalPixel(value)
    }

    function _visualOvershootFor(value, minimum, maximum) {
        var published = _publishedPosition(value, minimum, maximum)
        return _clamp(published, minimum, maximum) - published
    }

    function _restartBounceTimer(verticalAxis) {
        var timer = verticalAxis ? _bounceTimerV : _bounceTimerH
        if (!timer) {
            timer = bounceTimerComponent.createObject(
                helper, { "verticalAxis": verticalAxis }
            )
            if (!timer) {
                console.error("SmoothScrollHelper failed to create bounce timer")
                return
            }
            if (verticalAxis) _bounceTimerV = timer
            else _bounceTimerH = timer
        }
        timer.restart()
    }

    function _stopBounceTimer(verticalAxis) {
        var timer = verticalAxis ? _bounceTimerV : _bounceTimerH
        if (!timer) return
        timer.stop()
        if (verticalAxis) _bounceTimerV = null
        else _bounceTimerH = null
        timer.destroy()
    }

    function _releaseBounceTimer(verticalAxis, timer) {
        if (verticalAxis) {
            if (_bounceTimerV === timer) _bounceTimerV = null
        } else if (_bounceTimerH === timer) {
            _bounceTimerH = null
        }
        timer.destroy()
    }

    function _publishSmoothY() {
        if (!_isVertical || !target || _discardingStaleFrameV) return
        // The guard owns both frame-dropping cases: a clamp by the view, and a
        // stale catch-up peak after the whole outward window elapsed frameless.
        // 门闸掌管两类弃帧：视图夹紧，以及整段外移窗口无帧后的补算峰值。
        if (verticalOvershootGuard.consumesFrame(
                target.contentY, _lastPublishedY, _minY, _maxY,
                _isOvershotV, _isOutwardBounceV, _lastBounceFrameTimestampV)) return
        var published = _publishedPosition(_smoothY, _minY, _maxY)
        var contentPosition = _visualOvershootEnabled
            ? _clamp(published, _minY, _maxY) : published
        // Record the intended position before assignment; ListView may clamp synchronously
        // and re-enter geometry signals. 赋值前记录发布意图；ListView 可能同步夹紧并重入几何信号。
        _lastPublishedY = contentPosition
        target.contentY = contentPosition
        if (_isOutwardBounceV) _lastBounceFrameTimestampV = Date.now()
    }

    function _publishSmoothX() {
        if (_isVertical || !target || _discardingStaleFrameH) return
        // Keep the guard handling identical to the vertical path.
        // 门闸处理与垂直路径保持一致。
        if (horizontalOvershootGuard.consumesFrame(
                target.contentX, _lastPublishedX, _minX, _maxX,
                _isOvershotH, _isOutwardBounceH, _lastBounceFrameTimestampH)) return
        var published = _publishedPosition(_smoothX, _minX, _maxX)
        var contentPosition = _visualOvershootEnabled
            ? _clamp(published, _minX, _maxX) : published
        _lastPublishedX = contentPosition
        target.contentX = contentPosition
        if (_isOutwardBounceH) _lastBounceFrameTimestampH = Date.now()
    }

    // ListView/GridView may change origin while delegates are recycled.
    // ListView/GridView 复用 delegate 时可能动态改变 origin，目标与动画值必须同步回合法区间。
    // Bounds realignment is owned by the reconciler. 边界重对齐由校正器所有。
    function _reconcileVerticalBounds() { boundsReconciler.reconcile(true) }

    function _reconcileHorizontalBounds() { boundsReconciler.reconcile(false) }

    // Vertical implementation 垂直实现
    function _scrollToY(targetY) {
        _stopBounceTimer(true)
        _isOutwardBounceV = false
        verticalOvershootGuard.reset()
        _targetY = _clamp(targetY, _minY, _maxY)
        _isOvershotV = false
        verticalFrameDriver.moveTo(_targetY)
    }

    function _scrollByY(delta) {
        verticalOvershootGuard.noteRelativeScroll()
        var newTarget = _targetY + delta

        // Normal scroll 正常滚动
        if (newTarget >= _minY && newTarget <= _maxY) {
            _stopBounceTimer(true)
            _isOutwardBounceV = false
            verticalOvershootGuard.reset()
            _targetY = newTarget
            _isOvershotV = false
            verticalFrameDriver.moveTo(_targetY)
            return
        }

        // Overshoot handling 超出处理
        if (!bounceEnabled) {
            _scrollToY(newTarget)
            return
        }

        // A boundary whose overshoot the view already clamped away must not launch
        // another outward leg, otherwise it is clamped again and the axis jitters.
        // 视图已夹掉超出的边界不得再次外移，否则会被再次夹紧并造成轴向抖动。
        if (verticalOvershootGuard.blocksBoundary(newTarget < _minY)) {
            _targetY = newTarget < _minY ? _minY : _maxY
            verticalFrameDriver.moveTo(_targetY)
            return
        }

        if (newTarget < _minY) {
            // Top overshoot 顶部超出
            _targetY = _minY
            _isOvershotV = true
            _isOutwardBounceV = true
            verticalOvershootGuard.outwardBoundary = -1
            _lastPublishedY = target.contentY
            _lastBounceFrameTimestampV = Date.now()
            var overshootDelta = _minY - newTarget
            var currentOvershoot = _smoothY < _minY ? _minY - _smoothY : 0
            var nextOvershoot = Math.min(currentOvershoot + overshootDelta, _maxOvershoot)
            verticalFrameDriver.moveTo(_minY - nextOvershoot)
            _restartBounceTimer(true)
        } else {
            // Bottom overshoot 底部超出
            _targetY = _maxY
            _isOvershotV = true
            _isOutwardBounceV = true
            verticalOvershootGuard.outwardBoundary = 1
            _lastPublishedY = target.contentY
            _lastBounceFrameTimestampV = Date.now()
            var overshootDeltaBottom = newTarget - _maxY
            var currentOvershootBottom = _smoothY > _maxY ? _smoothY - _maxY : 0
            var nextOvershootBottom = Math.min(
                currentOvershootBottom + overshootDeltaBottom, _maxOvershoot)
            verticalFrameDriver.moveTo(_maxY + nextOvershootBottom)
            _restartBounceTimer(true)
        }
    }

    function _bounceBackV() {
        _isOutwardBounceV = false
        _isOvershotV = true
        verticalFrameDriver.moveTo(_targetY)
    }

    // Horizontal implementation 水平实现
    function _scrollToX(targetX) {
        _stopBounceTimer(false)
        _isOutwardBounceH = false
        horizontalOvershootGuard.reset()
        _targetX = _clamp(targetX, _minX, _maxX)
        _isOvershotH = false
        horizontalFrameDriver.moveTo(_targetX)
    }

    function _scrollByX(delta) {
        horizontalOvershootGuard.noteRelativeScroll()
        var newTarget = _targetX + delta

        // Normal scroll 正常滚动
        if (newTarget >= _minX && newTarget <= _maxX) {
            _stopBounceTimer(false)
            _isOutwardBounceH = false
            horizontalOvershootGuard.reset()
            _targetX = newTarget
            _isOvershotH = false
            horizontalFrameDriver.moveTo(_targetX)
            return
        }

        // Overshoot handling 超出处理
        if (!bounceEnabled) {
            _scrollToX(newTarget)
            return
        }

        // Keep the revoked-boundary handling identical to the vertical path.
        // 撤销边界处理与垂直路径保持一致。
        if (horizontalOvershootGuard.blocksBoundary(newTarget < _minX)) {
            _targetX = newTarget < _minX ? _minX : _maxX
            horizontalFrameDriver.moveTo(_targetX)
            return
        }

        if (newTarget < _minX) {
            // Left overshoot 左侧超出
            _targetX = _minX
            _isOvershotH = true
            _isOutwardBounceH = true
            horizontalOvershootGuard.outwardBoundary = -1
            _lastPublishedX = target.contentX
            _lastBounceFrameTimestampH = Date.now()
            var overshootDelta = _minX - newTarget
            var currentOvershoot = _smoothX < _minX ? _minX - _smoothX : 0
            var nextOvershoot = Math.min(currentOvershoot + overshootDelta, _maxOvershoot)
            horizontalFrameDriver.moveTo(_minX - nextOvershoot)
            _restartBounceTimer(false)
        } else {
            // Right overshoot 右侧超出
            _targetX = _maxX
            _isOvershotH = true
            _isOutwardBounceH = true
            horizontalOvershootGuard.outwardBoundary = 1
            _lastPublishedX = target.contentX
            _lastBounceFrameTimestampH = Date.now()
            var overshootDeltaRight = newTarget - _maxX
            var currentOvershootRight = _smoothX > _maxX ? _smoothX - _maxX : 0
            var nextOvershootRight = Math.min(
                currentOvershootRight + overshootDeltaRight, _maxOvershoot)
            horizontalFrameDriver.moveTo(_maxX + nextOvershootRight)
            _restartBounceTimer(false)
        }
    }

    function _bounceBackH() {
        _isOutwardBounceH = false
        _isOvershotH = true
        horizontalFrameDriver.moveTo(_targetX)
    }

    // Bindings 绑定
    on_SmoothYChanged: _publishSmoothY()
    on_SmoothXChanged: _publishSmoothX()
    // ListView can update contentHeight while contentY is changing. Reconcile
    // on the next turn so bound evaluation cannot synchronously write contentY
    // and re-enter the same _maxY binding. ListView 可能在 contentY 变化时更新
    // contentHeight；下一事件循环再校正，避免写回 contentY 时重入 _maxY 绑定。
    on_MinYChanged: verticalReconcileTimer.restart()
    on_MaxYChanged: verticalReconcileTimer.restart()
    on_MinXChanged: horizontalReconcileTimer.restart()
    on_MaxXChanged: horizontalReconcileTimer.restart()

    // Sync initial position 同步初始位置
    Component.onCompleted: {
        if (target) {
            _targetY = target.contentY
            verticalFrameDriver.setImmediate(target.contentY)
            _lastPublishedY = target.contentY
            _targetX = target.contentX
            horizontalFrameDriver.setImmediate(target.contentX)
            _lastPublishedX = target.contentX
        }
    }

    // ==================== Content 内容 ====================
    // Refresh-synchronized axis drivers 跟随刷新率的双轴驱动器
    ScrollBarInternal.SmoothScrollFrameDriver {
        id: verticalFrameDriverObject
        scrollHelper: helper
        verticalAxis: true
    }

    ScrollBarInternal.SmoothScrollFrameDriver {
        id: horizontalFrameDriverObject
        scrollHelper: helper
        verticalAxis: false
    }

    // Per-axis overshoot arbiters 双轴超出仲裁器
    ScrollBarInternal.SmoothScrollOvershootGuard {
        id: verticalOvershootGuardObject
        scrollHelper: helper
        verticalAxis: true
    }

    ScrollBarInternal.SmoothScrollOvershootGuard {
        id: horizontalOvershootGuardObject
        scrollHelper: helper
        verticalAxis: false
    }

    ScrollBarInternal.SmoothScrollBoundsReconciler {
        id: boundsReconcilerObject
        scrollHelper: helper
    }

    // On-demand bounce timer 按需回弹计时器
    Component {
        id: bounceTimerComponent

        ScrollBarInternal.SmoothScrollBounceTimer {
            scrollHelper: helper
        }
    }

    ScrollBarInternal.SmoothScrollBoundsReconcileTimer {
        id: verticalReconcileTimer
        objectName: "smoothScrollVerticalReconcileTimer"
        scrollHelper: helper
        verticalAxis: true
    }

    ScrollBarInternal.SmoothScrollBoundsReconcileTimer {
        id: horizontalReconcileTimer
        objectName: "smoothScrollHorizontalReconcileTimer"
        scrollHelper: helper
        verticalAxis: false
    }

    // Auto wheel handler 自动滚轮处理
    ScrollBarInternal.SmoothScrollWheelArea {
        scrollHelper: helper
    }
}
