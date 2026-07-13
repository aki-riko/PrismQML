# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Window builder fallback-boundary regressions. 窗口构建回退边界回归。"""

from pathlib import Path
from types import SimpleNamespace

import pytest


def test_generated_qml_helpers_empty_collections():
    from prismqml.python.window._window_builder import WindowBuilderMixin

    builder = WindowBuilderMixin()
    builder._nav_items = []
    builder._bottom_nav_items = []

    assert builder._render_navigation_items_qml() == ""
    assert builder._render_bottom_items_qml() == ""
    assert builder._render_page_containers_qml() == ""


def test_generated_qml_helpers_render_navigation_contract():
    from prismqml.python.window._window_builder import WindowBuilderMixin

    builder = WindowBuilderMixin()
    builder._resolve_icon_path = lambda name: f"icon://{name}"
    builder._nav_items = [
        SimpleNamespace(text='Top "one"', icon="home"),
        SimpleNamespace(text="Top two", icon="settings"),
    ]
    builder._bottom_nav_items = [
        SimpleNamespace(text="Default", icon="info"),
        SimpleNamespace(text="Action", icon="run", selectable=False),
    ]

    top = builder._render_navigation_items_qml()
    bottom = builder._render_bottom_items_qml()

    assert top == (
        '{ "text": "Top \\"one\\"", "icon": "icon://home" }, '
        '{ "text": "Top two", "icon": "icon://settings" }'
    )
    assert bottom == (
        '{ "text": "Default", "icon": "icon://info", '
        '"key": "page_2", "selectable": true }, '
        '{ "text": "Action", "icon": "icon://run", '
        '"key": "page_3", "selectable": false }'
    )


def test_generated_page_containers_keep_structure():
    from prismqml.python.window._window_builder import WindowBuilderMixin

    builder = WindowBuilderMixin()
    builder._nav_items = [object()]
    builder._bottom_nav_items = [object(), object()]

    pages = builder._render_page_containers_qml()

    assert pages.startswith("\n        Item {")
    assert pages.endswith("        }")
    assert pages.count('objectName: "page_') == 3
    assert [pages.index(f'objectName: "page_{i}"') for i in range(3)] == sorted(
        pages.index(f'objectName: "page_{i}"') for i in range(3)
    )
    assert pages.count("width: parent ? parent.width : 0") == 3
    assert pages.count("height: parent ? parent.height : 0") == 3


def test_window_template_preserves_dollar_values_and_boolean_literals():
    from prismqml.python.window._window_builder import WindowBuilderMixin

    builder = WindowBuilderMixin()
    builder._width = 640
    builder._height = 480
    builder._title = 'Dollar $HOME "quoted" {brace}\nline'
    builder._icon_colored = True

    source = builder._render_window_qml(
        Path("D:/Qml$Root"),
        "WindowsBar",
        "file:///D:/icon$1.svg",
        False,
        True,
        '{"text": "$nav"}',
        '{"text": "$bottom"}',
        "\n        Item {}",
    )

    assert 'import "file:///D:/Qml$Root"' in source
    assert 'windowTitle: "Dollar $HOME \\"quoted\\" \\u007Bbrace\\u007D\\nline"' in source
    assert 'windowIcon: "file:///D:/icon$1.svg"' in source
    assert "windowIconColored: true" in source
    assert "startupProfilingVerbose: false" in source
    assert "micaEnabled: true\n    \n" in source
    assert 'navigationItems: [{"text": "$nav"}]' in source
    assert source.endswith("}\n")


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_generated_window_file_boundary_process_control_propagates(
    monkeypatch, error_type
):
    from prismqml.python.window._window_builder import WindowBuilderMixin

    def stop_load(_self, _qml, _component, _profile, _verbose):
        raise error_type("stop")

    monkeypatch.setattr(
        WindowBuilderMixin,
        "_load_generated_window_component",
        stop_load,
    )
    builder = WindowBuilderMixin()
    with pytest.raises(error_type, match="stop"):
        builder._load_generated_window_boundary("", "", lambda _label: None, False)
