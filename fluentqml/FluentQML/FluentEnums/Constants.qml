// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// Constants - Small enum collections 小型枚举集合
// Merged for simplicity 合并以简化
QtObject {
    id: root
    
    required property bool isDark
    // neo 皮肤标志: neo 仅 light 配色, 文字色等需无视 isDark 强制走 light(否则深色主题下白字落 neo 米白底=隐形)
    property bool isNeo: false

    // ==================== ThemeColors 主题基础色 ====================
    readonly property QtObject themeColors: QtObject {
        // Backgrounds 背景
        // compact-nav window: outer=navigation+titlebar, inner=content area
        readonly property color backgroundDark: "#202020"   // Outer dark 外层深色
        readonly property color backgroundLight: "#f0f4f9"  // Outer light 外层浅色
        readonly property color surfaceDark: "#272727"      // Inner dark 内层深色
        readonly property color surfaceLight: "#f7f9fc"     // Inner light 内层浅色
        readonly property color cardDark: "#2d2d2d"  // Card uses opaque background 卡片使用不透明背景
        readonly property color cardLight: "#ffffff"  // Card uses opaque background 卡片使用不透明背景
        readonly property color toastCardDark: "#2d2d2d"  // Toast needs opaque background Toast需要不透明背景
        readonly property color toastCardLight: "#ffffff"  // Toast needs opaque background Toast需要不透明背景
        readonly property color dialogDark: "#2d2d30"
        readonly property color dialogLight: "#ffffff"
        readonly property color headerDark: "#252525"
        readonly property color headerLight: "#fafafa"
        readonly property color tableHoverDark: Qt.rgba(1, 1, 1, 0.06)
        // 全局统一: table/list hover 跟 controlBgHover 一致 (#f0f0f0)
        readonly property color tableHoverLight: "#f0f0f0"
        readonly property color alternateRowDark: Qt.rgba(1, 1, 1, 0.02)
        // 奇数行底色 — 比 cardLight 略灰但比 hover 淡, 让 hover 仍能跟它区分
        readonly property color alternateRowLight: "#f8f8f8"
        readonly property color scrollTrackDark: Qt.rgba(1, 1, 1, 0.04)
        readonly property color scrollTrackLight: "#f0f0f0"
        readonly property color scrollHandleDark: Qt.rgba(1, 1, 1, 0.2)
        readonly property color scrollHandleLight: "#bbb"
        readonly property color scrollHandleHoverDark: Qt.rgba(1, 1, 1, 0.3)
        readonly property color scrollHandleHoverLight: "#999"
        readonly property color tableBgDark: "#1a1a1a"
        readonly property color tableBgLight: "#f3f3f3"

        // Foregrounds 前景
        readonly property color foregroundDark: "#ffffff"
        readonly property color foregroundLight: "#1a1a1a"
        readonly property color secondaryForegroundDark: "#9d9d9d"
        readonly property color secondaryForegroundLight: "#606060"
        readonly property color tertiaryForegroundDark: "#717171"
        readonly property color tertiaryForegroundLight: "#8a8a8a"
        readonly property color disabledForegroundDark: "#6d6d6d"
        readonly property color disabledForegroundLight: "#a0a0a0"
        readonly property color accentForeground: "#ffffff"

        // Borders 边框
        readonly property color borderDark: "#454545"
        readonly property color borderLight: "#e5e5e5"
        readonly property color borderLightDark: "#3a3a3a"
        readonly property color borderLightLight: "#f0f0f0"
        readonly property color borderStrongDark: "#606060"
        readonly property color borderStrongLight: "#c0c0c0"
        readonly property color dividerDark: "#3d3d3d"
        readonly property color dividerLight: "#ebebeb"

        // Interaction 交互
        readonly property color hoverDark: "#3d3d3d"
        readonly property color hoverLight: "#f0f0f0"
        readonly property color pressedDark: "#333333"
        readonly property color pressedLight: "#e8e8e8"
        readonly property color disabledDark: "#4d4d4d"
        readonly property color disabledLight: "#cccccc"
        readonly property color selectedDark: "#0d3d6d"
        readonly property color selectedLight: "#cce4f7"
        readonly property color star: "#ffdc06"
        readonly property color infoAccentDark: "#60cdff"
        readonly property color infoAccentLight: "#005fb7"

        // Shadows 阴影
        readonly property color shadowDark: "#40000000"
        readonly property color shadowLight: "#20000000"
        readonly property color shadowStrongDark: "#60000000"
        readonly property color shadowStrongLight: "#30000000"
        
        // Tooltip/Flyout backgrounds Tooltip/弹出层背景
        readonly property color tooltipBgDark: "#282828"
        readonly property color tooltipBgLight: "#f8f8f8"

        // Tab selected background Tab选中背景
        readonly property color tabSelectedDark: "#282828"
        readonly property color tabSelectedLight: "#f9f9f9"
    }

    // ==================== NeoColors 新粗野皮肤原始调色板 ====================
    // neobrutalism 皮肤配色【单一真相源】, 参照 kiro_rs admin-ui(light) + neobrutalism.dev(dark 范式)。
    // light: 米白底/橙主色/黑边黑影; dark: 深炭底/提亮主色/黑边黑影(靠 surface 提亮区分)。
    // 控件与上层 token 读 neo.xxx 不变, 值按 isDark 自动切 → 加深色支持零控件改动。
    readonly property QtObject neoColors: QtObject {
        // 背景层: light 米白 / dark 深炭(surface 比 background 亮以靠层次区分)
        readonly property color background: root.isDark ? "#1A1A1A" : "#FAFAF0"
        readonly property color surface: root.isDark ? "#262626" : "#FFFFFF"
        readonly property color muted: root.isDark ? "#2E2E2E" : "#F5F5F5"
        // 文字: light 近黑 / dark 近白
        readonly property color foreground: root.isDark ? "#F5F5F0" : "#171717"
        readonly property color secondaryForeground: root.isDark ? "#A0A0A0" : "#666666"
        // 描边+硬阴影: light 纯黑(招牌); dark 反转成浅色(黑边在深底隐形, neo dark 用浅边+浅影立体区分)
        readonly property color border: root.isDark ? "#F5F5F0" : "#000000"
        readonly property color shadow: root.isDark ? "#F5F5F0" : "#000000"
        // 主色/语义色: dark 下提亮一档保证深底对比
        readonly property color primary: root.isDark ? "#FB923C" : "#F97316"      // 橙
        readonly property color primaryForeground: root.isDark ? "#1A1A1A" : "#FFFFFF"  // 主色块上文字(亮橙配深字)
        readonly property color success: root.isDark ? "#22C55E" : "#16A34A"      // 绿
        readonly property color danger: root.isDark ? "#F87171" : "#EF4444"       // 红
        readonly property color warning: root.isDark ? "#FBBF24" : "#F59E0B"      // 琥珀
        readonly property color info: root.isDark ? "#60A5FA" : "#3B82F6"         // 蓝
    }

    // ==================== SemanticColors 语义色 ====================
    // success/warning/error 及其背景色取自微软 WinUI 官方 SystemFillColor 资源
    // (Common_themeresources_any.xaml: SystemFillColorSuccess/Caution/Critical[Background])，
    // 系 Fluent Design System 公开标准语义色，非第三方库衍生。
    // info/attention/processing 为本项目自定义扩展(WinUI 无对应固定值)。
    // 来源: https://github.com/microsoft/microsoft-ui-xaml CommonStyles/Common_themeresources_any.xaml
    readonly property QtObject semanticColors: QtObject {
        // Foreground semantic colors 语义前景色
        readonly property color infoLight: "#676767"  // 自定义：中性灰信息色
        readonly property color successLight: "#0f7b0f"  // WinUI SystemFillColorSuccess (Light)
        readonly property color warningLight: "#9d5d00"  // WinUI SystemFillColorCaution (Light)
        readonly property color errorLight: "#c42b1c"  // WinUI SystemFillColorCritical (Light)
        readonly property color processingLight: "#7b2cbf"  // 自定义：鲜紫色代表处理中
        readonly property color attentionLight: "#0a93a8"  // 自定义：青色代表注意

        readonly property color infoDark: "#a3a3a3"  // 自定义：中性灰信息色
        readonly property color successDark: "#6ccb5f"  // WinUI SystemFillColorSuccess (Dark)
        readonly property color warningDark: "#c09000"  // 自定义：较 WinUI #FCE100 调深以提升暗色可读性
        readonly property color errorDark: "#ff99a4"  // WinUI SystemFillColorCritical (Dark)
        readonly property color processingDark: "#d8b4fe"  // 自定义：深色主题亮鲜紫
        readonly property color attentionDark: "#33b5bf"  // 自定义：深色主题亮青色

        // Background semantic colors (light) 语义背景色（浅色）
        readonly property color infoBgLight: "#cce4f7"  // 自定义
        readonly property color successBgLight: "#dff6dd"  // WinUI SystemFillColorSuccessBackground (Light)
        readonly property color warningBgLight: "#fff4ce"  // WinUI SystemFillColorCautionBackground (Light)
        readonly property color errorBgLight: "#fde7e9"  // WinUI SystemFillColorCriticalBackground (Light)
        readonly property color attentionBgLight: "#f0e6fa"  // 自定义
        readonly property color processingBgLight: "#f3e8ff"  // 自定义：浅紫色背景
    }

    // ==================== DemoPalette 示例色板 ====================
    // Used by examples to avoid scattered hardcoded colors 示例程序统一使用的色板
    readonly property QtObject demoPalette: QtObject {
        readonly property color blue: "#3b82f6"
        readonly property color green: "#10b981"
        readonly property color orange: "#f59e0b"
        readonly property color red: "#ef4444"
        readonly property color purple: "#8b5cf6"
        readonly property color cyan: "#06b6d4"
        readonly property color teal: "#14b8a6"
        readonly property color pink: "#ec4899"
        readonly property color sky: "#0ea5e9"
        readonly property color lime: "#84cc16"
    }

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
        readonly property real pressedLight: 0.7
    }

    // ==================== AccentDefaults 主题色默认值 ====================
    // 仅当 ThemeManager 缺失时作为 QML 兜底；正常运行时主色由 ThemeManager.DEFAULT_ACCENT 提供。
    // 三值与 ThemeManager 的 HSL 派生保持一致：base / light(L×1.1) / dark(L×0.85)。
    readonly property QtObject accentDefaults: QtObject {
        readonly property color accent: "#0e5a9c"       // 沉稳深 Fluent 蓝 (白字对比 7.09 AAA)
        readonly property color accentLight: "#0f63ac"   // hover 变体 (HSL L×1.1)
        readonly property color accentDark: "#0c4c85"    // pressed 变体 (HSL L×0.85)
    }

    // ==================== WindowButtonColors 窗口按钮颜色 ====================
    readonly property QtObject windowButtonColors: QtObject {
        readonly property color closeHover: semanticColors.errorLight
        readonly property color closePressed: semanticColors.errorLight
        readonly property color iconLight: themeColors.foregroundDark
        readonly property color iconDark: themeColors.foregroundLight

        // Non-close button background (pressed/hover) 非关闭按钮背景（按下/悬停）
        readonly property color normalPressedDark: grayColors.borderDark
        readonly property color normalPressedLight: grayColors.pressedLight
        readonly property color normalHoverDark: themeColors.surfaceDark
        readonly property color normalHoverLight: themeColors.borderLight
    }

    // ==================== DialogColors 对话框颜色 ====================
    readonly property QtObject dialogColors: QtObject {
        readonly property color containerBg: root.isDark ? "#2b2b2b" : grayColors.handleLight
        readonly property color borderDark: "#3a3a3a"
        // Light dialog border (Microsoft WinUI SurfaceStrokeColorDefault, 中性灰)
        readonly property color borderLight: "#c4c4c4"
        readonly property color border: root.isDark ? borderDark : borderLight

        readonly property color dividerDark: "#1d1d1d"
        readonly property color dividerLight: "#e5e5e5"
        readonly property color divider: root.isDark ? dividerDark : dividerLight

        readonly property color text: root.isDark ? themeColors.foregroundDark : grayColors.textPrimaryLight
        readonly property color selectedText: root.isDark ? grayColors.textPrimaryLight : grayColors.handleLight

        // Shadow
        readonly property color shadowColor: Qt.rgba(0, 0, 0, 0.2)
    }



    // ==================== ColorPalette 颜色表 ====================
    readonly property QtObject colorPalette: QtObject {
        readonly property color automaticColor: Qt.rgba(0, 0, 0, 1)

        // Theme colors (10 columns x 6 rows) 主题色
        readonly property var themeColors: [
            // Row 1
            "#ffffff", "#000000", "#e7e6e6", "#44546a", "#4472c4", "#ed7d31", "#a5a5a5", "#ffc000", "#5b9bd5", "#70ad47",
            // Row 2
            "#f2f2f2", "#7f7f7f", "#d0cece", "#d6dce4", "#d9e2f3", "#fbe5d5", "#ededed", "#fff2cc", "#deebf6", "#e2efd9",
            // Row 3
            "#d8d8d8", "#595959", "#aeabab", "#adb9ca", "#b4c6e7", "#f7cbac", "#dbdbdb", "#ffe599", "#bdd7ee", "#c5e0b3",
            // Row 4
            "#bfbfbf", "#3f3f3f", "#757070", "#8496b0", "#8eaadb", "#f4b183", "#c9c9c9", "#ffd966", "#9cc3e5", "#a8d08d",
            // Row 5
            "#a5a5a5", "#262626", "#3a3838", "#323f4f", "#2f5496", "#c55a11", "#7b7b7b", "#bf9000", "#2e75b5", "#538135",
            // Row 6
            "#7f7f7f", "#0c0c0c", "#171616", "#222a35", "#1f3864", "#833c0b", "#525252", "#7f6000", "#1e4e79", "#375623"
        ]

        // Standard colors (10 colors) 标准色
        readonly property var standardColors: [
            "#c00000", "#ff0000", "#ffc000", "#ffff00", "#92d050",
            "#00b050", "#00b0f0", "#0070c0", "#002060", "#7030a0"
        ]
    }

    // ==================== ColorPickerGradient 渐变参数 ====================
    readonly property QtObject colorPickerGradient: QtObject {
        // Hue slider stops 色相滑块渐变停靠点
        readonly property real huePos0: 0.0
        readonly property real huePos1: 0.166
        readonly property real huePos2: 0.333
        readonly property real huePos3: 0.5
        readonly property real huePos4: 0.666
        readonly property real huePos5: 0.833
        readonly property real huePos6: 1.0

        readonly property color hueColor0: "#ff0000"
        readonly property color hueColor1: "#ffff00"
        readonly property color hueColor2: "#00ff00"
        readonly property color hueColor3: "#00ffff"
        readonly property color hueColor4: "#0000ff"
        readonly property color hueColor5: "#ff00ff"
        readonly property color hueColor6: "#ff0000"
    }
    
    // ==================== Gray 灰色系 ====================
    readonly property QtObject gray: QtObject {
        readonly property color text: root.isDark ? themeColors.tertiaryForegroundLight : themeColors.secondaryForegroundLight
        readonly property color background: root.isDark ? themeColors.surfaceDark : themeColors.scrollTrackLight
        readonly property color border: root.isDark ? grayColors.borderDark : grayColors.borderLight
        readonly property color disabled: root.isDark ? themeColors.disabledForegroundLight : themeColors.scrollHandleHoverLight
        readonly property color handle: root.isDark ? themeColors.pressedDark : grayColors.handleLight
        readonly property color tooltip: root.isDark ? themeColors.hoverDark : themeColors.pressedDark
    }
    
    // ==================== TextColor 文字颜色 ====================
    readonly property QtObject textColor: QtObject {
        // neo: 文字色走 neoColors(已 dark-aware, light 近黑/dark 近白); 非 neo 走原 Fluent 明暗逻辑
        readonly property color primary: root.isNeo ? neoColors.foreground : (root.isDark ? themeColors.foregroundDark : grayColors.textPrimaryLight)
        readonly property color secondary: root.isNeo ? neoColors.secondaryForeground : (root.isDark ? Qt.rgba(1, 1, 1, textOpacity.secondary) : Qt.rgba(0, 0, 0, 0.6))
        readonly property color tertiary: root.isNeo ? neoColors.secondaryForeground : (root.isDark ? Qt.rgba(1, 1, 1, textOpacity.tertiary) : Qt.rgba(0, 0, 0, textOpacity.tertiary))
        readonly property color disabled: root.isDark ? Qt.rgba(1, 1, 1, textOpacity.disabled) : Qt.rgba(0, 0, 0, textOpacity.disabled)
        readonly property color strong: root.isNeo ? neoColors.foreground : (root.isDark ? Qt.rgba(1, 1, 1, textOpacity.strong) : Qt.rgba(0, 0, 0, textOpacity.strong))
        readonly property color pressed: root.isDark ? Qt.rgba(1, 1, 1, textOpacity.strong) : Qt.rgba(0, 0, 0, textOpacity.pressedLight)
    }
    
    // ==================== ChartColors 图表颜色 (Fluent Design) ====================
    readonly property QtObject chartColors: QtObject {
        // Fluent Design chart palette 柔和的Fluent图表调色板
        readonly property var palette: [
            "#0078D4", "#107C10", "#FFB900", "#D13438", "#8764B8",
            "#00B7C3", "#498205", "#FF8C00", "#E81123", "#881798"
        ]
        // Pie/Radar/Scatter chart palette 饼图/雷达图/散点图调色板
        readonly property var pieRadarPalette: [
            "#0078D4", "#107C10", "#FFB900", "#D13438", "#8764B8",
            "#00B7C3", "#498205", "#FF8C00", "#E81123", "#881798"
        ]
        // Extended palette for more data series 扩展调色板
        readonly property var extendedPalette: [
            "#0078D4", "#107C10", "#FFB900", "#D13438", "#8764B8",
            "#00B7C3", "#498205", "#FF8C00", "#E81123", "#881798"
        ]
        // Grid line color 网格线颜色
        readonly property color gridLine: root.isDark ? Qt.rgba(1, 1, 1, 0.1) : Qt.rgba(0, 0, 0, 0.08)
        // Axis label color 坐标轴标签颜色
        readonly property color axisLabel: root.isDark ? Qt.rgba(1, 1, 1, 0.6) : Qt.rgba(0, 0, 0, 0.6)
    }
    
    // ==================== ConfettiColors 彩纸颜色 ====================
    readonly property QtObject confettiColors: QtObject {
        readonly property var palette: [
            "#FFB900",  // Gold 金色
            "#E74856",  // Coral 珊瑚红
            "#0078D4",  // Fluent Blue Fluent蓝
            "#107C10",  // Green 翠绿
            "#8764B8",  // Purple 紫色
            "#00B7C3"   // Cyan 青色
        ]
    }
    
    // ==================== ColorPickerDefaults 颜色选择器默认值 ====================
    readonly property QtObject colorPickerDefaults: QtObject {
        readonly property color defaultColor: "#0078d4"  // Fluent accent blue
        readonly property color baseRed: "#ff0000"       // Base red for sliders
        readonly property var quickPalette: [
            "#0078d4", "#0099bc", "#2d7d9a", "#00b7c3", "#038387", "#7a7574"
        ]
    }
    
    // ==================== PasswordStrengthColors 密码强度颜色 ====================
    readonly property QtObject passwordStrengthColors: QtObject {
        readonly property var palette: ["#c42b1c", "#e87a18", "#e8b318", "#54a814", "#0f7b0f"]
    }
    
    // ==================== CalendarColors 日历颜色 ====================
    readonly property QtObject calendarColors: QtObject {
        readonly property color navIconDark: "#9c9c9c"
        readonly property color navIconLight: "#5e5e5e"
        readonly property color rangeBarDark: "#262626"
        readonly property color rangeBarLight: "#F0F0F0"
    }
    
    // ==================== ExampleCardColors 示例卡片颜色 ====================
    readonly property QtObject exampleCardColors: QtObject {
        readonly property color bgDark: "#3b3b3b"       // Dark mode top background 深色模式上部背景
        readonly property color bgLight: "#f7f7f7"      // Light mode top background 浅色模式上部背景
        readonly property color borderDark: "#3a3a3a"
        readonly property color descBgDark: "#535353"   // Dark mode bottom background 深色模式下部背景
        readonly property color descBgLight: "#fcfcfc"  // Light mode bottom background 浅色模式下部背景
    }


    // ==================== ChipColors 标签颜色 ====================
    readonly property QtObject chipColors: QtObject {
        readonly property color checkedText: "#ffffff"
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
}
