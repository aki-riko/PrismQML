# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Verify native fatal failures through the process runner. 验证原生致命失败。"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.test_process import (
    AUTOMATED_TEST_BOUNDARY_ENV,
    WINDOWS_DESCENDANT_EXIT_GRACE_SECONDS,
    WINDOWS_ERROR_MODE_FLAGS,
    WINDOWS_JOB_CLEANUP_WAIT_SECONDS,
)

if __package__:
    from ._native_failure_markers import (
        failure_markers as _failure_markers,
        only_marker as _only,
        qt_message_markers as _qt_message_markers,
        spawn_markers as _spawn_markers,
        trigger_markers as _trigger_markers,
        verify_boundary as _verify_boundary,
    )
else:
    from _native_failure_markers import (
        failure_markers as _failure_markers,
        only_marker as _only,
        qt_message_markers as _qt_message_markers,
        spawn_markers as _spawn_markers,
        trigger_markers as _trigger_markers,
        verify_boundary as _verify_boundary,
    )


LOGGER = logging.getLogger(__name__)
FIXTURE_FAILURE_EXIT_CODE = 70
STATUS_DLL_NOT_FOUND = 0xC0000135
STATUS_ACCESS_VIOLATION = 0xC0000005
STATUS_FAIL_FAST_EXCEPTION = 0xC0000602
STATUS_STACK_BUFFER_OVERRUN = 0xC0000409
ABORT_EXIT_CODES = frozenset((3, STATUS_STACK_BUFFER_OVERRUN))
SUBPROCESS_IO_GRACE_SECONDS = 5


def _positive_seconds(value: str) -> float:
    seconds = float(value)
    if not math.isfinite(seconds) or seconds <= 0:
        raise argparse.ArgumentTypeError(
            "timeout must be a finite number greater than zero"
        )
    return seconds


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--helper", type=Path, required=True)
    parser.add_argument("--loader", type=Path, required=True)
    parser.add_argument("--companion", type=Path, required=True)
    parser.add_argument("--qt-bin", type=Path, required=True)
    parser.add_argument("--case-timeout", type=_positive_seconds, required=True)
    return parser.parse_args()


def _unique_paths(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    results = []
    normalized = set()
    for path in paths:
        key = os.path.normcase(os.path.abspath(os.fspath(path)))
        if key not in normalized:
            normalized.add(key)
            results.append(path)
    return tuple(results)


def _runtime_paths(qt_bin: Path) -> tuple[Path, ...]:
    system_root_value = os.environ.get("SystemRoot")
    if not system_root_value:
        raise RuntimeError("SystemRoot is required for the native failure matrix")
    system_root = Path(system_root_value)
    candidates = _unique_paths(
        (qt_bin, Path(sys.executable).parent, system_root / "System32", system_root)
    )
    missing = [path for path in candidates if not path.is_dir()]
    if missing:
        raise FileNotFoundError(f"runtime PATH directories are missing: {missing!r}")
    return candidates


def _environment(path_entries: tuple[Path, ...]) -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop(AUTOMATED_TEST_BOUNDARY_ENV, None)
    environment["PATH"] = os.pathsep.join(map(str, path_entries))
    return environment


def _runner_command(
    runner: Path,
    command: list[str],
    case_timeout: float,
) -> list[str]:
    return [
        sys.executable,
        str(runner),
        "--qt-platform",
        "offscreen",
        "--timeout",
        str(case_timeout),
        "--",
        *command,
    ]


def _subprocess_timeout(case_timeout: float) -> float:
    return (
        case_timeout
        + WINDOWS_DESCENDANT_EXIT_GRACE_SECONDS
        + WINDOWS_JOB_CLEANUP_WAIT_SECONDS
        + SUBPROCESS_IO_GRACE_SECONDS
    )


def _case_timing(started_at: datetime, started_clock: float) -> dict:
    ended_at = datetime.now(timezone.utc)
    return {
        "started_at_utc": started_at.isoformat(),
        "ended_at_utc": ended_at.isoformat(),
        "duration_seconds": round(time.monotonic() - started_clock, 6),
    }


def _run_case(
    runner: Path,
    command: list[str],
    environment: dict[str, str],
    working_directory: Path,
    case_timeout: float,
) -> tuple[subprocess.CompletedProcess, dict]:
    started_at = datetime.now(timezone.utc)
    started_clock = time.monotonic()
    result = subprocess.run(
        _runner_command(runner, command, case_timeout),
        cwd=working_directory,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=_subprocess_timeout(case_timeout),
        check=False,
    )
    return result, _case_timing(started_at, started_clock)


def _assert_boundary_marker(marker: dict, boundary: dict, process_id: int) -> None:
    if marker["pid"] != process_id:
        raise AssertionError((marker, boundary, process_id))
    for field in ("desktop", "job"):
        if marker[field] != boundary[field]:
            raise AssertionError((field, marker, boundary))
    if marker["in_job"] != 1:
        raise AssertionError(marker)
    if marker["error_mode"] & WINDOWS_ERROR_MODE_FLAGS != WINDOWS_ERROR_MODE_FLAGS:
        raise AssertionError(marker)


def _assert_spawn_marker(marker: dict, boundary: dict) -> None:
    if marker["parent_pid"] != boundary["root_process_id"]:
        raise AssertionError((marker, boundary))
    if marker["child_pid"] <= 0 or marker["child_in_job"] != 1:
        raise AssertionError(marker)
    for field in ("desktop", "job"):
        if marker[field] != boundary[field]:
            raise AssertionError((field, marker, boundary))


def _verify_root_fatal(result, boundary: dict, mode: str) -> dict:
    marker = _only(_failure_markers(result.stderr), "root failure marker")
    _assert_boundary_marker(marker, boundary, boundary["root_process_id"])
    trigger = _only(_trigger_markers(result.stderr), "root trigger marker")
    if trigger != {"mode": mode, "pid": boundary["root_process_id"]}:
        raise AssertionError(trigger)
    if _spawn_markers(result.stderr):
        raise AssertionError(result.stderr)
    if marker["mode"] != mode:
        raise AssertionError(marker)
    return {"failure_process_id": marker["pid"]}


def _verify_spawned_fatal(result, boundary: dict, mode: str) -> dict:
    markers = _failure_markers(result.stderr)
    root = _only(
        [item for item in markers if item["mode"] == "spawn-self"],
        "root marker",
    )
    child = _only([item for item in markers if item["mode"] == mode], "child marker")
    if len(markers) != 2:
        raise AssertionError(markers)
    _assert_boundary_marker(root, boundary, boundary["root_process_id"])
    spawn = _only(_spawn_markers(result.stderr), "spawn marker")
    _assert_spawn_marker(spawn, boundary)
    _assert_boundary_marker(child, boundary, spawn["child_pid"])
    trigger = _only(_trigger_markers(result.stderr), "child trigger marker")
    if trigger != {"mode": mode, "pid": spawn["child_pid"]}:
        raise AssertionError(trigger)
    return {"failure_process_id": child["pid"], "child_process_id": child["pid"]}


def _verify_loader_evidence(result, boundary: dict, spawned: bool) -> dict:
    triggers = _trigger_markers(result.stderr)
    if triggers:
        raise AssertionError(triggers)
    if not spawned:
        if _failure_markers(result.stderr) or _spawn_markers(result.stderr):
            raise AssertionError(result.stderr)
        return {"failure_process_id": boundary["root_process_id"]}
    root = _only(_failure_markers(result.stderr), "loader parent marker")
    _assert_boundary_marker(root, boundary, boundary["root_process_id"])
    if root["mode"] != "spawn-executable":
        raise AssertionError(root)
    spawn = _only(_spawn_markers(result.stderr), "loader spawn marker")
    _assert_spawn_marker(spawn, boundary)
    return {
        "failure_process_id": spawn["child_pid"],
        "child_process_id": spawn["child_pid"],
    }


def _verify_loader_control(result) -> dict:
    markers = (
        _failure_markers(result.stderr),
        _spawn_markers(result.stderr),
        _trigger_markers(result.stderr),
    )
    if any(markers):
        raise AssertionError(markers)
    return {}


def _dword(value: int) -> int:
    return value & 0xFFFFFFFF


def _expected_exit_code(
    name: str,
    result: subprocess.CompletedProcess,
    expected_codes: frozenset[int],
) -> int:
    actual = _dword(result.returncode)
    if actual in expected_codes and actual != FIXTURE_FAILURE_EXIT_CODE:
        return actual
    expected = [f"0x{code:08X}" for code in expected_codes]
    raise AssertionError(
        f"{name}: expected {expected}, got 0x{actual:08X}\n{result.stderr}"
    )


def _verify_qfatal_message(messages: list[dict], evidence: dict) -> None:
    message = _only(messages, "qFatal message marker")
    expected = {
        "type": "fatal",
        "pid": evidence["failure_process_id"],
        "message": "PRISM_NATIVE_QFATAL_SENTINEL",
    }
    if message != expected:
        raise AssertionError((message, expected))


def _case_evidence(
    result: subprocess.CompletedProcess,
    boundary: dict,
    mode: str | None,
    spawned: bool,
    actual: int,
) -> dict:
    if mode is None:
        evidence = (
            _verify_loader_control(result)
            if actual == 0
            else _verify_loader_evidence(result, boundary, spawned)
        )
    else:
        evidence = (
            _verify_spawned_fatal(result, boundary, mode)
            if spawned
            else _verify_root_fatal(result, boundary, mode)
        )
    messages = _qt_message_markers(result.stderr)
    if mode != "qfatal":
        if messages:
            raise AssertionError(messages)
        return evidence
    _verify_qfatal_message(messages, evidence)
    return evidence


def _case_record(
    name: str,
    mode: str | None,
    spawned: bool,
    boundary: dict,
    actual: int,
    evidence: dict,
    timing: dict,
) -> dict:
    return {
        "case": name,
        "mode": mode or "loader",
        "outcome": "control" if actual == 0 else "expected-failure",
        "spawned": spawned,
        "desktop": boundary["desktop"],
        "job": boundary["job"],
        "root_process_id": boundary["root_process_id"],
        "exit_code": actual,
        "exit_code_hex": f"0x{actual:08X}",
        "private_desktop_visible_windows": 0,
        "final_active_processes": boundary["final_active_processes"],
        "cleanup_succeeded": boundary["cleanup_succeeded"],
        **timing,
        **evidence,
    }


def _verify_case(
    name: str,
    runner: Path,
    command: list[str],
    expected_codes: frozenset[int],
    environment: dict[str, str],
    working_directory: Path,
    case_timeout: float,
    mode: str | None = None,
    spawned: bool = False,
) -> dict:
    result, timing = _run_case(
        runner, command, environment, working_directory, case_timeout
    )
    boundary = _verify_boundary(result)
    actual = _expected_exit_code(name, result, expected_codes)
    evidence = _case_evidence(result, boundary, mode, spawned, actual)
    record = _case_record(
        name, mode, spawned, boundary, actual, evidence, timing
    )
    LOGGER.info("native_failure_case=%s", json.dumps(record, sort_keys=True))
    return record


def _assert_companion_absent(companion: Path, directories: tuple[Path, ...]) -> None:
    collisions = [directory / companion.name for directory in directories]
    existing = [path for path in collisions if path.exists()]
    if existing:
        raise AssertionError(f"companion DLL contaminates failure search: {existing!r}")


def _loader_cases(args, success_environment: dict, failure_environment: dict):
    missing = frozenset((STATUS_DLL_NOT_FOUND,))
    return (
        (
            "loader-success",
            [str(args.loader)],
            frozenset((0,)),
            success_environment,
            False,
        ),
        ("loader-root", [str(args.loader)], missing, failure_environment, False),
        (
            "loader-grandchild",
            [str(args.helper), "spawn-executable", str(args.loader)],
            missing,
            failure_environment,
            True,
        ),
    )


def _verify_loader(
    args: argparse.Namespace,
    runtime_paths: tuple[Path, ...],
    working_directory: Path,
) -> list[dict]:
    companion_directory = args.companion.parent
    _assert_companion_absent(
        args.companion,
        _unique_paths((*runtime_paths, args.loader.parent, working_directory)),
    )
    success_environment = _environment((companion_directory, *runtime_paths))
    failure_environment = _environment(runtime_paths)
    return [
        _verify_case(
            name, args.runner, command, expected_codes, environment,
            working_directory, args.case_timeout, spawned=spawned,
        )
        for name, command, expected_codes, environment, spawned in _loader_cases(
            args, success_environment, failure_environment
        )
    ]


def _verify_mode_pair(
    args: argparse.Namespace,
    mode: str,
    environment: dict[str, str],
    working_directory: Path,
    expected_codes: frozenset[int],
) -> list[dict]:
    root = _verify_case(
        f"{mode}-root", args.runner, [str(args.helper), mode], expected_codes,
        environment, working_directory, args.case_timeout, mode,
    )
    grandchild = _verify_case(
        f"{mode}-grandchild", args.runner,
        [str(args.helper), "spawn-self", mode], frozenset((root["exit_code"],)),
        environment, working_directory, args.case_timeout, mode, True,
    )
    return [root, grandchild]


def _verify_fatal_modes(
    args: argparse.Namespace,
    runtime_paths: tuple[Path, ...],
    working_directory: Path,
) -> list[dict]:
    environment = _environment(runtime_paths)
    expectations = {
        "access-violation": frozenset((STATUS_ACCESS_VIOLATION,)),
        "fail-fast": frozenset((STATUS_FAIL_FAST_EXCEPTION,)),
        "abort": ABORT_EXIT_CODES,
        "qfatal": ABORT_EXIT_CODES,
    }
    return [
        record
        for mode, expected_codes in expectations.items()
        for record in _verify_mode_pair(
            args, mode, environment, working_directory, expected_codes
        )
    ]


def main() -> int:
    args = _parse_args()
    if sys.platform != "win32":
        raise RuntimeError("native failure verification requires Windows")
    for path in (args.runner, args.helper, args.loader, args.companion):
        if not path.is_file():
            raise FileNotFoundError(path)
    if not args.qt_bin.is_dir():
        raise FileNotFoundError(args.qt_bin)
    runtime_paths = _runtime_paths(args.qt_bin)
    with tempfile.TemporaryDirectory(prefix="prism-native-failure-") as directory:
        working_directory = Path(directory)
        records = [
            *_verify_loader(args, runtime_paths, working_directory),
            *_verify_fatal_modes(args, runtime_paths, working_directory),
        ]
    LOGGER.info(
        "native_failure_matrix=%s",
        json.dumps(records, ensure_ascii=False, sort_keys=True),
    )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    raise SystemExit(main())
