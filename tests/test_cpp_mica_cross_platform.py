# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""C++ Mica cross-platform source contracts. C++ Mica 跨平台源码契约。"""

from pathlib import Path


SOURCE_PATH = (
    Path(__file__).resolve().parents[1] / "cpp" / "src" / "MicaManager.cpp"
)


def test_windows_build_thresholds_are_platform_independent():
    source = SOURCE_PATH.read_text(encoding="utf-8")
    namespace_start = source.index("namespace {")
    windows_only_start = source.index("#ifdef Q_OS_WIN", namespace_start)

    platform_independent = source[namespace_start:windows_only_start]
    assert "constexpr quint32 kWin11BuildThreshold" in platform_independent
    assert "constexpr quint32 kWin11BackdropBuildThreshold" in platform_independent
