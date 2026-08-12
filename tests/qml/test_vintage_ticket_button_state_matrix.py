# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Vintage ticket button and toggle state matrix. 复古票据按钮与切换状态矩阵。"""

from PySide6.QtCore import QObject
from PySide6.QtGui import QColor

from prismqml import Theme, setTheme

from _vintage_ticket_state_support import (
    PALETTES,
    _alpha,
    _color,
    _darker,
    _lighter,
    _pump,
    _set_button,
    _settle_colors,
    _transparent,
    _variant_list,
    ticket_scene,
)


def test_ticket_button_all_styles_and_states(ticket_scene):
    root, warnings = ticket_scene
    styles = dict(zip(
        ("default", "primary", "transparent", "filled", "text", "hyperlink", "gradient"),
        _variant_list(root.property("buttonStyles")),
    ))
    flat = {"transparent", "text", "hyperlink"}
    for theme, palette in PALETTES.items():
        setTheme(theme)
        _pump()
        transparent = _transparent(palette["muted"])
        idle_bg = {
            "default": _color(palette["surface"]), "primary": _color(palette["primary"]),
            "transparent": transparent, "filled": _color(palette["danger"]),
            "text": transparent, "hyperlink": transparent, "gradient": _color(palette["primary"]),
        }
        hover_bg = dict(idle_bg)
        hover_bg.update(default=_color(palette["muted"]), primary=_lighter(palette["primary"], 110),
                        transparent=_color(palette["muted"]), filled=_lighter(palette["danger"], 112),
                        text=_color(palette["muted"]), hyperlink=_color(palette["muted"]),
                        gradient=_lighter(palette["primary"], 110))
        pressed_bg = dict(idle_bg)
        pressed_bg.update(default=_darker(palette["muted"], 106), primary=_darker(palette["primary"], 110),
                          transparent=_darker(palette["muted"], 106), filled=_darker(palette["danger"], 112),
                          text=_darker(palette["muted"], 106), hyperlink=_darker(palette["muted"], 106),
                          gradient=_darker(palette["primary"], 110))
        disabled_bg = {
            "default": _color(palette["muted"]), "primary": _color(palette["divider"]),
            "transparent": transparent, "filled": _alpha(palette["danger"], 0.45),
            "text": transparent, "hyperlink": transparent, "gradient": _color(palette["muted"]),
        }
        idle_text = {
            "default": palette["foreground"], "primary": palette["primary_foreground"],
            "transparent": palette["foreground"], "filled": palette["primary_foreground"],
            "text": palette["danger"], "hyperlink": palette["primary"],
            "gradient": palette["primary_foreground"],
        }
        hover_text = dict(idle_text)
        hover_text.update(text=_lighter(palette["danger"], 110), hyperlink=_lighter(palette["primary"], 110))
        pressed_text = dict(idle_text)
        pressed_text.update(default=palette["secondary"], transparent=palette["secondary"],
                            text=_darker(palette["danger"], 120), hyperlink=_darker(palette["primary"], 120))
        disabled_text = {
            name: palette["secondary"] if name in {"primary", "filled", "gradient"}
            else palette["disabled"] for name in styles
        }
        for name, style in styles.items():
            for state, bg_map, text_map, values in (
                ("idle", idle_bg, idle_text, {}),
                ("hover", hover_bg, hover_text, {"buttonHovered": True}),
                ("pressed", pressed_bg, pressed_text, {"buttonPressed": True}),
                ("disabled", disabled_bg, disabled_text, {"buttonEnabled": False}),
                ("loading", disabled_bg, disabled_text, {"buttonLoading": True}),
            ):
                _set_button(root, style, **values)
                assert _color(root.property("buttonBackground")) == _color(bg_map[name]), (theme, name, state)
                assert _color(root.property("buttonText")) == _color(text_map[name]), (theme, name, state)
                expected_border = QColor("transparent") if name in flat else _color(palette["border"])
                assert _color(root.property("buttonBorder")) == expected_border, (theme, name, state)
    assert warnings == []


def test_ticket_button_checked_states_keep_ticket_colors(ticket_scene):
    root, warnings = ticket_scene
    styles = dict(zip(
        ("default", "primary", "transparent", "filled", "text", "hyperlink", "gradient"),
        _variant_list(root.property("buttonStyles")),
    ))
    for theme, palette in PALETTES.items():
        setTheme(theme)
        _pump()
        for name, style in styles.items():
            primary_style = name == "primary"
            for state, values in (
                ("checked", {}), ("hover", {"buttonHovered": True}),
                ("pressed", {"buttonPressed": True}), ("disabled", {"buttonEnabled": False}),
            ):
                _set_button(root, style, buttonChecked=True, **values)
                if state == "disabled":
                    expected_bg = palette["muted"]
                    expected_text = palette["disabled"] if primary_style else palette["secondary"]
                elif primary_style:
                    expected_bg = palette["surface"] if state == "checked" else (
                        palette["muted"] if state == "hover" else _darker(palette["muted"], 106)
                    )
                    expected_text = palette["primary"]
                else:
                    expected_bg = palette["primary"] if state == "checked" else (
                        _lighter(palette["primary"], 110) if state == "hover" else _darker(palette["primary"], 110)
                    )
                    expected_text = palette["foreground"] if state == "pressed" else palette["primary_foreground"]
                assert _color(root.property("buttonBackground")) == _color(expected_bg), (theme, name, state)
                assert _color(root.property("buttonText")) == _color(expected_text), (theme, name, state)
    assert warnings == []


def test_ticket_filled_button_preserves_every_semantic_level(ticket_scene):
    root, warnings = ticket_scene
    filled_style = _variant_list(root.property("buttonStyles"))[3]
    levels = _variant_list(root.property("statusLevels"))
    for theme, palette in PALETTES.items():
        setTheme(theme)
        _pump()
        expected = (
            palette["info"], palette["success"], palette["warning"],
            palette["danger"], palette["primary"], palette["primary"],
        )
        for level, base_color in zip(levels, expected):
            for state, values, expected_color in (
                ("idle", {}, _color(base_color)),
                ("hover", {"buttonHovered": True}, _lighter(base_color, 112)),
                ("pressed", {"buttonPressed": True}, _darker(base_color, 112)),
                ("disabled", {"buttonEnabled": False}, _alpha(base_color, 0.45)),
                ("loading", {"buttonLoading": True}, _alpha(base_color, 0.45)),
            ):
                _set_button(
                    root,
                    filled_style,
                    buttonLevel=level,
                    **values,
                )
                assert _color(root.property("buttonBackground")) == expected_color, (
                    theme,
                    level,
                    state,
                )
                assert _color(root.property("buttonBorder")) == _color(palette["border"])
    assert warnings == []


def test_ticket_toggle_state_matrix_and_dark_text(ticket_scene):
    root, warnings = ticket_scene
    check = root.findChild(QObject, "checkIndicator")
    radio = root.findChild(QObject, "radioIndicator")
    switch = root.findChild(QObject, "switchIndicator")
    assert check is not None and radio is not None and switch is not None
    for theme, palette in PALETTES.items():
        setTheme(theme)
        _pump()
        assert _color(root.property("toggleText")) == _color(palette["foreground"])
        for indicator in (check, radio):
            indicator.setProperty("enabled", True)
            indicator.setProperty("hovered", False)
            indicator.setProperty("pressed", False)
            if indicator is check:
                indicator.setProperty("checkState", 0)
            else:
                indicator.setProperty("checked", False)
            _settle_colors()
            assert _color(indicator.property("color")) == _color(palette["surface"])
            indicator.setProperty("hovered", True)
            _settle_colors()
            assert _color(indicator.property("color")) == _color(palette["muted"])
            indicator.setProperty("hovered", False)
            indicator.setProperty("pressed", True)
            _settle_colors()
            assert _color(indicator.property("color")) == _darker(palette["muted"], 106)
            indicator.setProperty("pressed", False)
            if indicator is check:
                indicator.setProperty("checkState", 2)
            else:
                indicator.setProperty("checked", True)
            _settle_colors()
            assert _color(indicator.property("color")) == _color(palette["primary"])
            indicator.setProperty("enabled", False)
            _settle_colors()
            assert _color(indicator.property("color")) == _color(palette["divider"])
        switch.setProperty("enabled", True)
        switch.setProperty("checked", False)
        switch.setProperty("hovered", True)
        switch.setProperty("pressed", True)
        _settle_colors()
        assert _color(switch.property("_trackColor")) == _color(palette["surface"])
        switch.setProperty("checked", True)
        _settle_colors()
        assert _color(switch.property("_trackColor")) == _color(palette["primary"])
        switch.setProperty("enabled", False)
        _settle_colors()
        assert _color(switch.property("_trackColor")) == _color(palette["divider"])
    assert warnings == []
