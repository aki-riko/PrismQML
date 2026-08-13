// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

pragma Singleton
import QtQuick
import "PrismEnums"

// Enums - Global unified enum entry point 全局统一枚举入口
// Usage 使用方式: Enums.radius.large, Enums.button.type_primary
// 
// Architecture 架构: Modular design, each category in separate file 模块化设计
// Files 文件: Theme.qml, StatusLevel.qml, Button.qml, StateColor.qml, Constants.qml, Metrics.qml, Icons.qml
// TODO: 45 个子组件在启动时同步创建，可能影响首帧渲染时间。
//       如需优化，可对低频使用的枚举组件改用 Loader 按需加载。

Item {
    id: root
    visible: false
    readonly property real _startupProfileStart: Date.now()
    readonly property bool _startupProfilingVerboseActive:
        (typeof PrismQmlStartupProfileVerbose !== "undefined" && PrismQmlStartupProfileVerbose)

    function _profileStartup(msg) {
        if (!_startupProfilingVerboseActive) return
        console.debug("[启动剖析] Enums " + msg + ": total " +
                    Math.round(Date.now() - _startupProfileStart) + "ms")
    }

    Component.onCompleted: _profileStartup("singleton completed")
    
    // ==================== Translation Shortcuts 快捷翻译方法 ====================
    function tr(key) { return Translator.tr(key) }
    function trCount(key, count) { return Translator.tr(key).replace("{count}", count) }
    function setTheme(value) {
        if (typeof ConfigManager !== "undefined" && ConfigManager)
            ConfigManager.setTheme(value)
        else if (ThemeManager)
            ThemeManager.setThemeFromQml(value)
    }
    function setSkin(value) {
        if (typeof ConfigManager !== "undefined" && ConfigManager)
            ConfigManager.setSkin(value)
        else if (ThemeManager)
            ThemeManager.setSkinFromQml(value)
    }
    function setAccentColor(value) {
        if (typeof ConfigManager !== "undefined" && ConfigManager)
            ConfigManager.setAccentColor(value.toString())
        else if (ThemeManager)
            ThemeManager.setAccentColor(value.toString())
    }
    function surfaceRadius(fluentRadius) {
        if (isVintageTicket) return ticket.radius
        if (isNeobrutalism) return neo.radius
        if (isNeumorphism) return neumorphism.radius
        return fluentRadius
    }
    function surfaceBorderWidth(fluentWidth) {
        if (isVintageTicket) return ticket.borderWidth
        if (isNeobrutalism) return neo.borderWidth
        if (isNeumorphism) return neumorphism.borderWidth
        return fluentWidth
    }
    
    // ==================== Global Theme Props 全局主题属性 ====================
    readonly property string theme: ThemeManager ? ThemeManager.theme : "auto"
    readonly property bool isDark: ThemeManager ? ThemeManager.isDark : false
    // Skin (design language) 皮肤（设计语言）: "fluent" | "neobrutalism" | "vintage_ticket" | "neumorphism"
    // 与 isDark 正交: isDark 控明暗, skin 控设计语言。控件按 skin 切换几何/阴影范式。
    readonly property string skin: ThemeManager ? ThemeManager.skin : "fluent"
    readonly property bool isNeobrutalism: skin === "neobrutalism"
    readonly property bool isVintageTicket: skin === "vintage_ticket"
    readonly property bool isNeumorphism: skin === "neumorphism"
    readonly property bool hasOutlinedSurfaces: isNeobrutalism || isVintageTicket
    readonly property bool usesSoftElevation: !hasOutlinedSurfaces && !isNeumorphism
    readonly property bool usesNeumorphicElevation: isNeumorphism
    readonly property bool allowsMica: !hasOutlinedSurfaces && !isNeumorphism
    readonly property string _uiFontFamily: ThemeManager ? ThemeManager.fontFamily : "Microsoft YaHei UI, Segoe UI Variable, Segoe UI, -apple-system, PingFang SC, Roboto, Noto Sans CJK SC, sans-serif"
    readonly property string fontFamily: isVintageTicket ? fontMonospace : _uiFontFamily
    readonly property string fontMonospace: ThemeManager ? ThemeManager.fontMonospace : "Cascadia Code, Consolas, SF Mono, Menlo, Roboto Mono, monospace"
    readonly property string canvasFontFamily: "'" + fontFamily.split(",")[0].trim() + "', sans-serif"
    // Skin accent resolver 皮肤主色解析器:
    // Existing accent consumers auto-switch colors under skins 现有主色消费者在皮肤下自动换色。
    readonly property color _rawAccentColor: ThemeManager ? ThemeManager.accentColor : _constants.accentDefaults.accent
    readonly property color accentColor: isNeobrutalism ? _constants.neoColors.primary
        : (isVintageTicket ? _constants.ticketColors.primary
        : (isNeumorphism ? _constants.neumorphismColors.primary : _rawAccentColor))
    readonly property color accentColorLight: isNeobrutalism ? Qt.lighter(_constants.neoColors.primary, 1.08)
        : (isVintageTicket ? Qt.lighter(_constants.ticketColors.primary, 1.12)
        : (isNeumorphism ? Qt.lighter(_constants.neumorphismColors.primary, 1.08)
        : (ThemeManager ? ThemeManager.accentColorLight : _constants.accentDefaults.accentLight)
        ))
    readonly property color accentColorDark: isNeobrutalism ? Qt.darker(_constants.neoColors.primary, 1.15)
        : (isVintageTicket ? Qt.darker(_constants.ticketColors.primary, 1.18)
        : (isNeumorphism ? Qt.darker(_constants.neumorphismColors.primary, 1.12)
        : (ThemeManager ? ThemeManager.accentColorDark : _constants.accentDefaults.accentDark)
        ))
    
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
    
    // ==================== Modular Components 模块化组件 ====================
    Theme { id: _theme; isDark: root.isDark; isNeo: root.isNeobrutalism; isTicket: root.isVintageTicket; isNeumorphism: root.isNeumorphism; accentColor: root.accentColor; accentColorLight: root.accentColorLight; accentColorDark: root.accentColorDark; constants: _constants }
    StatusLevel { id: _statusLevel; isDark: root.isDark; isNeo: root.isNeobrutalism; isTicket: root.isVintageTicket; isNeumorphism: root.isNeumorphism; accentColor: root.accentColor; constants: _constants }
    Button { id: _button; isTicket: root.isVintageTicket }
    Tab { id: _tab }
    CommandBar { id: _commandBar }
    StateColor { id: _stateColor; isDark: root.isDark; isNeo: root.isNeobrutalism; isTicket: root.isVintageTicket; isNeumorphism: root.isNeumorphism; accentColor: root.accentColor; constants: _constants }
    Constants { id: _constants; isDark: root.isDark; isNeo: root.isNeobrutalism; isTicket: root.isVintageTicket; isNeumorphism: root.isNeumorphism }
    Metrics {
        id: _metrics
        isDark: root.isDark
        isTicket: root.isVintageTicket
        isNeumorphism: root.isNeumorphism
        devicePixelRatio: DpiManager.devicePixelRatio
        constants: _constants
    }
    Orient { id: _orient }
    Flow { id: _flow }
    Chart { id: _chart }
    Card { id: _card }
    Drawer { id: _drawer }
    Position { id: _position }
    Notification { id: _notification }
    Slider { id: _slider }
    Animation { id: _animation }
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
    // Icon Enums Icon枚举
    // QML usage: Enums.icon.chevron_up (snake_case) QML侧使用: Enums.icon.chevron_up (小写下划线)
    // Python usage: Icon.CHEVRON_UP (UPPER_SNAKE_CASE) Python侧使用: Icon.CHEVRON_UP (大写下划线)
    // Both registries are generated from the same SVG assets 两侧注册表由同一 SVG 资源生成
    readonly property var icons: Icons.resolver
    readonly property var icon: Icons.resolver  // Alias 别名
    
    // Forward theme colors 转发主题色
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
    // Forward constants 转发常量（仅保留颜色/配置常量）
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
    
    // Forward metrics 转发度量
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
    readonly property alias windowCloseMetrics: _metrics.windowClose
    readonly property alias lazyLoadingTransitionMetrics: _metrics.lazyLoadingTransition
    readonly property alias progressRingMetrics: _metrics.progressRing
    readonly property alias colorPickerMetrics: _metrics.colorPicker
    readonly property alias typography: _metrics.typography
    readonly property alias shadow: _metrics.shadow
    readonly property alias listIndicator: _metrics.listIndicator
    
    // Global icon path (resolved once, used everywhere) 全局图标路径
    readonly property string iconPath: Qt.resolvedUrl("controls/icons/fluent/")
    
}
