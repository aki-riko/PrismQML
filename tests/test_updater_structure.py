# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Updater module structure gates. Updater 模块结构门禁。"""

from __future__ import annotations

import ast
import os
from pathlib import Path
import subprocess
import sys

from prismqml.python.core import (
    _updater_download,
    _updater_install,
    _updater_release,
    updater,
)


_MAX_FILE_LINES = 499
_MAX_FUNCTION_LINES = 30
_MODULES = (updater, _updater_download, _updater_install, _updater_release)
_ROOT = Path(__file__).resolve().parents[1]
_SUBPROCESS_TIMEOUT_SECONDS = 30


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


def test_default_updater_keeps_dual_slot_runtime_lazy():
    script = """
import sys
from PySide6.QtCore import QCoreApplication
import prismqml
from prismqml import Updater

app = QCoreApplication([])
default = Updater("owner/repo", prismqml.__version__)
slot_module = "prismqml.python.core.update_slots"
install_module = "prismqml.python.core._updater_install"
download_module = "prismqml.python.core._updater_download"
default_is_lazy = (
    slot_module not in sys.modules
    and install_module not in sys.modules
    and download_module not in sys.modules
    and default._slot_preparation is None
)
dual = Updater(
    "owner/repo", prismqml.__version__, install_strategy="dual_slot"
)
dual_is_ready = (
    slot_module in sys.modules
    and install_module in sys.modules
    and download_module not in sys.modules
    and dual._slot_preparation is not None
)
raise SystemExit(0 if default_is_lazy and dual_is_ready else 2)
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=os.fspath(_ROOT),
        capture_output=True,
        text=True,
        timeout=_SUBPROCESS_TIMEOUT_SECONDS,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
