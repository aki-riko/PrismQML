// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

// SkinResolver - Nearest ancestor skin scope lookup 最近祖先皮肤范围查找
//
// Pure helper shared by every consumer; it holds no state and never writes
// global appearance. 所有消费者共用的纯辅助模块；不持有状态，也不写全局外观。

.pragma library

// Marker property published by SkinScope. SkinScope 发布的标记属性。
var CONTEXT_MARKER = "_prismSkinScopeContext"

// Accepted design languages, kept identical to the global skin config values.
// 可接受的设计语言，与全局 skin 配置值保持一致。
var VALID_SKINS = ["fluent", "neobrutalism", "vintage_ticket", "neumorphism"]

// Guard against pathological parent cycles in hosts that rewrite parents.
// 防御宿主改写父级造成的异常父级环。
var MAX_DEPTH = 512

function isValidSkin(name) {
    return typeof name === "string" && VALID_SKINS.indexOf(name) !== -1
}

// Walk the visual parent chain and return the nearest SkinScope context.
// Returns null when no ancestor scope exists, so callers fall back to Enums.
// 沿视觉父级链向上查找最近的 SkinScope 上下文。没有祖先范围时返回 null，
// 由调用方回退到 Enums。
//
// This runs only on creation, parent changes, and explicit context changes —
// never per frame, per hover, or inside animation callbacks.
// 只在创建、父级变化与显式上下文变化时执行，不在每帧、hover 或动画回调内执行。
// Call from a property binding so every visited parent and context marker is
// observed, including changes above the consumer's immediate parent.
// 必须在属性绑定中调用，追踪每层父级和上下文标记，包括非直接父级的变化。
function nearestContext(item) {
    var node = item
    var depth = 0
    while (node && depth < MAX_DEPTH) {
        var context = node[CONTEXT_MARKER]
        if (context) return context
        node = node.parent
        depth += 1
    }
    return null
}
