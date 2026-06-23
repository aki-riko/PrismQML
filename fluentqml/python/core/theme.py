# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是FluentQML的一部分，采用MIT许可证授权。
"""
FluentQML 主题系统

支持功能：
- 深色/浅色/自动主题切换
- 自定义主题色（accentColor）
- QML属性绑定（自动通知更新）
"""

from enum import Enum
from PySide6.QtCore import QObject, Signal, Property, Slot
from PySide6.QtGui import QColor


class Theme(Enum):
    """主题枚举"""

    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class Skin(Enum):
    """皮肤（设计语言）枚举

    与 Theme（明暗）正交：theme 控制明暗，skin 控制设计语言。
    fluent       → 默认 Fluent Design（圆角、模糊阴影）
    neobrutalism → 新粗野（粗黑边、硬阴影、按下位移）
    """

    FLUENT = "fluent"
    NEOBRUTALISM = "neobrutalism"


class ThemeManager(QObject):
    """
    主题管理器（单例）

    功能：
    - 主题切换（Light/Dark/Auto）
    - 主题色管理（可自定义）
    - QML属性绑定支持

    使用示例：
        # Python端
        from fluentqml import setTheme, setAccentColor, Theme
        setTheme(Theme.DARK)
        setAccentColor("#0078d4")  # FluentQML 默认 Fluent 蓝

        # QML端
        Rectangle {
            color: ThemeManager.accentColor
        }
    """

    # Signals 信号
    themeChanged = Signal(str)
    accentColorChanged = Signal(str)
    skinChanged = Signal(str)

    # Default accent color (deep Fluent blue) 默认主题色：沉稳深蓝
    # 选用 #0E5A9C 的依据：白字对比度 7.09 达 WCAG AAA 级，浅色背景上比 #0078D4 更沉稳不刺眼，
    # 且与库内图表/Confetti 的 Fluent 蓝同色系统一。
    DEFAULT_ACCENT = "#0e5a9c"

    # Color variant factors 颜色变体系数
    LIGHTEN_FACTOR = 1.1  # Hover state lightening factor 悬停状态变亮系数
    DARKEN_FACTOR = 0.85  # Pressed state darkening factor 按下状态变暗系数

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._theme = Theme.LIGHT
        self._skin = Skin.FLUENT
        self._accent_color = self.DEFAULT_ACCENT
        self._accent_color_light = self._lighten_color(self._accent_color, self.LIGHTEN_FACTOR)
        self._accent_color_dark = self._darken_color(self._accent_color, self.DARKEN_FACTOR)
        self._initialized = True

    # ==================== 主题属性 ====================

    @Property(str, notify=themeChanged)
    def theme(self) -> str:
        """当前主题（light/dark/auto）"""
        return self._theme.value

    @Property(bool, notify=themeChanged)
    def isDark(self) -> bool:
        """是否为深色主题"""
        if self._theme == Theme.AUTO:
            # Detect system theme 检测系统主题
            try:
                from PySide6.QtWidgets import QApplication

                app = QApplication.instance()
                if app:
                    palette = app.palette()
                    return palette.window().color().lightness() < 128
            except (ImportError, AttributeError, RuntimeError):
                # System theme detection failed, default to light 系统主题检测失败
                pass
            return False
        return self._theme == Theme.DARK

    def setTheme(self, theme: Theme):
        """设置主题"""
        if self._theme != theme:
            self._theme = theme
            self.themeChanged.emit(theme.value)

    def getTheme(self) -> Theme:
        """获取当前主题枚举"""
        return self._theme

    @Slot()
    def toggleTheme(self):
        """切换深色/浅色主题（用于QML调用）"""
        if self._theme == Theme.DARK:
            self.setTheme(Theme.LIGHT)
        else:
            self.setTheme(Theme.DARK)

    @Slot(str)
    def setThemeFromQml(self, theme_str: str):
        """
        从QML设置主题（Slot方法）

        Args:
            theme_str: 主题字符串 "light"/"dark"/"auto"
        """
        theme_map = {"light": Theme.LIGHT, "dark": Theme.DARK, "auto": Theme.AUTO}
        theme = theme_map.get(theme_str.lower(), Theme.LIGHT)
        self.setTheme(theme)

    # ==================== 皮肤属性 ====================

    @Property(str, notify=skinChanged)
    def skin(self) -> str:
        """当前皮肤（fluent/neobrutalism）"""
        return self._skin.value

    def setSkin(self, skin: Skin):
        """设置皮肤（设计语言）"""
        if self._skin != skin:
            self._skin = skin
            self.skinChanged.emit(skin.value)

    def getSkin(self) -> Skin:
        """获取当前皮肤枚举"""
        return self._skin

    @Slot(str)
    def setSkinFromQml(self, skin_str: str):
        """从QML设置皮肤（Slot方法）

        Args:
            skin_str: 皮肤字符串 "fluent"/"neobrutalism"
        """
        skin_map = {"fluent": Skin.FLUENT, "neobrutalism": Skin.NEOBRUTALISM}
        skin = skin_map.get(skin_str.lower(), Skin.FLUENT)
        self.setSkin(skin)

    # ==================== 字体属性 ====================

    # 全平台字体 fallback 链: Windows → macOS/iOS → Android → Linux → 中文 → 通用兜底
    # Cross-platform font fallback: Windows → macOS/iOS → Android → Linux → CJK → generic
    FONT_FAMILY = (
        "Segoe UI Variable, Segoe UI, "        # Windows
        "-apple-system, PingFang SC, "          # macOS / iOS
        "Roboto, Noto Sans CJK SC, "            # Android / Linux
        "Microsoft YaHei UI, "                  # Windows 中文
        "sans-serif"                            # 通用兜底
    )
    FONT_MONOSPACE = (
        "Cascadia Code, Consolas, "             # Windows
        "SF Mono, Menlo, "                      # macOS / iOS
        "Roboto Mono, "                         # Android
        "monospace"                             # 通用兜底
    )

    @Property(str, constant=True)
    def fontFamily(self) -> str:
        """主字体"""
        return self.FONT_FAMILY

    @Property(str, constant=True)
    def fontMonospace(self) -> str:
        """等宽字体"""
        return self.FONT_MONOSPACE

    # ==================== 主题色属性 ====================

    @Property(str, notify=accentColorChanged)
    def accentColor(self) -> str:
        """主题色（HEX格式）"""
        return self._accent_color

    @Property(str, notify=accentColorChanged)
    def accentColorLight(self) -> str:
        """主题色亮色变体（hover状态）Accent color light variant (hover state)"""
        return self._accent_color_light

    @Property(str, notify=accentColorChanged)
    def accentColorDark(self) -> str:
        """主题色暗色变体（pressed状态）Accent color dark variant (pressed state)"""
        return self._accent_color_dark

    @Slot(str)
    def setAccentColor(self, color: str):
        """
        设置主题色

        Args:
            color: HEX颜色值，如 "#0078d4" 或 "#107c10"
        """
        # Validate color format 验证颜色格式
        if not color.startswith("#") or len(color) not in (4, 7, 9):
            raise ValueError(f"无效的颜色格式: {color}，请使用HEX格式如 #0078d4")

        if self._accent_color != color:
            self._accent_color = color
            # Pre-calculate variants cache 当颜色变化时直接更新对应的派生颜色缓存
            self._accent_color_light = self._lighten_color(color, self.LIGHTEN_FACTOR)
            self._accent_color_dark = self._darken_color(color, self.DARKEN_FACTOR)
            self.accentColorChanged.emit(color)

    def getAccentColor(self) -> str:
        """获取当前主题色"""
        return self._accent_color

    # ==================== 颜色工具方法 ====================

    def _lighten_color(self, hex_color: str, factor: float) -> str:
        """颜色变亮"""
        color = QColor(hex_color)
        h, s, l, a = color.getHslF()
        l = min(1.0, l * factor)
        color.setHslF(h, s, l, a)
        return color.name()

    def _darken_color(self, hex_color: str, factor: float) -> str:
        """颜色变暗"""
        color = QColor(hex_color)
        h, s, l, a = color.getHslF()
        l = max(0.0, l * factor)
        color.setHslF(h, s, l, a)
        return color.name()


# ==================== 全局函数 ====================


def setTheme(theme: Theme):
    """设置主题"""
    ThemeManager().setTheme(theme)


def getTheme() -> Theme:
    """获取当前主题"""
    return ThemeManager().getTheme()


def setSkin(skin: Skin):
    """设置皮肤（设计语言）

    Args:
        skin: Skin.FLUENT 或 Skin.NEOBRUTALISM

    示例:
        setSkin(Skin.NEOBRUTALISM)  # 切到新粗野皮肤
    """
    ThemeManager().setSkin(skin)


def getSkin() -> Skin:
    """获取当前皮肤"""
    return ThemeManager().getSkin()


def isDark() -> bool:
    """是否为深色主题"""
    return ThemeManager().isDark


def setAccentColor(color: str):
    """
    设置主题色

    Args:
        color: HEX颜色值，如 "#0078d4" 或 "#107c10"

    示例:
        setAccentColor("#0078d4")  # FluentQML 默认 Fluent 蓝
        setAccentColor("#0078d4")  # Microsoft Fluent蓝
    """
    ThemeManager().setAccentColor(color)


def getAccentColor() -> str:
    """获取当前主题色"""
    return ThemeManager().getAccentColor()


def accentQColor() -> QColor:
    """
    获取当前主题色（QColor对象）

    Returns:
        QColor: 当前主题色
    """
    color_str = ThemeManager().getAccentColor()
    return QColor(color_str)


def getThemeManager() -> ThemeManager:
    """获取主题管理器实例"""
    return ThemeManager()
