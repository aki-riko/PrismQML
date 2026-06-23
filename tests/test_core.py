# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
"""
FluentQML 核心模块单元测试

覆盖：
- ThemeManager（主题系统）
- Store（响应式状态存储）
- IconProvider（图标提供器）
- WindowType（窗口类型枚举）
- _escape_qml（QML 安全转义）
"""

import pytest


# ==================== ThemeManager 测试 ====================


class TestThemeManager:
    """主题管理器测试"""

    def setup_method(self):
        """每个测试方法前重置单例"""
        from prismqml.python.core.theme import ThemeManager

        ThemeManager._instance = None

    def test_singleton(self):
        """单例模式应返回同一实例"""
        from prismqml.python.core.theme import ThemeManager

        a = ThemeManager()
        b = ThemeManager()
        assert a is b

    def test_default_theme_is_light(self):
        """默认主题应为 light"""
        from prismqml.python.core.theme import ThemeManager, Theme

        tm = ThemeManager()
        assert tm.getTheme() == Theme.LIGHT
        assert tm.isDark is False

    def test_set_theme(self):
        """设置主题应生效"""
        from prismqml.python.core.theme import ThemeManager, Theme

        tm = ThemeManager()
        tm.setTheme(Theme.DARK)
        assert tm.getTheme() == Theme.DARK
        assert tm.isDark is True

    def test_set_theme_from_qml(self):
        """从 QML 侧设置主题字符串"""
        from prismqml.python.core.theme import ThemeManager, Theme

        tm = ThemeManager()
        tm.setThemeFromQml("dark")
        assert tm.getTheme() == Theme.DARK

        tm.setThemeFromQml("light")
        assert tm.getTheme() == Theme.LIGHT

        tm.setThemeFromQml("auto")
        assert tm.getTheme() == Theme.AUTO

    def test_toggle_theme(self):
        """切换主题应在 Light/Dark 之间交替"""
        from prismqml.python.core.theme import ThemeManager, Theme

        tm = ThemeManager()
        assert tm.getTheme() == Theme.LIGHT
        tm.toggleTheme()
        assert tm.getTheme() == Theme.DARK
        tm.toggleTheme()
        assert tm.getTheme() == Theme.LIGHT

    def test_default_accent_color(self):
        """默认主题色应为预设值"""
        from prismqml.python.core.theme import ThemeManager

        tm = ThemeManager()
        assert tm.getAccentColor() == ThemeManager.DEFAULT_ACCENT

    def test_set_accent_color(self):
        """设置主题色应更新 accent 和派生色"""
        from prismqml.python.core.theme import ThemeManager

        tm = ThemeManager()
        tm.setAccentColor("#ff0000")
        assert tm.getAccentColor() == "#ff0000"
        # 确保派生色也被更新
        assert tm.accentColorLight != "#ff0000"
        assert tm.accentColorDark != "#ff0000"

    def test_set_invalid_accent_color_raises(self):
        """无效的颜色格式应抛出 ValueError"""
        from prismqml.python.core.theme import ThemeManager

        tm = ThemeManager()
        with pytest.raises(ValueError):
            tm.setAccentColor("not_a_color")
        with pytest.raises(ValueError):
            tm.setAccentColor("123456")

    def test_global_functions(self):
        """全局便捷函数应正确工作"""
        from prismqml.python.core.theme import (
            setTheme,
            getTheme,
            isDark,
            setAccentColor,
            getAccentColor,
            Theme,
        )

        setTheme(Theme.DARK)
        assert getTheme() == Theme.DARK
        assert isDark() is True

        setAccentColor("#0078d4")
        assert getAccentColor() == "#0078d4"


# ==================== Store 测试 ====================


class TestStore:
    """响应式状态存储测试"""

    def test_define_and_get(self):
        """定义和获取状态"""
        from prismqml.python.state.store import Store

        store = Store("test")
        store.define("count", 0)
        assert store.get("count") == 0

    def test_set_and_get(self):
        """设置和获取状态"""
        from prismqml.python.state.store import Store

        store = Store("test")
        store.set("name", "Alice")
        assert store.get("name") == "Alice"

    def test_set_triggers_watcher(self):
        """设置值应触发 watcher 回调"""
        from prismqml.python.state.store import Store

        store = Store("test")
        store.define("count", 0)

        changes = []
        store.watch("count", lambda new, old: changes.append((new, old)))

        store.set("count", 1)
        assert changes == [(1, 0)]

        store.set("count", 5)
        assert changes == [(1, 0), (5, 1)]

    def test_same_value_no_notify(self):
        """相同值不应触发通知"""
        from prismqml.python.state.store import Store

        store = Store("test")
        store.define("x", 10)

        changes = []
        store.watch("x", lambda new, old: changes.append(True))

        store.set("x", 10)  # 值相同
        assert changes == []

    def test_unwatch(self):
        """取消监听后不应再收到通知"""
        from prismqml.python.state.store import Store

        store = Store("test")
        store.define("x", 0)

        changes = []
        unwatch = store.watch("x", lambda new, old: changes.append(True))

        store.set("x", 1)
        assert len(changes) == 1

        unwatch()  # 取消监听
        store.set("x", 2)
        assert len(changes) == 1  # 不应增加

    def test_batch_mode(self):
        """批量模式应合并通知"""
        from prismqml.python.state.store import Store

        store = Store("test")
        store.define("a", 0)
        store.define("b", 0)

        all_changes = []
        store.watch_all(lambda key, new, old: all_changes.append((key, new, old)))

        with store.batch():
            store.set("a", 1)
            store.set("b", 2)
            store.set("a", 3)  # 再次修改 a
            # 此时不应有通知
            assert all_changes == []

        # 退出 batch 后应有通知，且 a 保留最早的 old 值
        assert ("a", 3, 0) in all_changes
        assert ("b", 2, 0) in all_changes

    def test_reset(self):
        """重置应恢复默认值"""
        from prismqml.python.state.store import Store

        store = Store("test")
        store.define("theme", "light")
        store.set("theme", "dark")
        assert store.get("theme") == "dark"

        store.reset("theme")
        assert store.get("theme") == "light"

    def test_dict_syntax(self):
        """应支持字典语法"""
        from prismqml.python.state.store import Store

        store = Store("test")
        store["key"] = "value"
        assert store["key"] == "value"
        assert "key" in store

    def test_keys_and_values(self):
        """keys 和 values 方法应正常工作"""
        from prismqml.python.state.store import Store

        store = Store("test")
        store.define("a", 1)
        store.define("b", 2)
        assert set(store.keys()) == {"a", "b"}
        assert store.values() == {"a": 1, "b": 2}


# ==================== WindowType 测试 ====================


class TestWindowType:
    """窗口类型枚举测试"""

    def test_intenum_values(self):
        """IntEnum 值应正确"""
        from prismqml.python.window.fluent_window import WindowType

        assert WindowType.SPLIT == 0
        assert WindowType.BAR == 1
        assert WindowType.FILLED == 2

    def test_intenum_type(self):
        """WindowType 应为 IntEnum 实例"""
        from enum import IntEnum
        from prismqml.python.window.fluent_window import WindowType

        assert issubclass(WindowType, IntEnum)

    def test_qml_names_mapping(self):
        """QML 名称映射应覆盖所有类型"""
        from prismqml.python.window.fluent_window import WindowType
        from prismqml.python.window.window_base import _WINDOW_TYPE_QML_NAMES

        for wt in WindowType:
            assert wt in _WINDOW_TYPE_QML_NAMES


class TestIconBase:
    def test_get_icon_color_normal(self):
        """resolveIconColor 在普通模式下应返回 black/white 字符串契约。"""
        from prismqml.python.core import resolveIconColor, Theme

        assert resolveIconColor(Theme.LIGHT) == "black"
        assert resolveIconColor(Theme.DARK) == "white"

    def test_get_icon_color_reversed(self):
        """resolveIconColor reverse=True 应反转颜色。"""
        from prismqml.python.core import resolveIconColor, Theme

        assert resolveIconColor(Theme.LIGHT, reverse=True) == "white"
        assert resolveIconColor(Theme.DARK, reverse=True) == "black"

    def test_svg_engine_clone_preserves_source(self):
        """SvgRenderEngine.clone() 应保留 SVG 源串。"""
        from prismqml.python.core.icon_base import SvgRenderEngine

        engine = SvgRenderEngine("<svg/>")
        cloned = engine.clone()
        assert cloned._svgSource == "<svg/>"

    def test_fluent_engine_opacity_table(self):
        """ThemedIconProxy 按渲染模式给出弱化态不透明度。"""
        from PySide6.QtGui import QIcon

        from prismqml.python.core.icon_base import ThemedIconProxy

        assert ThemedIconProxy._state_alpha(QIcon.Disabled) == 0.5
        assert ThemedIconProxy._state_alpha(QIcon.Selected) == 0.7
        assert ThemedIconProxy._state_alpha(QIcon.Normal) == 1.0

    def test_fluent_engine_field_names(self):
        """ThemedIconProxy 内部字段名为 _iconSource/_invertTheme。"""
        from prismqml.python.core.icon_base import ThemedIconProxy

        engine = ThemedIconProxy("foo.svg", reverse=True)
        assert engine._iconSource == "foo.svg"
        assert engine._invertTheme is True
        cloned = engine.clone()
        assert cloned._iconSource == "foo.svg"
        assert cloned._invertTheme is True

    def test_rewrite_svg_preserves_xmlns_and_xlink(self, tmp_path):
        """_rewrite_svg_attrs 必须保留 xmlns / xmlns:xlink 命名空间声明,
        以及 xlink:href 这种带前缀属性, 否则复杂 SVG (渐变 / use 引用) 渲染会废。"""
        from prismqml.python.core.icon_base import _rewrite_svg_attrs

        svg = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'xmlns:xlink="http://www.w3.org/1999/xlink" '
            'viewBox="0 0 24 24">'
            '<defs><linearGradient id="g"/></defs>'
            '<path d="M0 0" fill="none"/>'
            '<use xlink:href="#g"/>'
            '</svg>'
        )
        svg_file = tmp_path / "ns.svg"
        svg_file.write_text(svg, encoding="utf-8")

        out = _rewrite_svg_attrs(str(svg_file), {"fill": "#ff0000"})

        # xmlns 默认命名空间保留
        assert 'xmlns="http://www.w3.org/2000/svg"' in out
        # xmlns:xlink 前缀命名空间保留
        assert 'xmlns:xlink="http://www.w3.org/1999/xlink"' in out
        # xlink:href 带前缀属性保留
        assert 'xlink:href="#g"' in out
        # path fill 已被覆盖
        assert "#ff0000" in out
        # 输出仍是合法 XML 头, 不出现 version=""
        assert 'version=""' not in out

    def test_rewrite_svg_indexes_empty_list(self, tmp_path):
        """indexes=[] 应等价于"一个都不改", 与 indexes=None"全改"区分。"""
        from prismqml.python.core.icon_base import _rewrite_svg_attrs

        svg = (
            '<?xml version="1.0"?>'
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<path d="A" fill="none"/>'
            '<path d="B" fill="#000000"/>'
            '</svg>'
        )
        svg_file = tmp_path / "idx.svg"
        svg_file.write_text(svg, encoding="utf-8")

        out = _rewrite_svg_attrs(str(svg_file), {"fill": "#ff0000"}, only_paths=[])

        # 没命中任何 path, 原 fill 全部保留
        assert "#ff0000" not in out
        assert 'fill="none"' in out
        assert 'fill="#000000"' in out

    def test_bake_pixmap_invalid_size_returns_empty(self, qapp):
        """_bake_pixmap 对 0 尺寸或 painter 非 active 应返回空 pixmap, 不静默丢帧。

        ``qapp`` fixture 由 pytest-qt 提供, 保证 QApplication 已就绪 (QPainter
        构造需要 GUI 线程)。
        """
        from PySide6.QtCore import QSize
        from PySide6.QtGui import QIcon

        from prismqml.python.core.icon_base import (
            ThemedIconProxy,
            _bake_pixmap,
        )

        engine = ThemedIconProxy("foo.svg")
        pm = _bake_pixmap(engine, QSize(0, 0), QIcon.Normal, QIcon.Off)
        assert pm.isNull()

        pm2 = _bake_pixmap(engine, QSize(-1, 10), QIcon.Normal, QIcon.Off)
        assert pm2.isNull()

    def test_bake_pixmap_normal_size_renders_nonempty(self, qapp):
        """_bake_pixmap 正常尺寸应绘制出非空、带透明背景的 pixmap。

        覆盖正常绘制路径 (QPixmap 直接构造 + Qt.transparent 填充), 与上面的
        非法尺寸路径互补; 确保不经 QImage 中转后绘制结果仍然正确。
        """
        from PySide6.QtCore import QSize
        from PySide6.QtGui import QIcon

        from prismqml.python.core.icon_base import (
            SvgRenderEngine,
            _bake_pixmap,
        )

        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48">'
            '<rect x="8" y="8" width="32" height="32" fill="#000000"/></svg>'
        )
        engine = SvgRenderEngine(svg)
        pm = _bake_pixmap(engine, QSize(48, 48), QIcon.Normal, QIcon.Off)

        assert not pm.isNull()
        assert pm.width() == 48 and pm.height() == 48
        assert pm.hasAlphaChannel()

        img = pm.toImage()
        # 四角应保持透明背景 (fill(Qt.transparent) 生效)
        assert img.pixelColor(0, 0).alpha() == 0
        # 中心矩形已绘制 -> 非透明
        assert img.pixelColor(24, 24).alpha() > 0


class TestTrayTypes:
    def test_tray_enums(self):
        """测试 P2-2: 系统托盘枚举拆分结果"""
        from prismqml.python.window.tray_types import MessageIcon, ActivationReason

        assert hasattr(MessageIcon, "Information")
        assert hasattr(ActivationReason, "Context")


# ==================== _escape_qml 测试 ====================


class TestEscapeQml:
    """QML 字符串转义测试"""

    def test_normal_text_unchanged(self):
        """普通文本不应被修改"""
        from prismqml.python.window.fluent_window import WindowCore

        assert WindowCore._escape_qml("Hello World") == "Hello World"

    def test_escape_quotes(self):
        """双引号应被转义"""
        from prismqml.python.window.fluent_window import WindowCore

        assert WindowCore._escape_qml('say "hello"') == 'say \\"hello\\"'

    def test_escape_backslash(self):
        """反斜杠应被转义"""
        from prismqml.python.window.fluent_window import WindowCore

        assert WindowCore._escape_qml("a\\b") == "a\\\\b"

    def test_escape_newlines(self):
        """换行符应被转义"""
        from prismqml.python.window.fluent_window import WindowCore

        result = WindowCore._escape_qml("line1\nline2\r\n")
        assert "\\n" in result
        assert "\\r" in result

    def test_escape_combined(self):
        """组合特殊字符都应被正确转义"""
        from prismqml.python.window.fluent_window import WindowCore

        input_str = 'path "C:\\Users"\nend'
        result = WindowCore._escape_qml(input_str)
        assert '\\"' in result
        assert "\\\\" in result
        assert "\\n" in result
