# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Runner boundary guard contracts. Runner 边界防误用契约。"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

import scripts.test_process as test_process
from scripts.test_process import (
    AUTOMATED_TEST_BOUNDARY_ENV,
    AUTOMATED_TEST_BOUNDARY_VERSION,
    automated_test_boundary_is_active,
    configure_automated_test_process,
    require_automated_test_boundary,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "test_process.py"
BOUNDARY_ERROR = "run through scripts/test_process.py"
CANARY_PLUGIN = "tests._pytest_qt_import_canary"
CANARY_SENTINEL_ENV = "PRISMQML_PYTEST_QT_CANARY_SENTINEL"
BOUNDARY_CHAIN_PROBE_CODE = f"""
import json
import os
import subprocess
import sys

from scripts.test_process import automated_test_boundary_is_active

marker = {AUTOMATED_TEST_BOUNDARY_ENV!r}
grandchild_code = (
    "import json,os; "
    "from scripts.test_process import automated_test_boundary_is_active; "
    "print(json.dumps({{'marker': os.environ[%r], "
    "'active': automated_test_boundary_is_active()}}))" % marker
)
grandchild = subprocess.run(
    [sys.executable, "-c", grandchild_code],
    capture_output=True,
    text=True,
    encoding="utf-8",
    check=False,
)
raise_code = grandchild.returncode
sys.stdout.write(json.dumps({{
    "child": {{
        "marker": os.environ[marker],
        "active": automated_test_boundary_is_active(),
    }},
    "grandchild": json.loads(grandchild.stdout),
}}))
raise SystemExit(raise_code)
"""


def _without_boundary_marker() -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop(AUTOMATED_TEST_BOUNDARY_ENV, None)
    return environment


def _run_runner(*command: str, timeout: int = 60):
    return subprocess.run(
        [
            sys.executable, str(RUNNER),
            "--qt-platform", "offscreen", "--timeout", str(timeout), "--",
            *command,
        ],
        cwd=REPO_ROOT,
        env=_without_boundary_marker(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout + 30,
        check=False,
    )


@pytest.mark.parametrize("value", (None, "", "v0", "invalid"))
def test_boundary_requirement_rejects_missing_or_invalid(monkeypatch, value):
    if value is None:
        monkeypatch.delenv(AUTOMATED_TEST_BOUNDARY_ENV, raising=False)
    else:
        monkeypatch.setenv(AUTOMATED_TEST_BOUNDARY_ENV, value)
    with pytest.raises(RuntimeError, match="scripts/test_process.py"):
        require_automated_test_boundary()


def test_low_level_configuration_does_not_create_boundary_marker(monkeypatch):
    monkeypatch.delenv(AUTOMATED_TEST_BOUNDARY_ENV, raising=False)
    configure_automated_test_process(None)
    assert not automated_test_boundary_is_active()
    assert AUTOMATED_TEST_BOUNDARY_ENV not in os.environ


@pytest.mark.skipif(sys.platform != "win32", reason="Windows boundary only")
def test_forged_marker_is_rejected_without_windows_boundary(monkeypatch):
    monkeypatch.setenv(
        AUTOMATED_TEST_BOUNDARY_ENV, AUTOMATED_TEST_BOUNDARY_VERSION
    )
    monkeypatch.setattr(
        test_process,
        "current_process_test_boundary_status",
        lambda: (False, "desktop 'Default' is not a PrismQML test desktop"),
    )

    assert not automated_test_boundary_is_active()
    with pytest.raises(RuntimeError, match="desktop 'Default'"):
        require_automated_test_boundary()


def test_runner_marks_and_attests_child_and_grandchild():
    result = _run_runner(sys.executable, "-c", BOUNDARY_CHAIN_PROBE_CODE)

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == {
        "child": {"marker": AUTOMATED_TEST_BOUNDARY_VERSION, "active": True},
        "grandchild": {
            "marker": AUTOMATED_TEST_BOUNDARY_VERSION,
            "active": True,
        },
    }


def test_missing_marker_pytest_is_rejected_before_collection():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_qml_conventions.py", "-q"],
        cwd=REPO_ROOT,
        env=_without_boundary_marker(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert BOUNDARY_ERROR in output
    assert "passed" not in output


def test_pytest_boundary_plugin_is_loaded(pytestconfig):
    assert pytestconfig.pluginmanager.hasplugin("scripts.pytest_boundary")
    assert pytestconfig.option.disable_plugin_autoload is True


def test_pytest_boundary_plugin_runs_before_explicit_plugins(tmp_path):
    sentinel = tmp_path / "qt-import-canary.json"
    environment = _without_boundary_marker()
    environment["QT_QPA_PLATFORM"] = "prism-boundary-sentinel"
    environment[CANARY_SENTINEL_ENV] = str(sentinel)
    result = subprocess.run(
        [
            sys.executable, str(RUNNER),
            "--qt-platform", "inherit", "--timeout", "60", "--",
            sys.executable, "-m", "pytest", "-p", CANARY_PLUGIN,
            "tests/test_qml_conventions.py", "-q",
        ],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(sentinel.read_text(encoding="utf-8")) == {
        "boundary_active": True,
        "pyside_preloaded": False,
        "qt_platform": "offscreen",
    }


def test_protected_pytest_still_runs():
    result = _run_runner(
        sys.executable, "-m", "pytest", "tests/test_qml_conventions.py", "-q"
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "passed" in result.stdout


def test_missing_marker_probe_is_rejected_before_qt_import():
    result = subprocess.run(
        [sys.executable, "tests/qml/probe_all_components.py"],
        cwd=REPO_ROOT,
        env=_without_boundary_marker(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert BOUNDARY_ERROR in output
    assert "组件加载 probe 结果" not in output


def test_protected_probe_still_runs():
    result = _run_runner(
        sys.executable, "tests/qml/probe_all_components.py", timeout=90
    )

    assert result.returncode == 0, result.stdout + result.stderr
    summary = re.search(r"(\d+) OK / (\d+) 错误 / (\d+) 跳过", result.stdout)
    assert summary is not None, result.stdout
    assert int(summary.group(2)) == 0
