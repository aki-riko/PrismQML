// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "_internal" as FilterBarInternal

// FilterBarCore - Filter base class 过滤器基类
// Pill buttons in gray container 药丸按钮在灰色容器中
// Supports: pure text / pure icon / icon+text (auto-detect) 支持纯文本/纯图标/图标+文本（自动识别）
Rectangle {
    id: control

    // ==================== Public Props 公开属性 ====================
    // Items format 选项格式:
    //   - String: "All" (text) or "Home" (icon name if PascalCase >3 chars)
    //   - Object: { text: "Home", icon: "Home" } or { text: "Home" } or { icon: "Home" }
    property var items: []
    property int currentIndex: 0  // Current selected index (exclusive mode) 当前选中索引（互斥模式）
    property bool exclusive: true  // true=单选, false=多选
    property var selectedIndices: [0]  // Selected indexes (multi-select mode) 选中索引（多选模式）
    property int iconSize: Enums.iconSize.s  // Icon size for filter items 过滤项图标尺寸

    // ==================== Readonly State 只读状态 ====================
    readonly property var _safeItems:
        items === null || items === undefined ? []
        : (typeof items.length === "number" ? items : [])
    readonly property var _safeSelectedIndices:
        selectedIndices === null || selectedIndices === undefined ? []
        : (typeof selectedIndices.length === "number" ? selectedIndices : [])

    // Color callables can be overridden by subclasses 颜色回调可由子类覆盖
    // Container background 容器背景色
    property var getContainerColor: function() {
        return Enums.stateColor.filterContainer
    }

    // Item background 选项背景色
    property var getItemBackgroundColor: function(selected, hovered) {
        if (selected) {
            return Enums.accentColor
        }
        if (hovered) {
            return Enums.stateColor.filterItemHover
        }
        return Enums.transparent
    }

    // Item text color 选项文字颜色
    property var getItemTextColor: function(selected) {
        if (selected) {
            return Enums.themeColors.accentForeground
        }
        return Enums.textColor.primary
    }

    // ==================== Signals 信号 ====================
    signal itemClicked(int index)
    signal selectionChanged(var indices)
    signal indexChanged(int index)  // Renamed to avoid conflict with currentIndex property 重命名避免与属性冲突

    // ==================== Public Methods 公开方法 ====================
    // Parse item data - auto detect icon/text 解析选项数据 - 自动识别图标/文本
    // Returns: { icon: string, text: string }
    function parseItem(data) {
        // Object format 对象格式
        if (typeof data === "object" && data !== null) {
            return {
                icon: data.icon || "",
                text: data.text || ""
            }
        }
        // String format - auto detect 字符串格式 - 自动识别
        if (typeof data === "string") {
            // Check for icon name (PascalCase, >3 chars) 检查是否为图标名称（PascalCase，>3 字符）
            var isIconName = /^[A-Z][a-zA-Z0-9]+$/.test(data) && data.length > 3
            if (isIconName) {
                return { icon: data, text: "" }
            }
            return { icon: "", text: data }
        }
        return { icon: "", text: String(data) }
    }

    // Calculate item position for sliding indicator 计算滑动指示器位置
    function getItemX(idx) {
        if (idx < 0 || idx >= contentLayer.itemRepeater.count) return 0
        var x = 0
        for (var i = 0; i < idx; i++) {
            var item = contentLayer.itemRepeater.itemAt(i)
            if (item) x += item.width + Enums.spacing.xs
        }
        return x
    }

    function getItemWidth(idx) {
        if (idx < 0 || idx >= contentLayer.itemRepeater.count) return 0
        var item = contentLayer.itemRepeater.itemAt(idx)
        return item ? item.width : 0
    }

    function getCurrentIndex() { return currentIndex }

    function isEnabled() { return enabled }

    // ==================== Size 尺寸 ====================
    implicitWidth: contentLayer.contentWidth + Enums.spacing.m * 2
    implicitHeight: Enums.controlSize.inputHeightLarge  // 40
    radius: Enums.surfaceRadius(Enums.radius.small)

    // Appearance 外观
    color: getContainerColor()
    opacity: enabled ? 1.0 : 0.5

    // ==================== Content 内容 ====================
    FilterBarInternal.FilterBarContent {
        id: contentLayer
        filterControl: control
    }
}
