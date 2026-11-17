// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."

// ViewportLoader - Create content only once it nears the viewport 内容接近视口时才创建
// Wrap a heavy section of a long scrolling page. Until the slot nears the nearest
// Flickable's viewport, nothing inside exists and the slot holds placeholderHeight.
// Once created the content stays: scrolling back never rebuilds it or loses its state.
// Outside any Flickable the content is created at once.
// 包裹长滚动页面中的一段重内容。槽位接近最近 Flickable 的视口前，内部对象都不存在，
// 槽位只占 placeholderHeight 高度。创建后常驻：滚回时不重建，也不丢状态。
// 不在任何 Flickable 内时立即创建。
//
// Usage 用法:
//   ViewportLoader {
//       width: parent.width
//       ExampleCard { title: "..." }   // becomes the deferred component 成为延迟创建的组件
//   }
// Do not set height: it follows the content once created. 不要设置 height：创建后跟随内容。
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    default property Component sourceComponent
    property real placeholderHeight: Enums.controlSize.viewportLoaderPlaceholderHeight
    // Extra distance beyond the viewport that already counts as near; -1 means one
    // viewport on each side. 视口外仍算"接近"的距离；-1 表示上下各一个视口。
    property real buffer: -1
    property bool asynchronous: false

    // ==================== Readonly State 只读状态 ====================
    readonly property bool created: loader.status === Loader.Ready
    readonly property Item item: loader.item

    // ==================== Internal Props 内部属性 ====================
    property bool _requested: false
    property Flickable _flickable: null
    // Lets sibling slots recognise each other 供兄弟槽位互相识别
    readonly property bool _viewportLoader: true
    // True for one tick after creation, until the layout has moved later siblings
    // 创建后的一拍内为真，直到布局把后面的兄弟槽位挪到新位置
    property bool _settling: false

    // ==================== Public Methods 公开方法 ====================
    // Create now regardless of position, e.g. before scrolling to this slot.
    // 不论位置立即创建，例如滚动到本槽位之前。
    function create() { _requested = true }

    // ==================== Internal Methods 内部方法 ====================
    function _findFlickable() {
        for (var p = control.parent; p; p = p.parent) {
            if (p instanceof Flickable) return p
        }
        return null
    }

    // Positions are read only after layout settles (settleTimer): while a Column is
    // still laying out, every slot briefly sits near the top and would be created.
    // 位置只在布局稳定后读取（settleTimer）：Column 仍在布局时，所有槽位都会短暂挤在
    // 顶部附近，此时判定会把它们全部创建。
    function _evaluate() {
        if (_requested || !control.parent) return
        if (!_flickable) _flickable = _findFlickable()
        if (!_flickable) {
            _requested = true
            return
        }
        if (_flickable.width <= 0 || _flickable.height <= 0) return
        var origin = control.mapToItem(_flickable.contentItem, 0, 0)
        var spanY = control.buffer >= 0 ? control.buffer : _flickable.height
        var spanX = control.buffer >= 0 ? control.buffer : _flickable.width
        var nearY = origin.y < _flickable.contentY + _flickable.height + spanY
            && origin.y + control.height > _flickable.contentY - spanY
        var nearX = origin.x < _flickable.contentX + _flickable.width + spanX
            && origin.x + Math.max(control.width, 1) > _flickable.contentX - spanX
        if (!nearY || !nearX) return
        // An earlier sibling still at placeholder height may grow and push this slot
        // out of range: let it settle first, then measure again on the next tick.
        // 前面仍是占位高度的兄弟槽位可能变高、把本槽位推出范围：先让它稳定，下一拍再量。
        if (_earlierSiblingPending()) {
            settleTimer.restart()
            return
        }
        _requested = true
    }

    function _earlierSiblingPending() {
        var siblings = control.parent ? control.parent.children : []
        for (var i = 0; i < siblings.length; ++i) {
            var sibling = siblings[i]
            if (sibling === control) return false
            if (sibling._viewportLoader !== true) continue
            if (sibling._settling) return true
            if (!sibling.created && sibling._nearViewport()) return true
        }
        return false
    }

    // Same test as _evaluate, without side effects 与 _evaluate 判定相同，无副作用
    function _nearViewport() {
        if (_requested && created) return false
        if (!_flickable) _flickable = _findFlickable()
        if (!_flickable || _flickable.height <= 0) return false
        var origin = control.mapToItem(_flickable.contentItem, 0, 0)
        var spanY = control.buffer >= 0 ? control.buffer : _flickable.height
        return origin.y < _flickable.contentY + _flickable.height + spanY
            && origin.y + control.height > _flickable.contentY - spanY
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: loader.item ? loader.item.implicitWidth : 0
    implicitHeight: created ? loader.item.height : placeholderHeight

    onXChanged: settleTimer.restart()
    onYChanged: settleTimer.restart()
    onParentChanged: {
        _flickable = null
        settleTimer.restart()
    }
    Component.onCompleted: settleTimer.restart()
    onCreatedChanged: {
        if (!created) return
        _settling = true
        settledTimer.restart()
    }

    // ==================== Content 内容 ====================
    Timer {
        id: settleTimer

        interval: Enums.duration.tick
        onTriggered: control._evaluate()
    }

    Timer {
        id: settledTimer

        interval: Enums.duration.tick
        onTriggered: control._settling = false
    }

    Connections {
        function onContentYChanged() { control._evaluate() }
        function onContentXChanged() { control._evaluate() }
        function onWidthChanged() { settleTimer.restart() }
        function onHeightChanged() { settleTimer.restart() }

        target: control._requested ? null : control._flickable
    }

    Loader {
        id: loader

        width: control.width > 0 ? control.width : undefined
        active: control._requested
        asynchronous: control.asynchronous
        sourceComponent: control.sourceComponent
    }
}
