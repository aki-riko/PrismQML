// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

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
            _smoothY = target.contentY
        } else {
            _stopBounceTimer(false)
            _isOutwardBounceH = false
            _boundaryTargetH = 0
            _targetX = target.contentX
            _smoothX = target.contentX
        }
        _syncing = false
    }

    // ==================== Internal Methods 内部方法 ====================
    function _clamp(value, minimum, maximum) {
        return Math.max(minimum, Math.min(maximum, value))
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
        var now = Date.now()
        // Do not publish a catch-up peak after the complete outward window
        // elapsed without a frame. 外移窗口内整段无帧时，不发布恢复后的补算峰值。
        if (_isOutwardBounceV && _lastBounceFrameTimestampV > 0
                && now - _lastBounceFrameTimestampV >= Enums.duration.fast) {
            _discardStaleOutwardFrameV()
            return
        }
        target.contentY = _publishedPosition(_smoothY, _minY, _maxY)
        _lastPublishedY = target.contentY
        if (_isOutwardBounceV) _lastBounceFrameTimestampV = now
    }

    function _publishSmoothX() {
        if (_isVertical || !target || _discardingStaleFrameH) return
        var now = Date.now()
        // Keep horizontal recovery identical to the vertical path.
        // 水平恢复与垂直路径保持一致。
        if (_isOutwardBounceH && _lastBounceFrameTimestampH > 0
                && now - _lastBounceFrameTimestampH >= Enums.duration.fast) {
            _discardStaleOutwardFrameH()
            return
        }
        target.contentX = _publishedPosition(_smoothX, _minX, _maxX)
        _lastPublishedX = target.contentX
        if (_isOutwardBounceH) _lastBounceFrameTimestampH = now
    }

    function _discardStaleOutwardFrameV() {
        _discardingStaleFrameV = true
        _stopBounceTimer(true)
        _syncing = true
        _smoothY = _lastPublishedY
        _syncing = false
        _discardingStaleFrameV = false
        _bounceBackV()
    }

    function _discardStaleOutwardFrameH() {
        _discardingStaleFrameH = true
        _stopBounceTimer(false)
        _syncing = true
        _smoothX = _lastPublishedX
        _syncing = false
        _discardingStaleFrameH = false
        _bounceBackH()
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
        _isOutwardBounceV = false
        _stopBounceTimer(true)
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
        _isOutwardBounceH = false
        _stopBounceTimer(false)
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
        _stopBounceTimer(true)
        _isOutwardBounceV = false
        _targetY = _clamp(targetY, _minY, _maxY)
        _isOvershotV = false
        _smoothY = _targetY
    }

    function _scrollByY(delta) {
        var newTarget = _targetY + delta

        // Normal scroll 正常滚动
        if (newTarget >= _minY && newTarget <= _maxY) {
            _stopBounceTimer(true)
            _isOutwardBounceV = false
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
            _targetY = _minY
            _isOvershotV = true
            _isOutwardBounceV = true
            _lastPublishedY = target.contentY
            _lastBounceFrameTimestampV = Date.now()
            var overshootDelta = _minY - newTarget
            var currentOvershoot = _smoothY < _minY ? _minY - _smoothY : 0
            _smoothY = _minY - Math.min(currentOvershoot + overshootDelta, _maxOvershoot)
            _restartBounceTimer(true)
        } else {
            // Bottom overshoot 底部超出
            _targetY = _maxY
            _isOvershotV = true
            _isOutwardBounceV = true
            _lastPublishedY = target.contentY
            _lastBounceFrameTimestampV = Date.now()
            var overshootDeltaBottom = newTarget - _maxY
            var currentOvershootBottom = _smoothY > _maxY ? _smoothY - _maxY : 0
            _smoothY = _maxY + Math.min(currentOvershootBottom + overshootDeltaBottom, _maxOvershoot)
            _restartBounceTimer(true)
        }
    }

    function _bounceBackV() {
        _isOutwardBounceV = false
        _isOvershotV = true
        _smoothY = _targetY
    }

    // Horizontal implementation 水平实现
    function _scrollToX(targetX) {
        _stopBounceTimer(false)
        _isOutwardBounceH = false
        _targetX = _clamp(targetX, _minX, _maxX)
        _isOvershotH = false
        _smoothX = _targetX
    }

    function _scrollByX(delta) {
        var newTarget = _targetX + delta

        // Normal scroll 正常滚动
        if (newTarget >= _minX && newTarget <= _maxX) {
            _stopBounceTimer(false)
            _isOutwardBounceH = false
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
            _targetX = _minX
            _isOvershotH = true
            _isOutwardBounceH = true
            _lastPublishedX = target.contentX
            _lastBounceFrameTimestampH = Date.now()
            var overshootDelta = _minX - newTarget
            var currentOvershoot = _smoothX < _minX ? _minX - _smoothX : 0
            _smoothX = _minX - Math.min(currentOvershoot + overshootDelta, _maxOvershoot)
            _restartBounceTimer(false)
        } else {
            // Right overshoot 右侧超出
            _targetX = _maxX
            _isOvershotH = true
            _isOutwardBounceH = true
            _lastPublishedX = target.contentX
            _lastBounceFrameTimestampH = Date.now()
            var overshootDeltaRight = newTarget - _maxX
            var currentOvershootRight = _smoothX > _maxX ? _smoothX - _maxX : 0
            _smoothX = _maxX + Math.min(currentOvershootRight + overshootDeltaRight, _maxOvershoot)
            _restartBounceTimer(false)
        }
    }

    function _bounceBackH() {
        _isOutwardBounceH = false
        _isOvershotH = true
        _smoothX = _targetX
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
            _smoothY = target.contentY
            _lastPublishedY = target.contentY
            _targetX = target.contentX
            _smoothX = target.contentX
            _lastPublishedX = target.contentX
        }
    }

    // Animations 动画
    Behavior on _smoothY {
        enabled: helper.enabled && helper._isVertical && !helper._syncing
        NumberAnimation {
            id: smoothYAnimation
            duration: helper._isOvershotV ? Enums.duration.bounce : helper.duration
            easing.type: helper._isOvershotV ? Easing.OutBack : helper.easing
        }
    }

    Behavior on _smoothX {
        enabled: helper.enabled && !helper._isVertical && !helper._syncing
        NumberAnimation {
            id: smoothXAnimation
            duration: helper._isOvershotH ? Enums.duration.bounce : helper.duration
            easing.type: helper._isOvershotH ? Easing.OutBack : helper.easing
        }
    }
    
    // ==================== Content 内容 ====================
    // On-demand bounce timer 按需回弹计时器
    Component {
        id: bounceTimerComponent

        Timer {
            id: bounceTimer

            required property bool verticalAxis

            interval: Enums.duration.fast
            onTriggered: {
                if (verticalAxis) helper._bounceBackV()
                else helper._bounceBackH()
                helper._releaseBounceTimer(verticalAxis, bounceTimer)
            }
        }
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
            // Check if scroll is needed 检查是否需要滚动
            var contentSize = helper._isVertical ? target.contentHeight : target.contentWidth
            var viewSize = helper._isVertical ? target.height : target.width
            if (contentSize <= viewSize) {
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
