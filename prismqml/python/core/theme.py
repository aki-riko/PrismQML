# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""
PrismQML 主题系统

支持功能：
- 深色/浅色/自动主题切换（AUTO 实时跟随系统配色方案）
- 自定义主题色（accentColor）与 WinUI 风格强调色阶
- 减少动态效果开关（reduceMotion）
- QML属性绑定（自动通知更新）
"""

from enum import Enum
import os
import re
import sys
from typing import Callable, Optional

from PySide6.QtCore import QObject, Qt, QTimer, Signal, Property, Slot
from PySide6.QtGui import QColor

from .appearance_defaults import DEFAULT_ACCENT as _DEFAULT_ACCENT
from .logger import debug, warning


_HEX_COLOR_PATTERN = re.compile(
    r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{5})?"
)
_appearance_persistence: Optional[Callable[[str, str], None]] = None

# Reduced-motion environment input. Only documented truthy/falsy spellings are
# accepted; anything else warns and falls back to "motion enabled".
# 减少动态效果的环境变量输入。仅接受文档化的真/假拼写；其他值告警并回退到"开启动效"。
REDUCE_MOTION_ENV = "PRISM_REDUCE_MOTION"
_REDUCE_MOTION_TRUTHY = frozenset({"1", "true", "yes", "on"})
_REDUCE_MOTION_FALSY = frozenset({"0", "false", "no", "off"})
_REDUCE_MOTION_DEFAULT = False

# WinUI-style accent scale steps, ordered light to dark. Each step is an HSL
# lightness delta applied to the current accent color, so the whole scale is a
# deterministic derivation instead of a second hardcoded palette.
# WinUI 风格强调色阶步进，由浅到深。每档是施加在当前强调色上的 HSL 明度增量，
# 因此整条色阶是确定性派生结果，而不是第二份硬编码调色板。
ACCENT_SCALE_STEPS = (
    ("light3", 0.30),
    ("light2", 0.20),
    ("light1", 0.10),
    ("accent", 0.0),
    ("dark1", -0.10),
    ("dark2", -0.20),
    ("dark3", -0.30),
)


def read_reduce_motion_env(raw: Optional[str] = None) -> bool:
    """Parse the reduced-motion environment input. 解析减少动态效果环境变量。

    非法值告警并回退默认值，不抛异常；空值/未设置视为未启用。
    """
    value = os.environ.get(REDUCE_MOTION_ENV) if raw is None else raw
    if value is None:
        return _REDUCE_MOTION_DEFAULT
    normalized = value.strip().casefold()
    if not normalized:
        return _REDUCE_MOTION_DEFAULT
    if normalized in _REDUCE_MOTION_TRUTHY:
        return True
    if normalized in _REDUCE_MOTION_FALSY:
        return False
    warning(
        f"{REDUCE_MOTION_ENV} 值非法: {value!r}，已回退为 {_REDUCE_MOTION_DEFAULT}"
    )
    return _REDUCE_MOTION_DEFAULT


# High-contrast environment override. Unset means "ask the platform"; the
# documented truthy/falsy spellings win over the platform answer so hosts and
# tests can pin the state deterministically.
# 高对比度环境变量覆盖。未设置表示"询问平台"；文档化的真/假拼写优先于平台结果，
# 使宿主与测试可以确定性地固定该状态。
HIGH_CONTRAST_ENV = "PRISM_HIGH_CONTRAST"
_HIGH_CONTRAST_TRUTHY = _REDUCE_MOTION_TRUTHY
_HIGH_CONTRAST_FALSY = _REDUCE_MOTION_FALSY
_SPI_GETHIGHCONTRAST = 0x0042
_HCF_HIGHCONTRASTON = 0x00000001


def read_high_contrast_env(raw: Optional[str] = None) -> Optional[bool]:
    """Parse the high-contrast override, or None when unset. 解析高对比度覆盖值。

    返回 True/False 表示显式覆盖；未设置或空值返回 None，交由平台判定。
    非法值告警并回退为未覆盖。
    """
    value = os.environ.get(HIGH_CONTRAST_ENV) if raw is None else raw
    if value is None:
        return None
    normalized = value.strip().casefold()
    if not normalized:
        return None
    if normalized in _HIGH_CONTRAST_TRUTHY:
        return True
    if normalized in _HIGH_CONTRAST_FALSY:
        return False
    warning(f"{HIGH_CONTRAST_ENV} 值非法: {value!r}，已忽略并回退平台判定")
    return None


def _read_high_contrast_flags() -> Optional[int]:
    """Read the Windows high-contrast flag word, or None when unavailable.

    返回 Windows 高对比度标志位；不可用时返回 None。
    """
    try:
        import ctypes
        from ctypes import wintypes

        class _HighContrast(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.UINT),
                ("dwFlags", wintypes.DWORD),
                ("lpszDefaultScheme", wintypes.LPWSTR),
            ]

        info = _HighContrast()
        info.cbSize = ctypes.sizeof(_HighContrast)
        succeeded = ctypes.windll.user32.SystemParametersInfoW(
            _SPI_GETHIGHCONTRAST, info.cbSize, ctypes.byref(info), 0
        )
        if not succeeded:
            debug("SystemParametersInfoW(SPI_GETHIGHCONTRAST) 调用失败，按未启用处理")
            return None
        return int(info.dwFlags)
    except (AttributeError, OSError, ValueError) as error:
        debug(f"高对比度探测失败: {error}")
        return None


def detect_high_contrast() -> bool:
    """Detect the platform high-contrast setting. 探测平台高对比度设置。

    Qt exposes no contrast signal (QStyleHints only carries the color scheme), so
    Windows is asked through SystemParametersInfoW(SPI_GETHIGHCONTRAST). Other
    platforms report False rather than guessing a value nobody can verify.
    Qt 不暴露对比度信号（QStyleHints 只有配色方案），因此 Windows 走
    SystemParametersInfoW(SPI_GETHIGHCONTRAST)。其他平台返回 False，而不是猜一个
    无法验证的值。
    """
    if sys.platform != "win32":
        return False
    flags = _read_high_contrast_flags()
    if flags is None:
        return False
    return bool(flags & _HCF_HIGHCONTRASTON)


def _shift_lightness(hex_color: str, delta: float) -> str:
    """Shift one color's HSL lightness by a clamped delta. 按限幅增量调整 HSL 明度。"""
    color = QColor(hex_color)
    h, s, l, a = color.getHslF()
    color.setHslF(h, s, max(0.0, min(1.0, l + delta)), a)
    return color.name()


def accent_scale_for(hex_color: str) -> dict:
    """Derive the WinUI-style accent scale from one accent color. 派生强调色阶。"""
    return {
        name: _shift_lightness(hex_color, delta)
        for name, delta in ACCENT_SCALE_STEPS
    }


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
    reduceMotionChanged = Signal(bool)
    highContrastChanged = Signal(bool)

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
        self._accent_scale = accent_scale_for(self._accent_color)
        self._reduce_motion = read_reduce_motion_env()
        # Read the contrast state once at construction so the property has a real
        # value before any consumer binds to it.
        # 构造时读取一次对比度状态，使属性在任何消费者绑定前就持有真实值。
        self._high_contrast = False
        self.refresh_high_contrast()
        # Platform color-scheme watch is installed lazily: the application object
        # may not exist yet when the singleton is created.
        # 平台配色方案监听延迟安装：单例创建时应用对象可能尚不存在。
        self._system_color_scheme_bound = False
        self._system_theme_notify_pending = False
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
            # Follow the platform color scheme live 实时跟随系统配色方案
            self.bind_system_theme_watch()
            return self._detect_system_dark()
        return self._theme == Theme.DARK

    def _detect_system_dark(self) -> bool:
        """Detect the system dark state for Theme.AUTO. 检测 AUTO 下的系统深色状态。"""
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

    # ==================== 系统配色方案跟随 ====================

    def _style_hints(self):
        """Return live style hints, or None without a GUI application. 返回样式提示。"""
        from PySide6.QtGui import QGuiApplication

        if QGuiApplication.instance() is None:
            return None
        return QGuiApplication.styleHints()

    def bind_system_theme_watch(self) -> bool:
        """Subscribe Theme.AUTO to the platform color scheme. 订阅平台配色方案。

        幂等；仅在 GUI 应用已存在时生效，未生效时返回 False 并留待下次调用重试。
        """
        if self._system_color_scheme_bound:
            return True
        hints = self._style_hints()
        if hints is None:
            return False
        changed = getattr(hints, "colorSchemeChanged", None)
        if changed is None:
            debug("当前 Qt 未提供 QStyleHints.colorSchemeChanged，AUTO 无法实时跟随")
            return False
        changed.connect(self._on_system_color_scheme_changed)
        self._system_color_scheme_bound = True
        return True

    def _on_system_color_scheme_changed(self, _scheme) -> None:
        """Re-notify only while Theme.AUTO owns the dark state. 仅在 AUTO 下重新通知。"""
        if self._theme != Theme.AUTO or self._system_theme_notify_pending:
            return
        self._system_theme_notify_pending = True
        # The platform palette is refreshed after this signal returns, so wait one
        # event-loop turn before re-reading the effective dark state.
        # 平台调色板在本信号返回后才刷新，因此延后一个事件循环再重读有效深色状态。
        QTimer.singleShot(0, self._emit_system_theme_changed)

    def _emit_system_theme_changed(self) -> None:
        """Notify AUTO followers once the palette settled. 调色板稳定后通知 AUTO 跟随者。"""
        self._system_theme_notify_pending = False
        if self._theme != Theme.AUTO:
            return
        # isDark is notified by themeChanged, so the existing binding contract is
        # reused instead of adding a second notify path.
        # isDark 以 themeChanged 作为通知信号，因此复用既有绑定契约而不新增通知路径。
        self.themeChanged.emit(self._theme.value)

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

    # ==================== 减少动态效果属性 ====================

    @Property(bool, notify=reduceMotionChanged)
    def reduceMotion(self) -> bool:
        """是否请求减少动态效果（只读，供 QML 绑定）"""
        return self._reduce_motion

    def set_reduce_motion(self, enabled: bool) -> None:
        """运行时切换减少动态效果（Python 公开入口）"""
        self._apply_reduce_motion(bool(enabled))

    @Slot(bool)
    def setReduceMotionFromQml(self, enabled: bool) -> None:
        """运行时切换减少动态效果（QML 调用入口）"""
        self._apply_reduce_motion(bool(enabled))

    def _apply_reduce_motion(self, enabled: bool) -> None:
        """Apply committed reduced-motion state. 提交减少动态效果状态。"""
        if self._reduce_motion != enabled:
            self._reduce_motion = enabled
            self.reduceMotionChanged.emit(enabled)

    def get_reduce_motion(self) -> bool:
        """获取当前减少动态效果状态"""
        return self._reduce_motion

    # ==================== 高对比度 ====================

    @Property(bool, notify=highContrastChanged)
    def highContrast(self) -> bool:
        """平台是否启用高对比度（只读，供 QML 绑定）"""
        return self._high_contrast

    def refresh_high_contrast(self) -> bool:
        """Re-read the platform contrast setting and notify on change. 重读并通知。

        环境变量覆盖优先，便于宿主与测试固定该状态。
        """
        override = read_high_contrast_env()
        detected = detect_high_contrast() if override is None else override
        if self._high_contrast != detected:
            self._high_contrast = detected
            self.highContrastChanged.emit(detected)
        return detected

    def get_high_contrast(self) -> bool:
        """获取当前高对比度状态"""
        return self._high_contrast

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

    @Property("QVariantMap", notify=accentColorChanged)
    def accentScale(self) -> dict:
        """WinUI 风格强调色阶 light3/light2/light1/accent/dark1/dark2/dark3"""
        return dict(self._accent_scale)

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
            self._accent_scale = accent_scale_for(color)
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


def get_accent_scale() -> dict:
    """获取当前 WinUI 风格强调色阶 light3..dark3"""
    return ThemeManager().accentScale


def is_reduce_motion() -> bool:
    """是否请求减少动态效果"""
    return ThemeManager().reduceMotion


def set_reduce_motion(enabled: bool) -> None:
    """运行时切换减少动态效果"""
    ThemeManager().set_reduce_motion(enabled)


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
