// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// StackedPageActivityController - Opt-in page activity synchronization 页面活动状态同步
Item {
    id: controller

    // ==================== Required Props 必需属性 ====================
    required property Item host
    required property Item directContainer

    // ==================== Internal Methods 内部方法 ====================
    function _pageRoot(index) {
        if (index < 0 || index >= host.count) return null
        if (host._useSourceMode) {
            var loader = index < host._loaders.length ? host._loaders[index] : null
            return loader ? loader.item : null
        }
        return index < directContainer.children.length
                ? directContainer.children[index] : null
    }

    function _setActivity(page, active) {
        if (!page) return
        // 页面对活动状态有两种声明方式: 可写属性(写入即生效) 与只读属性
        // (由页面自身从 visible 派生)。`"pageActive" in page` 对**只读**属性
        // 同样成立, 直接赋值会抛:
        //   TypeError: Cannot assign to read-only property "pageActive"
        // 该异常会沿 sync() → _updateVisibility() → cancelPendingLazySwitch()
        // 冒泡, 使一次「上一次切页未收尾就点下一页」的切换在 retarget 取消后
        // 中断, _displayIndex 永远停在旧页(实测 100% 复现: 点导航内容区不变)。
        // 因此每次写入独立 try/catch: 只读属性写入失败即视为"该页自管活动态",
        // 不影响其它页, 也不中断切换流程。
        _writeActivity(page, "schedulerActive", active)
        _writeActivity(page, "pageActive", active)
    }

    // 写入一个活动属性; 属性不存在或为只读时静默跳过, 绝不抛出。
    function _writeActivity(page, name, active) {
        if (!(name in page)) return
        try {
            page[name] = active
        } catch (error) {
            // 只读属性: 页面自行派生活动态, 这里无需也无法写入。
            // 保留 console 静默, 避免每次切页刷屏。
        }
    }

    // Only pages that declare an activity property opt into this contract.
    // 仅显式声明活动属性的页面加入此契约。
    function sync(activeIndex) {
        if (host._destroying) return
        var pageCount = host._useSourceMode
                ? host._loaders.length : directContainer.children.length
        for (var index = 0; index < pageCount; index++) {
            _setActivity(_pageRoot(index), index === activeIndex)
        }
    }

    visible: false
}
