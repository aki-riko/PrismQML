# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Updater module structure gates. Updater 模块结构门禁。"""

from __future__ import annotations

import ast
from pathlib import Path

from prismqml.python.core import (
    _updater_download,
    _updater_install,
    _updater_release,
    updater,
)


_MAX_FILE_LINES = 499
_MAX_FUNCTION_LINES = 30
_MODULES = (updater, _updater_download, _updater_install, _updater_release)


def _module_functions(path: Path):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path), feature_version=(3, 9))
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    return source, functions


def test_updater_modules_stay_within_structure_budget():
    for module in _MODULES:
        path = Path(module.__file__).resolve()
        source, functions = _module_functions(path)
        offenders = [
            (node.name, node.end_lineno - node.lineno + 1)
            for node in functions
            if node.end_lineno - node.lineno + 1 > _MAX_FUNCTION_LINES
        ]

        assert len(source.splitlines()) <= _MAX_FILE_LINES, path
        assert offenders == [], (path, offenders)
