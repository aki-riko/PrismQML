# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Real-crash child shared by tests and the installed-wheel probe. 真实崩溃子进程。

Imported by ``tests/test_crash_reporter.py`` for the source tree. Run directly to
probe an installed wheel: two applications crash once each, and each must leave
exactly one dump in its own directory, using only the runtime inside the wheel.
供 ``tests/test_crash_reporter.py`` 导入验证源码树；直接运行时验证已安装 wheel：
两个应用各崩溃一次，必须各自在自己的目录留下且仅留下一份 dump，且只用 wheel 内运行时。
"""

import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Optional


LOGGER = logging.getLogger("prismqml.crash_reporter_probe")
REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR_ENV = "PRISM_CRASH_RUNTIME_DIR"
DUMP_WAIT_SECONDS = 10.0
CHILD_TIMEOUT_SECONDS = 60
CHILD_NOT_INSTALLED = 3
CHILD_SURVIVED = 4
CRASH_CHILD = """
import ctypes
import os
import sys

app_name, database, root, runtime, max_reports = sys.argv[1:6]
if root:
    sys.path.insert(0, root)
if runtime:
    os.environ["PRISM_CRASH_RUNTIME_DIR"] = runtime
from PySide6.QtCore import QCoreApplication
from prismqml import install_crash_reporter

QCoreApplication.setApplicationName(app_name)
installed = install_crash_reporter(database, max_reports=int(max_reports))
print(f"installed={installed}", flush=True)
if not installed:
    raise SystemExit(3)
if sys.platform == "win32":
    # A thread entered at address 0 faults outside ctypes' SEH guard 线程入口为 0 触发真实访问违例
    kernel32 = ctypes.WinDLL("kernel32")
    kernel32.CreateThread.restype = ctypes.c_void_p
    kernel32.CreateThread.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p,
                                      ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p]
    thread = kernel32.CreateThread(None, 0, None, None, 0, None)
    kernel32.WaitForSingleObject(ctypes.c_void_p(thread), 0xFFFFFFFF)
else:
    ctypes.string_at(0)
raise SystemExit(4)
"""


def run_crash_child(
    app_name: str,
    database: Path,
    *,
    root: Optional[Path] = None,
    runtime: Optional[Path] = None,
    max_reports: int = 0,
) -> subprocess.CompletedProcess:
    """Install the reporter in a fresh interpreter and crash it. 在新解释器中启用并崩溃。

    ``root`` imports prismqml from a source tree; omit it to use the installed copy.
    -I drops PYTHONUTF8, so UTF-8 is forced explicitly; native handler output may
    still carry locale bytes, hence errors="replace".
    ``root`` 指定源码树；省略则用已安装副本。-I 会忽略 PYTHONUTF8，故显式指定 UTF-8。
    """
    command = [sys.executable, "-I", "-X", "utf8"]
    cache_prefix = os.environ.get("PYTHONPYCACHEPREFIX")
    if cache_prefix:
        command += ["-X", f"pycache_prefix={cache_prefix}"]
    command += ["-c", CRASH_CHILD, app_name, str(database),
                str(root) if root else "", str(runtime) if runtime else "", str(max_reports)]
    return subprocess.run(
        command, check=False, capture_output=True, encoding="utf-8", errors="replace",
        timeout=CHILD_TIMEOUT_SECONDS,
    )


def crash_failure(result: subprocess.CompletedProcess) -> Optional[str]:
    """Describe why a crash child did not crash as expected, or None. 描述子进程异常。"""
    if "installed=True" not in result.stdout:
        return f"reporter not installed: {result.stdout}{result.stderr}"
    if result.returncode in (0, CHILD_NOT_INSTALLED, CHILD_SURVIVED):
        return f"child did not crash (exit {result.returncode}): {result.stderr}"
    return None


def wait_for_dumps(database: Path, expected: int) -> List[Path]:
    """Poll until ``expected`` dumps exist or the wait expires. 等待 dump 落盘。

    Crashpad's layout differs by platform (Windows ``reports/``, Linux ``pending/``),
    and a report moves between state directories rather than being copied, so
    search the whole database.
    Crashpad 目录布局因平台而异（Windows ``reports/``、Linux ``pending/``），报告在状态目录间
    移动而非复制，因此搜索整个数据库。
    """
    deadline = time.monotonic() + DUMP_WAIT_SECONDS
    while True:
        dumps = sorted(database.rglob("*.dmp"))
        if len(dumps) >= expected or time.monotonic() > deadline:
            return dumps
        time.sleep(0.1)


def _installed_package_root() -> Path:
    import prismqml

    package_root = Path(prismqml.__file__).resolve().parent
    if package_root == (REPO_ROOT / "prismqml").resolve():
        raise RuntimeError("source tree shadows the installed prismqml package")
    if os.environ.get(RUNTIME_DIR_ENV):
        raise RuntimeError(f"{RUNTIME_DIR_ENV} must be unset to probe the wheel's own runtime")
    return package_root


def main() -> int:
    """Probe the crash reporter of an installed wheel. 验证已安装 wheel 的崩溃转储。"""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        package_root = _installed_package_root()
    except RuntimeError as exc:
        LOGGER.error("%s", exc)
        return 1
    workspace = Path(tempfile.mkdtemp(prefix="prism-crash-probe-"))
    try:
        for app in ("CrashProbeAppA", "CrashProbeAppB"):
            database = workspace / app
            failure = crash_failure(run_crash_child(app, database))
            if failure:
                LOGGER.error("%s: %s", app, failure)
                return 1
            dumps = wait_for_dumps(database, 1)
            if len(dumps) != 1:
                LOGGER.error("%s: expected 1 dump in %s, found %s", app, database, dumps)
                return 1
            LOGGER.info("%s wrote %s", app, dumps[0].name)
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
    LOGGER.info("installed crash reporter passed: %s", package_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
