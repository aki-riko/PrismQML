# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Shared runtime diagnostic switches. 共享运行时诊断开关。"""

import os


STARTUP_PROFILE_VERBOSE_ENV = "PRISMQML_STARTUP_PROFILE_VERBOSE"
SCROLL_TRACE_ENV = "PRISMQML_SCROLL_TRACE"
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


def startup_profile_verbose_enabled() -> bool:
    """Read the shared verbose profiling switch. 读取共享详细剖析开关。"""
    return os.environ.get(STARTUP_PROFILE_VERBOSE_ENV, "").lower() in _TRUE_VALUES


def scroll_trace_enabled() -> bool:
    """Read the opt-in scroll runtime trace switch. 读取显式滚动运行时跟踪开关。"""
    return os.environ.get(SCROLL_TRACE_ENV, "").lower() in _TRUE_VALUES
