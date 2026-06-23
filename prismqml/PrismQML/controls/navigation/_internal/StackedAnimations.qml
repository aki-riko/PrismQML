// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."

// StackedAnimations - Animation definitions for StackedWidget 堆叠动画定义
Item {
    id: animations
    
    // ==================== Required Props 必需属性 ====================
    required property Item control
    required property int animationDuration
    required property real cardScale
    required property real cardOpacity

    property Item _zoomOldWidget: null
    property Item _zoomNewWidget: null

    // ==================== Signals 信号 ====================
    signal animationFinished(int currentIndex)
    
    // ==================== Helper 辅助方法 ====================
    function widget(index) { return control.widget(index) }
    
    // Stop all running animations and reset states 停止所有动画并重置状态
    function stopAllAnimations() {
        // Stop all animation groups 停止所有动画组
        fadeGroup.stop()
        slideGroup.stop()
        popUpGroup.stop()
        popDownGroup.stop()
        zoomOutAnim.stop()
        zoomInAnim.stop()
        cardGroup.stop()
        
        // Stop enter-only animations 停止仅入场动画
        enterFadeAnim.stop()
        enterPopUpGroup.stop()
        enterPopDownGroup.stop()
        enterZoomAnim.stop()
        enterSlideAnim.stop()
        
        // Reset all targets to clean state 重置所有目标到干净状态
        if (fadeOutAnim.target) {
            fadeOutAnim.target.opacity = 1
            fadeOutAnim.target.visible = false
        }
        if (fadeInAnim.target && fadeInAnim.target !== fadeOutAnim.target) {
            fadeInAnim.target.y = 0
            fadeInAnim.target.x = 0
            fadeInAnim.target.scale = 1
        }
        if (slideOutAnim.target) {
            slideOutAnim.target.x = 0
            slideOutAnim.target.visible = false
        }
        if (popUpGroup._oldWidget) {
            popUpGroup._oldWidget.visible = false
            popUpGroup._oldWidget.y = 0
        }
        if (popDownGroup._oldWidget) {
            popDownGroup._oldWidget.visible = false
            popDownGroup._oldWidget.y = 0
        }
        if (_zoomOldWidget) {
            _zoomOldWidget.visible = false
            _zoomOldWidget.scale = 1
        }
        if (cardGroup._oldWidget) {
            cardGroup._oldWidget.visible = false
            cardGroup._oldWidget.x = 0
            cardGroup._oldWidget.scale = 1
            cardGroup._oldWidget.opacity = 1
        }
        // Reset enter-only animation targets 重置仅入场动画目标
        if (enterPopUpGroup.target) {
            enterPopUpGroup.target.y = 0
        }
        if (enterPopDownGroup.target) {
            enterPopDownGroup.target.y = 0
        }
        if (enterSlideAnim.target) {
            enterSlideAnim.target.x = 0
        }
    }
    
    // ==================== 1. Fade Animation 淡入淡出 ====================
    function fadeTransition(oldIndex, newIndex) {
        stopAllAnimations()
        
        var oldWidget = widget(oldIndex)
        var newWidget = widget(newIndex)
        if (!oldWidget || !newWidget) return
        
        // Ensure old widget is in correct state 确保旧页面状态正确
        oldWidget.visible = true
        oldWidget.opacity = 1
        
        newWidget.opacity = 0
        newWidget.visible = true
        fadeOutAnim.target = oldWidget
        fadeInAnim.target = newWidget
        fadeGroup.start()
    }
// __MOVED_FUNCS_PLACEHOLDER__
    // Fade enter only 仅淡入
    function enterFadeOnly(newIndex) {
        stopAllAnimations()
        var newWidget = widget(newIndex)
        if (!newWidget) return
        enterFadeAnim.target = newWidget
        enterFadeAnim.start()
    }

    // PopUp enter only 仅PopUp入场
    function enterPopUpOnly(newIndex) {
        stopAllAnimations()
        var newWidget = widget(newIndex)
        if (!newWidget) return
        enterPopUpGroup.target = newWidget
        enterPopUpGroup.start()
    }

    // PopDown enter only 仅PopDown入场
    function enterPopDownOnly(newIndex) {
        stopAllAnimations()
        var newWidget = widget(newIndex)
        if (!newWidget) return
        enterPopDownGroup.target = newWidget
        enterPopDownGroup.start()
    }

    // Zoom enter only 仅缩放入场
    function enterZoomOnly(newIndex) {
        stopAllAnimations()
        var newWidget = widget(newIndex)
        if (!newWidget) return
        enterZoomAnim.target = newWidget
        enterZoomAnim.start()
    }

    // Slide enter only 仅滑动入场
    function enterSlideOnly(newIndex) {
        stopAllAnimations()
        var newWidget = widget(newIndex)
        if (!newWidget) return
        enterSlideAnim.target = newWidget
        enterSlideAnim.start()
    }
// __MOVED_FUNCS_PLACEHOLDER2__
    // 2. Slide Animation 滑动
    function slideTransition(oldIndex, newIndex, isBack) {
        stopAllAnimations()

        var oldWidget = widget(oldIndex)
        var newWidget = widget(newIndex)
        if (!oldWidget || !newWidget) return

        // Ensure old widget is in correct state 确保旧页面状态正确
        oldWidget.visible = true
        oldWidget.opacity = 1
        oldWidget.x = 0

        var direction = isBack ? 1 : -1
        newWidget.x = control.width * direction
        newWidget.opacity = 1  // Ensure visible 确保可见
        newWidget.visible = true
        slideOutAnim.target = oldWidget
        slideOutAnim.to = -control.width * direction
        slideInAnim.target = newWidget
        slideInAnim.from = control.width * direction
        slideGroup.start()
    }

    // 3. PopUp Animation 弹出
    function popUpTransition(oldIndex, newIndex) {
        stopAllAnimations()

        var oldWidget = widget(oldIndex)
        var newWidget = widget(newIndex)
        if (!oldWidget || !newWidget) return

        // Ensure old widget is in correct state 确保旧页面状态正确
        oldWidget.visible = true
        oldWidget.opacity = 1
        oldWidget.y = 0

        var offset = control.popUpOffset
        newWidget.y = offset
        newWidget.opacity = 0
        newWidget.visible = true
        popUpYAnim.target = newWidget
        popUpYAnim.from = offset
        popUpOpacityAnim.target = newWidget
        popUpGroup._oldWidget = oldWidget
        popUpGroup.start()
    }
// __MOVED_FUNCS_PLACEHOLDER3__
    // 3.5 PopDown Animation 下落
    function popDownTransition(oldIndex, newIndex) {
        stopAllAnimations()

        var oldWidget = widget(oldIndex)
        var newWidget = widget(newIndex)
        if (!oldWidget || !newWidget) return

        // Ensure old widget is in correct state 确保旧页面状态正确
        oldWidget.visible = true
        oldWidget.opacity = 1
        oldWidget.y = 0

        var offset = -control.popUpOffset
        newWidget.y = offset
        newWidget.opacity = 0
        newWidget.visible = true
        popDownYAnim.target = newWidget
        popDownYAnim.from = offset
        popDownOpacityAnim.target = newWidget
        popDownGroup._oldWidget = oldWidget
        popDownGroup.start()
    }

    // 4. Zoom Animation 缩放
    function zoomTransition(oldIndex, newIndex) {
        stopAllAnimations()

        var oldWidget = widget(oldIndex)
        var newWidget = widget(newIndex)
        if (!oldWidget || !newWidget) return

        // Ensure old widget is in correct state 确保旧页面状态正确
        oldWidget.visible = true
        oldWidget.opacity = 1
        oldWidget.scale = 1

        _zoomOldWidget = oldWidget
        _zoomNewWidget = newWidget

        newWidget.visible = false
        newWidget.opacity = 1
        newWidget.scale = 1

        zoomOutAnim.start()
    }
// __MOVED_FUNCS_PLACEHOLDER4__
    // 5. Card Animation 卡片层叠
    function cardTransition(oldIndex, newIndex, isBack) {
        stopAllAnimations()

        var oldWidget = widget(oldIndex)
        var newWidget = widget(newIndex)
        if (!oldWidget || !newWidget) return

        // Ensure old widget is in correct state 确保旧页面状态正确
        oldWidget.visible = true
        oldWidget.opacity = 1
        oldWidget.x = 0
        oldWidget.scale = 1

        if (isBack) {
            newWidget.visible = true
            newWidget.x = 0
            newWidget.scale = cardScale
            newWidget.opacity = cardOpacity

            cardSlideAnim.target = oldWidget
            cardSlideAnim.from = 0
            cardSlideAnim.to = control.width
            cardScaleAnim.target = newWidget
            cardScaleAnim.from = cardScale
            cardScaleAnim.to = 1
            cardOpacityAnim.target = newWidget
            cardOpacityAnim.from = cardOpacity
            cardOpacityAnim.to = 1
        } else {
            newWidget.visible = true
            newWidget.x = control.width
            newWidget.scale = 1
            newWidget.opacity = 1

            cardSlideAnim.target = newWidget
            cardSlideAnim.from = control.width
            cardSlideAnim.to = 0
            cardScaleAnim.target = oldWidget
            cardScaleAnim.from = 1
            cardScaleAnim.to = cardScale
            cardOpacityAnim.target = oldWidget
            cardOpacityAnim.from = 1
            cardOpacityAnim.to = cardOpacity
        }

        cardGroup._isBack = isBack
        cardGroup._oldWidget = oldWidget
        cardGroup.start()
    }

    ParallelAnimation {
        id: fadeGroup
        NumberAnimation { id: fadeOutAnim; property: "opacity"; from: 1.0; to: 0.0; duration: animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { id: fadeInAnim; property: "opacity"; from: 0.0; to: 1.0; duration: animationDuration; easing.type: Easing.InCubic }
        onFinished: {
            fadeOutAnim.target.visible = false
            fadeOutAnim.target.opacity = 1.0
            animations.animationFinished(control.currentIndex)
        }
    }
    
    // ==================== Enter Only Animations 仅入场动画（懒加载第二阶段） ====================

    NumberAnimation {
        id: enterFadeAnim
        property: "opacity"
        from: 0.0; to: 1.0
        duration: animationDuration
        easing.type: Easing.OutCubic
        onFinished: animations.animationFinished(control.currentIndex)
    }

    // PopUp enter only 仅PopUp入场
    ParallelAnimation {
        id: enterPopUpGroup
        property Item target
        NumberAnimation { target: enterPopUpGroup.target; property: "y"; to: 0; duration: animationDuration; easing.type: Easing.OutQuad }
        NumberAnimation { target: enterPopUpGroup.target; property: "opacity"; to: 1.0; duration: animationDuration; easing.type: Easing.OutQuad }
        onFinished: animations.animationFinished(control.currentIndex)
    }

    // PopDown enter only 仅PopDown入场
    ParallelAnimation {
        id: enterPopDownGroup
        property Item target
        NumberAnimation { target: enterPopDownGroup.target; property: "y"; to: 0; duration: animationDuration; easing.type: Easing.OutBounce }
        NumberAnimation { target: enterPopDownGroup.target; property: "opacity"; to: 1.0; duration: animationDuration; easing.type: Easing.OutQuad }
        onFinished: animations.animationFinished(control.currentIndex)
    }

    // Zoom enter only 仅缩放入场
    NumberAnimation {
        id: enterZoomAnim
        property: "scale"
        from: 0; to: 1
        duration: animationDuration / 2
        easing.type: Easing.OutQuad
        onFinished: animations.animationFinished(control.currentIndex)
    }

    // Slide enter only 仅滑动入场
    NumberAnimation {
        id: enterSlideAnim
        property: "x"
        to: 0
        duration: animationDuration
        easing.type: Easing.OutCubic
        onFinished: animations.animationFinished(control.currentIndex)
    }
    
    // ==================== 2. Slide Animation 滑动 ====================
    ParallelAnimation {
        id: slideGroup
        NumberAnimation { id: slideOutAnim; property: "x"; from: 0; duration: animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { id: slideInAnim; property: "x"; to: 0; duration: animationDuration; easing.type: Easing.OutCubic }
        onFinished: {
            slideOutAnim.target.visible = false
            slideOutAnim.target.x = 0
            animations.animationFinished(control.currentIndex)
        }
    }
    
    // ==================== 3. PopUp Animation 弹出 ====================
    ParallelAnimation {
        id: popUpGroup
        property Item _oldWidget: null
        NumberAnimation { id: popUpYAnim; property: "y"; to: 0; duration: animationDuration; easing.type: Easing.OutQuad }
        NumberAnimation { id: popUpOpacityAnim; property: "opacity"; from: 0.0; to: 1.0; duration: animationDuration; easing.type: Easing.OutQuad }
        onStarted: { if (_oldWidget) _oldWidget.visible = false }
        onFinished: animations.animationFinished(control.currentIndex)
    }
    
    // ==================== 3.5 PopDown Animation 下落 ====================
    ParallelAnimation {
        id: popDownGroup
        property Item _oldWidget: null
        NumberAnimation { id: popDownYAnim; property: "y"; to: 0; duration: animationDuration; easing.type: Easing.OutBounce }
        NumberAnimation { id: popDownOpacityAnim; property: "opacity"; from: 0.0; to: 1.0; duration: animationDuration; easing.type: Easing.OutQuad }
        onStarted: { if (_oldWidget) _oldWidget.visible = false }
        onFinished: animations.animationFinished(control.currentIndex)
    }
    
    // ==================== 4. Zoom Animation 缩放 ====================
    // Old page scale down (scale: 1 -> 0) 旧页面缩小
    SequentialAnimation {
        id: zoomOutAnim
        NumberAnimation {
            target: _zoomOldWidget
            property: "scale"
            from: 1; to: 0
            duration: animationDuration / 2
            easing.type: Easing.InQuad
        }
        ScriptAction {
            script: {
                _zoomOldWidget.visible = false
                _zoomOldWidget.scale = 1
                _zoomNewWidget.visible = true
                _zoomNewWidget.scale = 0
                zoomInAnim.start()
            }
        }
    }
    
    // New page scale up (scale: 0 -> 1) 新页面放大
    NumberAnimation {
        id: zoomInAnim
        target: _zoomNewWidget
        property: "scale"
        from: 0; to: 1
        duration: animationDuration / 2
        easing.type: Easing.OutQuad
        onFinished: animations.animationFinished(control.currentIndex)
    }
    
    // ==================== 5. Card Animation 卡片层叠 ====================
    ParallelAnimation {
        id: cardGroup
        property bool _isBack: false
        property Item _oldWidget: null
        
        NumberAnimation { id: cardSlideAnim; property: "x"; duration: animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { id: cardScaleAnim; property: "scale"; duration: animationDuration; easing.type: Easing.OutCubic }
        NumberAnimation { id: cardOpacityAnim; property: "opacity"; duration: animationDuration; easing.type: Easing.OutCubic }
        
        onFinished: {
            if (_oldWidget) {
                _oldWidget.visible = false
                _oldWidget.x = 0
                _oldWidget.scale = 1
                _oldWidget.opacity = 1
            }
            animations.animationFinished(control.currentIndex)
        }
    }
}
