# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Native crash dumps via the bundled sentry-native runtime. 原生崩溃转储。

``install_crash_reporter()`` starts an out-of-process Crashpad handler that writes
a minidump into a directory owned by this application. Nothing is uploaded: the
runtime is built without a network transport and no DSN is set.
``install_crash_reporter()`` 启动进程外 Crashpad handler，把 minidump 写入本应用专属
目录。运行时不含网络传输且不设置 DSN，不会上传任何内容。
"""

import atexit
import ctypes
import os
import re
import sys
import threading
from pathlib import Path
from typing import Optional, Union

from .logger import getLogger

logger = getLogger()

# Override for checkouts without a bundled runtime 未内置运行时的源码检出可用此覆盖
RUNTIME_DIR_ENV = "PRISM_CRASH_RUNTIME_DIR"
DEFAULT_RUNTIME_DIR = Path(__file__).resolve().parents[2] / "_native" / "crash"
DATABASE_SUBDIR = "crashpad"
DEFAULT_MAX_REPORTS = 20
DEFAULT_MAX_AGE_DAYS = 30
DEFAULT_MAX_SIZE_MB = 200
_SECONDS_PER_DAY = 24 * 60 * 60
_BYTES_PER_MB = 1024 * 1024
# SENTRY_CACHE_KEEP_ALWAYS makes the cache_max_* limits govern crash reports
# SENTRY_CACHE_KEEP_ALWAYS 使 cache_max_* 上限作用于崩溃报告
_CACHE_KEEP_ALWAYS = 2
# Library and handler file names, per platform 各平台库与 handler 文件名
RUNTIME_FILES = {
    "win32": ("sentry.dll", "crashpad_handler.exe"),
    "linux": ("libsentry.so", "crashpad_handler"),
    "darwin": ("libsentry.dylib", "crashpad_handler"),
}
# Interpreter names; every script run by that interpreter would share them
# 解释器名；由它运行的所有脚本都会共用
_INTERPRETER_NAME = re.compile(r"^pythonw?(\d+(\.\d+)?)?$", re.IGNORECASE)

_lock = threading.Lock()
_installed_dir: Optional[Path] = None


def _validate_limits(**limits: int) -> None:
    for name, value in limits.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative int, got {value!r}")


def runtime_dir() -> Path:
    """Return the directory holding the native runtime. 返回原生运行时目录。"""
    configured = os.environ.get(RUNTIME_DIR_ENV)
    return Path(configured) if configured else DEFAULT_RUNTIME_DIR


def _fallback_names(core_application) -> set:
    """Names Qt may use when no application name was set. Qt 未设置应用名时可能使用的名字。

    Without an explicit name Qt derives one from the program: the executable on
    Windows (``python``), ``arguments()[0]`` on Linux (``main.py``, ``-c``). Any
    of these is shared by unrelated programs, so it never identifies one.
    未显式设置时 Qt 从程序推导：Windows 取可执行文件（``python``），Linux 取
    ``arguments()[0]``（``main.py``、``-c``）。这些名字会被无关程序共用，不能标识应用。
    """
    arguments = core_application.arguments() if core_application.instance() else []
    programs = [arguments[0] if arguments else "", sys.argv[0] if sys.argv else "", sys.executable]
    names = set()
    for program in filter(None, programs):
        path = Path(program)
        names.update((path.name.casefold(), path.stem.casefold()))
    return names - {""}


def default_database_dir() -> Optional[Path]:
    """Return the per-application dump directory, or None if unnamed. 返回应用专属转储目录。"""
    from PySide6.QtCore import QCoreApplication, QStandardPaths

    name = QCoreApplication.applicationName().strip()
    if (not name or _INTERPRETER_NAME.match(name)
            or name.casefold() in _fallback_names(QCoreApplication)):
        return None
    location = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppLocalDataLocation
    )
    return Path(location) / DATABASE_SUBDIR if location else None


def _set_path(library, function_name: str, options, path: Path) -> None:
    if sys.platform == "win32":
        setter = getattr(library, f"{function_name}w")
        setter.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
        setter(options, str(path))
    else:
        setter = getattr(library, function_name)
        setter.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        setter(options, os.fsencode(path))


def _configure(library, options, database: Path, handler: Path, limits) -> None:
    _set_path(library, "sentry_options_set_database_path", options, database)
    _set_path(library, "sentry_options_set_handler_path", options, handler)
    library.sentry_options_set_auto_session_tracking.argtypes = [ctypes.c_void_p, ctypes.c_int]
    library.sentry_options_set_auto_session_tracking(options, 0)
    library.sentry_options_set_cache_keep.argtypes = [ctypes.c_void_p, ctypes.c_int]
    library.sentry_options_set_cache_keep(options, _CACHE_KEEP_ALWAYS)
    max_reports, max_age_days, max_size_mb = limits
    library.sentry_options_set_cache_max_items.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    library.sentry_options_set_cache_max_items(options, max_reports)
    library.sentry_options_set_cache_max_age.argtypes = [ctypes.c_void_p, ctypes.c_int64]
    library.sentry_options_set_cache_max_age(options, max_age_days * _SECONDS_PER_DAY)
    library.sentry_options_set_cache_max_size.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    library.sentry_options_set_cache_max_size(options, max_size_mb * _BYTES_PER_MB)


def _start(database: Path, limits) -> bool:
    files = RUNTIME_FILES.get(sys.platform)
    if files is None:
        logger.warning(f"[CrashReporter] 不支持的平台: {sys.platform}")
        return False
    runtime = runtime_dir()
    library_path, handler_path = (runtime / name for name in files)
    if not (library_path.is_file() and handler_path.is_file()):
        logger.warning(f"[CrashReporter] 未找到崩溃运行时: {runtime}")
        return False
    try:
        library = ctypes.CDLL(str(library_path))
    except OSError as exc:
        logger.error(f"[CrashReporter] 加载 {library_path} 失败: {exc}")
        return False
    library.sentry_options_new.restype = ctypes.c_void_p
    options = library.sentry_options_new()
    _configure(library, options, database, handler_path, limits)
    library.sentry_init.argtypes = [ctypes.c_void_p]
    # sentry_init takes ownership of options, also on failure 无论成败 options 都归 sentry_init
    status = library.sentry_init(options)
    if status != 0:
        logger.error(f"[CrashReporter] sentry_init 返回 {status}")
        return False
    atexit.register(library.sentry_close)
    return True


def _prepare_database(database_dir) -> Optional[Path]:
    database = Path(database_dir) if database_dir is not None else default_database_dir()
    if database is None:
        logger.error("[CrashReporter] 未设置专属应用名且未传 database_dir，拒绝启用")
        return None
    database = database.expanduser().resolve()
    try:
        database.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.error(f"[CrashReporter] 创建转储目录 {database} 失败: {exc}")
        return None
    return database


def install_crash_reporter(
    database_dir: Union[str, os.PathLike, None] = None,
    *,
    max_reports: int = DEFAULT_MAX_REPORTS,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
    max_size_mb: int = DEFAULT_MAX_SIZE_MB,
) -> bool:
    """Write native crash dumps to an application-owned directory. 启用原生崩溃转储。

    See docs/api/python.*.md for the directory rule and limits 目录规则与上限见 API 文档。
    """
    _validate_limits(max_reports=max_reports, max_age_days=max_age_days, max_size_mb=max_size_mb)
    global _installed_dir
    with _lock:
        if _installed_dir is not None:
            logger.warning(f"[CrashReporter] 已在 {_installed_dir} 启用，忽略重复调用")
            return True
        database = _prepare_database(database_dir)
        if database is None or not _start(database, (max_reports, max_age_days, max_size_mb)):
            return False
        _installed_dir = database
    logger.info(f"[CrashReporter] 崩溃转储已启用: {database}")
    return True
