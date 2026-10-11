// AppBarDisplayStateResolver - Nearest AppBar display-state lookup 最近应用栏显示状态查找
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

// Pure helper shared by RibbonBar, RibbonGroup, RibbonTab, AppBarButton and
// AppBarSeparator; it holds no state and never writes a host property.
// 供功能区、功能分组、标签页、应用栏按钮与应用栏分隔线共用的纯辅助模块；
// 不持有状态，也不写宿主属性。

.pragma library

// Marker property published by every AppBar display-state host. 每个应用栏显示状态宿主发布的标记属性。
var HOST_MARKER = "_isAppBarDisplayStateHost"

// State property read from the nearest host. 从最近宿主读取的状态属性。
var STATE_MARKER = "displayState"

// Guard against pathological parent cycles in hosts that rewrite parents.
// 防御宿主改写父级造成的异常父级环。
var MAX_DEPTH = 64

// Walk the visual parent chain and return the nearest host display state.
// Falls back to the expanded state when no host is reachable.
// 沿视觉父级链向上查找最近的宿主显示状态；没有可达宿主时回退为展开态。
//
// Call from a property binding so every visited parent and host marker is
// observed, including changes above the consumer's immediate parent.
// 必须在属性绑定中调用，追踪每层父级与宿主标记，包括非直接父级的变化。
function resolve(item, enums) {
    var node = item
    var depth = 0
    while (node && depth < MAX_DEPTH) {
        if (node[HOST_MARKER] === true)
            return node[STATE_MARKER]
        node = node.parent
        depth += 1
    }
    return enums.commandBar.appBar_expanded
}
