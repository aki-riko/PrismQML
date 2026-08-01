// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "_internal"

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
    // Vertical state 垂直状态
    property real _targetY: 0
    property real _smoothY: 0
    property bool _isOvershotV: false
    property int _boundaryTargetV: 0  // -1=start, 0=absolute, 1=end
    property int _bounceBoundaryV: 0  // Boundary of the active bounce 当前回弹边界
    readonly property int _blockedBounceBoundaryV: verticalBounce.blockedBoundary
    
    // Horizontal state 水平状态
    property real _targetX: 0
    property real _smoothX: 0
    property bool _isOvershotH: false
    property int _boundaryTargetH: 0  // -1=start, 0=absolute, 1=end
    property int _bounceBoundaryH: 0  // Boundary of the active bounce 当前回弹边界
    readonly property int _blockedBounceBoundaryH: horizontalBounce.blockedBoundary
    // _syncing = true 时禁用动画, 让 ScrollBar 拖拽场景下 contentX/Y 立即跟随 handle,
    // 不被 Behavior 平滑过渡反向拖拽.
    property bool _syncing: false

    // ==================== Readonly State 只读状态 ====================
    readonly property real targetPos: _isVertical ? _targetY : _targetX
    readonly property real smoothPos: _isVertical ? _smoothY : _smoothX
    readonly property real minScroll: _isVertical ? _minY : _minX
    readonly property real maxScroll: _isVertical ? _maxY : _maxX
    readonly property bool isOvershot: _isVertical ? _isOvershotV : _isOvershotH
    readonly property bool _isVertical: orientation === Qt.Vertical
    readonly property real _minY: target ? target.originY : 0
    readonly property real _minX: target ? target.originX : 0
    readonly property real _maxY: _minY + Math.max(0, target.contentHeight - target.height)
    readonly property real _maxX: _minX + Math.max(0, target.contentWidth - target.width)
    readonly property real _maxOvershoot: Enums.spacing.scrollOvershoot
    readonly property bool _traceEnabled:
        typeof PrismQmlScrollTraceEnabled !== "undefined" && PrismQmlScrollTraceEnabled
    readonly property string _bouncePhase: _isVertical
        ? verticalBounce.phase : horizontalBounce.phase

    // ==================== Public Methods 公开方法 ====================
    // Scroll to absolute position 滚动到绝对位置
    function scrollTo(pos) {
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
        _trace("request.scrollBy", "delta=" + delta)
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
        _trace("sync.begin", "")
        _syncing = true
        if (_isVertical) {
            verticalBounce.stop("sync-position")
            _bounceBoundaryV = 0
            verticalBounce.resetInputGate()
            _boundaryTargetV = 0
            _targetY = target.contentY
            _smoothY = target.contentY
        } else {
            horizontalBounce.stop("sync-position")
            _bounceBoundaryH = 0
            horizontalBounce.resetInputGate()
            _boundaryTargetH = 0
            _targetX = target.contentX
            _smoothX = target.contentX
        }
        _syncing = false
        _trace("sync.finish", "")
    }

    // ==================== Internal Methods 内部方法 ====================
    function _clamp(value, minimum, maximum) {
        return Math.max(minimum, Math.min(maximum, value))
    }

    function _trace(stage, details) {
        if (_traceEnabled) scrollTrace.record(stage, details)
    }

    function _scheduleReconcile(axis, reason) {
        _trace("reconcile." + axis + ".scheduled", "reason=" + reason)
        if (axis === "vertical") verticalReconcileTimer.restart()
        else horizontalReconcileTimer.restart()
    }

    function _returnStarted(axis) {
        var vertical = axis === "vertical"
        if (vertical) verticalBounce.lockInput(_bounceBoundaryV)
        else horizontalBounce.lockInput(_bounceBoundaryH)
        var boundary = vertical ? _bounceBoundaryV : _bounceBoundaryH
        _trace("bounce." + axis + ".locked", "boundary=" + boundary)
    }

    // ListView/GridView may change origin while delegates are recycled.
    // ListView/GridView 复用 delegate 时可能动态改变 origin，目标与动画值必须同步回合法区间。
    function _reconcileVerticalBounds() {
        if (!target) return
        if (_boundaryTargetV === 0 && !smoothYAnimation.running && !_isOvershotV) {
            var currentY = _clamp(target.contentY, _minY, _maxY)
            if (currentY === _targetY && currentY === _smoothY) return
            _syncing = true
            _targetY = currentY
            _smoothY = currentY
            _syncing = false
            return
        }
        var targetY = _boundaryTargetV < 0
            ? _minY
            : (_boundaryTargetV > 0 ? _maxY : _clamp(_targetY, _minY, _maxY))
        var smoothY = _clamp(_smoothY, _minY, _maxY)
        if (targetY === _targetY && smoothY === _smoothY) return
        _isOvershotV = false
        _bounceBoundaryV = 0
        verticalBounce.resetInputGate()
        verticalBounce.stop("bounds-reconcile")
        _targetY = targetY
        if (smoothY !== _smoothY) {
            _syncing = true
            _smoothY = smoothY
            _syncing = false
        }
        if (_smoothY !== _targetY) _smoothY = _targetY
    }

    function _reconcileHorizontalBounds() {
        if (!target) return
        if (_boundaryTargetH === 0 && !smoothXAnimation.running && !_isOvershotH) {
            var currentX = _clamp(target.contentX, _minX, _maxX)
            if (currentX === _targetX && currentX === _smoothX) return
            _syncing = true
            _targetX = currentX
            _smoothX = currentX
            _syncing = false
            return
        }
        var targetX = _boundaryTargetH < 0
            ? _minX
            : (_boundaryTargetH > 0 ? _maxX : _clamp(_targetX, _minX, _maxX))
        var smoothX = _clamp(_smoothX, _minX, _maxX)
        if (targetX === _targetX && smoothX === _smoothX) return
        _isOvershotH = false
        _bounceBoundaryH = 0
        horizontalBounce.resetInputGate()
        horizontalBounce.stop("bounds-reconcile")
        _targetX = targetX
        if (smoothX !== _smoothX) {
            _syncing = true
            _smoothX = smoothX
            _syncing = false
        }
        if (_smoothX !== _targetX) _smoothX = _targetX
    }

    // Vertical implementation 垂直实现
    function _scrollToY(targetY) {
        _trace("scroll.vertical.to", "position=" + targetY)
        verticalBounce.stop("scroll-to")
        _bounceBoundaryV = 0
        verticalBounce.resetInputGate()
        _targetY = _clamp(targetY, _minY, _maxY)
        _isOvershotV = false
        _smoothY = _targetY
    }

    function _scrollByY(delta) {
        var newTarget = _targetY + delta
        _trace("scroll.vertical.evaluate", "delta=" + delta + " newTarget=" + newTarget)

        // Normal scroll 正常滚动
        if (newTarget >= _minY && newTarget <= _maxY) {
            verticalBounce.stop("normal-scroll")
            _bounceBoundaryV = 0
            if (delta !== 0) verticalBounce.resetInputGate()
            _targetY = newTarget
            _isOvershotV = false
            _smoothY = _targetY
            return
        }

        // Overshoot handling 超出处理
        if (!bounceEnabled) {
            _scrollToY(newTarget)
            return
        }

        if (newTarget < _minY) {
            // Top overshoot 顶部超出
            if (!verticalBounce.acceptInput(-1)) {
                _trace("bounce.vertical.blocked", "boundary=-1")
                return
            }
            var startTopBounce = _bounceBoundaryV !== -1
            _bounceBoundaryV = -1
            _targetY = _minY
            _isOvershotV = true
            var overshootDelta = _minY - newTarget
            var currentOvershoot = _smoothY < _minY ? _minY - _smoothY : 0
            var outwardY = _minY - Math.min(currentOvershoot + overshootDelta, _maxOvershoot)
            _trace("bounce.vertical.request", "boundary=-1 delta=" + overshootDelta +
                   " currentOvershoot=" + currentOvershoot + " outward=" + outwardY)
            if (startTopBounce || !verticalBounce.extendOutward(outwardY)) verticalBounce.start(_smoothY, outwardY, _targetY)
        } else {
            // Bottom overshoot 底部超出
            if (!verticalBounce.acceptInput(1)) {
                _trace("bounce.vertical.blocked", "boundary=1")
                return
            }
            var startBottomBounce = _bounceBoundaryV !== 1
            _bounceBoundaryV = 1
            _targetY = _maxY
            _isOvershotV = true
            var overshootDeltaBottom = newTarget - _maxY
            var currentOvershootBottom = _smoothY > _maxY ? _smoothY - _maxY : 0
            var outwardYBottom = _maxY + Math.min(currentOvershootBottom + overshootDeltaBottom, _maxOvershoot)
            _trace("bounce.vertical.request", "boundary=1 delta=" + overshootDeltaBottom +
                   " currentOvershoot=" + currentOvershootBottom +
                   " outward=" + outwardYBottom)
            if (startBottomBounce || !verticalBounce.extendOutward(outwardYBottom)) verticalBounce.start(_smoothY, outwardYBottom, _targetY)
        }
    }

    // Horizontal implementation 水平实现
    function _scrollToX(targetX) {
        _trace("scroll.horizontal.to", "position=" + targetX)
        horizontalBounce.stop("scroll-to")
        _bounceBoundaryH = 0
        horizontalBounce.resetInputGate()
        _targetX = _clamp(targetX, _minX, _maxX)
        _isOvershotH = false
        _smoothX = _targetX
    }

    function _scrollByX(delta) {
        var newTarget = _targetX + delta
        _trace("scroll.horizontal.evaluate", "delta=" + delta + " newTarget=" + newTarget)

        // Normal scroll 正常滚动
        if (newTarget >= _minX && newTarget <= _maxX) {
            horizontalBounce.stop("normal-scroll")
            _bounceBoundaryH = 0
            if (delta !== 0) horizontalBounce.resetInputGate()
            _targetX = newTarget
            _isOvershotH = false
            _smoothX = _targetX
            return
        }

        // Overshoot handling 超出处理
        if (!bounceEnabled) {
            _scrollToX(newTarget)
            return
        }

        if (newTarget < _minX) {
            // Left overshoot 左侧超出
            if (!horizontalBounce.acceptInput(-1)) {
                _trace("bounce.horizontal.blocked", "boundary=-1")
                return
            }
            var startLeftBounce = _bounceBoundaryH !== -1
            _bounceBoundaryH = -1
            _targetX = _minX
            _isOvershotH = true
            var overshootDelta = _minX - newTarget
            var currentOvershoot = _smoothX < _minX ? _minX - _smoothX : 0
            var outwardX = _minX - Math.min(currentOvershoot + overshootDelta, _maxOvershoot)
            _trace("bounce.horizontal.request", "boundary=-1 delta=" + overshootDelta +
                   " currentOvershoot=" + currentOvershoot + " outward=" + outwardX)
            if (startLeftBounce || !horizontalBounce.extendOutward(outwardX)) horizontalBounce.start(_smoothX, outwardX, _targetX)
        } else {
            // Right overshoot 右侧超出
            if (!horizontalBounce.acceptInput(1)) {
                _trace("bounce.horizontal.blocked", "boundary=1")
                return
            }
            var startRightBounce = _bounceBoundaryH !== 1
            _bounceBoundaryH = 1
            _targetX = _maxX
            _isOvershotH = true
            var overshootDeltaRight = newTarget - _maxX
            var currentOvershootRight = _smoothX > _maxX ? _smoothX - _maxX : 0
            var outwardXRight = _maxX + Math.min(currentOvershootRight + overshootDeltaRight, _maxOvershoot)
            _trace("bounce.horizontal.request", "boundary=1 delta=" + overshootDeltaRight +
                   " currentOvershoot=" + currentOvershootRight +
                   " outward=" + outwardXRight)
            if (startRightBounce || !horizontalBounce.extendOutward(outwardXRight)) horizontalBounce.start(_smoothX, outwardXRight, _targetX)
        }
    }

    // Bindings 绑定
    on_SmoothYChanged: {
        _trace("smooth.changed", "axis=y value=" + _smoothY)
        if (_traceEnabled) scrollTrace.writeSource = scrollTrace.currentWriteSource()
        if (_isVertical && target) target.contentY = _smoothY
        if (_traceEnabled) scrollTrace.writeSource = ""
    }
    on_SmoothXChanged: {
        _trace("smooth.changed", "axis=x value=" + _smoothX)
        if (_traceEnabled) scrollTrace.writeSource = scrollTrace.currentWriteSource()
        if (!_isVertical && target) target.contentX = _smoothX
        if (_traceEnabled) scrollTrace.writeSource = ""
    }
    // ListView can update contentHeight while contentY is changing. Reconcile
    // on the next turn so bound evaluation cannot synchronously write contentY
    // and re-enter the same _maxY binding. ListView 可能在 contentY 变化时更新
    // contentHeight；下一事件循环再校正，避免写回 contentY 时重入 _maxY 绑定。
    on_MinYChanged: _scheduleReconcile("vertical", "minY")
    on_MaxYChanged: _scheduleReconcile("vertical", "maxY")
    on_MinXChanged: _scheduleReconcile("horizontal", "minX")
    on_MaxXChanged: _scheduleReconcile("horizontal", "maxX")

    // Sync initial position 同步初始位置
    Component.onCompleted: {
        if (target) {
            _targetY = target.contentY
            _smoothY = target.contentY
            _targetX = target.contentX
            _smoothX = target.contentX
        }
    }

    // Animations 动画
    Behavior on _smoothY {
        enabled: helper.enabled && helper._isVertical && !helper._syncing
            && !verticalBounce.active
        NumberAnimation {
            id: smoothYAnimation
            duration: helper._isOvershotV ? Enums.duration.bounce : helper.duration
            easing.type: helper._isOvershotV ? Easing.OutBack : helper.easing
        }
    }

    Behavior on _smoothX {
        enabled: helper.enabled && !helper._isVertical && !helper._syncing
            && !horizontalBounce.active
        NumberAnimation {
            id: smoothXAnimation
            duration: helper._isOvershotH ? Enums.duration.bounce : helper.duration
            easing.type: helper._isOvershotH ? Easing.OutBack : helper.easing
        }
    }
    
    // ==================== Content 内容 ====================
    // Deterministic two-phase bounce 确定性的两阶段回弹
    DeterministicBounce {
        id: verticalBounce
        animated: helper.enabled && helper._isVertical
        sourceDuration: Enums.duration.bounce
        outwardDuration: Enums.duration.fast
        returnDuration: Enums.duration.bounce
        easing: Easing.OutBack
        returnOvershoot: Enums.motion.scrollReturnBackOvershoot
        inputQuietDuration: Enums.duration.normal
        traceEnabled: helper._traceEnabled
        onPositionChanged: (position) => helper._smoothY = position
        onReturnStarted: helper._returnStarted("vertical")
        onTraceEvent: (stage, details) => helper._trace(
            "bounce.vertical." + stage, details)
    }

    DeterministicBounce {
        id: horizontalBounce
        animated: helper.enabled && !helper._isVertical
        sourceDuration: Enums.duration.bounce
        outwardDuration: Enums.duration.fast
        returnDuration: Enums.duration.bounce
        easing: Easing.OutBack
        returnOvershoot: Enums.motion.scrollReturnBackOvershoot
        inputQuietDuration: Enums.duration.normal
        traceEnabled: helper._traceEnabled
        onPositionChanged: (position) => helper._smoothX = position
        onReturnStarted: helper._returnStarted("horizontal")
        onTraceEvent: (stage, details) => helper._trace(
            "bounce.horizontal." + stage, details)
    }

    SmoothScrollTrace {
        id: scrollTrace
        enabled: helper._traceEnabled
        helper: helper
        target: helper.target
    }

    Timer {
        id: verticalReconcileTimer
        interval: Enums.duration.instant
        repeat: false
        onTriggered: helper._reconcileVerticalBounds()
    }

    Timer {
        id: horizontalReconcileTimer
        interval: Enums.duration.instant
        repeat: false
        onTriggered: helper._reconcileHorizontalBounds()
    }

    // Auto wheel handler 自动滚轮处理
    // Use parent binding instead of anchors to avoid "not a parent or sibling" warning 使用 parent 绑定而非 anchors 避免锚点警告
    MouseArea {
        id: wheelArea
        parent: helper.target
        anchors.fill: parent
        enabled: helper.handleWheel
        visible: helper.handleWheel
        propagateComposedEvents: true
        z: Enums.zIndex.background
        
        onWheel: (event) => {
            helper._trace("wheel.input", "angleX=" + event.angleDelta.x +
                          " angleY=" + event.angleDelta.y +
                          " pixelX=" + event.pixelDelta.x +
                          " pixelY=" + event.pixelDelta.y +
                          " phase=" + (typeof event.phase === "undefined"
                                       ? "undefined" : event.phase) +
                          " inverted=" + event.inverted)
            // Check if scroll is needed 检查是否需要滚动
            var contentSize = helper._isVertical ? target.contentHeight : target.contentWidth
            var viewSize = helper._isVertical ? target.height : target.width
            if (contentSize <= viewSize) {
                helper._trace("wheel.propagated", "reason=content-fits")
                event.accepted = false
                return
            }
            
            helper.scrollBy(-event.angleDelta.y / 120 * helper.step)
            event.accepted = true
        }
        onPressed: (event) => event.accepted = false
        onReleased: (event) => event.accepted = false
        onClicked: (event) => event.accepted = false
    }
}
