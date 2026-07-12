# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Validate the fixed local style data contract. 验证固定局部样式数据契约。"""

from __future__ import annotations

import re

if __package__:
    from .qml_lexer import sanitize_qml
else:
    from qml_lexer import sanitize_qml


THEME_NAME_PATTERN = r"[A-Za-z][A-Za-z0-9_-]*"
HEX_COLOR_PATTERN = r"#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})"
THEME_ENTRY_PATTERN = (
    rf'"{THEME_NAME_PATTERN}"\s*:\s*\{{\s*'
    rf'main\s*:\s*"{HEX_COLOR_PATTERN}"\s*,\s*'
    rf'head\s*:\s*"{HEX_COLOR_PATTERN}"\s*,\s*'
    rf'bg\s*:\s*"{HEX_COLOR_PATTERN}"\s*\}}'
)
DATA_STRUCTURE_RE = re.compile(
    rf"^\s*\.pragma\s+library\s+"
    rf"var\s+themes\s*=\s*\{{\s*"
    rf"(?P<themes>{THEME_ENTRY_PATTERN}"
    rf"(?:\s*,\s*{THEME_ENTRY_PATTERN})*\s*,?)"
    rf"\s*\}}\s*"
    rf"var\s+themeNames\s*=\s*\[\s*"
    rf'(?P<names>"{THEME_NAME_PATTERN}"'
    rf'(?:\s*,\s*"{THEME_NAME_PATTERN}")*\s*,?)'
    rf"\s*\]\s*$",
    re.DOTALL,
)
THEME_ENTRY_NAME_RE = re.compile(rf'"(?P<name>{THEME_NAME_PATTERN})"\s*:')
THEME_NAME_RE = re.compile(rf'"(?P<name>{THEME_NAME_PATTERN})"')


def _names(pattern: re.Pattern[str], text: str) -> list[str]:
    return [item.group("name") for item in pattern.finditer(text)]


def local_style_contract_error(text: str) -> str | None:
    """Return the contract error or None. 返回契约错误或空值。"""
    sanitized = sanitize_qml(text, mask_strings=False)
    match = DATA_STRUCTURE_RE.fullmatch(sanitized)
    if match is None:
        return "local style data contains unsupported structure"
    theme_names = _names(THEME_ENTRY_NAME_RE, match.group("themes"))
    listed_names = _names(THEME_NAME_RE, match.group("names"))
    if theme_names == listed_names and len(theme_names) == len(set(theme_names)):
        return None
    return "local style themeNames must match themes order"
