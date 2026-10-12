// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "_internal" as ConstantsInternal
import "_internal/ConstantsStaticData.js" as ConstantsStaticData

// Constants - Small enum collections 小型枚举集合
// Merged for simplicity 合并以简化
QtObject {
    id: root
    
    required property bool isDark
    // neo 皮肤标志: neo 仅 light 配色, 文字色等需无视 isDark 强制走 light(否则深色主题下白字落 neo 米白底=隐形)
    property bool isNeo: false
    property bool isTicket: false
    property bool isNeumorphism: false

    // ==================== ThemeColors 主题基础色 ====================
    readonly property QtObject themeColors: ConstantsInternal.ConstantsThemeColors {}

    // ==================== NeoColors 新粗野皮肤原始调色板 ====================
    // neobrutalism 皮肤配色【单一真相源】, 参照 kiro_rs admin-ui(light) + neobrutalism.dev(dark 范式)。
    // light: 米白底/橙主色/黑边黑影; dark: 深炭底/提亮主色/黑边黑影(靠 surface 提亮区分)。
    // 控件与上层 token 读 neo.xxx 不变, 值按 isDark 自动切 → 加深色支持零控件改动。
    readonly property QtObject neoColors: QtObject {
        // Background layer: light cream / dark charcoal 背景层: light 米白 / dark 深炭(surface 比 background 亮以靠层次区分)
        readonly property color background: root.isDark ? "#1A1A1A" : "#FAFAF0"
        readonly property color surface: root.isDark ? "#262626" : "#FFFFFF"
        readonly property color muted: root.isDark ? "#2E2E2E" : "#F5F5F5"
        // Text: light near-black / dark near-white 文字: light 近黑 / dark 近白
        readonly property color foreground: root.isDark ? "#F5F5F0" : "#171717"
        readonly property color secondaryForeground: root.isDark ? "#A0A0A0" : "#666666"
        // Stroke + hard shadow: light pure black (signature) 描边+硬阴影: light 纯黑(招牌); dark 反转成浅色(黑边在深底隐形, neo dark 用浅边+浅影立体区分)
        readonly property color border: root.isDark ? "#F5F5F0" : "#000000"
        readonly property color shadow: root.isDark ? "#F5F5F0" : "#000000"
        // Accent/semantic colors: brightened one step on dark for contrast 主色/语义色: dark 下提亮一档保证深底对比
        readonly property color primary: root.isDark ? "#FB923C" : "#F97316"      // Orange 橙
        readonly property color primaryForeground: root.isDark ? "#1A1A1A" : "#FFFFFF"  // Text on primary swatch (bright orange, dark text) 主色块上文字(亮橙配深字)
        readonly property color success: root.isDark ? "#22C55E" : "#16A34A"      // Green 绿
        readonly property color danger: root.isDark ? "#F87171" : "#EF4444"       // Red 红
        readonly property color warning: root.isDark ? "#FBBF24" : "#F59E0B"      // Amber 琥珀
        readonly property color info: root.isDark ? "#60A5FA" : "#3B82F6"         // Blue 蓝
    }

    // ==================== TicketColors 复古票据皮肤原始调色板 ====================
    // Warm paper, aged ink and stamp colors are the single source of truth for vintage_ticket.
    // 暖纸、旧油墨与印章色是 vintage_ticket 皮肤的唯一配色真相源。
    readonly property QtObject ticketColors: QtObject {
        readonly property color background: root.isDark ? "#1D1A17" : "#E9E1D2"
        readonly property color surface: root.isDark ? "#28231E" : "#F8F3E8"
        readonly property color muted: root.isDark ? "#342E27" : "#EEE6D8"
        readonly property color foreground: root.isDark ? "#EDE3D2" : "#2B211A"
        readonly property color secondaryForeground: root.isDark ? "#B9AB98" : "#74685B"
        readonly property color disabledForeground: root.isDark ? "#766B60" : "#A79B8B"
        readonly property color border: root.isDark ? "#B4A48E" : "#5A4637"
        readonly property color divider: root.isDark ? "#776A5B" : "#B8AA96"
        readonly property color primary: root.isDark ? "#C6A66B" : "#5A3D2B"
        readonly property color primaryForeground: root.isDark ? "#1D1A17" : "#FFF9EE"
        readonly property color success: root.isDark ? "#68A77C" : "#267451"
        readonly property color danger: root.isDark ? "#D37B72" : "#A33E36"
        readonly property color warning: root.isDark ? "#C9A45D" : "#91651F"
        readonly property color info: root.isDark ? "#88A9AE" : "#416C73"
    }

    // ==================== NeumorphismColors 新拟态原始调色板 ====================
    // Surface and canvas intentionally share a base color; depth comes from paired soft shadows.
    // 表面与画布有意保持同色，立体感由双向软阴影产生。
    readonly property QtObject neumorphismColors: QtObject {
        readonly property color background: root.isDark ? "#252B35" : "#E4EBF3"
        readonly property color surface: root.isDark ? "#252B35" : "#E4EBF3"
        readonly property color muted: root.isDark ? "#303947" : "#D7E0EB"
        readonly property color hover: root.isDark ? "#2D3541" : "#DCE5EF"
        readonly property color pressed: root.isDark ? "#202731" : "#CDD8E5"
        readonly property color disabledSurface: root.isDark ? "#2A313C" : "#DDE5EE"
        readonly property color divider: root.isDark ? "#465365" : "#C2CCD9"
        readonly property color indicator: root.isDark ? "#7F8DA1" : "#7A899D"
        readonly property color indicatorHover: root.isDark ? "#AAB7C8" : "#596A80"
        readonly property color foreground: root.isDark ? "#E8EEF7" : "#27364A"
        readonly property color secondaryForeground: root.isDark ? "#AAB7C8" : "#66758A"
        readonly property color disabledForeground: root.isDark ? "#697687" : "#9BA8B8"
        readonly property color shadowDark: root.isDark ? "#171C24" : "#B7C2D0"
        readonly property color shadowLight: root.isDark ? "#3E4A5B" : "#FFFFFF"
        readonly property color primary: root.isDark ? "#8CB4FF" : "#3867D6"
        readonly property color primaryForeground: "#FFFFFF"
        readonly property color selected: root.isDark ? "#344159" : "#CCD9EF"
        readonly property color selectedHover: root.isDark ? "#3A4A64" : "#C2D2EC"
        readonly property color success: root.isDark ? "#72D6A0" : "#238B64"
        readonly property color danger: root.isDark ? "#FF9A9A" : "#C94B58"
        readonly property color warning: root.isDark ? "#F2C879" : "#A86F1E"
        readonly property color info: root.isDark ? "#82C8E8" : "#397A9A"
    }

    // ==================== SemanticColors 语义色 ====================
    // success/warning/error 及其背景色取自微软 WinUI 官方 SystemFillColor 资源
    // (Common_themeresources_any.xaml: SystemFillColorSuccess/Caution/Critical[Background])，
    // 系 Fluent Design System 公开标准语义色，非第三方库衍生。
    // info/attention/processing/caution 为本项目自定义扩展(WinUI 无对应固定值)。
    // 来源: https://github.com/microsoft/microsoft-ui-xaml CommonStyles/Common_themeresources_any.xaml
    readonly property var semanticColors: ConstantsStaticData.semanticColors()

    // ==================== DemoPalette 示例色板 ====================
    // Used by examples to avoid scattered hardcoded colors 示例程序统一使用的色板
    readonly property var demoPalette: ConstantsStaticData.demoPalette()

    // ==================== GrayColors 灰度色 ====================
    readonly property QtObject grayColors: QtObject {
        readonly property color borderDark: "#404040"
        readonly property color borderLight: "#e8e8e8"
        readonly property color handleLight: "white"
        readonly property color textPrimaryLight: "black"
        readonly property color pressedLight: "#c0c0c0"
    }

    // ==================== TextOpacity 文字透明度 ====================
    readonly property QtObject textOpacity: QtObject {
        readonly property real secondary: 0.7
        readonly property real tertiary: 0.5
        readonly property real disabled: 0.4
        readonly property real strong: 0.8
        readonly property real timestamp: 0.6
        readonly property real pressedLight: 0.7
    }

    // ==================== AccentDefaults 主题色默认值 ====================
    // 仅当 ThemeManager 缺失时作为 QML 兜底；正常运行时主色由 ThemeManager.DEFAULT_ACCENT 提供。
    // 三值与 ThemeManager 的 HSL 派生保持一致：base / light(L×1.1) / dark(L×0.85)。
    readonly property QtObject accentDefaults: QtObject {
        readonly property color accent: "#0e5a9c"       // Deep steady Fluent blue (white-text contrast 7.09 AAA) 沉稳深 Fluent 蓝 (白字对比 7.09 AAA)
        readonly property color accentLight: "#0f63ac"   // hover 变体 (HSL L×1.1)
        readonly property color accentDark: "#0c4c85"    // pressed 变体 (HSL L×0.85)
    }

    // ==================== WindowButtonColors 窗口按钮颜色 ====================
    readonly property QtObject windowButtonColors: QtObject {
        readonly property color closeHover: root.isTicket ? ticketColors.danger : semanticColors.errorLight
        readonly property color closePressed: root.isTicket ? Qt.darker(ticketColors.danger, 1.08) : semanticColors.errorLight
        readonly property color iconLight: root.isTicket ? ticketColors.foreground : themeColors.foregroundDark
        readonly property color iconDark: root.isTicket ? ticketColors.foreground : themeColors.foregroundLight

        // Non-close button background (pressed/hover) 非关闭按钮背景（按下/悬停）
        readonly property color normalPressedDark: root.isTicket ? Qt.darker(ticketColors.muted, 1.06) : grayColors.borderDark
        readonly property color normalPressedLight: root.isTicket ? Qt.darker(ticketColors.muted, 1.06) : grayColors.pressedLight
        readonly property color normalHoverDark: root.isTicket ? ticketColors.muted : themeColors.surfaceDark
        readonly property color normalHoverLight: root.isTicket ? ticketColors.muted : themeColors.borderLight
    }

    // ==================== DialogColors 对话框颜色 ====================
    readonly property QtObject dialogColors: QtObject {
        readonly property color containerBg: root.isTicket ? ticketColors.surface : (root.isDark ? "#2b2b2b" : grayColors.handleLight)
        readonly property color borderDark: root.isTicket ? ticketColors.border : "#3a3a3a"
        // Light dialog border (Microsoft WinUI SurfaceStrokeColorDefault, 中性灰)
        readonly property color borderLight: root.isTicket ? ticketColors.border : "#c4c4c4"
        readonly property color border: root.isDark ? borderDark : borderLight

        readonly property color dividerDark: root.isTicket ? ticketColors.divider : "#1d1d1d"
        readonly property color dividerLight: root.isTicket ? ticketColors.divider : "#e5e5e5"
        readonly property color divider: root.isDark ? dividerDark : dividerLight

        readonly property color text: root.isTicket ? ticketColors.foreground : (root.isDark ? themeColors.foregroundDark : grayColors.textPrimaryLight)
        readonly property color selectedText: root.isTicket ? ticketColors.primaryForeground : (root.isDark ? grayColors.textPrimaryLight : grayColors.handleLight)

        // Shadow
        readonly property color shadowColor: root.isTicket ? Qt.rgba(0, 0, 0, 0) : Qt.rgba(0, 0, 0, 0.2)
    }



    // ==================== ColorPalette 颜色表 ====================
    readonly property var colorPalette: ConstantsStaticData.colorPalette()

    // ==================== ColorPickerGradient 渐变参数 ====================
    readonly property var colorPickerGradient: ConstantsStaticData.colorPickerGradient()
    
    // ==================== Gray 灰色系 ====================
    readonly property QtObject gray: QtObject {
        readonly property color text: root.isNeumorphism ? neumorphismColors.secondaryForeground
            : (root.isTicket ? ticketColors.secondaryForeground
            : (root.isDark ? themeColors.tertiaryForegroundLight : themeColors.secondaryForegroundLight)
            )
        readonly property color background: root.isNeumorphism ? neumorphismColors.surface
            : (root.isTicket ? ticketColors.surface
            : (root.isDark ? themeColors.surfaceDark : themeColors.scrollTrackLight))
        readonly property color border: root.isNeumorphism ? Qt.rgba(0, 0, 0, 0)
            : (root.isTicket ? ticketColors.border
            : (root.isDark ? grayColors.borderDark : grayColors.borderLight))
        readonly property color disabled: root.isNeumorphism ? neumorphismColors.disabledForeground
            : (root.isTicket ? ticketColors.disabledForeground
            : (root.isDark ? themeColors.disabledForegroundLight : themeColors.scrollHandleHoverLight))
        readonly property color handle: root.isNeumorphism ? neumorphismColors.indicator
            : (root.isTicket ? ticketColors.surface
            : (root.isDark ? themeColors.pressedDark : grayColors.handleLight))
        readonly property color tooltip: root.isNeumorphism ? neumorphismColors.surface
            : (root.isTicket ? ticketColors.surface
            : (root.isDark ? themeColors.hoverDark : themeColors.pressedDark))
    }
    
    // ==================== TextColor 文字颜色 ====================
    readonly property QtObject textColor: QtObject {
        // Non-Fluent text uses its skin tokens; Fluent follows the light/dark theme.
        // 非 Fluent 文字使用对应皮肤 token；Fluent 跟随明暗主题。
        readonly property color onAccent: root.isNeo ? neoColors.primaryForeground
            : (root.isNeumorphism ? neumorphismColors.primaryForeground
            : (root.isTicket ? ticketColors.primaryForeground : themeColors.accentForeground))
        readonly property color onAccentTimestamp: Qt.rgba(
            onAccent.r,
            onAccent.g,
            onAccent.b,
            textOpacity.timestamp
        )
        readonly property color primary: root.isNeo ? neoColors.foreground
            : (root.isNeumorphism ? neumorphismColors.foreground
            : (root.isTicket ? ticketColors.foreground : (root.isDark ? themeColors.foregroundDark : grayColors.textPrimaryLight)))
        readonly property color secondary: root.isNeo ? neoColors.secondaryForeground
            : (root.isNeumorphism ? neumorphismColors.secondaryForeground
            : (root.isTicket ? ticketColors.secondaryForeground : (root.isDark ? Qt.rgba(1, 1, 1, textOpacity.secondary) : Qt.rgba(0, 0, 0, 0.6))))
        readonly property color tertiary: root.isNeo ? neoColors.secondaryForeground
            : (root.isNeumorphism ? neumorphismColors.secondaryForeground
            : (root.isTicket ? ticketColors.secondaryForeground : (root.isDark ? Qt.rgba(1, 1, 1, textOpacity.tertiary) : Qt.rgba(0, 0, 0, textOpacity.tertiary))))
        readonly property color disabled: root.isNeumorphism ? neumorphismColors.disabledForeground
            : (root.isTicket ? ticketColors.disabledForeground
            : (root.isDark ? Qt.rgba(1, 1, 1, textOpacity.disabled) : Qt.rgba(0, 0, 0, textOpacity.disabled)))
        readonly property color strong: root.isNeo ? neoColors.foreground
            : (root.isNeumorphism ? neumorphismColors.foreground
            : (root.isTicket ? ticketColors.foreground : (root.isDark ? Qt.rgba(1, 1, 1, textOpacity.strong) : Qt.rgba(0, 0, 0, textOpacity.strong))))
        readonly property color pressed: root.isNeumorphism ? neumorphismColors.secondaryForeground
            : (root.isTicket ? ticketColors.primary
            : (root.isDark ? Qt.rgba(1, 1, 1, textOpacity.strong) : Qt.rgba(0, 0, 0, textOpacity.pressedLight)))
    }

    // Fixed code-block palette 固定代码块色板
    readonly property QtObject codeBlockColors: QtObject {
        readonly property color background: root.isTicket ? ticketColors.muted : "#1E1E1E"
        readonly property color border: root.isTicket ? ticketColors.border : Qt.rgba(1, 1, 1, 0.08)
        readonly property color secondaryText: root.isTicket ? ticketColors.secondaryForeground : "#9CA3AF"
        readonly property color hover: root.isTicket ? Qt.darker(ticketColors.muted, 1.06) : Qt.rgba(1, 1, 1, 0.1)
        readonly property color copySuccess: root.isTicket ? ticketColors.success : "#10B981"
        readonly property color foreground: root.isTicket ? ticketColors.foreground : "#E5E7EB"
    }
    
    // ==================== ChartColors 图表颜色 ====================
    readonly property QtObject chartColors: QtObject {
        // Fixed strong text on colored markers and dark tooltips 彩色标记与深色提示框上的固定强文字
        readonly property color strongText: root.isNeumorphism ? neumorphismColors.foreground
            : (root.isTicket ? ticketColors.foreground : themeColors.accentForeground)
        // Contrast text for labels rendered directly on series colors 直接绘制在系列色上的标签对比文字
        readonly property color markerText: root.isTicket
            ? ticketColors.primaryForeground : strongText
        readonly property var _fluentPalette: [
            "#0078D4", "#107C10", "#FFB900", "#D13438", "#8764B8",
            "#00B7C3", "#498205", "#FF8C00", "#E81123", "#881798"
        ]
        readonly property var _ticketPalette: [
            ticketColors.primary, ticketColors.success, ticketColors.warning,
            ticketColors.danger, ticketColors.info, ticketColors.border,
            Qt.lighter(ticketColors.success, 1.12),
            Qt.lighter(ticketColors.warning, 1.12),
            Qt.lighter(ticketColors.danger, 1.12),
            Qt.lighter(ticketColors.info, 1.12)
        ]
        // Fluent chart palette Fluent 图表调色板
        readonly property var palette: root.isTicket ? _ticketPalette : _fluentPalette
        // Pie/Radar/Scatter chart palette 饼图/雷达图/散点图调色板
        readonly property var pieRadarPalette: palette
        // Extended palette for more data series 扩展调色板
        readonly property var extendedPalette: palette
        // Grid line color 网格线颜色
        readonly property color gridLine: root.isTicket ? ticketColors.divider : (root.isDark ? Qt.rgba(1, 1, 1, 0.1) : Qt.rgba(0, 0, 0, 0.08))
        // Axis label color 坐标轴标签颜色
        readonly property color axisLabel: root.isTicket ? ticketColors.secondaryForeground : (root.isDark ? Qt.rgba(1, 1, 1, 0.6) : Qt.rgba(0, 0, 0, 0.6))
    }
    
    // ==================== ConfettiColors 彩纸颜色 ====================
    readonly property QtObject confettiColors: QtObject {
        readonly property var _fluentPalette: [
            "#FFB900",  // Gold 金色
            "#E74856",  // Coral 珊瑚红
            "#0078D4",  // Fluent Blue Fluent蓝
            "#107C10",  // Green 翠绿
            "#8764B8",  // Purple 紫色
            "#00B7C3"   // Cyan 青色
        ]
        readonly property var _ticketPalette: [
            ticketColors.primary,
            ticketColors.warning,
            ticketColors.danger,
            ticketColors.success,
            ticketColors.info,
            ticketColors.border
        ]
        readonly property var palette: root.isTicket ? _ticketPalette : _fluentPalette
    }
    
    // ==================== ColorPickerDefaults 颜色选择器默认值 ====================
    readonly property QtObject colorPickerDefaults: QtObject {
        readonly property color defaultColor: "#0078d4"  // Fluent accent blue
        readonly property color baseRed: "#ff0000"       // Base red for sliders 滑块基础红色
        readonly property var quickPalette: [
            "#0078d4", "#0099bc", "#2d7d9a", "#00b7c3", "#038387", "#7a7574"
        ]
    }
    
    // ==================== PasswordStrengthColors 密码强度颜色 ====================
    readonly property QtObject passwordStrengthColors: QtObject {
        readonly property var lightPalette: ["#c42b1c", "#e87a18", "#e8b318", "#54a814", semanticColors.successLight]
        readonly property var darkPalette: [semanticColors.errorDark, "#f6b44b", semanticColors.warningDark, "#59d6c7", semanticColors.successDark]
        readonly property var ticketPalette: [
            ticketColors.danger,
            Qt.lighter(ticketColors.danger, 1.12),
            ticketColors.warning,
            Qt.lighter(ticketColors.success, 1.12),
            ticketColors.success
        ]
        readonly property var palette: root.isTicket ? ticketPalette
            : (root.isDark ? darkPalette : lightPalette)
    }
    
    // ==================== CalendarColors 日历颜色 ====================
    readonly property QtObject calendarColors: QtObject {
        readonly property color navIconDark: root.isTicket ? ticketColors.foreground : "#9c9c9c"
        readonly property color navIconLight: root.isTicket ? ticketColors.foreground : "#5e5e5e"
        readonly property color rangeBarDark: root.isTicket ? ticketColors.muted : "#262626"
        readonly property color rangeBarLight: root.isTicket ? ticketColors.muted : "#F0F0F0"
    }
    
    // ==================== ExampleCardColors 示例卡片颜色 ====================
    readonly property QtObject exampleCardColors: QtObject {
        readonly property color bgDark: "#3b3b3b"       // Dark mode top background 深色模式上部背景
        readonly property color bgLight: "#f7f7f7"      // Light mode top background 浅色模式上部背景
        readonly property color borderDark: "#3a3a3a"
        readonly property color descBgDark: "#535353"   // Dark mode bottom background 深色模式下部背景
        readonly property color descBgLight: "#fcfcfc"  // Light mode bottom background 浅色模式下部背景
    }

    // ==================== ExamplePageColors 示例页面颜色 ====================
    readonly property QtObject examplePageColors: QtObject {
        readonly property color carouselRed: "#e74c3c"
        readonly property color carouselBlue: "#3498db"
        readonly property color carouselGreen: "#2ecc71"
        readonly property color carouselPurple: "#9b59b6"
        readonly property color tableDivider: root.isDark
            ? Qt.rgba(1, 1, 1, 0.06)
            : Qt.rgba(0, 0, 0, 0.05)
        readonly property color statusEnabledBg: Qt.rgba(0.18, 0.75, 0.45, 0.12)
        readonly property color statusDisabledBg: Qt.rgba(0.85, 0.25, 0.25, 0.10)
        readonly property color statusEnabledText: "#1fa84d"
        readonly property color statusDisabledText: "#c93c3c"
        readonly property color settingsCustomAccent: "#ff6b6b"
    }


    // ==================== ChipColors 标签颜色 ====================
    readonly property QtObject chipColors: QtObject {
        readonly property color checkedText: root.isTicket ? ticketColors.primaryForeground : "#ffffff"
        // Text on light/dark backgrounds 浅色/深色背景上的文字
        readonly property color textOnLight: grayColors.textPrimaryLight
        readonly property color textOnDark: themeColors.accentForeground
    }
    
    // ==================== TableCellColors 表格单元格颜色 ====================
    readonly property QtObject tableCellColors: QtObject {
        // Currency/Profit colors 货币/利润颜色
        readonly property color positive: "#2e7d32"
        readonly property color negative: "#c62828"
        readonly property color profitPositive: "#1565c0"
        readonly property color defaultText: "#333333"
        // Mode badge colors 模式徽章颜色
        readonly property color modeContinuousBg: "#e8f5e9"
        readonly property color modeContinuousText: "#2e7d32"
        readonly property color modeOnceBg: "#fff3e0"
        readonly property color modeOnceText: "#e65100"
        readonly property color modeDefaultBg: "#e3f2fd"
        readonly property color modeDefaultText: "#1565c0"
        // Edit button colors 编辑按钮颜色
        readonly property color editBtnNormal: "#2196f3"
        readonly property color editBtnHover: "#1976d2"
        readonly property color editBtnPressed: "#1565c0"
    }

    // ==================== AccentScale 强调色阶 ====================
    // WinUI 风格色阶，仅当 ThemeManager 缺失时兜底；运行时由 ThemeManager.accentScale
    // 以同一算法(HSL 明度 ±0.10/0.20/0.30, 限幅 0..1)从当前 accentColor 确定性派生。
    // 本组数值即 #0e5a9c 按该算法的派生结果, 由 tests/test_accent_scale_tokens.py 交叉校验。
    // 追加在文件末尾, 以免平移既有颜色数组的行号基线。
    readonly property QtObject accentScale: QtObject {
        readonly property color light3: "#53a7f0"  // accent L+0.30
        readonly property color light2: "#258feb"  // accent L+0.20
        readonly property color light1: "#1275cb"  // accent L+0.10
        readonly property color accent: "#0e5a9c"  // base accent 基准强调色
        readonly property color dark1: "#0a3f6d"   // accent L-0.10
        readonly property color dark2: "#06243e"   // accent L-0.20
        readonly property color dark3: "#010910"   // accent L-0.30
    }

    // ==================== High Contrast 高对比度 ====================
    // Windows high-contrast themes maximise luminance separation instead of using
    // soft greys: strokes reach full white and secondary text stops being faded.
    // These are absolute endpoints, so they stay readable under either theme.
    // Windows 高对比度主题以最大化亮度差代替柔和灰阶：描边取纯白、次要文本不再淡化。
    // 它们是绝对端点值，因此在两种明暗主题下都可读。
    // 同样追加在文件末尾, 以免平移既有颜色数组的行号基线。
    readonly property QtObject highContrastColors: QtObject {
        readonly property color background: "#000000"
        readonly property color surface: "#000000"
        readonly property color foreground: "#ffffff"
        readonly property color secondaryForeground: "#ffffff"
        readonly property color border: "#ffffff"
        readonly property color borderStrong: "#ffffff"
        readonly property color divider: "#ffffff"
        readonly property color disabled: "#c0c0c0"
    }
}
