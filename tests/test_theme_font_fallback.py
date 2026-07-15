# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Theme font fallback regressions. 主题字体兜底回归。"""

import pytest
from PySide6.QtGui import QFontDatabase

from prismqml.python.core.theme import ThemeManager


@pytest.mark.parametrize(
    ("fallback_name", "cache_attr", "system_role"),
    (
        (
            "sans-serif",
            "_resolved_font_family",
            QFontDatabase.SystemFont.GeneralFont,
        ),
        (
            "monospace",
            "_resolved_font_monospace",
            QFontDatabase.SystemFont.FixedFont,
        ),
    ),
)
def test_missing_named_fonts_resolve_to_qt_system_family(
    qapp, monkeypatch, fallback_name, cache_attr, system_role
):
    monkeypatch.setattr(ThemeManager, cache_attr, None)
    fallback_chain = f"Definitely Missing Prism Font, {fallback_name}"

    resolved = ThemeManager._resolve_qt_font_family(fallback_chain, cache_attr)

    assert resolved == QFontDatabase.systemFont(system_role).family()
    assert getattr(ThemeManager, cache_attr) == resolved
