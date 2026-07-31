# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""QML incubation policy and lazy controller facade. QML 孵化策略与延迟控制器门面。

Windows Qt 6.11.1 uses synchronous Loader creation because its sliced
incubation path can crash while finalizing QQmlConnections. That fallback must
not import the controller, timer, and logger implementation only to discard it.
Windows Qt 6.11.1 因 QQmlConnections 原生崩溃而使用同步 Loader；回退路径无需先
加载随后不会使用的控制器、定时器和日志实现。
"""

from __future__ import annotations

import sys

from PySide6.QtCore import qVersion

from .diagnostics import startup_profile_verbose_enabled


_DIAGNOSTIC_TAG = "Incubation"
_CONNECTIONS_VME_CRASH_PLATFORM = "win32"
_CONNECTIONS_VME_CRASH_QT_VERSIONS = frozenset(("6.11.1",))
_LAZY_RUNTIME_EXPORTS = frozenset(("PrismIncubationController",))


def asynchronous_page_loader_enabled(qt_version=None, platform_name=None):
    """Return whether framework page Loaders may use sliced incubation.

    返回框架页面 Loader 是否可安全使用分片孵化。
    """
    resolved_qt_version = qVersion() if qt_version is None else qt_version
    resolved_platform = sys.platform if platform_name is None else platform_name
    return not _requires_synchronous_incubation_fallback(
        resolved_qt_version, resolved_platform
    )


def install_incubation_controller(engine, budget_ms: int = 5):
    """Explicitly load and install the sliced controller. 显式加载并安装分片控制器。"""
    from ._incubation_controller import install_incubation_controller as install

    return install(engine, budget_ms=budget_ms)


def install_default_incubation_controller(engine, budget_ms: int = 5):
    """Install the default controller unless this Qt build is unsafe.

    当前 Qt 构建存在已知风险时保持同步回退，否则安装默认控制器。
    """
    qt_version = qVersion()
    if not asynchronous_page_loader_enabled(qt_version, sys.platform):
        _log_synchronous_incubation_fallback(qt_version)
        return None
    return install_incubation_controller(engine, budget_ms=budget_ms)


def debug(message, tag=None):
    """Load the runtime logger only when diagnostics emit. 仅在输出诊断时加载日志器。"""
    from .logger import debug as emit

    return emit(message, tag=tag)


def info(message, tag=None):
    """Load the runtime logger only when diagnostics emit. 仅在输出诊断时加载日志器。"""
    from .logger import info as emit

    return emit(message, tag=tag)


def exception(message, tag=None):
    """Load the runtime logger only when diagnostics emit. 仅在输出诊断时加载日志器。"""
    from .logger import exception as emit

    return emit(message, tag=tag)


def _requires_synchronous_incubation_fallback(qt_version, platform_name):
    """Return whether automatic sliced incubation is unsafe. 判断自动分片孵化是否不安全。"""
    return (
        platform_name == _CONNECTIONS_VME_CRASH_PLATFORM
        and qt_version in _CONNECTIONS_VME_CRASH_QT_VERSIONS
    )


def _log_synchronous_incubation_fallback(qt_version):
    """Log the fallback only in verbose diagnostics. 仅在详细诊断中记录回退。"""
    if not startup_profile_verbose_enabled():
        return
    debug(
        "controller skipped "
        f"qt_version={qt_version} "
        f"platform={sys.platform} "
        "reason=QQmlConnections null VME method during sliced incubation",
        tag=_DIAGNOSTIC_TAG,
    )


def __getattr__(name):
    """Resolve explicit controller-class access without penalizing fallback startup.

    仅在显式访问控制器类时加载实现，避免拖慢同步回退启动。
    """
    if name not in _LAZY_RUNTIME_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from ._incubation_controller import PrismIncubationController

    globals()[name] = PrismIncubationController
    return PrismIncubationController


def __dir__():
    """Include lazy public exports in module introspection. 在模块内省中包含延迟公开项。"""
    return sorted((*globals(), *_LAZY_RUNTIME_EXPORTS))


__all__ = [
    "PrismIncubationController",
    "asynchronous_page_loader_enabled",
    "install_default_incubation_controller",
    "install_incubation_controller",
]
