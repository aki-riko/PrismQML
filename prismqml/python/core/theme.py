# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""
PrismQML 主题系统

支持功能：
- 深色/浅色/自动主题切换
- 自定义主题色（accentColor）
- QML属性绑定（自动通知更新）
"""

from enum import Enum
import re
from typing import Callable, Optional

from PySide6.QtCore import QObject, Signal, Property, Slot
from PySide6.QtGui import QColor

from .appearance_defaults import DEFAULT_ACCENT as _DEFAULT_ACCENT
from .logger import debug


_HEX_COLOR_PATTERN = re.compile(
    r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{5})?"
)
_appearance_persistence: Optional[Callable[[str, str], None]] = None


def _bind_appearance_persistence(
    callback: Optional[Callable[[str, str], None]]
) -> None:
    """Bind the outer persistence port. 绑定外层持久化端口。"""
    global _appearance_persistence
    _appearance_persistence = callback


def _request_appearance_persistence(field: str, value: str) -> bool:
    """Forward a mutation when persistence is installed. 持久化已装配时转发修改。"""
    if _appearance_persistence is None:
        return False
    _appearance_persistence(field, value)
    return True


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
    vintage_ticket → 复古票据（暖纸、油墨细线、印章语义色）
    neumorphism → 新拟态（同色表面、双向软阴影、凹凸压按）
    """

    FLUENT = "fluent"
    NEOBRUTALISM = "neobrutalism"
    VINTAGE_TICKET = "vintage_ticket"
    NEUMORPHISM = "neumorphism"


class ThemeManager(QObject):
    """
    主题管理器（单例）

    功能：
    - 主题切换（Light/Dark/Auto）
    - 主题色管理（可自定义）
    - QML属性绑定支持

    使用示例：
        # Python端
        from prismqml import setTheme, setAccentColor, Theme
        setTheme(Theme.DARK)
        setAccentColor("#0078d4")  # PrismQML 默认 Fluent 蓝

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
    DEFAULT_ACCENT = _DEFAULT_ACCENT

    # Color variant factors 颜色变体系数
    LIGHTEN_FACTOR = 1.1  # Hover state lightening factor 悬停状态变亮系数
    DARKEN_FACTOR = 0.85  # Pressed state darkening factor 按下状态变暗系数

    _instance = None
    _resolved_font_family = None
    _resolved_font_monospace = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._theme = Theme.AUTO
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
            except (ImportError, AttributeError, RuntimeError) as exc:
                # System theme detection failed, default to light 系统主题检测失败
                debug(f"系统主题检测失败,默认使用浅色: {exc}")
            return False
        return self._theme == Theme.DARK

    def setTheme(self, theme: Theme):
        """立即设置主题并在后台持久化。"""
        if not isinstance(theme, Theme):
            raise TypeError("theme must be a Theme")
        if not _request_appearance_persistence("theme", theme.value):
            self._apply_theme(theme)

    def _apply_theme(self, theme: Theme):
        """Apply committed runtime state without scheduling persistence."""
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

    def _apply_theme_from_qml(self, theme_str: str):
        """Apply a validated persisted theme without writing it again."""
        theme_map = {"light": Theme.LIGHT, "dark": Theme.DARK, "auto": Theme.AUTO}
        self._apply_theme(theme_map.get(theme_str.lower(), Theme.LIGHT))

    # ==================== 皮肤属性 ====================

    @Property(str, notify=skinChanged)
    def skin(self) -> str:
        """当前皮肤（fluent/neobrutalism/vintage_ticket）"""
        return self._skin.value

    def setSkin(self, skin: Skin):
        """立即设置皮肤并在后台持久化。"""
        if not isinstance(skin, Skin):
            raise TypeError("skin must be a Skin")
        if not _request_appearance_persistence("skin", skin.value):
            self._apply_skin(skin)

    def _apply_skin(self, skin: Skin):
        """Apply committed runtime state without scheduling persistence."""
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
            skin_str: 皮肤字符串 "fluent"/"neobrutalism"/"vintage_ticket"
        """
        skin_map = {
            "fluent": Skin.FLUENT,
            "neobrutalism": Skin.NEOBRUTALISM,
            "vintage_ticket": Skin.VINTAGE_TICKET,
            "neumorphism": Skin.NEUMORPHISM,
        }
        skin = skin_map.get(skin_str.lower(), Skin.FLUENT)
        self.setSkin(skin)

    def _apply_skin_from_qml(self, skin_str: str):
        """Apply a validated persisted skin without writing it again."""
        skin_map = {
            "fluent": Skin.FLUENT,
            "neobrutalism": Skin.NEOBRUTALISM,
            "vintage_ticket": Skin.VINTAGE_TICKET,
            "neumorphism": Skin.NEUMORPHISM,
        }
        self._apply_skin(skin_map.get(skin_str.lower(), Skin.FLUENT))

    # ==================== 字体属性 ====================

    # 全平台字体 fallback 链: Windows 中文 UI → Windows → macOS/iOS → Android/Linux → 通用兜底
    # Cross-platform font fallback: Windows CJK UI → Windows → macOS/iOS → Android/Linux → generic
    FONT_FAMILY = (
        "Microsoft YaHei UI, "                  # Windows 中文 UI
        "Segoe UI Variable, Segoe UI, "        # Windows
        "-apple-system, PingFang SC, "          # macOS / iOS
        "Roboto, Noto Sans CJK SC, "            # Android / Linux
        "sans-serif"                            # 通用兜底
    )
    FONT_MONOSPACE = (
        "Cascadia Code, Consolas, "             # Windows
        "SF Mono, Menlo, "                      # macOS / iOS
        "Roboto Mono, "                         # Android
        "monospace"                             # 通用兜底
    )

    @classmethod
    def _font_candidates(cls, fallback_chain: str) -> list[str]:
        return [
            candidate.strip().strip("'\"")
            for candidate in fallback_chain.split(",")
            if candidate.strip()
        ]

    @staticmethod
    def _generic_qt_font_family(candidate: str) -> str:
        from PySide6.QtGui import QFontDatabase

        system_font_roles = {
            "sans-serif": QFontDatabase.SystemFont.GeneralFont,
            "monospace": QFontDatabase.SystemFont.FixedFont,
        }
        role = system_font_roles.get(candidate.casefold())
        if role is None:
            return ""
        return QFontDatabase.systemFont(role).family()

    @classmethod
    def _cache_font_family(cls, cache_attr: str, family: str) -> str:
        setattr(cls, cache_attr, family)
        return family

    @classmethod
    def _resolve_qt_font_family(cls, fallback_chain: str, cache_attr: str) -> str:
        cached = getattr(cls, cache_attr)
        if cached:
            return cached

        candidates = cls._font_candidates(fallback_chain)
        if not candidates:
            return ""

        from PySide6.QtWidgets import QApplication

        if QApplication.instance() is None:
            return candidates[0]

        from PySide6.QtGui import QFontDatabase

        available_families = set(QFontDatabase.families())
        for candidate in candidates:
            if candidate in available_families:
                return cls._cache_font_family(cache_attr, candidate)

            generic_family = cls._generic_qt_font_family(candidate)
            if generic_family:
                return cls._cache_font_family(cache_attr, generic_family)

        system_family = QFontDatabase.systemFont(
            QFontDatabase.SystemFont.GeneralFont
        ).family()
        return cls._cache_font_family(cache_attr, system_family or candidates[0])

    @Property(str, constant=True)
    def fontFamily(self) -> str:
        """主字体"""
        return self._resolve_qt_font_family(self.FONT_FAMILY, "_resolved_font_family")

    @Property(str, constant=True)
    def fontMonospace(self) -> str:
        """等宽字体"""
        return self._resolve_qt_font_family(self.FONT_MONOSPACE, "_resolved_font_monospace")

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
        if not isinstance(color, str) or _HEX_COLOR_PATTERN.fullmatch(color) is None:
            raise ValueError(f"无效的颜色格式: {color}，请使用HEX格式如 #0078d4")
        if not _request_appearance_persistence("accent_color", color):
            self._apply_accent_color(color)

    def _apply_accent_color(self, color: str):
        """Apply a validated persisted accent without writing it again."""

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
    """设置并持久化主题"""
    ThemeManager().setTheme(theme)


def getTheme() -> Theme:
    """获取当前主题"""
    return ThemeManager().getTheme()


def setSkin(skin: Skin):
    """设置并持久化皮肤（设计语言）

    Args:
        skin: Skin.FLUENT、Skin.NEOBRUTALISM、Skin.VINTAGE_TICKET 或 Skin.NEUMORPHISM

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
        setAccentColor("#0078d4")  # PrismQML 默认 Fluent 蓝
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
