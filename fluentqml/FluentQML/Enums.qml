// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

pragma Singleton
import QtQuick
import "FluentEnums"

// Enums - Global unified enum entry point 全局统一枚举入口
// Usage 使用方式: Enums.radius.large, Enums.button.type_primary
// 
// Architecture 架构: Modular design, each category in separate file 模块化设计
// Files 文件: Theme.qml, StatusLevel.qml, Button.qml, StateColor.qml, Constants.qml, Metrics.qml, Icons.qml
// TODO: 44 个子组件在启动时同步创建，可能影响首帧渲染时间。
//       如需优化，可对低频使用的枚举组件改用 Loader 按需加载。

Item {
    id: root
    visible: false
    
    // ==================== Translation Shortcuts 快捷翻译方法 ====================
    function tr(key) { return Translator.tr(key) }
    function trCount(key, count) { return Translator.tr(key).replace("{count}", count) }
    
    // ==================== Global Theme Props 全局主题属性 ====================
    readonly property bool isDark: ThemeManager ? ThemeManager.isDark : false
    // Skin (design language) 皮肤（设计语言）: "fluent" | "neobrutalism"
    // 与 isDark 正交: isDark 控明暗, skin 控设计语言。控件按 skin 切换几何/阴影范式。
    readonly property string skin: ThemeManager ? ThemeManager.skin : "fluent"
    readonly property bool isNeobrutalism: skin === "neobrutalism"
    readonly property string fontFamily: ThemeManager ? ThemeManager.fontFamily : "Segoe UI Variable, Segoe UI, -apple-system, PingFang SC, Roboto, Noto Sans CJK SC, Microsoft YaHei UI, sans-serif"
    readonly property string canvasFontFamily: "'" + fontFamily.split(",")[0].trim() + "', sans-serif"
    // accentColor 在 neo 皮肤下解析成 neo 主色(橙) —— 这是换皮杠杆点:
    // 凡引用 accentColor 的 Fluent 逻辑(primary 按钮/toggle 选中/输入聚焦)在 neo 下自动变橙, 控件零改动。
    readonly property color _rawAccentColor: ThemeManager ? ThemeManager.accentColor : _constants.accentDefaults.accent
    readonly property color accentColor: isNeobrutalism ? _constants.neoColors.primary : _rawAccentColor
    readonly property color accentColorLight: isNeobrutalism ? Qt.lighter(_constants.neoColors.primary, 1.08)
        : (ThemeManager ? ThemeManager.accentColorLight : _constants.accentDefaults.accentLight)
    readonly property color accentColorDark: isNeobrutalism ? Qt.darker(_constants.neoColors.primary, 1.15)
        : (ThemeManager ? ThemeManager.accentColorDark : _constants.accentDefaults.accentDark)
    
    // Transparent color constant 透明色常量
    readonly property color transparent: "transparent"
    
    // ==================== Modular Components 模块化组件 ====================
    Theme { id: _theme; isDark: root.isDark; isNeo: root.isNeobrutalism; accentColor: root.accentColor; accentColorLight: root.accentColorLight; accentColorDark: root.accentColorDark; constants: _constants }
    StatusLevel { id: _statusLevel; isDark: root.isDark; isNeo: root.isNeobrutalism; accentColor: root.accentColor; constants: _constants }
    Button { id: _button }
    Tab { id: _tab }
    CommandBar { id: _commandBar }
    StateColor { id: _stateColor; isDark: root.isDark; isNeo: root.isNeobrutalism; accentColor: root.accentColor; constants: _constants }
    Constants { id: _constants; isDark: root.isDark }
    Metrics { id: _metrics; isDark: root.isDark }
    Orient { id: _orient }
    Flow { id: _flow }
    Chart { id: _chart }
    Card { id: _card }
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
    // Both data consistent, 2479 icons in total 两者数据一致，都是2479个图标
    readonly property var icons: Icons
    readonly property var icon: Icons  // Alias 别名
    
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
    // Icon font family 图标字体
    readonly property string iconFontFamily: fontFamily
    
    // Forward constants 转发常量（仅保留颜色/配置常量）
    readonly property alias accentDefaults: _constants.accentDefaults
    readonly property alias windowButtonColors: _constants.windowButtonColors
    readonly property alias dialogColors: _constants.dialogColors
    readonly property alias colorPalette: _constants.colorPalette
    readonly property alias colorPickerGradient: _constants.colorPickerGradient
    readonly property alias gray: _constants.gray
    readonly property alias demoPalette: _constants.demoPalette
    readonly property alias themeColors: _constants.themeColors
    readonly property alias textColor: _constants.textColor
    readonly property alias chartColors: _constants.chartColors
    readonly property alias confettiColors: _constants.confettiColors
    readonly property alias colorPickerDefaults: _constants.colorPickerDefaults
    readonly property alias passwordStrengthColors: _constants.passwordStrengthColors
    readonly property alias calendarColors: _constants.calendarColors
    readonly property alias exampleCardColors: _constants.exampleCardColors
    readonly property alias chipColors: _constants.chipColors
    readonly property alias tableCellColors: _constants.tableCellColors
    
    // Forward metrics 转发度量
    readonly property alias duration: _metrics.duration
    readonly property alias demoMetrics: _metrics.demoMetrics
    readonly property alias zIndex: _metrics.zIndex
    readonly property alias opacityLevel: _metrics.opacity
    readonly property alias mask: _metrics.mask
    readonly property alias border: _metrics.border
    readonly property alias neo: _metrics.neo
    readonly property alias iconSize: _metrics.iconSize
    readonly property alias spacing: _metrics.spacing
    readonly property alias radius: _metrics.radius
    readonly property alias controlSize: _metrics.controlSize
    readonly property alias window: _metrics.window
    readonly property alias popupMetrics: _metrics.popup
    readonly property alias infoBarMetrics: _metrics.infoBar
    readonly property alias comboBoxMetrics: _metrics.comboBox
    readonly property alias skeletonMetrics: _metrics.skeletonMetrics
    readonly property alias imageCropperDialogMetrics: _metrics.imageCropperDialog
    readonly property alias colorPickerMetrics: _metrics.colorPicker
    readonly property alias typography: _metrics.typography
    readonly property alias shadow: _metrics.shadow
    readonly property alias listIndicator: _metrics.listIndicator
    
    // Global icon path (resolved once, used everywhere) 全局图标路径
    readonly property string iconPath: Qt.resolvedUrl("controls/icons/fluent/")
    
    // Helper: get icon file name from Icons mapping 从映射获取图标文件名
    // Usage: Enums.icon("ADD") returns "Add.svg"
    function icon(enumKey) {
        var name = Icons.iconList[enumKey]
        return name ? (name + ".svg") : ""
    }
}