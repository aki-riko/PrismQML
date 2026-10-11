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
        if ("schedulerActive" in page) page.schedulerActive = active
        if ("pageActive" in page) page.pageActive = active
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
