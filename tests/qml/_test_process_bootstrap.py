# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Shared bootstrap for standalone QML tests. QML 独立测试共享启动保护。"""

from __future__ import annotations

import runpy
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_PROCESS = runpy.run_path(str(REPO_ROOT / "scripts" / "test_process.py"))
configure_qml_test_process = TEST_PROCESS[
    "configure_automated_test_process"
]
if not callable(configure_qml_test_process):
    raise TypeError("configure_automated_test_process must be callable")
