# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Native crash reporter contracts and real-crash checks. 原生崩溃转储契约与真实崩溃验证。"""

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

import prismqml
from prismqml.python.core import crash_reporter
from scripts import build_crash_runtime


REPO_ROOT = Path(__file__).resolve().parents[1]
# Set to "1" where the runtime must exist (release CI) so a missing build fails
# 必须有运行时的环境（发布 CI）设为 "1"，缺失时失败而非跳过
REQUIRE_RUNTIME_ENV = "PRISM_REQUIRE_CRASH_RUNTIME"
DUMP_WAIT_SECONDS = 10.0
CHILD_TIMEOUT_SECONDS = 60
CRASH_CHILD = """
import ctypes
import os
import sys

root, runtime, app_name, database, max_reports = sys.argv[1:6]
sys.path.insert(0, root)
os.environ["PRISM_CRASH_RUNTIME_DIR"] = runtime
from PySide6.QtCore import QCoreApplication
from prismqml import install_crash_reporter

QCoreApplication.setApplicationName(app_name)
installed = install_crash_reporter(database or None, max_reports=int(max_reports))
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


@pytest.fixture
def fresh_state(monkeypatch):
    monkeypatch.setattr(crash_reporter, "_installed_dir", None)
    monkeypatch.delenv(crash_reporter.RUNTIME_DIR_ENV, raising=False)


@pytest.fixture
def app_name(qapp):
    from PySide6.QtCore import QCoreApplication

    previous = QCoreApplication.applicationName()
    yield QCoreApplication.setApplicationName
    QCoreApplication.setApplicationName(previous)


def _built_runtime() -> Path:
    runtime = build_crash_runtime.resolve_layout().runtime
    library, handler = crash_runtime_files()
    if (runtime / library).is_file() and (runtime / handler).is_file():
        return runtime
    if os.environ.get(REQUIRE_RUNTIME_ENV) == "1":
        pytest.fail(f"crash runtime required but missing in {runtime}")
    pytest.skip(f"crash runtime not built; run scripts/build_crash_runtime.py ({runtime})")


def crash_runtime_files():
    if sys.platform not in crash_reporter.RUNTIME_FILES:
        pytest.skip(f"crash reporting not supported on {sys.platform}")
    return crash_reporter.RUNTIME_FILES[sys.platform]


def _crash(runtime: Path, app: str, database: Path, max_reports: int = 0) -> None:
    cache_prefix = os.environ["PYTHONPYCACHEPREFIX"]
    # -I drops PYTHONUTF8, so force UTF-8 explicitly; native handler output may still
    # carry locale bytes, hence errors="replace"
    # -I 会忽略 PYTHONUTF8，故显式指定 UTF-8；原生 handler 输出仍可能含区域编码字节，故用 replace
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-X", f"pycache_prefix={cache_prefix}",
         "-c", CRASH_CHILD, str(REPO_ROOT), str(runtime), app, str(database), str(max_reports)],
        check=False, capture_output=True, encoding="utf-8", errors="replace",
        timeout=CHILD_TIMEOUT_SECONDS,
    )
    assert "installed=True" in result.stdout, result.stdout + result.stderr
    assert result.returncode not in (0, 3, 4), (result.returncode, result.stderr)


def _dumps(database: Path, expected: int) -> list:
    deadline = time.monotonic() + DUMP_WAIT_SECONDS
    while True:
        dumps = sorted((database / "reports").glob("*.dmp"))
        if len(dumps) >= expected or time.monotonic() > deadline:
            return dumps
        time.sleep(0.1)


def test_root_package_exports_the_core_installer():
    assert prismqml.install_crash_reporter is crash_reporter.install_crash_reporter
    assert "install_crash_reporter" in prismqml.__all__


def test_runtime_file_names_match_the_build_script():
    for platform, files in crash_reporter.RUNTIME_FILES.items():
        assert set(files) <= set(build_crash_runtime.RUNTIME_FILES[platform])


def test_runtime_dir_defaults_to_the_wheel_location_and_honours_override(fresh_state, monkeypatch, tmp_path):
    assert crash_reporter.runtime_dir() == REPO_ROOT / "prismqml" / "_native" / "crash"
    monkeypatch.setenv(crash_reporter.RUNTIME_DIR_ENV, str(tmp_path))
    assert crash_reporter.runtime_dir() == tmp_path


@pytest.mark.parametrize("name", ["", "  ", "python", "pythonw", "Python3", "python3.12"])
def test_default_database_refuses_shared_names(app_name, name):
    app_name(name)
    assert crash_reporter.default_database_dir() is None


def test_default_database_is_per_application(app_name):
    from PySide6.QtCore import QStandardPaths

    app_name("CrashReporterContractApp")
    expected = Path(QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppLocalDataLocation
    )) / crash_reporter.DATABASE_SUBDIR
    assert crash_reporter.default_database_dir() == expected
    assert "CrashReporterContractApp" in expected.parts


@pytest.mark.parametrize("limits", [{"max_reports": -1}, {"max_age_days": 1.5}, {"max_size_mb": True}])
def test_invalid_limits_raise(fresh_state, tmp_path, limits):
    with pytest.raises(ValueError, match="non-negative int"):
        crash_reporter.install_crash_reporter(tmp_path, **limits)


def test_unnamed_application_without_directory_is_refused(fresh_state, app_name, tmp_path, monkeypatch):
    app_name("python")
    monkeypatch.setenv(crash_reporter.RUNTIME_DIR_ENV, str(tmp_path / "unused"))
    assert crash_reporter.install_crash_reporter() is False
    assert crash_reporter._installed_dir is None


def test_missing_runtime_returns_false_without_raising(fresh_state, tmp_path, monkeypatch):
    monkeypatch.setenv(crash_reporter.RUNTIME_DIR_ENV, str(tmp_path / "missing"))
    assert crash_reporter.install_crash_reporter(tmp_path / "db") is False
    assert crash_reporter._installed_dir is None


def test_two_applications_write_dumps_to_separate_directories(tmp_path):
    runtime = _built_runtime()
    first, second = tmp_path / "AppA", tmp_path / "AppB"
    _crash(runtime, "CrashReporterAppA", first)
    _crash(runtime, "CrashReporterAppB", second)
    assert len(_dumps(first, 1)) == 1
    assert len(_dumps(second, 1)) == 1


def test_max_reports_prunes_on_next_start(tmp_path):
    runtime = _built_runtime()
    database = tmp_path / "Pruned"
    for _ in range(3):
        _crash(runtime, "CrashReporterPruned", database, max_reports=1)
        _dumps(database, 1)
    # Pruning runs at start-up, so the last crash adds one on top of the kept one
    # 清理发生在启动时，最后一次崩溃会在保留的一份之上再加一份
    assert len(_dumps(database, 2)) == 2
