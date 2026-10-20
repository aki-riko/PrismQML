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

// Declared skeleton structure for one page, or an empty list when unusable. An
// unusable declaration makes the skeleton renderer fall back to the generic one.
// 某页声明的骨架结构; 不可用时返回空列表。不可用声明会让骨架渲染器回退通用骨架。
function skeletonBlocksFor(host, index) {
    var declared = propertiesFor(host, index).skeleton
    if (!declared || typeof declared !== "object") return []
    if (typeof declared.length !== "number") return []
    return declared
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
