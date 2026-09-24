// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."

// RefreshContainer - Pull-to-refresh wrapper 下拉刷新容器
//
// 内容在顶部（Flickable.atYBeginning）时向下拖拽即下拉：拖过阈值松手触发一次
// refreshRequested 并把容器置为 refreshing，宿主刷新完成后把 refreshing 置回 false，
// 内容随之收回。指示器用 ProgressRing: 拖动中按进度填充，刷新中转圈。
//
// 为什么在顶部拦截手势是安全的: Flickable 已经停在顶部时, 向上拖本来就不会滚动
// (StopAtBounds), 因此在 atYBeginning 期间接管纵向拖拽不损失任何滚动能力; 一旦内容
// 离开顶部, 本容器的手势处理立即禁用, 滚动完全交还给 Flickable。
//
// 用法 / Usage:
//   Fluent.RefreshContainer {
//       refreshing: model.refreshing            // 宿主状态
//       onRefreshRequested: model.reload()
//       ListView { ... }                        // 内容走默认属性, 内含 Flickable
//   }
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    // Host-owned flag: the container sets it true when a refresh starts and the host
    // must set it back to false when the work is done.
    // 宿主所有: 触发时容器置 true, 宿主完成后必须置回 false。
    property bool refreshing: false
    // Distance the user must pull to arm a refresh 触发刷新所需的下拉距离
    property int pullThreshold: Enums.controlSize.refreshPullThreshold
    property bool interactionEnabled: true
    // Optional explicit scroll surface; null auto-detects the first Flickable inside
    // 可选显式滚动面; 为空则自动取内容里第一个 Flickable
    property Flickable target: null

    // Caller content collected into the host item 调用方内容收进宿主 Item
    default property alias content: contentHost.data

    // ==================== Internal Props 内部属性 ====================
    // Content displacement; negative values are clamped away 内容位移, 负值被夹掉
    property real _offset: 0
    property bool _dragging: false
    // childItems() is not reactive, so content creation bumps this key and the
    // flickable binding below watches it. childItems() 不具响应性, 因此内容变化时递增
    // 此键, 下面的滚动面绑定依赖它。
    property int _contentRevision: 0
    readonly property Flickable _flickable: {
        var revision = _contentRevision
        if (target) return target
        return _findFlickable()
    }

    // ==================== Readonly State 只读状态 ====================
    readonly property real progress: pullThreshold > 0
        ? Math.max(0, Math.min(1, _offset / pullThreshold)) : 0
    readonly property bool armed: progress >= 1
    readonly property bool indicatorVisible: _offset > 0 || refreshing

    // ==================== Signals 信号 ====================
    signal refreshRequested()

    // ==================== Public Methods 公开方法 ====================
    // Start a refresh programmatically 以编程方式开始一次刷新
    function requestRefresh() {
        if (refreshing || !interactionEnabled) return
        refreshing = true
        refreshRequested()
    }

    // ==================== Internal Methods 内部方法 ====================
    // First scroll surface in the content tree 内容树里的第一个滚动面
    // Duck-typed on contentY so non-Flickable items are skipped without throwing.
    // 以 contentY 做鸭子类型判断, 非 Flickable 会被跳过且不抛异常。
    function _findFlickable() {
        var pending = []
        var i
        for (i = 0; i < contentHost.children.length; i++) {
            pending.push(contentHost.children[i])
        }
        while (pending.length > 0) {
            var item = pending.shift()
            if (item.contentY !== undefined) return item
            for (i = 0; i < item.children.length; i++) {
                pending.push(item.children[i])
            }
        }
        return null
    }
    // Only pull from the very top, and never while a refresh is running
    // 只允许在顶部下拉, 且刷新期间不再重复触发
    function _canPull() {
        if (!interactionEnabled || refreshing) return false
        var flickable = _flickable
        return flickable !== null && flickable.atYBeginning
    }
    function _release() {
        if (armed && !refreshing) {
            refreshing = true
            refreshRequested()
            _offset = pullThreshold
            return
        }
        _offset = 0
    }

    // ==================== Size 尺寸 ====================
    // Parent geometry via plain bindings: the container is commonly declared inside a
    // Layout. 父级几何用普通绑定: 容器常被声明在布局里。
    implicitWidth: contentHost.childrenRect.width
    implicitHeight: contentHost.childrenRect.height
    clip: true

    onRefreshingChanged: if (!refreshing && !_dragging) _offset = 0

    // ==================== Content 内容 ====================
    // Pull indicator 下拉指示器
    Item {
        id: indicator
        objectName: "refreshIndicator"
        anchors.horizontalCenter: parent.horizontalCenter
        width: Enums.controlSize.refreshIndicatorSize
        height: width
        // Slides in from under the top edge as the content is pulled down
        // 随内容下拉从顶边下方滑出
        y: control._offset - height
        visible: control.indicatorVisible
        opacity: control.progress

        ProgressRing {
            anchors.fill: parent
            indeterminate: control.refreshing
            value: control.progress * 100
            from: 0
            to: 100
        }
    }

    Item {
        id: contentHost
        objectName: "refreshContent"
        y: control._offset
        width: control.width
        height: control.height

        // Content creation/removal re-resolves the scroll surface
        // 内容增删时重新解析滚动面
        onChildrenChanged: control._contentRevision++

        // Follow the finger, then settle when released (unless a refresh holds it)
        // 拖拽时跟手, 松手后归位(刷新中则保持)
        Behavior on y {
            enabled: !control._dragging
            NumberAnimation {
                duration: Enums.duration.fast
                easing.type: Easing.OutCubic
            }
        }
    }

    // Gesture layer: only live while the surface is at the top, so ordinary scrolling
    // is never intercepted. 手势层仅在滚动面位于顶部时生效, 因此不会拦截正常滚动。
    DragHandler {
        id: pullHandler
        target: null
        enabled: control._canPull()
        xAxis.enabled: false
        yAxis.enabled: true
        dragThreshold: Enums.controlSize.refreshPullThreshold / 4

        onActiveChanged: {
            control._dragging = active
            if (!active) control._release()
        }
        onActiveTranslationChanged: {
            if (!active) return
            // A pull never shrinks below zero 下拉位移不会小于零
            control._offset = Math.max(
                0, Math.min(control.pullThreshold, activeTranslation.y))
        }
    }
}
