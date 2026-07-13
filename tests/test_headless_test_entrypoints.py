# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""测试入口默认无界面行为的回归验证。"""

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.test_process import (
    PROCESS_FORCE_KILL_WAIT_SECONDS,
    PROCESS_GRACEFUL_WAIT_SECONDS,
    WINDOWS_DESCENDANT_EXIT_GRACE_SECONDS,
    WINDOWS_JOB_CLEANUP_WAIT_SECONDS,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_PROCESS_RUNNER = REPO_ROOT / "scripts" / "test_process.py"
QT_PLATFORM_MUST_BE_OVERRIDDEN = "prismqml_must_be_overridden"
RUNNER_SUPERVISOR_GRACE_SECONDS = (
    WINDOWS_DESCENDANT_EXIT_GRACE_SECONDS
    + WINDOWS_JOB_CLEANUP_WAIT_SECONDS
    + PROCESS_GRACEFUL_WAIT_SECONDS
    + PROCESS_FORCE_KILL_WAIT_SECONDS
    + 10
)
MANUAL_VISIBLE_ENTRYPOINTS = {
    Path("scripts/fps_probe.py"),
    Path("scripts/run_with_fps.py"),
    Path("tests/qml/bench_skin_frames.py"),
    Path("tests/test_window_buttons.py"),
}
BOOTSTRAP_NAME = "configure_qml_test_process"
BOOTSTRAP_MODULE = "_test_process_bootstrap"
AUTOMATED_BOOTSTRAP_NAME = "prepare_automated_test_process"
TEST_PROCESS_BINDING = "TEST_PROCESS"
STANDALONE_QML_RUNTIME_CASES = (
    (Path("tests/qml/probe_neo_skin.py"), 15),
    (Path("tests/qml/test_card_autoheight.py"), 15),
    (Path("tests/qml/test_incubation_controller.py"), 15),
    (Path("tests/qml/test_lazy_reload.py"), 20),
    (Path("tests/qml/test_lazy_reload_components.py"), 20),
    (Path("tests/qml/test_system_tray_message_icon.py"), 10),
    (Path("tests/qml/test_realwindow_lazy_reload.py"), 30),
    (Path("tests/qml/test_splash_timing.py"), 20),
    (Path("tests/qml/test_splash_builder_fallback.py"), 20),
    (Path("tests/qml/test_page_manager_boundaries.py"), 20),
    (Path("tests/qml/test_window_default_visible.py"), 15),
    (Path("tests/qml/test_window_builder_file_fallback.py"), 15),
    (Path("tests/qml/test_close_request_handshake.py"), 15),
    (Path("tests/qml/test_splash_default_mount.py"), 15),
    (Path("tests/qml/test_timeline_virtual_shadow_padding.py"), 15),
    (Path("tests/qml/test_window_restore_visible_state.py"), 15),
)
AUTOMATED_QT_RUNTIME_COVERED_ELSEWHERE = {
    Path("tests/qml/probe_all_components.py"),
    Path("tests/test_input_focus_filter.py"),
    Path("tests/test_provider_lifecycle.py"),
}
SHARED_BOOTSTRAP_PROBE = """
import json
import os
import runpy
import sys

assert not any(name.startswith("PySide6") for name in sys.modules)
bootstrap = runpy.run_path("tests/qml/_test_process_bootstrap.py")
assert not any(name.startswith("PySide6") for name in sys.modules)
bootstrap["configure_qml_test_process"]()
from scripts.test_process import automated_test_process_is_noninteractive

sys.stdout.write(json.dumps({
    "platform": os.environ["QT_QPA_PLATFORM"],
    "noninteractive": automated_test_process_is_noninteractive(),
}))
"""


def _pyside_import_lines(tree: ast.Module) -> list[int]:
    lines: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("PySide6"):
            lines.append(node.lineno)
        if isinstance(node, ast.Import) and any(
            alias.name.startswith("PySide6") for alias in node.names
        ):
            lines.append(node.lineno)
    return sorted(lines)


def _contains_main_guard(test: ast.AST) -> bool:
    if isinstance(test, ast.BoolOp):
        return any(_contains_main_guard(value) for value in test.values)
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return False
    if not isinstance(test.ops[0], ast.Eq) or len(test.comparators) != 1:
        return False
    values = (test.left, test.comparators[0])
    return any(
        isinstance(value, ast.Name) and value.id == "__name__"
        for value in values
    ) and any(
        isinstance(value, ast.Constant) and value.value == "__main__"
        for value in values
    )


def _has_main_guard(tree: ast.Module) -> bool:
    return any(
        isinstance(node, ast.If) and _contains_main_guard(node.test)
        for node in tree.body
    )


def _trusted_bootstrap_import_line(tree: ast.Module) -> int | None:
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level != 0 or node.module != BOOTSTRAP_MODULE:
            continue
        if any(
            alias.name == BOOTSTRAP_NAME and alias.asname in (None, BOOTSTRAP_NAME)
            for alias in node.names
        ):
            return node.lineno
    return None


def _top_level_call_line(tree: ast.Module, function_name: str) -> int | None:
    for node in tree.body:
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        if node.value.args or node.value.keywords:
            continue
        function = node.value.func
        if isinstance(function, ast.Name) and function.id == function_name:
            return node.lineno
    return None


def _name_rebinding_lines(tree: ast.Module, name: str) -> list[int]:
    lines: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == name:
                lines.append(node.lineno)
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(
                isinstance(target, ast.Name) and target.id == name
                for target in targets
            ):
                lines.append(node.lineno)
    return sorted(lines)


def _repo_path_parts(node: ast.AST) -> list[str] | None:
    if isinstance(node, ast.Name) and node.id == "REPO_ROOT":
        return []
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Div):
        return None
    parts = _repo_path_parts(node.left)
    if parts is None or not isinstance(node.right, ast.Constant):
        return None
    if not isinstance(node.right.value, str):
        return None
    return [*parts, node.right.value]


def _is_test_process_runpy_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call) or len(node.args) != 1 or node.keywords:
        return False
    function = node.func
    if not (
        isinstance(function, ast.Attribute)
        and isinstance(function.value, ast.Name)
        and function.value.id == "runpy"
        and function.attr == "run_path"
    ):
        return False
    path_call = node.args[0]
    if not (
        isinstance(path_call, ast.Call)
        and isinstance(path_call.func, ast.Name)
        and path_call.func.id == "str"
        and len(path_call.args) == 1
        and not path_call.keywords
    ):
        return False
    return _repo_path_parts(path_call.args[0]) == ["scripts", "test_process.py"]


def _trusted_runpy_bootstrap_lines(
    tree: ast.Module,
) -> tuple[int | None, int | None, int | None]:
    load_line = None
    alias_line = None
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if target.id == TEST_PROCESS_BINDING and _is_test_process_runpy_call(node.value):
            load_line = node.lineno
        if target.id != AUTOMATED_BOOTSTRAP_NAME:
            continue
        value = node.value
        if not (
            isinstance(value, ast.Subscript)
            and isinstance(value.value, ast.Name)
            and value.value.id == TEST_PROCESS_BINDING
            and isinstance(value.slice, ast.Constant)
            and value.slice.value == AUTOMATED_BOOTSTRAP_NAME
        ):
            continue
        alias_line = node.lineno
    call_line = _top_level_call_line(tree, AUTOMATED_BOOTSTRAP_NAME)
    return load_line, alias_line, call_line


def _automated_qt_entrypoints() -> list[Path]:
    entrypoints: list[Path] = []
    for root_name in ("scripts", "tests"):
        for path in sorted((REPO_ROOT / root_name).rglob("*.py")):
            relative = path.relative_to(REPO_ROOT)
            if relative in MANUAL_VISIBLE_ENTRYPOINTS:
                continue
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(relative))
            if _has_main_guard(tree) and _pyside_import_lines(tree):
                entrypoints.append(relative)
    return entrypoints


def _run_shared_bootstrap_probe() -> subprocess.CompletedProcess[str]:
    env = _clean_qt_platform_environment()
    env["QT_QPA_PLATFORM"] = "windows"
    return subprocess.run(
        [sys.executable, "-c", SHARED_BOOTSTRAP_PROBE],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )


def _qml_bootstrap_state(
    tree: ast.Module, pyside_line: int
) -> tuple[bool, tuple[int | None, int | None, list[int]]]:
    import_line = _trusted_bootstrap_import_line(tree)
    call_line = _top_level_call_line(tree, BOOTSTRAP_NAME)
    rebindings = _name_rebinding_lines(tree, BOOTSTRAP_NAME)
    valid = (
        import_line is not None
        and call_line is not None
        and import_line < call_line < pyside_line
        and not rebindings
    )
    return valid, (import_line, call_line, rebindings)


def _runpy_bootstrap_state(
    tree: ast.Module, pyside_line: int
) -> tuple[bool, tuple[tuple[int | None, int | None, int | None], list[int]]]:
    lines = _trusted_runpy_bootstrap_lines(tree)
    rebindings = _name_rebinding_lines(tree, AUTOMATED_BOOTSTRAP_NAME)
    load_line, alias_line, call_line = lines
    valid = (
        load_line is not None
        and alias_line is not None
        and call_line is not None
        and load_line < alias_line < call_line < pyside_line
        and rebindings == [alias_line]
    )
    return valid, (lines, rebindings)


def _entrypoint_bootstrap_failure(relative: Path) -> str | None:
    source = (REPO_ROOT / relative).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(relative))
    pyside_line = min(_pyside_import_lines(tree))
    qml_valid, qml_state = _qml_bootstrap_state(tree, pyside_line)
    runpy_valid, runpy_state = _runpy_bootstrap_state(tree, pyside_line)
    if qml_valid or runpy_valid:
        return None
    return (
        f"{relative.as_posix()}: qml={qml_state}, runpy={runpy_state}, "
        f"PySide={pyside_line}"
    )


def _clean_qt_platform_environment() -> dict[str, str]:
    """返回移除 Qt 平台覆盖后的子进程环境。"""
    env = os.environ.copy()
    env.pop("QT_QPA_PLATFORM", None)
    return env


def test_probe_defaults_to_headless_through_process_runner():
    """runner 启动全组件 probe 时由入口自身启用 headless。"""
    result = subprocess.run(
        [
            sys.executable, str(TEST_PROCESS_RUNNER),
            "--qt-platform", "inherit", "--timeout", "60", "--",
            sys.executable, "-X", "utf8", "tests/qml/probe_all_components.py",
        ],
        cwd=REPO_ROOT,
        env=_clean_qt_platform_environment(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60 + RUNNER_SUPERVISOR_GRACE_SECONDS,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    summary = re.search(
        r"组件加载 probe 结果:\s+\d+ OK / (\d+) 错误 / \d+ 跳过",
        result.stdout,
    )
    assert summary is not None, result.stdout
    assert int(summary.group(1)) == 0


def test_pytest_conftest_forces_headless_even_with_explicit_platform_value():
    """conftest 必须覆盖可能弹窗的调用者平台配置。"""
    code = """
import os
import runpy

os.environ.pop("QT_QPA_PLATFORM", None)
runpy.run_path("tests/conftest.py")
assert os.environ["QT_QPA_PLATFORM"] == "offscreen"

os.environ["QT_QPA_PLATFORM"] = "minimal"
runpy.run_path("tests/conftest.py")
assert os.environ["QT_QPA_PLATFORM"] == "offscreen"
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env=_clean_qt_platform_environment(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_shared_qml_bootstrap_forces_noninteractive_policy_before_pyside_import():
    """共享入口必须覆盖可视平台，并且自身不得提前加载 PySide6。"""
    result = _run_shared_bootstrap_probe()
    assert result.returncode == 0, result.stdout + result.stderr
    state = json.loads(result.stdout)
    assert state == {"platform": "offscreen", "noninteractive": True}


def test_standalone_qt_entrypoints_bootstrap_before_pyside_import():
    """可直接执行的自动 Qt 入口必须先接入统一无界面策略。"""
    missing_manual = sorted(
        path.as_posix()
        for path in MANUAL_VISIBLE_ENTRYPOINTS
        if not (REPO_ROOT / path).is_file()
    )
    assert missing_manual == []

    failures = [
        failure
        for relative in _automated_qt_entrypoints()
        if (failure := _entrypoint_bootstrap_failure(relative)) is not None
    ]
    assert failures == []


def test_runtime_matrix_covers_every_automated_qt_entrypoint():
    """新增自动 Qt 入口必须加入运行矩阵或已有专项运行门禁。"""
    runtime_paths = [path for path, _timeout in STANDALONE_QML_RUNTIME_CASES]
    assert len(runtime_paths) == len(set(runtime_paths))
    covered = set(runtime_paths) | AUTOMATED_QT_RUNTIME_COVERED_ELSEWHERE
    assert covered == set(_automated_qt_entrypoints())


@pytest.mark.parametrize(
    ("relative", "timeout"),
    STANDALONE_QML_RUNTIME_CASES,
    ids=[path.stem for path, _timeout in STANDALONE_QML_RUNTIME_CASES],
)
def test_standalone_qml_entrypoint_runtime(relative: Path, timeout: int):
    """入口必须覆盖无效平台哨兵，并在 offscreen 下按时通过。"""
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = QT_PLATFORM_MUST_BE_OVERRIDDEN
    try:
        result = subprocess.run(
            [
                sys.executable, str(TEST_PROCESS_RUNNER),
                "--qt-platform", "inherit", "--timeout", str(timeout), "--",
                sys.executable, "-X", "utf8", str(relative),
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout + RUNNER_SUPERVISOR_GRACE_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        pytest.fail(
            f"{relative.as_posix()} runner cleanup timed out: "
            f"stdout={error.stdout!r} stderr={error.stderr!r}"
        )
    assert result.returncode == 0, result.stdout + result.stderr
