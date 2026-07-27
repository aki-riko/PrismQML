# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Splash configuration regressions. 启动画面配置回归。"""

from pathlib import Path
from types import SimpleNamespace

import pytest

from prismqml.python.window._splash_builder import (
    build_splash_properties,
    build_splash_template_values,
)


ROOT = Path(__file__).resolve().parents[1]


def _builder(**overrides):
    resolved = []

    def resolve_icon(value):
        resolved.append(value)
        return "qrc" + value if value.startswith(":/") else value

    values = {
        "_splash_enabled": True,
        "_splash_icon": "",
        "_splash_title": "",
        "_splash_subtitle": "",
        "_resolve_icon_path": resolve_icon,
    }
    values.update(overrides)
    builder = SimpleNamespace(**values)
    builder.resolved = resolved
    return builder


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        (
            {},
            {
                "splashEnabled": True,
                "splashIcon": "",
                "splashTitle": "",
                "splashSubtitle": "",
            },
        ),
        (
            {
                "_splash_enabled": False,
                "_splash_icon": ":/icons/splash.svg",
                "_splash_title": 'Title "quoted" {brace}\nline',
                "_splash_subtitle": "Loading",
            },
            {
                "splashEnabled": False,
                "splashIcon": "qrc:/icons/splash.svg",
                "splashTitle": 'Title "quoted" {brace}\nline',
                "splashSubtitle": "Loading",
            },
        ),
    ],
)
def test_build_splash_properties(overrides, expected):
    builder = _builder(**overrides)
    assert build_splash_properties(builder) == expected
    expected_resolved = (
        [overrides["_splash_icon"]] if overrides.get("_splash_icon") else []
    )
    assert builder.resolved == expected_resolved


def test_build_splash_template_values_escapes_strings():
    builder = _builder(
        _splash_icon=":/icon.svg",
        _splash_title='Title "quoted"',
        _splash_subtitle="Loading",
    )
    escaped = build_splash_template_values(builder, lambda value: f"<{value}>")
    assert escaped == {
        "splash_enabled": "true",
        "splash_icon": "<qrc:/icon.svg>",
        "splash_title": '<Title "quoted">',
        "splash_subtitle": "<Loading>",
    }


def test_build_splash_properties_supports_bare_window_builder():
    builder = SimpleNamespace(_resolve_icon_path=lambda value: value)
    assert build_splash_properties(builder) == {
        "splashEnabled": True,
        "splashIcon": "",
        "splashTitle": "",
        "splashSubtitle": "",
    }


def test_splash_lifecycle_is_owned_by_navigation_window_core():
    qml_source = (ROOT / "prismqml/PrismQML/NavigationWindowCore.qml").read_text(
        encoding="utf-8"
    )
    python_source = (ROOT / "prismqml/python/window/_window_builder.py").read_text(
        encoding="utf-8"
    )
    cpp_source = (ROOT / "cpp/src/Window.cpp").read_text(encoding="utf-8")
    gallery_source = (ROOT / "examples/main.qml").read_text(encoding="utf-8")

    assert "property bool splashEnabled: true" in qml_source
    assert "property int splashMinimumVisibleDuration:" in qml_source
    assert "_splashVisibleSinceMs = Date.now()" in qml_source
    assert "_splashMinimumVisibleTimer.restart()" in qml_source
    assert "property Component splashComponent:" in qml_source
    assert 'objectName: "windowSplashLoader"' in qml_source
    assert "build_splash_properties(self)" in python_source
    assert "create_splash" not in python_source
    assert "Window::createSplash" not in cpp_source
    assert "createSplash();" not in cpp_source
    assert "splashSubtitle:" in gallery_source
    assert "splashComponent.createObject" not in gallery_source
