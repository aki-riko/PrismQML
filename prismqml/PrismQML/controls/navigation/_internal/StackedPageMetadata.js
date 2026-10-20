// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

.pragma library

// StackedPageMetadata - Page metadata reading and filtering 页面元数据读取与过滤
//
// `pageProperties` carries two different kinds of data: real initial properties for
// the page, and engine-reserved metadata (currently the `skeleton` declaration) that
// the engine reads to render the lazy-loading skeleton before the page exists. The
// helpers below keep the two apart so reserved keys are never forwarded to a page.
// `pageProperties` 承载两类不同数据: 页面真实初始属性, 以及引擎保留元数据(当前为
// `skeleton` 声明)——引擎在页面存在前读取它以渲染懒加载骨架。下面的助手把二者分开,
// 使保留键永不转发给页面。

// Reserved keys the engine consumes itself and must never assign to a page.
// 引擎自行消费、绝不赋值给页面的保留键。
var RESERVED_KEYS = ["skeleton"]

// One page's metadata object, or an empty object when absent or malformed.
// 某页的元数据对象; 缺失或非法时返回空对象。
function propertiesFor(host, index) {
    var all = host._safePageProperties
    if (index < 0 || index >= all.length) return ({})
    var value = all[index]
    return value && typeof value === "object" ? value : ({})
}

// Skeleton structure for one page, resolved in three tiers:
//   1. a user declaration in `pageProperties[index].skeleton` wins;
//   2. otherwise the injected `skeletonSourceResolver` infers it from page source;
//   3. otherwise an empty list, which makes the renderer use the generic skeleton.
// The resolver is optional: a host without Python injection leaves it null and the
// page silently falls back instead of erroring.
// 某页的骨架结构, 三级解析:
//   1. `pageProperties[index].skeleton` 的用户声明优先;
//   2. 否则由注入的 `skeletonSourceResolver` 从页面源码推断;
//   3. 否则返回空列表, 渲染器据此使用通用骨架。
// 解析器是可选的: 没有 Python 注入的宿主保持 null, 页面静默回退而不报错。
function skeletonBlocksFor(host, index) {
    var declared = propertiesFor(host, index).skeleton
    if (declared && typeof declared === "object"
            && typeof declared.length === "number" && declared.length > 0) {
        return declared
    }
    return resolvedBlocksFor(host, index)
}

// Blocks inferred by the injected resolver for one page, or an empty list when the
// resolver is absent, the page has no source, or the result is not an array.
// 由注入解析器为某页推断的块; 解析器缺失、页面无源码或结果非数组时返回空列表。
function resolvedBlocksFor(host, index) {
    var resolver = resolverFor(host)
    if (!resolver || typeof resolver.blocksFor !== "function") return []
    var sources = host._safePageSources
    if (index < 0 || index >= sources.length) return []
    var source = sources[index]
    if (!source) return []
    var resolved = resolver.blocksFor(String(source))
    if (!resolved || typeof resolved !== "object") return []
    if (typeof resolved.length !== "number") return []
    return resolved
}

// The host's skeleton resolver: the bound property when present, otherwise the
// Python-injected global so a QML-only host still infers layouts. The global is
// never written into the property, which would destroy a binding the host assigns
// later. Kept here so the entry file stays inside its size gate.
// 宿主的骨架解析器: 已绑定的属性优先, 否则用 Python 注入的全局, 使纯 QML 宿主同样能推断
// 布局。全局绝不写回属性, 否则会破坏宿主之后建立的绑定。放在此处以保持入口文件体积门禁。
function resolverFor(host) {
    if (host.skeletonSourceResolver) return host.skeletonSourceResolver
    return typeof SkeletonSource !== "undefined" ? SkeletonSource : null
}

// Pre-parse every page source during window construction, where the cost is allowed
// to exceed one frame, so the lazy switch later never pays a cold source read on the
// UI thread. Guarded for the construction order: `pageSources` and the resolver can
// each still be undefined when this first runs.
// 在窗口构建期预解析全部页面源码(该阶段允许超过一帧), 使之后的懒加载切换不必在 UI 线程
// 支付冷读取。针对构造顺序做了守卫: 首次运行时 `pageSources` 与解析器都可能仍未就绪。
function warmSkeletonSources(host) {
    var resolver = resolverFor(host)
    if (!resolver || typeof resolver.warm !== "function") return
    var sources = host._safePageSources
    if (!sources || typeof sources.length !== "number" || sources.length === 0) return
    resolver.warm(sources)
}

// The page's real initial properties, with reserved engine metadata removed. The
// common case has no reserved key and returns the original object untouched.
// 页面真实初始属性, 已剔除引擎保留元数据。常见情形没有保留键, 原样返回原对象。
function initialPropertiesFor(host, index) {
    var properties = propertiesFor(host, index)
    var keys = Object.keys(properties)
    var reserved = false
    for (var keyIndex = 0; keyIndex < keys.length; keyIndex++) {
        if (RESERVED_KEYS.indexOf(keys[keyIndex]) !== -1) {
            reserved = true
            break
        }
    }
    if (!reserved) return properties
    var filtered = ({})
    for (var copyIndex = 0; copyIndex < keys.length; copyIndex++) {
        var key = keys[copyIndex]
        if (RESERVED_KEYS.indexOf(key) === -1) filtered[key] = properties[key]
    }
    return filtered
}
