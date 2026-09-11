# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Child-command executable resolution contract for the test launcher.

测试启动器的子命令可执行文件解析契约。

Background 背景:
``CreateProcessW`` performs no ``PATH`` lookup, so a bare ``argv[0]`` such as
``pytest`` fails with ``ERROR_FILE_NOT_FOUND`` on the private test desktop.
This is the mechanism that made a Windows CI job die with
``FileNotFoundError: [WinError 2]`` before any test ran.
``CreateProcessW`` 不做 PATH 查找, 裸命令名 ``pytest`` 会在私有测试桌面上以
``ERROR_FILE_NOT_FOUND`` 失败 —— 这正是让 Windows CI 在跑测试前就报
``FileNotFoundError: [WinError 2]`` 的机制。

Resolution must not touch an explicitly named interpreter: ``python3`` / ``py`` /
``pythonw.exe`` keep the caller's identity, which
``test_test_process_command.py`` locks for ``_normalize_child_command``.
解析不得触碰显式点名的解释器: ``python3`` / ``py`` / ``pythonw.exe`` 必须保留
调用者给出的身份, 该契约由 ``test_test_process_command.py`` 锁定。

This module must stay importable where ``ctypes.WINFUNCTYPE`` does not exist, because
Linux CI collects it too; the Windows-only helper is imported inside the single test
that needs it, so collection cannot fail on a non-Windows platform.
本模块必须在不存在 ``ctypes.WINFUNCTYPE`` 的平台上保持可导入 —— Linux CI 同样会收集
本文件; 仅 Windows 才需要的辅助模块只在需要它的那一个测试内部导入, 收集期不得失败。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.test_process import (
    _PYTHON_COMMAND_ALIASES,
    _is_python_interpreter_command,
    _normalize_child_command,
    _resolve_executable,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_MODULE = Path(__file__).resolve()
WINDOWS_PATH_FORM_ONLY = pytest.mark.skipif(
    sys.platform != "win32",
    reason="Windows path forms need os.path.basename Windows semantics",
)


def test_python_aliases_use_the_running_interpreter():
    for alias in sorted(_PYTHON_COMMAND_ALIASES):
        assert _normalize_child_command((alias, "-c", "print(1)")) == (
            sys.executable,
            "-c",
            "print(1)",
        )


def test_bare_console_script_is_resolved_to_an_absolute_path():
    resolved = _normalize_child_command(("pytest", "-q"))

    assert resolved[0] != "pytest"
    assert os.path.isabs(resolved[0])
    assert os.path.isfile(resolved[0])
    assert resolved[1:] == ("-q",)


@pytest.mark.parametrize(
    "interpreter",
    (
        "python3",
        "python3.12",
        "py",
        "pyw",
        "pythonw.exe",
        "PYTHON",
        "pypy3",
        "/usr/bin/python",
        pytest.param(r".\python.exe", marks=WINDOWS_PATH_FORM_ONLY),
        pytest.param(r"C:\Tools\Python\python.exe", marks=WINDOWS_PATH_FORM_ONLY),
    ),
)
def test_explicit_interpreter_name_is_never_path_resolved(interpreter):
    """An explicitly named interpreter keeps the caller's identity.

    显式点名的解释器保持调用者给出的身份, 不得解析成绝对路径。

    Windows path forms classify as an interpreter only under Windows path
    semantics: ``_is_python_interpreter_command`` uses ``os.path.basename``, which
    does not split on a backslash under POSIX.
    Windows 路径形式只在 Windows 路径语义下被识别为解释器: 分类函数使用
    ``os.path.basename``, POSIX 下不按反斜杠切分, 故这两个用例仅在 Windows 执行。
    """
    assert _is_python_interpreter_command(interpreter) is True
    assert _resolve_executable(interpreter) == interpreter
    assert _normalize_child_command((interpreter, "-V")) == (interpreter, "-V")


@pytest.mark.parametrize(
    "console_script",
    ("pytest", "pytest.exe", "python-tool", "mypy.cmd", "black"),
)
def test_console_script_is_not_mistaken_for_an_interpreter(console_script):
    """Only interpreter names are excluded from resolution.

    只有解释器名被排除在解析之外, 控制台脚本仍须解析。
    """
    assert _is_python_interpreter_command(console_script) is False


def test_absolute_command_is_preserved_unchanged():
    absolute = os.path.join(os.getcwd(), ".venv", "Scripts", "pytest.exe")

    assert _normalize_child_command((absolute, "-q")) == (absolute, "-q")
    assert _normalize_child_command((sys.executable, "-q")) == (sys.executable, "-q")


def test_relative_path_command_is_not_path_searched():
    """A command carrying a separator is a path, not a PATH lookup.

    带路径分隔符的命令按路径处理, 不参与 PATH 查找。
    """
    relative = os.path.join("scripts", "test_process.py")

    assert _resolve_executable(relative) == relative


def test_unresolvable_command_is_returned_unchanged():
    """Leave the failure to CreateProcessW so its error stays actionable.

    无法解析时原样返回, 交由 CreateProcessW 报错以保留可诊断性。
    """
    missing = "prismqml-definitely-missing-executable"

    assert _resolve_executable(missing) == missing
    assert _normalize_child_command((missing,)) == (missing,)


@pytest.mark.skipif(
    sys.platform != "win32",
    reason="Windows PATH lookup error codes only",
)
def test_path_lookup_error_codes_cover_the_windows_lookup_failures():
    from scripts._test_support.windows import api as windows_api

    assert windows_api.PATH_LOOKUP_ERROR_CODES == frozenset(
        (windows_api.ERROR_FILE_NOT_FOUND, windows_api.ERROR_PATH_NOT_FOUND)
    )


def test_contract_module_stays_importable_without_windows_ctypes_api():
    """Collection must survive a platform without ``ctypes.WINFUNCTYPE``.

    收集期必须能在没有 ``ctypes.WINFUNCTYPE`` 的平台上存活: Linux CI 会真实收集本文件,
    模块级导入 Windows 专属辅助模块会让整轮测试在收集阶段以 exit 2 中断。
    """
    script = (
        "import ctypes, sys\n"
        "if hasattr(ctypes, 'WINFUNCTYPE'):\n"
        "    del ctypes.WINFUNCTYPE\n"
        "sys.platform = 'linux'\n"
        "import importlib.util\n"
        "spec = importlib.util.spec_from_file_location(\n"
        f"    'child_command_contract', {str(CONTRACT_MODULE)!r}\n"
        ")\n"
        "module = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(module)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_empty_command_is_rejected():
    with pytest.raises(ValueError):
        _normalize_child_command(())
