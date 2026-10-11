// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "RelativePanelEngine.js" as RelativePanelEngine

// RelativePanelContent - RelativePanel visual layer 相对布局视觉层
// Owns the positioned children and the deferred relation pass 承载被定位的子项与延迟关系求解
Item {
    id: content

    // ==================== Required Props 必需属性 ====================
    required property Item host

    // ==================== Public Props 公开属性 ====================
    // Relation rules 关系规则
    property var relations: []

    default property alias content: contentHost.data

    // ==================== Readonly State 只读状态 ====================
    readonly property int itemCount: _getLayoutChildren().length
    readonly property int unresolvedCount: _unresolved
    // Child geometry watch 子项几何监听
    // The binding captures every child width / height read, so a natural size change
    // re-runs the relation pass without an explicit relayout call.
    // 该绑定捕获每个子项宽高读取, 因此自然尺寸变化会自动重跑关系求解。
    readonly property real _geometryRevision: {
        var revision = 0
        var children = contentHost.children
        for (var index = 0; index < children.length; index++) {
            revision += (children[index].width + children[index].height)
                * (index + 1)
        }
        return revision
    }

    // ==================== Internal Props 内部属性 ====================
    property int _unresolved: 0
    property bool _layoutPending: false
    // Natural sizes survive layout applied stretching 自然尺寸在布局拉伸后仍然保留
    property var _sizeCache: []

    // ==================== Signals 信号 ====================
    signal layoutUpdated()

    // ==================== Public Methods 公开方法 ====================
    // relayout - Queue a relation pass 排队一次关系求解
    function relayout() {
        _scheduleLayout()
    }

    // itemAt - Get the positioned child at index 获取指定索引的子项
    function itemAt(index) {
        var children = _getLayoutChildren()
        if (index >= 0 && index < children.length) return children[index]
        return null
    }

    // indexOf - Get the index of a positioned child 获取子项索引
    function indexOf(item) {
        var children = _getLayoutChildren()
        for (var index = 0; index < children.length; index++) {
            if (children[index] === item) return index
        }
        return -1
    }

    // ==================== Internal Methods 内部方法 ====================
    function _isLayoutChild(child) {
        if (!child) return false
        if (child.toString().indexOf("QQuickRepeater") !== -1) return false
        if (typeof child.width !== "number" || typeof child.height !== "number") {
            return false
        }
        return child.width > 0 || child.height > 0
    }

    // Positioned children 参与定位的子项
    function _getLayoutChildren() {
        var items = []
        for (var index = 0; index < contentHost.children.length; index++) {
            var child = contentHost.children[index]
            if (_isLayoutChild(child)) items.push(child)
        }
        return items
    }

    function _scheduleLayout() {
        if (_layoutPending) return
        _layoutPending = true
        layoutTimer.restart()
    }

    // Size cache entry of one child 子项的尺寸缓存条目
    function _cacheEntry(item) {
        for (var index = 0; index < _sizeCache.length; index++) {
            if (_sizeCache[index].item === item) return _sizeCache[index]
        }
        return null
    }

    // Natural extent: an external resize replaces the cached natural size
    // 自然尺寸: 外部改尺寸会替换缓存的自然尺寸
    function _naturalExtent(item, horizontal) {
        var entry = _cacheEntry(item)
        var current = horizontal ? item.width : item.height
        if (!entry) return current
        var applied = horizontal ? entry.appliedWidth : entry.appliedHeight
        if (current !== applied) return current
        return horizontal ? entry.naturalWidth : entry.naturalHeight
    }

    // Apply one solved frame without breaking untouched child bindings
    // 在不破坏未参与关系绑定的前提下应用求解结果
    function _applyFrame(frame) {
        if (frame.item.x !== frame.x) frame.item.x = frame.x
        if (frame.item.y !== frame.y) frame.item.y = frame.y
        if (frame.item.width !== frame.width) frame.item.width = frame.width
        if (frame.item.height !== frame.height) frame.item.height = frame.height
    }

    function _performLayout() {
        _layoutPending = false
        var children = _getLayoutChildren()
        var items = []
        var cache = []
        for (var index = 0; index < children.length; index++) {
            var child = children[index]
            var naturalWidth = _naturalExtent(child, true)
            var naturalHeight = _naturalExtent(child, false)
            items.push({
                item: child,
                width: naturalWidth,
                height: naturalHeight
            })
            cache.push({
                item: child,
                naturalWidth: naturalWidth,
                naturalHeight: naturalHeight,
                appliedWidth: naturalWidth,
                appliedHeight: naturalHeight
            })
        }
        var result = RelativePanelEngine.resolve(
            items, relations, content.width, content.height
        )
        _unresolved = result.unresolved
        for (var frame = 0; frame < result.geometry.length; frame++) {
            _applyFrame(result.geometry[frame])
            cache[frame].appliedWidth = result.geometry[frame].width
            cache[frame].appliedHeight = result.geometry[frame].height
        }
        _sizeCache = cache
        layoutUpdated()
    }

    // ==================== Size 尺寸 ====================
    onWidthChanged: relayout()
    onHeightChanged: relayout()
    onRelationsChanged: relayout()
    on_GeometryRevisionChanged: relayout()
    Component.onCompleted: relayout()

    // ==================== Content 内容 ====================
    // Deferred relation pass 延迟关系求解
    Timer {
        id: layoutTimer
        objectName: "relativePanelLayoutTimer"
        interval: 0
        repeat: false
        onTriggered: content._performLayout()
    }

    // Positioned children host 被定位子项承载
    Item {
        id: contentHost
        objectName: "relativePanelContentHost"
        anchors.fill: parent

        onChildrenChanged: content.relayout()
    }
}
