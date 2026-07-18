# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Window startup profiling and path setup. 窗口启动剖析与路径装配。"""

import os
import time

from PySide6.QtCore import QStandardPaths

from ..core.diagnostics import startup_profile_verbose_enabled
from ..core.logger import info


_WINDOW_BUILDER_LOG_TAG = "WindowBuilder"


def _make_window_profile():
    """Create the shared startup profiler. 创建共享启动剖析器。"""
    profile_start = time.perf_counter()
    profile_last = profile_start

    def profile(label: str):
        nonlocal profile_last
        now = time.perf_counter()
        info(
            f"[启动剖析] PrismQML._create_window {label}: "
            f"+{int((now - profile_last) * 1000)}ms / "
            f"total {int((now - profile_start) * 1000)}ms",
            tag=_WINDOW_BUILDER_LOG_TAG,
        )
        profile_last = now

    return profile


def _startup_profile_verbose() -> bool:
    """Read the existing verbose startup switch. 读取既有启动详细剖析开关。"""
    return startup_profile_verbose_enabled()


def _log_window_cache_environment() -> None:
    """Log QML cache inputs before engine setup. 在引擎装配前记录 QML 缓存输入。"""
    cache_location = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.CacheLocation
    )
    info(
        "[启动剖析] PrismQML QML cache env: "
        f"QML_DISK_CACHE_PATH={os.environ.get('QML_DISK_CACHE_PATH', '')!r}, "
        f"QML_DISABLE_DISK_CACHE={os.environ.get('QML_DISABLE_DISK_CACHE', '')!r}, "
        f"QML_FORCE_DISK_CACHE={os.environ.get('QML_FORCE_DISK_CACHE', '')!r}, "
        f"QtCacheLocation={cache_location!r}",
        tag=_WINDOW_BUILDER_LOG_TAG,
    )


def prepare_window_startup_profile():
    """Prepare one profiler and one verbose snapshot. 准备单一剖析器与详细开关快照。"""
    profile = _make_window_profile()
    startup_profile_verbose = _startup_profile_verbose()
    if startup_profile_verbose:
        _log_window_cache_environment()
    return profile, startup_profile_verbose


def resolve_window_qml_paths(profile):
    """Resolve QML and fluent icon paths at the original boundary. 在原边界解析 QML 与图标路径。"""
    from ..core.utils import qml_path

    qml_dir = qml_path()
    icon_dir = qml_dir / "controls" / "icons" / "fluent"
    profile("解析 QML 路径")
    return qml_dir, icon_dir
