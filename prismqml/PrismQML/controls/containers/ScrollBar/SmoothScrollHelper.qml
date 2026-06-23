// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

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
    
    // ==================== Config Props 配置属性 ====================
    property int orientation: Qt.Vertical  // Qt.Vertical or Qt.Horizontal 滚动方向
    property int duration: Enums.duration.scroll
    property real step: Enums.spacing.xxxl * 3  // Scroll step per wheel tick 每次滚轮滚动距离
    property int easing: Easing.OutQuart
    property bool bounceEnabled: true  // Enable overshoot bounce 启用边界回弹
    property bool handleWheel: false  // Auto handle mouse wheel 自动处理鼠标滚轮
    
    // ==================== Read-only State 只读状态 ====================
    readonly property real targetPos: _isVertical ? _targetY : _targetX
    readonly property real smoothPos: _isVertical ? _smoothY : _smoothX
    readonly property real maxScroll: _isVertical ? _maxY : _maxX
    readonly property bool isOvershot: _isVertical ? _isOvershotV : _isOvershotH
    
    // ==================== Internal State 内部状态 ====================
    readonly property bool _isVertical: orientation === Qt.Vertical
    readonly property real _maxY: Math.max(0, target.contentHeight - target.height)
    readonly property real _maxX: Math.max(0, target.contentWidth - target.width)
    readonly property real _maxOvershoot: Enums.spacing.scrollOvershoot
    
    // Vertical state 垂直状态
    property real _targetY: 0
    property real _smoothY: 0
    property bool _isOvershotV: false
    
    // Horizontal state 水平状态
    property real _targetX: 0
    property real _smoothX: 0
    property bool _isOvershotH: false
    
    // ==================== Bindings 绑定 ====================
    on_SmoothYChanged: if (_isVertical && target) target.contentY = _smoothY
    on_SmoothXChanged: if (!_isVertical && target) target.contentX = _smoothX
    
    // ==================== Animations 动画 ====================
    // _syncing = true 时禁用动画, 让 ScrollBar 拖拽场景下 contentX/Y 立即跟随 handle,
    // 不被 Behavior 平滑过渡反向拖拽.
    property bool _syncing: false

    // ==================== Public Methods 公开方法 ====================

    // Scroll to absolute position 滚动到绝对位置
    function scrollTo(pos) {
        if (_isVertical) _scrollToY(pos)
        else _scrollToX(pos)
    }

    // Scroll by delta 相对滚动
    function scrollBy(delta) {
        if (_isVertical) _scrollByY(delta)
        else _scrollByX(delta)
    }

    // Scroll to top/left 滚动到顶部/左侧
    function scrollToStart() { scrollTo(0) }

    // Scroll to bottom/right 滚动到底部/右侧
    function scrollToEnd() { scrollTo(_isVertical ? _maxY : _maxX) }

    // Sync position (call after drag) 同步位置（拖拽后调用）
    function syncPosition() {
        _syncing = true
        if (_isVertical) {
            _targetY = target.contentY
            _smoothY = target.contentY
        } else {
            _targetX = target.contentX
            _smoothX = target.contentX
        }
        _syncing = false
    }

    // ==================== Vertical Implementation 垂直实现 ====================
    function _scrollToY(targetY) {
        _targetY = Math.max(0, Math.min(_maxY, targetY))
        _isOvershotV = false
        _smoothY = _targetY
    }

    function _scrollByY(delta) {
        var newTarget = _targetY + delta

        // Normal scroll 正常滚动
        if (newTarget >= 0 && newTarget <= _maxY) {
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

        if (newTarget < 0) {
            // Top overshoot 顶部超出
            _targetY = 0
            _isOvershotV = true
            var overshootDelta = -newTarget
            var currentOvershoot = _smoothY < 0 ? -_smoothY : 0
            _smoothY = -Math.min(currentOvershoot + overshootDelta, _maxOvershoot)
            bounceTimerV.restart()
        } else {
            // Bottom overshoot 底部超出
            _targetY = _maxY
            _isOvershotV = true
            var overshootDeltaBottom = newTarget - _maxY
            var currentOvershootBottom = _smoothY > _maxY ? _smoothY - _maxY : 0
            _smoothY = _maxY + Math.min(currentOvershootBottom + overshootDeltaBottom, _maxOvershoot)
            bounceTimerV.restart()
        }
    }

    function _bounceBackV() {
        _isOvershotV = true
        _smoothY = _targetY
    }

    // ==================== Horizontal Implementation 水平实现 ====================
    function _scrollToX(targetX) {
        _targetX = Math.max(0, Math.min(_maxX, targetX))
        _isOvershotH = false
        _smoothX = _targetX
    }

    function _scrollByX(delta) {
        var newTarget = _targetX + delta

        // Normal scroll 正常滚动
        if (newTarget >= 0 && newTarget <= _maxX) {
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

        if (newTarget < 0) {
            // Left overshoot 左侧超出
            _targetX = 0
            _isOvershotH = true
            var overshootDelta = -newTarget
            var currentOvershoot = _smoothX < 0 ? -_smoothX : 0
            _smoothX = -Math.min(currentOvershoot + overshootDelta, _maxOvershoot)
            bounceTimerH.restart()
        } else {
            // Right overshoot 右侧超出
            _targetX = _maxX
            _isOvershotH = true
            var overshootDeltaRight = newTarget - _maxX
            var currentOvershootRight = _smoothX > _maxX ? _smoothX - _maxX : 0
            _smoothX = _maxX + Math.min(currentOvershootRight + overshootDeltaRight, _maxOvershoot)
            bounceTimerH.restart()
        }
    }

    function _bounceBackH() {
        _isOvershotH = true
        _smoothX = _targetX
    }

    Behavior on _smoothY {
        enabled: helper.enabled && helper._isVertical && !helper._syncing
        NumberAnimation {
            duration: helper._isOvershotV ? Enums.duration.bounce : helper.duration
            easing.type: helper._isOvershotV ? Easing.OutBack : helper.easing
        }
    }

    Behavior on _smoothX {
        enabled: helper.enabled && !helper._isVertical && !helper._syncing
        NumberAnimation {
            duration: helper._isOvershotH ? Enums.duration.bounce : helper.duration
            easing.type: helper._isOvershotH ? Easing.OutBack : helper.easing
        }
    }
    
    // ==================== Bounce Timers 回弹定时器 ====================
    Timer {
        id: bounceTimerV
        interval: Enums.duration.fast
        onTriggered: helper._bounceBackV()
    }
    
    Timer {
        id: bounceTimerH
        interval: Enums.duration.fast
        onTriggered: helper._bounceBackH()
    }

    // ==================== Init 初始化 ====================
    Component.onCompleted: {
        if (target) {
            _targetY = target.contentY
            _smoothY = target.contentY
            _targetX = target.contentX
            _smoothX = target.contentX
        }
    }
    
    // ==================== Auto Wheel Handler 自动滚轮处理 ====================
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
