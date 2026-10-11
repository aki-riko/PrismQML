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
    navigate(control)
    control.clicked()
}

// Open the configured hyperlink target and mark the button visited.
// 打开配置的超链接目标并把按钮标记为已访问。
// An empty navigateUri keeps the plain button behavior untouched.
// navigateUri 为空时按钮行为与普通按钮完全一致。
function navigate(control) {
    var uri = control.navigateUri
    if (uri === undefined || uri === null || uri === "") return
    control.visited = true
    control.navigationRequested(uri)
    if (!control.navigateOnClick) return
    if (typeof control.urlOpener === "function") control.urlOpener(uri)
    else Qt.openUrlExternally(uri)
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

// ==================== Appearance overrides 外观覆盖 ====================

// A supplied face override switches the caller to an instant face change, so the
// animated colour is bypassed entirely.
// 提供面色覆盖时，调用方同时要求即时切换面色，因此完全绕过动画色。
function hasPressedBgOverride(control) {
    return control.pressedBgColor !== null && control.pressedBgColor !== undefined
}

function hasHoverBgOverride(control) {
    return control.hoverBgColor !== null && control.hoverBgColor !== undefined
}

// Overrides resolve against the shared disabled state so a disabled icon button never
// keeps a hover tint. The disabled branch falls back to the style snapshot instead of a
// token, because each style derives its own disabled foreground.
// 覆盖值结合共享禁用态解析，确保禁用图标按钮不残留悬浮底色。禁用分支回退到样式快照
// 而不是固定 token，因为各样式有自己的禁用前景推导。
function effectiveIconColor(control) {
    if (!control._styleEffectiveEnabled) return control._styleTextColor
    return control._touchActive ? control.iconHoverColor : control.iconColor
}

function effectiveBgColor(control, stateColor) {
    // Disabled, loading, and countdown states keep the style-specific face. 禁用、加载和倒计时状态保留样式专属面色。
    // Transparent styles already resolve to a transparent face, while solid styles must not expose only their shadow. 透明样式本身会解析为透明面色，实心样式不能只显示阴影。
    if (!control._styleEffectiveEnabled) return control._styleBgColor
    if (control.pressed) {
        return hasPressedBgOverride(control) ? control.pressedBgColor
                                             : control._animatedBgColor
    }
    if (hasHoverBgOverride(control)) {
        return control._touchActive ? control.hoverBgColor : control._styleBgColor
    }
    return hasPressedBgOverride(control) ? control._styleBgColor
                                         : control._animatedBgColor
}
