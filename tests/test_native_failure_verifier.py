# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Native failure-verifier fail-closed tests. 原生失败验证器闭合失败测试。"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from cpp.tests import verify_native_failures as verifier
from cpp.tests import _native_failure_markers as markers


BOUNDARY = {
    "desktop": "PrismQMLTest-unit",
    "job": "PrismQMLTestJob-unit",
    "root_process_id": 101,
    "final_active_processes": 0,
    "cleanup_succeeded": True,
    "exit_code": 0,
}
TIMING = {
    "started_at_utc": "2026-07-11T16:00:00+00:00",
    "ended_at_utc": "2026-07-11T16:00:01+00:00",
    "duration_seconds": 1.0,
}


def _completed(returncode: int, stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], returncode, "", stderr)


def test_fixture_failure_exit_code_is_never_accepted(monkeypatch, tmp_path):
    result = _completed(verifier.FIXTURE_FAILURE_EXIT_CODE)
    monkeypatch.setattr(verifier, "_run_case", lambda *_args: (result, TIMING))
    monkeypatch.setattr(verifier, "_verify_boundary", lambda _result: BOUNDARY)

    with pytest.raises(AssertionError, match="0x00000046"):
        verifier._verify_case(
            "fallback",
            Path("runner"),
            ["helper"],
            frozenset((verifier.FIXTURE_FAILURE_EXIT_CODE,)),
            {},
            tmp_path,
            1,
            "abort",
        )


def test_case_record_schema_includes_boundary_and_utc_evidence():
    record = verifier._case_record(
        "loader-success",
        None,
        False,
        BOUNDARY,
        0,
        {},
        TIMING,
    )

    assert record == {
        "case": "loader-success",
        "mode": "loader",
        "outcome": "control",
        "spawned": False,
        "desktop": BOUNDARY["desktop"],
        "job": BOUNDARY["job"],
        "root_process_id": BOUNDARY["root_process_id"],
        "exit_code": 0,
        "exit_code_hex": "0x00000000",
        "private_desktop_visible_windows": 0,
        "final_active_processes": 0,
        "cleanup_succeeded": True,
        **TIMING,
    }


def test_boundary_marker_allows_additional_error_mode_bits():
    marker = {
        "pid": BOUNDARY["root_process_id"],
        "desktop": BOUNDARY["desktop"],
        "job": BOUNDARY["job"],
        "in_job": 1,
        "error_mode": verifier.WINDOWS_ERROR_MODE_FLAGS | 0x0004,
    }

    verifier._assert_boundary_marker(marker, BOUNDARY, BOUNDARY["root_process_id"])


def test_boundary_rejects_mismatched_named_job(monkeypatch):
    boundary = {**BOUNDARY, "job": "PrismQMLTestJob-other"}
    monkeypatch.setattr(markers, "boundary_result", lambda _stderr: boundary)
    result = _completed(0, "visible_windows=0 / job_active_processes=0")

    with pytest.raises(AssertionError):
        verifier._verify_boundary(result)


def test_environment_discards_inherited_path_and_boundary_marker(monkeypatch):
    monkeypatch.setenv("PATH", "malicious-inherited-path")
    monkeypatch.setenv(verifier.AUTOMATED_TEST_BOUNDARY_ENV, "forged")
    paths = (Path("safe-one"), Path("safe-two"))

    environment = verifier._environment(paths)

    assert environment["PATH"] == os.pathsep.join(map(str, paths))
    assert verifier.AUTOMATED_TEST_BOUNDARY_ENV not in environment


def test_companion_collision_fails_closed(tmp_path):
    companion = tmp_path / "prism_native_failure_companion.dll"
    companion.write_bytes(b"sentinel")

    with pytest.raises(AssertionError, match="contaminates failure search"):
        verifier._assert_companion_absent(companion, (tmp_path,))


def test_run_case_passes_runner_environment_and_temporary_cwd(
    monkeypatch,
    tmp_path,
):
    captured = {}

    def fake_run(command, **kwargs):
        captured.update(command=command, **kwargs)
        return _completed(0)

    monkeypatch.setattr(verifier.subprocess, "run", fake_run)
    environment = {"PATH": "closed"}

    verifier._run_case(Path("runner"), ["child"], environment, tmp_path, 1)

    assert captured["command"][1] == "runner"
    assert captured["command"][-1] == "child"
    assert captured["cwd"] == tmp_path
    assert captured["env"] is environment


def test_qfatal_requires_runtime_sentinel(monkeypatch, tmp_path):
    result = _completed(verifier.STATUS_STACK_BUFFER_OVERRUN)
    boundary = {**BOUNDARY, "exit_code": result.returncode}
    monkeypatch.setattr(verifier, "_run_case", lambda *_args: (result, TIMING))
    monkeypatch.setattr(verifier, "_verify_boundary", lambda _result: boundary)
    monkeypatch.setattr(
        verifier,
        "_verify_root_fatal",
        lambda *_args: {"failure_process_id": BOUNDARY["root_process_id"]},
    )

    with pytest.raises(AssertionError):
        verifier._verify_case(
            "qfatal-root",
            Path("runner"),
            ["helper", "qfatal"],
            frozenset((verifier.STATUS_STACK_BUFFER_OVERRUN,)),
            {},
            tmp_path,
            1,
            "qfatal",
        )


def test_grandchild_must_match_root_exit_code(monkeypatch, tmp_path):
    calls = []

    def capture_case(*args, **kwargs):
        calls.append((args, kwargs))
        return {"exit_code": verifier.STATUS_STACK_BUFFER_OVERRUN}

    monkeypatch.setattr(verifier, "_verify_case", capture_case)
    args = SimpleNamespace(
        runner=Path("runner"),
        helper=Path("helper"),
        case_timeout=1,
    )

    verifier._verify_mode_pair(
        args,
        "abort",
        {},
        tmp_path,
        verifier.ABORT_EXIT_CODES,
    )

    assert len(calls) == 2
    assert calls[1][0][3] == frozenset((verifier.STATUS_STACK_BUFFER_OVERRUN,))
