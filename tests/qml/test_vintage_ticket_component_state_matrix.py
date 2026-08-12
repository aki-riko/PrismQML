# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Vintage ticket component visual contracts. 复古票据组件视觉合同。"""

from PySide6.QtCore import QObject
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlProperty

from prismqml import Theme, setTheme

from _vintage_ticket_state_support import (
    PALETTES,
    _color,
    _darker,
    _find_type,
    _lighter,
    _pump,
    _variant_list,
    ticket_scene,
)


def test_ticket_progress_and_gray_consumers_use_runtime_ticket_tokens(ticket_scene):
    root, warnings = ticket_scene
    button = root.findChild(QObject, "buttonRing")
    assert button is not None
    ring = _find_type(button, "ProgressRing")
    for theme, palette in PALETTES.items():
        setTheme(theme)
        _pump()
        expected_track = palette["divider"] if theme == Theme.LIGHT else palette["muted"]
        assert _color(root.property("progressCoreTrack")) == _color(expected_track)
        assert _color(root.property("progressRingTrack")) == _color(expected_track)
        assert _color(ring.property("trackColor")) == _color(expected_track)
        assert _color(root.property("cropperBackground")) == _color(palette["surface"])
        assert _color(root.property("cropperBorder")) == _color(palette["border"])
        assert _color(root.property("cropperIcon")) == _color(palette["disabled"])
        assert _color(root.property("cropperText")) == _color(palette["secondary"])
        assert _color(root.property("ratingFill")) == _color(palette["warning"])
        assert _color(root.property("ratingOutline")) == _color(palette["secondary"])
        assert _color(root.property("sliderHandle")) == _color(palette["surface"])
    assert warnings == []


def test_ticket_focus_and_selected_states_use_ink_contract(ticket_scene):
    root, warnings = ticket_scene
    state_input = root.findChild(QObject, "stateInput")
    navigation_item = root.findChild(QObject, "navigationItem")
    assert state_input is not None and navigation_item is not None
    for theme, palette in PALETTES.items():
        setTheme(theme)
        state_input.setProperty("enabled", True)
        state_input.setProperty("focused", False)
        navigation_item.setProperty("selected", False)
        _pump()
        assert _color(root.property("inputBackground")) == _color(palette["surface"])
        assert _color(root.property("inputBorder")) == _color(palette["border"])
        assert _color(root.property("navigationBackground")) == QColor("transparent")
        assert _color(root.property("navigationContent")) == _color(palette["foreground"])

        state_input.setProperty("focused", True)
        navigation_item.setProperty("selected", True)
        _pump()
        assert _color(root.property("inputBackground")) == _color(palette["surface"])
        assert _color(root.property("inputBorder")) == _color(palette["primary"])
        assert _color(root.property("navigationBackground")) == _color(palette["muted"])
        assert _color(root.property("navigationBorder")) == _color(palette["border"])
        assert _color(root.property("navigationContent")) == _color(palette["primary"])

        state_input.setProperty("focused", False)
        state_input.setProperty("enabled", False)
        _pump()
        assert _color(root.property("inputBackground")) == _color(palette["muted"])
        assert _color(root.property("inputBorder")) == _color(palette["divider"])
    assert warnings == []


def test_ticket_tooltips_login_and_effects_use_ticket_visual_contract(ticket_scene):
    root, warnings = ticket_scene
    login_matrix = root.findChild(QObject, "loginMatrixRain")
    splash_icon = root.findChild(QObject, "splashIconContainer")
    boxplot_tooltip = root.findChild(QObject, "boxplotTooltip")
    chart_tooltip = root.findChild(QObject, "chartTooltip")
    assert all((login_matrix, splash_icon, boxplot_tooltip, chart_tooltip))
    for theme, palette in PALETTES.items():
        setTheme(theme)
        _pump()
        assert _color(root.property("chartTooltipBackground")) == _color(palette["surface"])
        assert _color(root.property("chartTooltipBorder")) == _color(palette["border"])
        labels = {
            child.property("text"): child
            for child in chart_tooltip.findChildren(QObject)
            if child.metaObject().indexOfProperty("text") >= 0
            and child.property("text") in {"Ticket label", "42"}
        }
        assert _color(labels["Ticket label"].property("color")) == _color(palette["secondary"])
        assert _color(labels["42"].property("color")) == _color(palette["foreground"])
        assert _color(root.property("tipBackground")) == _color(palette["surface"])
        assert _color(root.property("tipBorder")) == _color(palette["border"])
        assert _color(root.property("loginBackground")) == _color(palette["background"])
        assert login_matrix.property("visible") is False
        assert login_matrix.property("running") is False
        assert QQmlProperty(splash_icon, "layer.enabled").read() is False
        assert QQmlProperty(boxplot_tooltip, "layer.enabled").read() is False
        assert _color(root.property("matrixMain")) == _color(palette["divider"])
        assert _color(root.property("matrixHead")) == _color(palette["foreground"])
        assert _color(root.property("matrixBackground")) == _color(palette["background"])
    assert warnings == []


def test_ticket_semantic_animation_palettes_are_ticket_derived(ticket_scene):
    root, warnings = ticket_scene
    for theme, palette in PALETTES.items():
        setTheme(theme)
        _pump()
        expected_confetti = [
            _color(palette["primary"]), _lighter(palette["primary"], 130),
            _darker(palette["primary"], 120), _color(palette["primary"]),
            _color(palette["warning"]), _color(palette["danger"]),
            _color(palette["success"]), _color(palette["info"]), _color(palette["border"]),
        ]
        expected_password = [
            _color(palette["danger"]), _lighter(palette["danger"], 112),
            _color(palette["warning"]), _lighter(palette["success"], 112),
            _color(palette["success"]),
        ]
        assert [_color(value) for value in _variant_list(root.property("confettiPalette"))] == expected_confetti
        assert [_color(value) for value in _variant_list(root.property("passwordPalette"))] == expected_password
    assert warnings == []
