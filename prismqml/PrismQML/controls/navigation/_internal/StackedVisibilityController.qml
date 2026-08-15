// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// StackedVisibilityController - Page visibility and animation orchestration
// StackedVisibilityController - 页面可见性与动画编排
Item {
    id: controller

    // ==================== Required Props 必需属性 ====================
    required property Item host
    required property Item animations
    required property Item container

    // ==================== Public Methods 公开方法 ====================
    function doAnimation(oldIndex, newIndex) {
        hideAllExcept([oldIndex, newIndex])

        if (!host.animationEnabled || host.animationType === Enums.animation.none) {
            updateVisibility(newIndex)
            host.currentChanged(newIndex)
            return
        }

        var isBack = newIndex < oldIndex
        switch (host.animationType) {
        case Enums.animation.opacity:
            animations.fadeTransition(oldIndex, newIndex)
            break
        case Enums.animation.popup:
            animations.popUpTransition(oldIndex, newIndex)
            break
        case Enums.animation.popdown:
            animations.popDownTransition(oldIndex, newIndex)
            break
        case Enums.animation.slide:
            animations.slideTransition(oldIndex, newIndex, isBack)
            break
        case Enums.animation.card:
            animations.cardTransition(oldIndex, newIndex, isBack)
            break
        case Enums.animation.zoom:
            animations.zoomTransition(oldIndex, newIndex)
            break
        default:
            animations.fadeTransition(oldIndex, newIndex)
        }

        host.animationStarted()
    }

    function doEnterAnimation(newIndex) {
        hideAllExcept([newIndex])

        if (!host.animationEnabled || host.animationType === Enums.animation.none) {
            updateVisibility(newIndex)
            host.currentChanged(newIndex)
            return
        }

        switch (host.animationType) {
        case Enums.animation.opacity:
            animations.enterFadeOnly(newIndex)
            break
        case Enums.animation.popup:
            animations.enterPopUpOnly(newIndex)
            break
        case Enums.animation.popdown:
            animations.enterPopDownOnly(newIndex)
            break
        case Enums.animation.zoom:
            animations.enterZoomOnly(newIndex)
            break
        case Enums.animation.slide:
        case Enums.animation.card:
            animations.enterSlideOnly(newIndex)
            break
        default:
            animations.enterFadeOnly(newIndex)
        }
        host.animationStarted()
    }

    function hideAllExcept(exceptIndices) {
        if (host._destroying) return
        if (host._useSourceMode) {
            for (var i = 0; i < host._loaders.length; i++) {
                var loader = host._loaders[i]
                if (loader && exceptIndices.indexOf(i) === -1) {
                    // Each assignment may synchronously destroy a Loader through bindings.
                    // 每次赋值都可能通过绑定同步销毁 Loader，因此逐项重验引用。
                    loader.visible = false
                    if (!loader) continue
                    loader.opacity = 0
                    if (!loader) continue
                    loader.y = 0
                    if (!loader) continue
                    loader.x = 0
                    if (!loader) continue
                    loader.scale = 1
                }
            }
        } else {
            for (var j = 0; j < container.children.length; j++) {
                if (exceptIndices.indexOf(j) === -1) {
                    var child = container.children[j]
                    child.visible = false
                    child.opacity = 0
                    child.y = 0
                    child.x = 0
                    child.scale = 1
                }
            }
        }
    }

    function updateVisibility(newIndex) {
        if (host._useSourceMode) {
            for (var i = 0; i < host._loaders.length; i++) {
                if (host._loaders[i]) {
                    var isCurrent = i === newIndex
                    host._loaders[i].visible = isCurrent
                    host._loaders[i].opacity = isCurrent ? 1 : 0
                }
            }
        } else {
            for (var j = 0; j < container.children.length; j++) {
                var child = container.children[j]
                child.visible = j === newIndex
                child.opacity = j === newIndex ? 1 : 0
            }
        }
    }
}
