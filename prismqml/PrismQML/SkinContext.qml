// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "PrismEnums"

// SkinContext - One observable token set for a single design language 单套设计语言的可观察 token 集合
//
// This is the shared token assembly behind both the global theme and local
// skin scopes. Global `Enums` owns one instance driven by ThemeManager;
// `SkinScope` owns one instance per scope driven by its own `skin` name.
// Both consume the same Theme / StateColor / Metrics modules, so a local scope
// can never drift from the global palette logic.
// 这是全局主题与局部皮肤范围共用的 token 装配体。全局 `Enums` 持有一份由
// ThemeManager 驱动的实例；`SkinScope` 每个范围持有一份由自身 `skin` 驱动的实例。
// 两者复用同一批 Theme / StateColor / Metrics 模块，局部范围不会复制第二套配色逻辑。
//
// It is an invisible Item (not a QtObject) so the token modules can be declared
// as children with ids and forwarded through single-level aliases. QtObject has
// no default property and therefore cannot host child declarations.
// 这里使用不可见 Item 而非 QtObject：token 模块需要作为带 id 的子对象声明，
// 并通过单层 alias 转发；QtObject 没有默认属性，无法承载子对象声明。
//
// Not a public type. Business code uses `SkinScope`; tests may import this file
// by path. 非公开类型。业务侧使用 `SkinScope`；测试可按路径导入本文件。
Item {
    id: root
    visible: false
    enabled: false

    // ==================== Inputs 输入 ====================
    // Light/dark axis stays global; a scope only overrides the design language.
    // 明暗轴保持全局；局部范围只覆盖设计语言。
    property bool isDark: false
    // Design language 设计语言: "fluent" | "neobrutalism" | "vintage_ticket" | "neumorphism"
    property string skin: "fluent"
    // Base UI font before the skin override 皮肤覆盖前的界面字体
    property string uiFontFamily: "Microsoft YaHei UI, Segoe UI Variable, Segoe UI, -apple-system, PingFang SC, Roboto, Noto Sans CJK SC, sans-serif"
    property string fontMonospace: "Cascadia Code, Consolas, SF Mono, Menlo, Roboto Mono, monospace"
    // Raw accent before the skin palette override 皮肤调色板覆盖前的原始主色。
    // Defaults come from Constants so a context without a ThemeManager still
    // resolves a complete palette. 默认值取自 Constants，没有 ThemeManager 的
    // 上下文也能解析出完整调色板。
    property color rawAccentColor: rawAccentColorDefault
    property color rawAccentColorLight: rawAccentColorLightDefault
    property color rawAccentColorDark: rawAccentColorDarkDefault
    property real devicePixelRatio: 1

    // Fallbacks for hosts without a ThemeManager; an alias cannot walk the
    // two-level Constants path, so these bind instead.
    // 没有 ThemeManager 的宿主使用的回退值；alias 无法穿透 Constants 的两层路径，故用绑定。
    readonly property color rawAccentColorDefault: _constants.accentDefaults.accent
    readonly property color rawAccentColorLightDefault: _constants.accentDefaults.accentLight
    readonly property color rawAccentColorDarkDefault: _constants.accentDefaults.accentDark

    // ==================== Derived Skin Flags 派生皮肤标志 ====================
    readonly property bool isNeobrutalism: skin === "neobrutalism"
    readonly property bool isVintageTicket: skin === "vintage_ticket"
    readonly property bool isNeumorphism: skin === "neumorphism"
    readonly property bool hasOutlinedSurfaces: isNeobrutalism || isVintageTicket
    readonly property bool usesSoftElevation: !hasOutlinedSurfaces && !isNeumorphism
    readonly property bool usesNeumorphicElevation: isNeumorphism
    readonly property bool allowsMica: !hasOutlinedSurfaces && !isNeumorphism

    // ==================== Derived Fonts 派生字体 ====================
    readonly property string fontFamily: isVintageTicket ? fontMonospace : uiFontFamily
    readonly property string canvasFontFamily: "'" + fontFamily.split(",")[0].trim() + "', sans-serif"

    // ==================== Derived Accent 派生主色 ====================
    // Existing accent consumers auto-switch colors under skins 现有主色消费者在皮肤下自动换色。
    readonly property color accentColor: isNeobrutalism ? _constants.neoColors.primary
        : (isVintageTicket ? _constants.ticketColors.primary
        : (isNeumorphism ? _constants.neumorphismColors.primary : root.rawAccentColor))
    readonly property color accentColorLight: isNeobrutalism ? Qt.lighter(_constants.neoColors.primary, 1.08)
        : (isVintageTicket ? Qt.lighter(_constants.ticketColors.primary, 1.12)
        : (isNeumorphism ? Qt.lighter(_constants.neumorphismColors.primary, 1.08)
        : root.rawAccentColorLight))
    readonly property color accentColorDark: isNeobrutalism ? Qt.darker(_constants.neoColors.primary, 1.15)
        : (isVintageTicket ? Qt.darker(_constants.ticketColors.primary, 1.18)
        : (isNeumorphism ? Qt.darker(_constants.neumorphismColors.primary, 1.12)
        : root.rawAccentColorDark))

    // Transparent color constant 透明色常量
    readonly property color transparent: "transparent"

    // Shared button gradient resource; all gradient buttons use the same
    // theme-bound stops. 共享按钮渐变资源；所有渐变按钮复用同一组主题绑定色标。
    readonly property Gradient _buttonGradientDef: Gradient {
        GradientStop {
            position: _button.gradientStart
            color: Qt.lighter(root.accentColor, _button.gradientLighten)
        }
        GradientStop {
            position: _button.gradientEnd
            color: root.accentColor
        }
    }

    // ==================== Timeline 时间线 ====================
    readonly property QtObject timeline: QtObject {
        readonly property int type_standard: 0
        readonly property int type_graph: 1
    }

    // ==================== Module Aliases 模块别名 ====================
    readonly property alias statusLevel: _statusLevel
    readonly property alias button: _button
    readonly property alias tab: _tab
    readonly property alias commandBar: _commandBar
    readonly property alias stateColor: _stateColor
    readonly property alias orient: _orient
    readonly property alias flow: _flow
    readonly property alias chart: _chart
    readonly property alias card: _card
    readonly property alias drawer: _drawer
    readonly property alias position: _position
    readonly property alias notification: _notification
    readonly property alias slider: _slider
    readonly property alias animation: _animation
    readonly property alias lazyAnimation: _lazyAnimation
    readonly property alias input: _input
    readonly property alias scroll: _scroll
    readonly property alias comboBox: _comboBox
    readonly property alias toggle: _toggle
    readonly property alias imageCropper: _imageCropper
    readonly property alias badge: _badge
    readonly property alias gradientSlider: _gradientSlider
    readonly property alias colorPicker: _colorPicker
    readonly property alias windowShadow: _windowShadow
    readonly property alias windowType: _windowType
    readonly property alias backdrop: _backdrop
    readonly property alias picker: _picker
    readonly property alias calendarPicker: _calendarPicker
    readonly property alias pipsPager: _pipsPager
    readonly property alias state: _state
    readonly property alias progress: _progress
    readonly property alias skeleton: _skeleton
    readonly property alias dialog: _dialog
    readonly property alias flyout: _flyout
    readonly property alias teachingTip: _teachingTip
    readonly property alias tip: _tip
    readonly property alias lang: _lang
    readonly property alias separator: _separator
    readonly property alias label: _label
    readonly property alias carousel: _carousel
    readonly property alias settingCard: _settingCard
    readonly property alias auth: _auth
    readonly property alias indicatorBar: _indicatorBar

    // Icon registries are global resources; scopes reuse them instead of
    // cloning the icon table. 图标注册表是全局资源；局部范围复用而不复制图标表。
    readonly property var icons: Icons.resolver
    readonly property var icon: Icons.resolver  // Alias 别名

    // ==================== Forward Theme Colors 转发主题色 ====================
    readonly property alias backgroundColor: _theme.backgroundColor
    readonly property alias surfaceColor: _theme.surfaceColor
    readonly property alias cardColor: _theme.cardColor
    readonly property alias toastCardColor: _theme.toastCardColor
    readonly property alias dialogColor: _theme.dialogColor
    readonly property alias headerColor: _theme.headerColor
    readonly property alias tableHoverColor: _theme.tableHoverColor
    readonly property alias alternateRowColor: _theme.alternateRowColor
    readonly property alias scrollTrackColor: _theme.scrollTrackColor
    readonly property alias scrollHandleColor: _theme.scrollHandleColor
    readonly property alias scrollHandleHoverColor: _theme.scrollHandleHoverColor
    readonly property alias tableBgColor: _theme.tableBgColor
    readonly property alias foregroundColor: _theme.foregroundColor
    readonly property alias secondaryForeground: _theme.secondaryForeground
    readonly property alias tertiaryForeground: _theme.tertiaryForeground
    readonly property alias disabledForeground: _theme.disabledForeground
    readonly property alias accentForeground: _theme.accentForeground
    readonly property alias borderColor: _theme.borderColor
    readonly property alias borderLightColor: _theme.borderLightColor
    readonly property alias borderStrongColor: _theme.borderStrongColor
    readonly property alias dividerColor: _theme.dividerColor
    readonly property alias hoverColor: _theme.hoverColor
    readonly property alias pressedColor: _theme.pressedColor
    readonly property alias disabledColor: _theme.disabledColor
    readonly property alias selectedColor: _theme.selectedColor
    readonly property alias starColor: _theme.starColor
    readonly property alias infoAccentColor: _theme.infoAccentColor
    readonly property alias shadowColor: _theme.shadowColor
    readonly property alias shadowStrongColor: _theme.shadowStrongColor

    // ==================== Forward Constants 转发常量 ====================
    readonly property alias accentDefaults: _constants.accentDefaults
    readonly property alias windowButtonColors: _constants.windowButtonColors
    readonly property alias dialogColors: _constants.dialogColors
    readonly property alias colorPalette: _constants.colorPalette
    readonly property alias colorPickerGradient: _constants.colorPickerGradient
    readonly property alias gray: _constants.gray
    readonly property alias grayColors: _constants.grayColors
    readonly property alias demoPalette: _constants.demoPalette
    readonly property alias themeColors: _constants.themeColors
    readonly property alias textColor: _constants.textColor
    readonly property alias codeBlockColors: _constants.codeBlockColors
    readonly property alias chartColors: _constants.chartColors
    readonly property alias confettiColors: _constants.confettiColors
    readonly property alias colorPickerDefaults: _constants.colorPickerDefaults
    readonly property alias passwordStrengthColors: _constants.passwordStrengthColors
    readonly property alias calendarColors: _constants.calendarColors
    readonly property alias exampleCardColors: _constants.exampleCardColors
    readonly property alias examplePageColors: _constants.examplePageColors
    readonly property alias chipColors: _constants.chipColors
    readonly property alias tableCellColors: _constants.tableCellColors

    // ==================== Forward Metrics 转发度量 ====================
    readonly property alias duration: _metrics.duration
    readonly property alias motion: _metrics.motion
    readonly property alias demoMetrics: _metrics.demoMetrics
    readonly property alias zIndex: _metrics.zIndex
    readonly property alias opacityLevel: _metrics.opacity
    readonly property alias mask: _metrics.mask
    readonly property alias border: _metrics.border
    readonly property alias neo: _metrics.neo
    readonly property alias ticket: _metrics.ticket
    readonly property alias neumorphism: _metrics.neumorphism
    readonly property alias iconSize: _metrics.iconSize
    readonly property alias spacing: _metrics.spacing
    readonly property alias radius: _metrics.radius
    readonly property alias controlSize: _metrics.controlSize
    readonly property alias window: _metrics.window
    readonly property alias popupMetrics: _metrics.popup
    readonly property alias infoBarMetrics: _metrics.infoBar
    readonly property alias comboBoxMetrics: _metrics.comboBox
    readonly property alias searchMetrics: _metrics.search
    readonly property alias skeletonMetrics: _metrics.skeletonMetrics
    readonly property alias imageCropperDialogMetrics: _metrics.imageCropperDialog
    readonly property alias splashScreenMetrics: _metrics.splashScreen
    readonly property alias lazyLoadingTransitionMetrics: _metrics.lazyLoadingTransition
    readonly property alias progressRingMetrics: _metrics.progressRing
    readonly property alias colorPickerMetrics: _metrics.colorPicker
    readonly property alias typography: _metrics.typography
    readonly property alias shadow: _metrics.shadow
    readonly property alias listIndicator: _metrics.listIndicator
    readonly property alias navigationFade: _metrics.navigationFade
    readonly property alias navigationRail: _metrics.navigationRail

    // ==================== Geometry Resolvers 几何解析 ====================
    // Resolve the effective corner radius for the active design language.
    // 解析当前设计语言下的有效圆角。
    function surfaceRadius(fluentRadius) {
        if (isVintageTicket) return ticket.radius
        if (isNeobrutalism) return neo.radius
        if (isNeumorphism) return neumorphism.radius
        return fluentRadius
    }

    // Resolve the effective border width for the active design language.
    // 解析当前设计语言下的有效边框宽度。
    function surfaceBorderWidth(fluentWidth) {
        if (isVintageTicket) return ticket.borderWidth
        if (isNeobrutalism) return neo.borderWidth
        if (isNeumorphism) return neumorphism.borderWidth
        return fluentWidth
    }

    // Resolve translucent strokes against their target surface before different
    // render layers draw them.
    // 在不同渲染层绘制前，先将半透明描边与目标表面合成，避免最终像素颜色不一致。
    function surfaceBorderColor(borderColor, surfaceColor) {
        var borderAlpha = borderColor.a
        if (borderAlpha <= 0 || borderAlpha >= 1) return borderColor
        var surfaceContribution = surfaceColor.a * (1 - borderAlpha)
        var outputAlpha = borderAlpha + surfaceContribution
        if (outputAlpha <= 0) return transparent
        return Qt.rgba(
            (borderColor.r * borderAlpha + surfaceColor.r * surfaceContribution) / outputAlpha,
            (borderColor.g * borderAlpha + surfaceColor.g * surfaceContribution) / outputAlpha,
            (borderColor.b * borderAlpha + surfaceColor.b * surfaceContribution) / outputAlpha,
            outputAlpha
        )
    }

    // Build the same color at an explicit alpha, keeping the source RGB untouched.
    // 生成指定 alpha 的同色变体，保留源 RGB，避免透明黑参与颜色插值产生脏灰帧。
    function withAlpha(base, alpha) {
        return Qt.rgba(base.r, base.g, base.b, alpha)
    }

    // ==================== Skin-Dependent Token Modules 随皮肤变化的 token 模块 ====================
    Constants {
        id: _constants
        isDark: root.isDark
        isNeo: root.isNeobrutalism
        isTicket: root.isVintageTicket
        isNeumorphism: root.isNeumorphism
    }
    Theme {
        id: _theme
        isDark: root.isDark
        isNeo: root.isNeobrutalism
        isTicket: root.isVintageTicket
        isNeumorphism: root.isNeumorphism
        accentColor: root.accentColor
        accentColorLight: root.accentColorLight
        accentColorDark: root.accentColorDark
        constants: _constants
    }
    StatusLevel {
        id: _statusLevel
        isDark: root.isDark
        isNeo: root.isNeobrutalism
        isTicket: root.isVintageTicket
        isNeumorphism: root.isNeumorphism
        accentColor: root.accentColor
        constants: _constants
    }
    Button { id: _button; isTicket: root.isVintageTicket }
    StateColor {
        id: _stateColor
        isDark: root.isDark
        isNeo: root.isNeobrutalism
        isTicket: root.isVintageTicket
        isNeumorphism: root.isNeumorphism
        accentColor: root.accentColor
        constants: _constants
    }
    Metrics {
        id: _metrics
        isDark: root.isDark
        isTicket: root.isVintageTicket
        isNeumorphism: root.isNeumorphism
        devicePixelRatio: root.devicePixelRatio
        constants: _constants
    }

    // ==================== Skin-Independent Token Modules 与皮肤无关的 token 模块 ====================
    // These carry enum values and fixed geometry only. They are still declared
    // per context so a context stays a complete drop-in replacement for Enums;
    // the objects are trivial constant holders.
    // 这些模块只承载枚举值与固定几何。仍然按上下文各声明一份，使上下文始终是
    // Enums 的完整替身；这些对象本身只是极轻量的常量容器。
    Tab { id: _tab }
    CommandBar { id: _commandBar }
    Orient { id: _orient }
    Flow { id: _flow }
    Chart { id: _chart }
    Card { id: _card }
    Drawer { id: _drawer }
    Position { id: _position }
    Notification { id: _notification }
    Slider { id: _slider }
    Animation { id: _animation }
    LazyAnimation { id: _lazyAnimation }
    Input { id: _input }
    Scroll { id: _scroll }
    ComboBox { id: _comboBox }
    Toggle { id: _toggle }
    ImageCropper { id: _imageCropper }
    Badge { id: _badge }
    GradientSlider { id: _gradientSlider }
    ColorPicker { id: _colorPicker }
    WindowShadow { id: _windowShadow }
    WindowType { id: _windowType }
    Backdrop { id: _backdrop }
    Picker { id: _picker }
    CalendarPicker { id: _calendarPicker }
    PipsPager { id: _pipsPager }
    State { id: _state }
    Progress { id: _progress }
    Skeleton { id: _skeleton }
    Dialog { id: _dialog }
    Flyout { id: _flyout }
    TeachingTip { id: _teachingTip }
    Tip { id: _tip }
    Lang { id: _lang }
    Separator { id: _separator }
    Label { id: _label }
    Carousel { id: _carousel }
    SettingsCard { id: _settingCard }
    Auth { id: _auth }
    IndicatorBar { id: _indicatorBar }
}
