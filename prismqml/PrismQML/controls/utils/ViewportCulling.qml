// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// ViewportCulling - 视口裁剪感知 helper
// 放入任意 Item 内部, 自动探测最近祖先 Flickable 并暴露 inViewport bool.
// 组件绑定重内容到 inViewport, 视口外自动降级 (Image.source="" / Timer.running=false 等).
//
// 用法:
//   Item {
//       ViewportCulling { id: _vpc }
//       Image { source: _vpc.inViewport ? realSource : "" }
//       Timer { running: _vpc.inViewport && autoPlay }
//   }
//
// 原理: Qt 场景图不做 CPU 侧视口裁剪 (官方文档明确), visible=true 的 item 即使在 clip 外
// 仍然全量参与 scene graph sync + 绑定求值. 手动 visible=false 是开发者责任.
// 本 helper 把这个职责抽象成声明式 property, 组件无需关心 Flickable 层级细节.

Item {
    id: root

    // ==================== Public ====================
    // 当前宿主 Item 是否在视口内 (含 buffer 区)
    readonly property bool inViewport: _flickable === null || _visible

    // 视口外扩缓冲 (像素). 越大越早"预加载", 越小越省. 默认 1 个视口高度.
    property real buffer: _flickable ? _flickable.height : 200

    // ==================== Internal ====================
    property Flickable _flickable: null
    property bool _visible: true

    // ==================== Methods 方法 ====================
    function _updateVisibility() {
        if (!_flickable || !root.parent) { _visible = true; return }

        // 宿主 Item 在 Flickable contentItem 坐标系中的位置
        var hostItem = root.parent
        var mapped = hostItem.mapToItem(_flickable.contentItem, 0, 0)
        var itemTop = mapped.y
        var itemBottom = itemTop + hostItem.height

        // 视口范围 (含 buffer)
        var vpTop = _flickable.contentY - root.buffer
        var vpBottom = _flickable.contentY + _flickable.height + root.buffer

        _visible = (itemBottom > vpTop && itemTop < vpBottom)
    }

    // 零尺寸, 不参与布局
    width: 0; height: 0; visible: false

    Component.onCompleted: {
        // 向上找最近的 Flickable 祖先
        var p = root.parent
        while (p) {
            if (p instanceof Flickable) {
                _flickable = p
                break
            }
            p = p.parent
        }
    }

    // ==================== 视口判定 ====================
    // 仅用 Timer 低频判定 (每 150ms), 避免 contentY binding 每帧触发 mapToItem 开销.
    // 150ms 在快速滚动时 ≈ 2 帧延迟切换, 人眼不可察觉, 但不增加每帧 GUI 线程负担.
    Timer {
        interval: 150
        running: root._flickable !== null
        repeat: true
        triggeredOnStart: true  // 首次立即判定
        onTriggered: root._updateVisibility()
    }
}
