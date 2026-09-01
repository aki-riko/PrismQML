# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Automated test command boundary contracts. 自动测试命令边界契约。"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANUAL_VISIBLE_ENTRYPOINTS = {
    Path("scripts/fps_probe.py"),
    Path("scripts/run_with_fps.py"),
    Path("tests/qml/bench_skin_frames.py"),
    Path("tests/test_window_buttons.py"),
}
PYTHON_BASENAME_PATTERN = (
    r"(?:python(?:3(?:\.\d+)?)?(?:\.exe)?|py(?:\.exe)?)"
)
PYTHON_EXECUTABLE_PATTERN = (
    rf"(?:[\"'](?:[^\"']*/)?{PYTHON_BASENAME_PATTERN}[\"']"
    rf"|(?:[^\s`\"']+/)?{PYTHON_BASENAME_PATTERN})"
)
PYTEST_COMMAND_PATTERN = re.compile(
    rf"(?<![\w.-]){PYTHON_EXECUTABLE_PATTERN}"
    r"\s+(?:-X\s+\S+\s+)?-m\s+pytest\b",
    re.IGNORECASE,
)
PYTHON_LAUNCHER_PATTERN = re.compile(
    rf"(?<![\w.-]){PYTHON_EXECUTABLE_PATTERN}(?=\s|$)",
    re.IGNORECASE,
)
BARE_PYTEST_COMMAND_PATTERN = re.compile(
    r"^\s*(?:(?:[-*+>]|\d+\.)?\s*[`$]?\s*|(?:用法|usage)\s*:\s*)"
    r"(pytest(?:\.exe)?\b)"
    r"(?=\s*(?:`?\s*$|--?[\w-]|(?:tests?|\.{1,2})(?:/|\\)|[^\s`]+\.py\b))",
    re.IGNORECASE,
)
TEST_SCRIPT_PATTERN = re.compile(
    r"(?P<path>(?:cpp/)?tests/[A-Za-z0-9_./-]+\.py)\b",
    re.IGNORECASE,
)
COMMAND_SEPARATOR_PATTERN = re.compile(r"\s*(?:&&|\|\||;)\s*")
WORKFLOW_BLOCK_STYLES = {"|", "|-", "|+", ">", ">-", ">+"}
RUNNER_SCRIPT_PATTERN = (
    r"(?:[\"'`][^\"'`]*scripts/test_process\.py[\"'`]"
    r"|[^\s\"'`]*scripts/test_process\.py)"
)
RUNNER_PREFIX_PATTERN = re.compile(
    rf"^\s*(?:(?:[-*+>]|\d+\.)?\s*[`$]?\s*|(?:用法|usage)\s*:\s*)"
    rf"{PYTHON_EXECUTABLE_PATTERN}"
    rf"\s+(?:-X\s+\S+\s+)?{RUNNER_SCRIPT_PATTERN}.*(?<!\S)--\s*$",
    re.IGNORECASE,
)


def _automated_test_documents() -> tuple[Path, ...]:
    candidates = {PROJECT_ROOT / "AGENTS.md"}
    candidates.update(PROJECT_ROOT.glob("README*.md"))
    candidates.update((PROJECT_ROOT / "docs").rglob("*.md"))
    candidates.update((PROJECT_ROOT / "cpp").glob("README*.md"))
    return tuple(path.relative_to(PROJECT_ROOT) for path in sorted(candidates))


def _automated_child_starts(segment: str) -> list[int]:
    starts = [match.start() for match in PYTEST_COMMAND_PATTERN.finditer(segment)]
    bare_pytest = BARE_PYTEST_COMMAND_PATTERN.match(segment)
    if bare_pytest is not None:
        starts.append(bare_pytest.start(1))
    for script_match in TEST_SCRIPT_PATTERN.finditer(segment):
        relative = Path(script_match.group("path"))
        if relative in MANUAL_VISIBLE_ENTRYPOINTS:
            continue
        launchers = list(
            PYTHON_LAUNCHER_PATTERN.finditer(segment, 0, script_match.start())
        )
        if launchers:
            starts.append(launchers[-1].start())
    return sorted(set(starts))


def _runner_precedes_child(segment: str, child_start: int) -> bool:
    return RUNNER_PREFIX_PATTERN.match(segment[:child_start]) is not None


def _logical_command_lines(source: str) -> list[tuple[int, str]]:
    commands = []
    parts = []
    start_line = 1
    for line_number, line in enumerate(source.splitlines(), start=1):
        if not parts:
            start_line = line_number
        continued = line.rstrip().endswith(("\\", "`"))
        parts.append(line.rstrip()[:-1] if continued else line)
        if continued:
            continue
        commands.append((start_line, " ".join(part.strip() for part in parts)))
        parts = []
    if parts:
        commands.append((start_line, " ".join(part.strip() for part in parts)))
    return commands


def _unprotected_commands_in_source(
    source: str,
    label: str,
    line_offset: int = 0,
    join_continuations: bool = False,
) -> list[str]:
    failures = []
    lines = (
        _logical_command_lines(source)
        if join_continuations
        else list(enumerate(source.splitlines(), start=1))
    )
    for line_number, line in lines:
        normalized = line.replace("\\", "/")
        for segment in COMMAND_SEPARATOR_PATTERN.split(normalized):
            child_starts = _automated_child_starts(segment)
            if any(not _runner_precedes_child(segment, start) for start in child_starts):
                actual_line = line_number + line_offset
                failures.append(f"{label}:{actual_line}: {line.strip()}")
                break
    return failures


def _unprotected_documented_test_commands() -> list[str]:
    failures = []
    for relative in _automated_test_documents():
        source = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
        failures.extend(_unprotected_commands_in_source(source, relative.as_posix()))
    return failures


def _indent_width(line: str) -> int:
    return len(line) - len(line.lstrip())


def _workflow_scalar(
    lines: list[str], index: int, indent: int, body: str
) -> tuple[str, int]:
    is_block = body in WORKFLOW_BLOCK_STYLES
    parts = [] if is_block else [body]
    folded = body.startswith(">")
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            if not is_block:
                break
            parts.append("")
            index += 1
            continue
        if _indent_width(line) <= indent:
            break
        if not is_block and not parts[-1].rstrip().endswith(("\\", "`")):
            break
        parts.append(line.strip())
        index += 1
    separator = " " if folded else "\n"
    return separator.join(parts), index


def _workflow_test_command_blocks(source: str) -> list[tuple[int, str]]:
    lines = source.splitlines()
    commands = []
    index = 0
    pattern = re.compile(
        r"^(?P<indent>\s*)(?:-\s+)?"
        r"(?:run|[A-Z][A-Z0-9_]*TEST_COMMAND):\s*(?P<body>.*)$"
    )
    while index < len(lines):
        key_line = index + 1
        match = pattern.match(lines[index])
        index += 1
        if match is None:
            continue
        command, index = _workflow_scalar(
            lines, index, len(match.group("indent")), match.group("body").strip()
        )
        body = match.group("body").strip()
        start_line = key_line + 1 if body in WORKFLOW_BLOCK_STYLES else key_line
        commands.append((start_line, command))
    return commands


def _workflow_test_commands(source: str) -> list[str]:
    return [command for _line, command in _workflow_test_command_blocks(source)]


def _unprotected_workflow_test_commands() -> list[str]:
    failures = []
    workflow_root = PROJECT_ROOT / ".github" / "workflows"
    for path in sorted((*workflow_root.glob("*.yml"), *workflow_root.glob("*.yaml"))):
        relative = path.relative_to(PROJECT_ROOT).as_posix()
        source = path.read_text(encoding="utf-8")
        for start_line, command in _workflow_test_command_blocks(source):
            failures.extend(
                _unprotected_commands_in_source(
                    command,
                    relative,
                    line_offset=start_line - 1,
                    join_continuations=True,
                )
            )
    return failures


def _usage_docstrings() -> list[tuple[Path, str]]:
    results = []
    roots = (PROJECT_ROOT / "scripts", PROJECT_ROOT / "tests", PROJECT_ROOT / "cpp" / "tests")
    for root in roots:
        for path in sorted(root.rglob("*.py")):
            relative = path.relative_to(PROJECT_ROOT)
            if relative in MANUAL_VISIBLE_ENTRYPOINTS:
                continue
            source = path.read_text(encoding="utf-8")
            docstring = ast.get_docstring(ast.parse(source), clean=False) or ""
            if re.search(r"(?im)^(?:用法|usage)\s*:", docstring):
                results.append((relative, docstring))
    return results


def test_documented_automated_test_commands_use_process_runner():
    assert _unprotected_documented_test_commands() == []


def test_automated_test_usage_docstrings_use_process_runner():
    failures = []
    for relative, docstring in _usage_docstrings():
        failures.extend(
            _unprotected_commands_in_source(docstring, relative.as_posix())
        )
    assert failures == []


def test_ci_automated_test_commands_use_process_runner():
    assert _unprotected_workflow_test_commands() == []


@pytest.mark.parametrize(
    ("relative", "timeout_reference", "timeout_seconds"),
    (
        (
            Path(".github/workflows/build-all.yml"),
            "$env:PRISM_FULL_PYTEST_TIMEOUT_SECONDS",
            2400,
        ),
        (
            Path(".github/workflows/release.yml"),
            "$PRISM_FULL_PYTEST_TIMEOUT_SECONDS",
            2400,
        ),
    ),
)
def test_ci_full_python_gates_have_current_timeout_budget(
    relative: Path,
    timeout_reference: str,
    timeout_seconds: int,
):
    """全量 Python CI 必须保留对应 runner 的时间余量。"""
    source = (PROJECT_ROOT / relative).read_text(encoding="utf-8")

    assert f'PRISM_FULL_PYTEST_TIMEOUT_SECONDS: "{timeout_seconds}"' in source
    assert f"--timeout {timeout_reference} --" in source


def test_release_linux_wheel_probe_provisions_openssl3_runtime():
    """Linux wheel probe must match Qt's OpenSSL runtime.

    Linux wheel 探测必须匹配 Qt 所需的 OpenSSL 运行时。
    """
    source = (PROJECT_ROOT / ".github/workflows/release.yml").read_text(
        encoding="utf-8"
    )

    assert 'dnf install -y "$PRISM_EPEL_RELEASE_RPM"' in source
    assert "dnf install -y openssl3-libs" in source
    assert "PRISM_EPEL_RELEASE_RPM=https://" in source


def test_release_python_compatibility_matrix_blocks_publish():
    """Published abi3 wheel must pass every supported Python minor.

    发布的 abi3 wheel 必须通过全部受支持 Python 小版本。
    """
    source = (PROJECT_ROOT / ".github/workflows/release.yml").read_text(
        encoding="utf-8"
    )

    assert (
        'python-version: ["3.9", "3.10", "3.11", "3.12", "3.13", "3.14"]'
        in source
    )
    assert "name: wheels-ubuntu-latest" in source
    assert "probe_all_components.py\" --installed" in source
    assert (
        "needs: [quality_gate, build_wheels, python_compatibility, build_sdist]"
        in source
    )


@pytest.mark.parametrize(
    "source",
    (
        "steps:\n  - run: python -m pytest -q\n",
        "steps:\n  - run: |\n      python \\\n        -m pytest -q\n",
        "steps:\n  - run: |\n      echo before\n\n      python -m pytest -q\n",
        "env:\n  CIBW_TEST_COMMAND: >-\n    python -m pytest -q\n",
    ),
)
def test_workflow_guard_rejects_unprotected_command_fields(source: str):
    commands = _workflow_test_commands(source)
    assert commands
    assert any(
        _unprotected_commands_in_source(
            command, "synthetic", join_continuations=True
        )
        for command in commands
    )


def test_workflow_guard_reports_yaml_source_line():
    source = (
        "name: synthetic\nsteps:\n  - run: |\n"
        "      echo before\n\n      python -m pytest -q\n"
    )
    start_line, command = _workflow_test_command_blocks(source)[0]
    failures = _unprotected_commands_in_source(
        command,
        "synthetic",
        line_offset=start_line - 1,
        join_continuations=True,
    )

    assert failures == ["synthetic:6: python -m pytest -q"]


def test_workflow_guard_preserves_line_after_continuation():
    source = (
        "steps:\n  - run: |\n      echo before \\\n"
        "        continued\n      python -m pytest -q\n"
    )
    start_line, command = _workflow_test_command_blocks(source)[0]
    failures = _unprotected_commands_in_source(
        command,
        "synthetic",
        line_offset=start_line - 1,
        join_continuations=True,
    )

    assert failures == ["synthetic:5: python -m pytest -q"]


@pytest.mark.parametrize(
    "command",
    (
        "python -m pytest  # runner: scripts/test_process.py",
        "python3 -m pytest tests/test_core.py",
        "py -m pytest -q",
        "pytest -q",
        "python tests/qml/probe_all_components.py",
        "python scripts/test_process.py -- python -m pytest; python -m pytest",
        "python scripts/test_process.py python -m pytest",
        "echo scripts/test_process.py -- python -m pytest",
        "echo python scripts/test_process.py -- python -m pytest",
    ),
)
def test_command_guard_rejects_unprotected_forms(command: str):
    assert _unprotected_commands_in_source(command, "synthetic")


def test_command_guard_allows_protected_and_manual_forms():
    source = (
        "python scripts/test_process.py --qt-platform offscreen -- "
        "python -m pytest\n"
        "python tests/qml/bench_skin_frames.py"
    )
    assert _unprotected_commands_in_source(source, "synthetic") == []


def _assert_cpp_test_targets_use_registration_helper(content: str) -> None:
    targets = re.findall(
        r"qt_add_executable\(\s*(prism_test_[A-Za-z0-9_]+)", content
    )
    assert targets
    for target in targets:
        registration = re.compile(
            rf"prism_add_cpp_test\(\s*{re.escape(target)}\s+{re.escape(target)}\b"
        )
        assert registration.search(content), f"unprotected CTest target: {target}"


def test_cpp_tests_are_registered_through_process_runner():
    content = (PROJECT_ROOT / "cpp" / "CMakeLists.txt").read_text(encoding="utf-8")
    function_match = re.search(
        r"function\(prism_add_cpp_test\b(?P<body>.*?)endfunction\(\)",
        content,
        re.DOTALL,
    )
    assert function_match is not None
    function_body = function_match.group("body")
    assert function_body.count("${PRISM_TEST_PROCESS_RUNNER}") == 2
    assert 'PATH=$<TARGET_FILE_DIR:Qt6::Core>' in function_body

    add_test_blocks = re.findall(r"\badd_test\s*\((.*?)\)", content, re.DOTALL)
    assert add_test_blocks
    assert all(
        "${PRISM_TEST_PROCESS_RUNNER}" in block for block in add_test_blocks
    )

    _assert_cpp_test_targets_use_registration_helper(content)

    assert re.search(
        r'COMMAND\s+"\$<TARGET_FILE:prism_test_[A-Za-z0-9_]+>"', content
    ) is None
