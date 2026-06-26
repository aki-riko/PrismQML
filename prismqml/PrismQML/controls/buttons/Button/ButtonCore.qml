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

    // ==================== Auto Type Detection 自动类型识别 ====================
    // icon only → ToolButton style, icon+text or text only → PushButton style 仅图标 → 工具按钮样式，图标+文本或仅文本 → 普通按钮样式

    readonly property bool isToolButton: icon !== "" && text === ""

    // ==================== Style Props 样式属性 ====================
    property int style: Enums.button.style_default
    property int shape: Enums.button.shape_default
    property int feature: Enums.button.feature_none
    property int contentAlignment: Enums.button.align_center  // Content alignment 内容对齐

    // ==================== Content Props 内容属性 ====================
    property string text: ""
    property string icon: ""           // Icon name / image path 图标名或图片路径
    property int iconSize: Enums.iconSize.m
    default property alias contentData: customContentContainer.data  // Custom content 自定义内容
    property bool hasCustomContent: customContentContainer.children.length > 0

    // ==================== Feature Props 功能属性 ====================
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

    // ==================== Base Props 基础属性 ====================
    property bool flat: style === Enums.button.style_transparent ||
                        style === Enums.button.style_text ||
                        style === Enums.button.style_hyperlink

    // ==================== Text Style 文本样式 ====================
    readonly property string fontFamily: Enums.fontFamily
    readonly property int fontSize: Enums.typography.body
    // Optional font flags 可选字体修饰 (e.g. 富文本工具栏 B/I/U/S 按钮)
    property bool fontBold: false
    property bool fontItalic: false
    property bool fontUnderline: false
    property bool fontStrikeout: false

    // ==================== State 状态 ====================
    property bool pseudoHovered: false
    property bool pseudoPressed: false
    property bool hovered: feature === Enums.button.feature_split ? false : (hoverHandler.hovered || pseudoHovered)
    property bool pressed: feature === Enums.button.feature_split ? false : ((mouseArea && mouseArea.pressed) || pseudoPressed)

    // ==================== Style Helper 样式助手 ====================
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

    // ==================== Appearance Props 外观属性 ====================
    property int radius: shape === Enums.button.shape_pill ? height / 2
                         : (Enums.isNeobrutalism ? Enums.neo.radius : Enums.radius.small)
    property color color: styleHelper.bgColor

    // Neobrutalism 按下位移量: 按下时控件向右下偏移, 视觉上"压平"硬阴影。Fluent 皮肤恒为 0。
    readonly property real _neoPressShift: (Enums.isNeobrutalism && pressed && !flat) ? Enums.neo.pressOffset : 0

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

    // ==================== Layout Override 布局覆盖 ====================
    // 按钮默认不应填充父布局宽度（覆盖Widget基类的layoutFillWidth: true）
    layoutFillWidth: false

    // ==================== Size 尺寸 ====================
    // Content size calculation (inherited from Widget) 内容尺寸计算（继承自Widget）
    contentWidth: {
        if (_countdownActive && _countdownInitialWidth > 0) return _countdownInitialWidth
        if (isToolButton) return Enums.controlSize.buttonHeight
        // Transparent/text/hyperlink styles have no minimum width 透明/文本/超链接样式无最小宽度
        var cw = contentLoader.item ? contentLoader.item.width + Enums.spacing.xl : 0
        var extraWidth = feature === Enums.button.feature_split ? Enums.controlSize.splitButtonArrowWidth :
                        (feature === Enums.button.feature_dropdown ? Enums.controlSize.dropdownArrowWidth : 0)
        if (flat) return Math.max(cw + extraWidth, Enums.controlSize.buttonHeight)
        return Math.max(Enums.controlSize.buttonMinWidth, cw + extraWidth)
    }
    contentHeight: Enums.controlSize.buttonHeight

    // border alias references child _bg, kept in body per ordering rule
    property alias border: _bg.border

    HoverHandler {
        id: hoverHandler
        enabled: control.enabled && !control.loading && !control._countdownActive && feature !== Enums.button.feature_split
    }

    // ToolTip timer for Button - override Widget's _hoverArea
    // Button专用ToolTip定时器 - 覆盖Widget的_hoverArea
    Timer {
        id: _btnToolTipTimer
        interval: toolTipShowDelay
        onTriggered: if (control.hovered) control.showToolTip()
    }

    // ==================== Shadow 阴影 ====================
    // Fluent: 模糊阴影(RectangularShadow)。Neobrutalism: 硬阴影(偏移纯色矩形, 无模糊)。
    RectangularShadow {
        anchors.fill: _bg
        radius: _bg.radius
        color: Enums.shadow.level2.color
        blur: Enums.shadow.level2.blur
        offset.x: 0
        offset.y: Enums.shadow.level2.offset
        visible: !control.flat && !Enums.isNeobrutalism
    }

    // Neobrutalism 硬阴影: 复用 NeoShadow 组件(纯黑零模糊, 偏移)。按下位移由下方 Translate 压平。
    NeoShadow {
        target: _bg
        visible: Enums.isNeobrutalism && !control.flat
        z: _bg.z - 1
    }

    // ==================== Background 背景 ====================
    Rectangle {
        id: _bg
        anchors.fill: parent
        radius: control.radius
        color: _animatedBgColor
        border.width: Enums.isNeobrutalism
            ? (flat ? 0 : Enums.neo.borderWidth)
            : ((styleHelper.isToggleChecked && style === Enums.button.style_primary) ? Enums.border.normal : (flat ? 0 : Enums.border.thin))
        border.color: _animatedBorderColor  // neo 黑边由 styleHelper.borderColor 经 token 返回

        // Gradient (for gradient style) 渐变
        gradient: style === Enums.button.style_gradient ? _gradientDef : null

        // Neobrutalism 按下位移: face 向右下滑向硬阴影, 视觉压平。Fluent 下 shift 恒 0 无影响。
        transform: Translate {
            x: control._neoPressShift; y: control._neoPressShift
            Behavior on x { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
            Behavior on y { NumberAnimation { duration: Enums.duration.fast; easing.type: Easing.OutCubic } }
        }
    }

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

    // Watch for target color changes (from styleHelper) 监听目标颜色变化
    Connections {
        target: styleHelper
        function onBgColorChanged() { control._updateTargetColors() }
        function onBorderColorChanged() { control._updateTargetColors() }
    }

    // Direct hover state monitoring for reliable updates 直接监听hover确保可靠更新
    onHoveredChanged: {
        _updateTargetColors()
        // ToolTip trigger 触发ToolTip
        if (toolTipText !== "") {
            if (hovered) _btnToolTipTimer.start()
            else { _btnToolTipTimer.stop(); hideToolTip() }
        }
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

    // ==================== Content (modular) 内容模块 ====================
    // Custom content container 自定义内容容器
    Item {
        id: customContentContainer
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: contentAlignment === Enums.button.align_left ? parent.left : undefined
        anchors.right: contentAlignment === Enums.button.align_right ? parent.right : undefined
        anchors.horizontalCenter: contentAlignment === Enums.button.align_center ? parent.horizontalCenter : undefined
        anchors.leftMargin: contentAlignment === Enums.button.align_left ? Enums.spacing.m : 0
        anchors.rightMargin: contentAlignment === Enums.button.align_right ? Enums.spacing.m : 0
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
        anchors.leftMargin: contentAlignment === Enums.button.align_left ? Enums.spacing.m : 0
        anchors.rightMargin: contentAlignment === Enums.button.align_right ? Enums.spacing.m : 0
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
            fontFamily: control.fontFamily
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

    // ==================== Dropdown Arrow 下拉箭头 ====================
    Loader {
        anchors.right: parent.right
        anchors.rightMargin: Enums.spacing.m
        anchors.verticalCenter: parent.verticalCenter
        active: feature === Enums.button.feature_dropdown

        readonly property bool _useAccentForeground: control.style === Enums.button.style_primary ||
                                                      control.style === Enums.button.style_filled ||
                                                      control.style === Enums.button.style_gradient

        sourceComponent: ChevronIcon {
            animated: true
            isOpen: control.dropdownOpen || (dropdownFeature.item ? dropdownFeature.item.isMenuOpen : false)
            color: !control.enabled ? Enums.stateColor.indicatorActive :
                   (parent._useAccentForeground ? Enums.accentForeground : Enums.textColor.secondary)
        }
    }

    // ==================== Progress Feature 进度条模块 ====================
    Item {
        id: progressClipRect
        anchors.fill: parent
        visible: feature === Enums.button.feature_progress_bar ||
                 feature === Enums.button.feature_indeterminate_bar

        Rectangle {
            id: progressMask
            anchors.fill: parent
            radius: control.radius
            color: "white"
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
                active: progressClipRect.visible
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

    // ==================== Main Interaction 主交互 ====================
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

    // ==================== Dropdown Feature 下拉模块 ====================
    Loader {
        id: dropdownFeature
        anchors.fill: parent
        active: feature === Enums.button.feature_split ||
                feature === Enums.button.feature_dropdown
        sourceComponent: ButtonDropdown {
            isToolButton: control.isToolButton
            feature: control.feature
            menuItems: control.menuItems
            controlEnabled: control.enabled
            loading: control.loading
            parentRadius: control.radius
            fontFamily: control.fontFamily
            fontSize: control.fontSize
            parentStyle: control.style
            textColor: styleHelper.textColor
            onMenuItemClicked: (index, text) => control.menuItemClicked(index, text)
            onMainButtonClicked: control.clicked()
        }
    }

    // ==================== Toggle Animation 切换动画 ====================
    ToggleAnimation {
        id: toggleAnim
        target: _bg
        running: control.checked
    }

    // ==================== Countdown Timer 倒计时定时器 ====================
    Timer {
        id: countdownTimer
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
