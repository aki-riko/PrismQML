// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../../effects"
import QtQuick.Effects
import "../../icons"
import "../../utils"
import "../../containers"

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
    property int contentAlignment: feature === Enums.button.feature_dropdown ||
                                   feature === Enums.button.feature_split
                                   ? Enums.button.align_left
                                   : Enums.button.align_center  // Content alignment 内容对齐

    // Button content 按钮内容
    property string text: ""
    property string icon: ""           // Icon name / image path 图标名或图片路径
    property int iconSize: Enums.iconSize.m
    default property alias contentData: customContentContainer.data  // Custom content 自定义内容
    property bool hasCustomContent: customContentContainer.children.length > 0

    // Button features 按钮功能
    property bool checked: false
    property bool loading: false
    property string loadingText: ""
    property real progress: 0
    property bool showProgress: false
    property var menuItems: []
    property int level: 0
    property string textToCopy: ""
    property int countdown: Enums.button.countdownDefault
    property string countdownText: Enums.button.countdownSuffix
    property int _countdownRemaining: 0
    property bool _countdownActive: false
    property real _countdownInitialWidth: 0
    property bool dropdownOpen: false  // External dropdown open state 外部下拉打开状态

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
    property bool hovered: feature === Enums.button.feature_split ? false : (hoverHandler.hovered || pseudoHovered)
    property bool pressed: feature === Enums.button.feature_split ? false : ((mouseArea && mouseArea.pressed) || pseudoPressed)
    readonly property bool _toolTipHovered: feature === Enums.button.feature_split
        ? (pseudoHovered || (dropdownFeature.item &&
            (dropdownFeature.item.mainHovered || dropdownFeature.item.dropHovered)))
        : hovered

    // Style helper 样式辅助
    // 用具名 property 持有(而非匿名子项), 避免被 default property alias
    // contentData(→customContentContainer.data) 的归属探测卷入。
    // ButtonStyleHelper 是 QtObject(无 data 成员), 作为匿名子项时
    // 编译器对每个按钮实例都报 "Cannot find member data" 警告并干扰加载。
    readonly property ButtonStyleHelper styleHelper: ButtonStyleHelper {
        style: control.style
        feature: control.feature
        level: control.level
        controlEnabled: control.enabled
        loading: control.loading
        countdownActive: control._countdownActive
        hovered: control.hovered
        pressed: control.pressed
        isToggleChecked: feature === Enums.button.feature_toggle && control.checked
    }

    // Appearance and animated colors 外观与动画颜色
    property int radius: shape === Enums.button.shape_pill ? height / 2
                         : (Enums.isNeobrutalism ? Enums.neo.radius
                            : (Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.small))
    property color color: styleHelper.bgColor

    // Neobrutalism 按下位移量: 按下时控件向右下偏移, 视觉上"压平"硬阴影。Fluent 皮肤恒为 0。
    readonly property real _neoPressShift: (Enums.isNeobrutalism && pressed && !flat) ? Enums.neo.pressOffset : 0
    readonly property int _spectralEdgeInset: Math.min(radius, Math.max(Enums.spacing.none, width / 2 - Enums.spacing.xs))
    readonly property bool _hasMenuFeature: feature === Enums.button.feature_dropdown ||
                                            feature === Enums.button.feature_split
    readonly property int _contentLeadingPadding: _hasMenuFeature ? Enums.spacing.l : Enums.spacing.m
    readonly property int _contentTrailingPadding: _hasMenuFeature ? Enums.spacing.xs : Enums.spacing.m

    // Animated colors with instant press, smooth release 动画颜色：按下瞬间，释放平滑
    property color _animatedBgColor
    property color _animatedBorderColor
    property color _targetBgColor
    property color _targetBorderColor

    property Gradient _gradientDef: Gradient {
        GradientStop { position: Enums.button.gradientStart; color: Qt.lighter(Enums.accentColor, Enums.button.gradientLighten) }
        GradientStop { position: Enums.button.gradientEnd; color: Enums.accentColor }
    }

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
    signal countdownFinished()

    // ==================== Public Methods 公开方法 ====================
    function getTextColor() { return styleHelper.textColor }

    // Programmatic click 程序化点击
    function click() {
        if (!enabled || loading || _countdownActive) return
        if (feature === Enums.button.feature_toggle) {
            checked = !checked
            toggled(checked)
        }
        clicked()
    }

    // Toggle state 切换状态
    function toggle() {
        if (feature === Enums.button.feature_toggle) {
            checked = !checked
            toggled(checked)
        }
    }

    // Set checkable state 设置可切换状态
    function setCheckable(checkable) {
        if (checkable) {
            feature = Enums.button.feature_toggle
        } else if (feature === Enums.button.feature_toggle) {
            feature = Enums.button.feature_none
        }
    }

    // Check if checkable 检查是否可切换
    function isCheckable() {
        return feature === Enums.button.feature_toggle
    }

    function _updateTargetColors() {
        var newBg = styleHelper.bgColor
        var newBorder = styleHelper.borderColor

        if (pressed) {
            // During press: instant update 按下时：瞬间更新
            _animatedBgColor = newBg
            _animatedBorderColor = newBorder
        } else {
            // Not pressed: always animate to new color 非按下：始终动画到新颜色
            _targetBgColor = newBg
            _targetBorderColor = newBorder
            bgColorAnim.restart()
            borderColorAnim.restart()
        }
    }

    function getText() { return text }


    function isChecked() { return checked }

    function isEnabled() { return enabled }


    // Set flat 设置扁平样式
    function setFlat(f) {
        if (f) style = Enums.button.style_transparent
    }


    function getUrl() { return textToCopy }

    function resetCountdown() {
        _countdownActive = false
        _countdownRemaining = 0
        _countdownInitialWidth = 0
    }

    function startCountdown() {
        _countdownInitialWidth = width
        _countdownRemaining = countdown
        _countdownActive = true
    }

    function _prewarmMenu() {
        var hasMenuFeature = feature === Enums.button.feature_dropdown ||
                             feature === Enums.button.feature_split
        if (hasMenuFeature && enabled && !loading && menuItems.length > 0 &&
                dropdownFeature.item) {
            dropdownFeature.item.prewarmMenu()
        }
    }

    function _retryMenuPrewarm() {
        var splitArrowHovered = feature === Enums.button.feature_split &&
            dropdownFeature.item && dropdownFeature.item.dropHovered
        if (activeFocus || hoverHandler.hovered || splitArrowHovered) {
            _prewarmMenu()
        }
    }

    function _scheduleMenuPrewarmRetry() {
        if (!_hasMenuFeature || !_menuPrewarmRetryTimer.item) return
        if (!_menuPrewarmRetryTimer.item.running) _menuPrewarmRetryTimer.item.start()
    }

    function _startButtonToolTipTimer() {
        if (_btnToolTipTimer.item) _btnToolTipTimer.item.start()
    }

    function _stopButtonToolTipTimer() {
        if (_btnToolTipTimer.item) _btnToolTipTimer.item.stop()
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
        if (isToolButton) return Enums.controlSize.buttonHeight
        // Transparent/text/hyperlink styles have no minimum width 透明/文本/超链接样式无最小宽度
        var cw = contentLoader.item ?
            contentLoader.item.width + _contentLeadingPadding + _contentTrailingPadding : 0
        var extraWidth = feature === Enums.button.feature_split ? Enums.controlSize.splitButtonArrowWidth :
                        (feature === Enums.button.feature_dropdown ? Enums.controlSize.dropdownArrowWidth : 0)
        if (flat || _hasMenuFeature) return Math.max(cw + extraWidth, Enums.controlSize.buttonHeight)
        return Math.max(Enums.controlSize.buttonMinWidth, cw + extraWidth)
    }
    contentHeight: Enums.controlSize.buttonHeight

    Component.onCompleted: {
        // Initialize with current values (break binding) 用当前值初始化（打破绑定）
        _animatedBgColor = styleHelper.bgColor
        _animatedBorderColor = styleHelper.borderColor
        _targetBgColor = styleHelper.bgColor
        _targetBorderColor = styleHelper.borderColor
    }

    onPressedChanged: {
        if (pressed) {
            // Instant press: stop any running animation and set directly 按下瞬间：停止动画直接设置
            bgColorAnim.stop()
            borderColorAnim.stop()
            _animatedBgColor = styleHelper.bgColor
            _animatedBorderColor = styleHelper.borderColor
        }
    }

    // Watch hover changes directly for reliable updates 直接监听悬浮变化以确保可靠更新
    onHoveredChanged: {
        _updateTargetColors()
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
    HoverHandler {
        id: hoverHandler
        enabled: control.enabled && !control.loading && !control._countdownActive &&
                 feature !== Enums.button.feature_split
        onHoveredChanged: if (hovered) control._prewarmMenu()
    }

    Loader {
        id: _menuPrewarmRetryTimer
        active: control._hasMenuFeature

        sourceComponent: Timer {
            interval: Enums.duration.none
            onTriggered: control._retryMenuPrewarm()
        }
    }

    // ToolTip timer for Button - override Widget's _hoverArea
    // Button专用ToolTip定时器 - 覆盖Widget的_hoverArea
    Loader {
        id: _btnToolTipTimer
        active: control.toolTipText !== ""

        sourceComponent: Timer {
            interval: control.toolTipShowDelay
            onTriggered: if (control._toolTipHovered) control.showToolTip()
        }
    }

    // Shadow layer 阴影层
    // Fluent: 模糊阴影(RectangularShadow)。Neobrutalism: 硬阴影(偏移纯色矩形, 无模糊)。
    RectangularShadow {
        anchors.fill: _bg
        radius: _bg.radius
        color: Enums.shadow.level2.color
        blur: Enums.shadow.level2.blur
        offset.x: 0
        offset.y: Enums.shadow.level2.offset
        visible: !control.flat && !Enums.isNeobrutalism && !Enums.isPrismDesign
    }

    // Neobrutalism 硬阴影: 复用 NeoShadow 组件(纯黑零模糊, 偏移)。按下位移由下方 Translate 压平。
    Loader {
        id: neoShadowLoader
        active: Enums.isNeobrutalism && !control.flat
        z: _bg.z - 1

        sourceComponent: NeoShadow {
            target: _bg
        }
    }

    // Background 背景
    // Keep border alias next to child _bg per ordering rule 按排序规则将 border 别名紧邻子项 _bg
    property alias border: _bg.border
    Rectangle {
        id: _bg
        anchors.fill: parent
        radius: control.radius
        color: _animatedBgColor
        border.width: Enums.isNeobrutalism
            ? (flat ? 0 : Enums.neo.borderWidth)
            : (Enums.isPrismDesign
               ? (flat ? 0 : Enums.prismDesign.borderWidth)
               : ((styleHelper.isToggleChecked && style === Enums.button.style_primary) ? Enums.border.normal : (flat ? 0 : Enums.border.thin)))
        border.color: _animatedBorderColor  // neo 黑边由 styleHelper.borderColor 经 token 返回

        // Gradient (for gradient style) 渐变
        gradient: style === Enums.button.style_gradient ? _gradientDef : null

        // Neobrutalism 按下位移: face 向右下滑向硬阴影, 视觉压平。Fluent 下 shift 恒 0 无影响。
        transform: Translate {
            x: control._neoPressShift; y: control._neoPressShift
            Behavior on x { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
            Behavior on y { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
        }

        // Prism glass rim Prism玻璃边缘
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: Enums.prismDesign.borderWidth
            color: Enums.prismDesign.glassRimLight
            visible: Enums.isPrismDesign && !control.flat && control.enabled
        }

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: Enums.prismDesign.borderWidth
            color: Enums.prismDesign.glassRimShadow
            visible: Enums.isPrismDesign && !control.flat && control.enabled
        }

        // Spectral edge for active glass 光谱边用于激活玻璃态
        Rectangle {
            anchors.left: parent.left
            anchors.leftMargin: control._spectralEdgeInset
            anchors.right: parent.right
            anchors.rightMargin: control._spectralEdgeInset
            anchors.bottom: parent.bottom
            height: Enums.prismDesign.focusBorderWidth
            color: Enums.prismDesign.spectralEdge
            opacity: control.activeFocus ? 0.38 : 0.0
            visible: Enums.isPrismDesign && !control.flat && control.enabled
                     && control.activeFocus

            Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
        }
    }

    // Watch for target color changes (from styleHelper) 监听目标颜色变化
    Connections {
        function onBgColorChanged() { control._updateTargetColors() }
        function onBorderColorChanged() { control._updateTargetColors() }

        target: styleHelper
    }

    ColorAnimation {
        id: bgColorAnim
        target: control
        property: "_animatedBgColor"
        to: control._targetBgColor
        duration: Enums.duration.medium
        easing.type: Easing.InOutCubic
    }

    ColorAnimation {
        id: borderColorAnim
        target: control
        property: "_animatedBorderColor"
        to: control._targetBorderColor
        duration: Enums.duration.medium
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
                                        (feature === Enums.button.feature_dropdown ? -Enums.spacing.m : 0)) : 0
        z: Enums.zIndex.content
        visible: control.hasCustomContent
        // Neobrutalism 按下位移: 内容随 face 一起滑动
        transform: Translate {
            x: control._neoPressShift; y: control._neoPressShift
            Behavior on x { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
            Behavior on y { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
        }
    }

    Loader {
        id: contentLoader
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: contentAlignment === Enums.button.align_left ? parent.left : undefined
        anchors.right: contentAlignment === Enums.button.align_right ? parent.right : undefined
        anchors.horizontalCenter: contentAlignment === Enums.button.align_center ? parent.horizontalCenter : undefined
        anchors.leftMargin: contentAlignment === Enums.button.align_left ? control._contentLeadingPadding : 0
        anchors.rightMargin: contentAlignment === Enums.button.align_right ? control._contentTrailingPadding : 0
        anchors.horizontalCenterOffset: contentAlignment === Enums.button.align_center ?
                                        (feature === Enums.button.feature_split ? -Enums.controlSize.splitButtonContentOffset :
                                        (feature === Enums.button.feature_dropdown ? -Enums.spacing.m : 0)) : 0
        z: Enums.zIndex.content
        active: !control.hasCustomContent  // Only load default content when no custom content 仅在无自定义内容时加载默认内容
        // Neobrutalism 按下位移: 默认内容(文字/图标)随 face 一起滑动
        transform: Translate {
            x: control._neoPressShift; y: control._neoPressShift
            Behavior on x { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
            Behavior on y { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
        }
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
            controlEnabled: control.enabled
            fontSize: control.fontSize
            fontBold: control.fontBold
            fontItalic: control.fontItalic
            fontUnderline: control.fontUnderline
            fontStrikeout: control.fontStrikeout
            pressed: control.pressed
            countdownActive: control._countdownActive
            countdownRemaining: control._countdownRemaining
            countdownText: control.countdownText
        }
    }

    // Dropdown arrow 下拉箭头
    Loader {
        readonly property bool _useAccentForeground: control.style === Enums.button.style_primary ||
                                                      control.style === Enums.button.style_filled ||
                                                      control.style === Enums.button.style_gradient

        anchors.right: parent.right
        anchors.rightMargin: Enums.spacing.m
        anchors.verticalCenter: parent.verticalCenter
        active: feature === Enums.button.feature_dropdown

        sourceComponent: ChevronIcon {
            animated: true
            isOpen: control.dropdownOpen || (dropdownFeature.item ? dropdownFeature.item.isMenuOpen : false)
            color: !control.enabled ? Enums.stateColor.indicatorActive :
                   (parent._useAccentForeground ? Enums.accentForeground : Enums.textColor.secondary)
        }
    }

    // Progress feature 进度条模块
    Loader {
        id: progressFeatureLoader
        anchors.fill: parent
        active: feature === Enums.button.feature_progress_bar ||
                feature === Enums.button.feature_indeterminate_bar

        sourceComponent: Item {
            anchors.fill: parent

            // Rectangle defaults to opaque white, the intended mask source Rectangle 默认不透明白色，正是所需的遮罩源
            Rectangle {
                id: progressMask
                anchors.fill: parent
                radius: control.radius
                layer.enabled: true
                visible: false
            }

            Item {
                id: progressContent
                anchors.fill: parent
                layer.enabled: true
                layer.effect: MultiEffect {
                    maskEnabled: true
                    maskSource: progressMask
                    maskThresholdMin: Enums.mask.thresholdMin
                    maskSpreadAtMin: Enums.mask.spreadAtMin
                }

                Loader {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: Enums.border.thick
                    active: true
                    sourceComponent: ButtonProgress {
                        feature: control.feature
                        style: control.style
                        progress: control.progress
                        showProgress: control.showProgress
                        parentRadius: control.radius
                    }
                }
            }
        }
    }

    // Main interaction 主交互
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        enabled: control.enabled && !control.loading && !control._countdownActive && feature !== Enums.button.feature_split
        visible: feature !== Enums.button.feature_split

        onClicked: {
            if (feature === Enums.button.feature_toggle) {
                control.checked = !control.checked
                control.toggled(control.checked)
            }
            if (feature === Enums.button.feature_dropdown && control.menuItems.length > 0) {
                if (dropdownFeature.item) dropdownFeature.item.openMenu()
                return
            }
            if (feature === Enums.button.feature_countdown) {
                control._countdownInitialWidth = control.width
                control._countdownRemaining = control.countdown
                control._countdownActive = true
            }
            control.clicked()
        }
        onPressed: {
            // 让按钮获得焦点, 这样外部 LineEdit 等输入控件被点击其它 UI 时自动失焦
            control.forceActiveFocus()
            control.buttonPressed()
        }
        onReleased: control.released()
        onDoubleClicked: control.doubleClicked()
    }

    // Dropdown feature 下拉模块
    Loader {
        id: dropdownFeature
        anchors.fill: parent
        active: feature === Enums.button.feature_split ||
                feature === Enums.button.feature_dropdown
        onLoaded: {
            if (control.activeFocus ||
                    (feature === Enums.button.feature_dropdown && hoverHandler.hovered)) {
                control._prewarmMenu()
            }
        }
        sourceComponent: ButtonDropdown {
            isToolButton: control.isToolButton
            feature: control.feature
            menuItems: control.menuItems
            controlEnabled: control.enabled
            loading: control.loading
            parentRadius: control.radius
            fontSize: control.fontSize
            parentStyle: control.style
            textColor: styleHelper.textColor
            onMenuItemClicked: (index, text) => control.menuItemClicked(index, text)
            onMainButtonClicked: control.clicked()
            onMenuAboutToOpen: control._dismissToolTipForMenu()
        }
    }

    // Toggle animation 切换动画
    Loader {
        id: toggleAnimLoader
        active: feature === Enums.button.feature_toggle

        sourceComponent: ToggleAnimation {
            target: _bg
            running: control.checked
        }
    }

    // Countdown timer 倒计时定时器
    Loader {
        id: countdownTimer
        active: feature === Enums.button.feature_countdown ||
                control._countdownActive

        sourceComponent: Timer {
            interval: Enums.duration.countUp
            repeat: true
            running: control._countdownActive
            onTriggered: {
                control._countdownRemaining--
                if (control._countdownRemaining <= 0) {
                    control._countdownActive = false
                    control.countdownFinished()
                }
            }
        }
    }
}
