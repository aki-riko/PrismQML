# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Test runner command identity regressions. 测试 runner 命令身份回归。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import scripts.test_process as test_process_module
from scripts.test_process import _normalize_child_command


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "test_process.py"


def _run_runner(*arguments: str):
    return subprocess.run(
        [sys.executable, str(RUNNER), *arguments],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )


def _normalized_path(path: str) -> str:
    return os.path.normcase(os.path.abspath(path))


@pytest.mark.parametrize("alias", ("python", "python.exe"))
def test_generic_python_alias_uses_launcher_interpreter(monkeypatch, alias):
    launcher = r"C:\Program Files\Prism Python\python.exe"
    monkeypatch.setattr(test_process_module.sys, "executable", launcher)

    assert _normalize_child_command((alias, "-V")) == (launcher, "-V")


@pytest.mark.parametrize(
    "executable",
    (
        "python3",
        "python3.12",
        "py",
        "pythonw.exe",
        "PYTHON",
        r".\python.exe",
        "/usr/bin/python",
        r"C:\Tools\Python\python.exe",
    ),
)
def test_non_generic_python_command_is_preserved(executable):
    assert _normalize_child_command((executable, "-V")) == (executable, "-V")


def test_child_command_normalization_fails_closed(monkeypatch):
    with pytest.raises(ValueError, match="child command is empty"):
        _normalize_child_command(())

    monkeypatch.setattr(test_process_module.sys, "executable", "")
    with pytest.raises(RuntimeError, match="Python executable is unavailable"):
        _normalize_child_command(("python", "-V"))


def test_runner_generic_python_preserves_environment_identity():
    code = (
        "import json, sys; "
        "print(json.dumps({'executable': sys.executable, 'prefix': sys.prefix, "
        "'base_prefix': sys.base_prefix}))"
    )

    result = _run_runner("--", "python", "-c", code)

    assert result.returncode == 0, result.stdout + result.stderr
    child = json.loads(result.stdout)
    assert _normalized_path(child["executable"]) == _normalized_path(sys.executable)
    assert _normalized_path(child["prefix"]) == _normalized_path(sys.prefix)
    assert _normalized_path(child["base_prefix"]) == _normalized_path(sys.base_prefix)
