// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../utils"
import "../../containers"
import "ButtonStyle.js" as ButtonStyle
import "_internal" as ButtonInternal
import "_internal/ButtonLogic.js" as ButtonLogic

// Button - Unified button component 统一按钮组件
// Auto-detect type by icon/text content 根据图标/文本自动识别类型
// Modular architecture: uses internal modules 模块化架构
Widget {
    id: control

    // ==================== Public Props 公开属性 ====================
    // icon only → ToolButton style, icon+text or text only → PushButton style 仅图标 → 工具按钮样式，图标+文本或仅文本 → 普通按钮样式

    readonly property bool isToolButton: icon !== "" && text === ""

    // Button style 按钮样式
    property int style: Enums.button.style_default
    property int shape: Enums.button.shape_default
    property int feature: Enums.button.feature_none
    property bool showDropdownIndicator: true
    property int contentAlignment: feature === Enums.button.feature_dropdown && showDropdownIndicator
                                   ? Enums.button.align_left
                                   : Enums.button.align_center  // Content alignment 内容对齐

    // Button content 按钮内容
    property string text: ""
    property string icon: ""           // Icon name / image path 图标名或图片路径
    property int iconSize: isToolButton && !_hasMenuFeature
                           ? Enums.iconSize.xl
                           : Enums.iconSize.m
    default property alias contentData: customContentContainer.data  // Custom content 自定义内容
    property alias border: surface.border
    property bool hasCustomContent: false

    // Button features 按钮功能
    property bool checked: false
    property bool loading: false
    property string loadingText: ""
    property real progress: 0
    property bool showProgress: false
    property var menuItems: []
    property var menu: null  // Optional external PopupWindowCore-compatible menu 外部菜单
    property int level: 0
    property string textToCopy: ""
    property int countdown: Enums.button.countdownDefault
    property string countdownText: Enums.button.countdownSuffix
    property int _countdownRemaining: 0
    property bool _countdownActive: false
    property real _countdownInitialWidth: 0
    property bool dropdownOpen: false  // External dropdown open state 外部下拉打开状态

    readonly property var _safeMenuItems:
        menuItems === null || menuItems === undefined ? []
        : (typeof menuItems.length === "number" ? menuItems : [])

    // Base appearance 基础外观
    property bool flat: style === Enums.button.style_transparent ||
                        style === Enums.button.style_text ||
                        style === Enums.button.style_hyperlink

    // Text style 文本样式
    readonly property int fontSize: Enums.typography.body
    // Optional font flags 可选字体修饰 (e.g. 富文本工具栏 B/I/U/S 按钮)
    property bool fontBold: false
    property bool fontItalic: false
    property bool fontUnderline: false
    property bool fontStrikeout: false

    // Interaction state 交互状态
    property bool pseudoHovered: false
    property bool pseudoPressed: false
    property bool hovered: feature === Enums.button.feature_split
                           ? false : (mouseArea.containsMouse || pseudoHovered)
    property bool pressed: feature === Enums.button.feature_split ? false : ((mouseArea && mouseArea.pressed) || pseudoPressed)
    readonly property bool _toolTipHovered: feature === Enums.button.feature_split
        ? (pseudoHovered || (featureLoader.item &&
            (featureLoader.item.mainHovered || featureLoader.item.dropHovered)))
        : hovered

    // Shared style calculations avoid one resident QtObject per button.
    // 共享样式计算避免每个按钮常驻一个QtObject。
    readonly property bool _styleEffectiveEnabled:
        control.enabled && !control.loading && !control._countdownActive
    readonly property bool _styleToggleChecked:
        feature === Enums.button.feature_toggle && control.checked
    readonly property var styleHelper: ButtonStyle.snapshot(
        style, level, _styleEffectiveEnabled, hovered, pressed,
        _styleToggleChecked, Enums.isNeobrutalism, Enums.isVintageTicket,
        Enums.isNeumorphism,
        Enums.button, Enums.stateColor, Enums.textColor, Enums.statusLevel,
        Enums.accentColor, Enums.cardColor, Enums.accentForeground,
        Enums.transparent, Enums.opacityLevel, Enums.neo, Enums.ticket)
    readonly property color _styleBgColor: styleHelper.bgColor
    readonly property color _styleBorderColor: styleHelper.borderColor
    readonly property color _styleTextColor: styleHelper.textColor

    // Appearance and animated colors 外观与动画颜色
    property int radius: shape === Enums.button.shape_pill ? height / 2
                         : (Enums.isNeobrutalism ? Enums.neo.radius
                         : (Enums.isNeumorphism ? Enums.neumorphism.radius
                            : (Enums.isVintageTicket ? Enums.ticket.radius
                               : Enums.radius.small)))
    property color color: _styleBgColor

    // Neobrutalism target press shift. Neo按压目标位移。
    readonly property real _neoPressTargetShift:
        (Enums.isNeobrutalism && pressed && !flat) ? Enums.neo.pressOffset : 0
    // The loaded Neo surface owns animation; Fluent keeps no resident Behavior. 动画由已加载的Neo表面持有，Fluent不常驻Behavior。
    property real _neoPressShift:
        surface.animatedPressShift
    readonly property bool _hasMenuFeature: feature === Enums.button.feature_dropdown ||
                                            feature === Enums.button.feature_split
    readonly property bool _hasProgressBarFeature:
        feature === Enums.button.feature_progress_bar ||
        feature === Enums.button.feature_indeterminate_bar
    readonly property bool _hasFeatureVisual:
        _hasProgressBarFeature || feature === Enums.button.feature_toggle
    readonly property bool _showsDropdownIndicator: feature === Enums.button.feature_dropdown &&
                                                    showDropdownIndicator
    readonly property int _contentLeadingPadding: _hasMenuFeature ? Enums.spacing.l : Enums.spacing.m
    readonly property int _contentTrailingPadding: _hasMenuFeature ? Enums.spacing.xs : Enums.spacing.m

    // Animated colors with instant press, smooth release 动画颜色：按下瞬间，释放平滑
    property color _animatedBgColor
    property color _animatedBorderColor
    property color _targetBgColor
    property color _targetBorderColor
    property bool _colorAnimationsReady: false
    property bool _hoverExitPending: false
    property bool _menuPrewarmRetryScheduled: false

    // ==================== Signals 信号 ====================
    signal clicked()
    // 注意: 不能命名为 pressed, 会与下方 `property bool pressed` 同名,
    // QML 中属性会遮蔽同名信号, 导致 emit (pressed()) 把 bool 当函数调而报 TypeError。
    // 外部监听按下请用 onButtonPressed。
    signal buttonPressed()
    signal released()
    signal doubleClicked()
    signal toggled(bool checked)
    signal menuItemClicked(int index, string text)
    signal menuAboutToOpen()
    signal countdownFinished()

    // ==================== Public Methods 公开方法 ====================
    function getTextColor() { return _styleTextColor }

    // Programmatic click 程序化点击
    function click() { ButtonLogic.click(control, Enums) }

    // Toggle state 切换状态
    function toggle() { ButtonLogic.toggle(control, Enums) }

    // Set checkable state 设置可切换状态
    function setCheckable(checkable) { ButtonLogic.setCheckable(control, Enums, checkable) }

    // Check if checkable 检查是否可切换
    function isCheckable() { return ButtonLogic.isCheckable(control, Enums) }

    function _updateTargetColors(hoverActive) {
        ButtonLogic.updateTargetColors(
            control, Enums, hoverActive,
            surface.bgColorAnimation, surface.borderColorAnimation
        )
    }

    function _completeHoverExit() {
        ButtonLogic.completeHoverExit(
            control, Enums,
            surface.bgColorAnimation, surface.borderColorAnimation
        )
    }

    function _syncCustomContentState() {
        ButtonLogic.syncCustomContentState(control, customContentContainer)
    }

    function getText() { return text }


    function isChecked() { return checked }

    function isEnabled() { return enabled }


    // Set flat 设置扁平样式
    function setFlat(f) { ButtonLogic.setFlat(control, Enums, f) }


    function getUrl() { return textToCopy }

    function resetCountdown() { ButtonLogic.resetCountdown(control) }

    function startCountdown() { ButtonLogic.startCountdown(control) }

    function _prewarmMenu() {
        ButtonLogic.prewarmMenu(control, Enums, featureLoader.item)
    }

    function _retryMenuPrewarm() {
        ButtonLogic.retryMenuPrewarm(control, Enums, featureLoader.item, mouseArea)
    }

    function _scheduleMenuPrewarmRetry() {
        if (!_hasMenuFeature || _menuPrewarmRetryScheduled) return
        _menuPrewarmRetryScheduled = true
        Qt.callLater(control._runMenuPrewarmRetry)
    }

    function _runMenuPrewarmRetry() {
        ButtonLogic.runMenuPrewarmRetry(control, Enums, featureLoader.item, mouseArea)
    }

    function _startButtonToolTipTimer() {
        _startToolTipShowTimer()
    }

    function _stopButtonToolTipTimer() {
        _stopToolTipShowTimer()
    }

    function _dismissToolTipForMenu() {
        _stopButtonToolTipTimer()
        _dismissToolTip()
    }

    // Layout override 布局覆盖
    // 按钮默认不应填充父布局宽度（覆盖Widget基类的layoutFillWidth: true）
    layoutFillWidth: false

    // ==================== Size 尺寸 ====================
    // Content size calculation (inherited from Widget) 内容尺寸计算（继承自Widget）
    contentWidth: {
        if (_countdownActive && _countdownInitialWidth > 0) return _countdownInitialWidth
        if (isToolButton) {
            return Enums.controlSize.buttonHeight +
                   (_showsDropdownIndicator ? Enums.controlSize.dropdownArrowWidth : 0)
        }
        // Transparent/text/hyperlink styles have no minimum width 透明/文本/超链接样式无最小宽度
        var cw = contentLoader.item ?
            contentLoader.item.width + _contentLeadingPadding + _contentTrailingPadding : 0
        var extraWidth = feature === Enums.button.feature_split ? Enums.controlSize.splitButtonArrowWidth :
                        (_showsDropdownIndicator ? Enums.controlSize.dropdownArrowWidth : 0)
        if (flat || _hasMenuFeature) return Math.max(cw + extraWidth, Enums.controlSize.buttonHeight)
        return Math.max(Enums.controlSize.buttonMinWidth, cw + extraWidth)
    }
    contentHeight: Enums.controlSize.buttonHeight

    Component.onCompleted: {
        // Initialize with current values (break binding) 用当前值初始化（打破绑定）
        _animatedBgColor = _styleBgColor
        _animatedBorderColor = _styleBorderColor
        _targetBgColor = _styleBgColor
        _targetBorderColor = _styleBorderColor
        _colorAnimationsReady = true
    }

    onPressedChanged: {
        if (pressed) {
            // Instant press: stop any running animation and set directly 按下瞬间：停止动画直接设置
            surface.bgColorAnimation.stop()
            surface.borderColorAnimation.stop()
            _animatedBgColor = _styleBgColor
            _animatedBorderColor = _styleBorderColor
        }
    }

    onShowDropdownIndicatorChanged: {
        if (showDropdownIndicator &&
                feature === Enums.button.feature_dropdown &&
                contentLoader.item) {
            contentLoader._indicatorTransitionWidth = Math.max(
                contentLoader.item.implicitWidth,
                width - _contentLeadingPadding - _contentTrailingPadding)
        }
    }

    // Watch hover changes directly for reliable updates 直接监听悬浮变化以确保可靠更新
    onHoveredChanged: {
        _hoverExitPending = !hovered
        _updateTargetColors(hovered)
        if (_hoverExitPending) Qt.callLater(control._completeHoverExit)
    }
    on_StyleBgColorChanged: {
        if (_colorAnimationsReady) _updateTargetColors(!_hoverExitPending)
    }
    on_StyleBorderColorChanged: {
        if (_colorAnimationsReady) _updateTargetColors(!_hoverExitPending)
    }

    on_ToolTipHoveredChanged: {
        // ToolTip trigger 触发ToolTip
        if (toolTipText !== "") {
            if (_toolTipHovered) _startButtonToolTipTimer()
            else { _stopButtonToolTipTimer(); hideToolTip() }
        }
    }

    onActiveFocusChanged: {
        if (activeFocus) _prewarmMenu()
    }
    onMenuItemsChanged: _scheduleMenuPrewarmRetry()
    onLoadingChanged: if (!loading) _scheduleMenuPrewarmRetry()
    onEnabledChanged: if (enabled) _scheduleMenuPrewarmRetry()
    on_ToolTipTimersCanceled: _stopButtonToolTipTimer()

    // ==================== Content 内容 ====================
    ButtonInternal.ButtonSurface {
        id: surface
        buttonControl: control
    }

    // Modular content 模块化内容
    // Custom content container 自定义内容容器
    Item {
        id: customContentContainer
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: contentAlignment === Enums.button.align_left ? parent.left : undefined
        anchors.right: contentAlignment === Enums.button.align_right ? parent.right : undefined
        anchors.horizontalCenter: contentAlignment === Enums.button.align_center ? parent.horizontalCenter : undefined
        anchors.leftMargin: contentAlignment === Enums.button.align_left ? control._contentLeadingPadding : 0
        anchors.rightMargin: contentAlignment === Enums.button.align_right ? control._contentTrailingPadding : 0
        anchors.horizontalCenterOffset: contentAlignment === Enums.button.align_center ?
                                        (feature === Enums.button.feature_split ? -Enums.controlSize.splitButtonContentOffset :
                                        (control._showsDropdownIndicator ? -Enums.spacing.m : 0)) : 0
        z: Enums.zIndex.content
        visible: control.hasCustomContent
        onChildrenChanged: control._syncCustomContentState()
        Component.onCompleted: control._syncCustomContentState()
        // Neobrutalism 按下位移: 内容随 face 一起滑动
        transform: surface.pressTransform
    }

    Loader {
        id: contentLoader
        property real _indicatorTransitionWidth: -1

        width: item ? (_indicatorTransitionWidth >= 0
                       ? _indicatorTransitionWidth : item.implicitWidth) : 0
        x: {
            if (contentAlignment === Enums.button.align_left)
                return control._contentLeadingPadding
            if (contentAlignment === Enums.button.align_right)
                return parent.width - width - control._contentTrailingPadding
            var centerOffset = feature === Enums.button.feature_split
                               ? -Enums.controlSize.splitButtonContentOffset
                               : (control._showsDropdownIndicator ? -Enums.spacing.m : 0)
            return (parent.width - width) / 2 + centerOffset
        }
        anchors.verticalCenter: parent.verticalCenter
        z: Enums.zIndex.content
        active: !control.hasCustomContent  // Only load default content when no custom content 仅在无自定义内容时加载默认内容
        // Neobrutalism 按下位移: 默认内容(文字/图标)随 face 一起滑动
        transform: surface.pressTransform
        sourceComponent: ButtonContent {
            feature: control.feature
            style: control.style
            text: control.text
            icon: control.icon
            iconSize: control.iconSize
            loading: control.loading
            loadingText: control.loadingText
            progress: control.progress
            textColor: control.getTextColor()
            fontSize: control.fontSize
            fontBold: control.fontBold
            fontItalic: control.fontItalic
            fontUnderline: control.fontUnderline
            fontStrikeout: control.fontStrikeout
            countdownActive: control._countdownActive
            countdownRemaining: control._countdownRemaining
            countdownText: control.countdownText
        }
    }

    // Menu, progress, and toggle features are mutually exclusive. 菜单、进度与切换功能互斥。
    ButtonInternal.ButtonFeatureLoader {
        id: featureLoader
        button: control
        background: surface.background
        mainHovered: mouseArea.containsMouse
    }

    // Main interaction 主交互
    ButtonInternal.ButtonInteraction {
        id: mouseArea
        button: control
        featureItem: featureLoader.item
    }

    // Countdown timer 倒计时定时器
    ButtonInternal.ButtonCountdown {
        id: countdownTimer
        button: control
    }
}
