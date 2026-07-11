# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""测试入口默认无界面行为的回归验证。"""

import os
import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _clean_qt_platform_environment() -> dict[str, str]:
    """返回移除 Qt 平台覆盖后的子进程环境。"""
    env = os.environ.copy()
    env.pop("QT_QPA_PLATFORM", None)
    return env


def test_probe_defaults_to_headless_without_caller_environment():
    """裸跑全组件 probe 时由入口自身启用 headless。"""
    result = subprocess.run(
        [sys.executable, "-X", "utf8", "tests/qml/probe_all_components.py"],
        cwd=REPO_ROOT,
        env=_clean_qt_platform_environment(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    summary = re.search(
        r"组件加载 probe 结果:\s+\d+ OK / (\d+) 错误 / \d+ 跳过",
        result.stdout,
    )
    assert summary is not None, result.stdout
    assert int(summary.group(1)) == 0


def test_pytest_conftest_forces_headless_even_with_explicit_platform_value():
    """conftest 必须覆盖可能弹窗的调用者平台配置。"""
    code = """
import os
import runpy

os.environ.pop("QT_QPA_PLATFORM", None)
runpy.run_path("tests/conftest.py")
assert os.environ["QT_QPA_PLATFORM"] == "offscreen"

os.environ["QT_QPA_PLATFORM"] = "minimal"
runpy.run_path("tests/conftest.py")
assert os.environ["QT_QPA_PLATFORM"] == "offscreen"
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env=_clean_qt_platform_environment(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
