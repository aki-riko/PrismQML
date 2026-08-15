// ButtonLogic - Stateless button behavior helpers 无状态按钮行为辅助
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

.pragma library

function click(control, enums) {
    if (!control.enabled || control.loading || control._countdownActive) return
    if (control.feature === enums.button.feature_toggle) {
        control.checked = !control.checked
        control.toggled(control.checked)
    }
    control.clicked()
}

function toggle(control, enums) {
    if (control.feature === enums.button.feature_toggle) {
        control.checked = !control.checked
        control.toggled(control.checked)
    }
}

function setCheckable(control, enums, checkable) {
    if (checkable) {
        control.feature = enums.button.feature_toggle
    } else if (control.feature === enums.button.feature_toggle) {
        control.feature = enums.button.feature_none
    }
}

function isCheckable(control, enums) {
    return control.feature === enums.button.feature_toggle
}

function setFlat(control, enums, flat) {
    if (flat) control.style = enums.button.style_transparent
}

function updateTargetColors(control, enums, hoverActive, bgColorAnim, borderColorAnim) {
    var newBg = control._styleBgColor
    var newBorder = control._styleBorderColor
    var animate = hoverActive === undefined ? true : hoverActive
    var transitionDuration = animate
        ? enums.duration.medium : enums.motion.hoverExitDuration

    if (control.pressed || transitionDuration === enums.duration.none) {
        // Press and hover exit reset immediately. 按下与悬浮退出立即复位。
        bgColorAnim.stop()
        borderColorAnim.stop()
        control._targetBgColor = newBg
        control._targetBorderColor = newBorder
        control._animatedBgColor = newBg
        control._animatedBorderColor = newBorder
    } else {
        // Hover entry and non-hover style changes retain their animation. 悬浮进入及非悬浮样式变化保留动画。
        control._targetBgColor = newBg
        control._targetBorderColor = newBorder
        bgColorAnim.restart()
        borderColorAnim.restart()
    }
}

function completeHoverExit(control, enums, bgColorAnim, borderColorAnim) {
    if (!control._hoverExitPending || control.hovered) return
    updateTargetColors(control, enums, false, bgColorAnim, borderColorAnim)
    control._hoverExitPending = false
}

function syncCustomContentState(control, customContentContainer) {
    // Snapshot only when children actually change. 仅在子项真实变化时取快照。
    // Avoid a long-lived QQuickItem.children list binding across page transitions. 避免跨页面切换长期持有 QQuickItem.children 列表绑定。
    control.hasCustomContent = customContentContainer.children.length > 0
}

function prewarmMenu(control, enums, featureItem) {
    var hasMenuFeature = control.feature === enums.button.feature_dropdown
        || control.feature === enums.button.feature_split
    if (hasMenuFeature && control.enabled && !control.loading
            && (control.menu !== null && control.menu !== undefined
                || control._safeMenuItems.length > 0)
            && featureItem) {
        featureItem.prewarmMenu()
    }
}

function retryMenuPrewarm(control, enums, featureItem, mouseArea) {
    var splitArrowHovered = control.feature === enums.button.feature_split
        && featureItem && featureItem.dropHovered
    if (control.activeFocus || mouseArea.containsMouse || splitArrowHovered) {
        prewarmMenu(control, enums, featureItem)
    }
}

function runMenuPrewarmRetry(control, enums, featureItem, mouseArea) {
    control._menuPrewarmRetryScheduled = false
    retryMenuPrewarm(control, enums, featureItem, mouseArea)
}

function resetCountdown(control) {
    control._countdownActive = false
    control._countdownRemaining = 0
    control._countdownInitialWidth = 0
}

function startCountdown(control) {
    control._countdownInitialWidth = control.width
    control._countdownRemaining = control.countdown
    control._countdownActive = true
}
