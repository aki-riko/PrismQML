# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Automated test command boundary contracts. 自动测试命令边界契约。"""

import ast
import re
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANUAL_VISIBLE_ENTRYPOINTS = {
    Path("scripts/fps_probe.py"),
    Path("scripts/run_with_fps.py"),
    Path("tests/qml/bench_skin_frames.py"),
    Path("tests/test_window_buttons.py"),
}
PYTHON_EXECUTABLE_PATTERN = (
    r"(?:[^\s`]+/)?(?:python(?:3(?:\.\d+)?)?(?:\.exe)?|py(?:\.exe)?)"
)
PYTEST_COMMAND_PATTERN = re.compile(
    rf"(?<![\w.-]){PYTHON_EXECUTABLE_PATTERN}"
    r"\s+(?:-X\s+\S+\s+)?-m\s+pytest\b",
    re.IGNORECASE,
)
PYTHON_LAUNCHER_PATTERN = re.compile(
    rf"(?<![\w.-]){PYTHON_EXECUTABLE_PATTERN}\b",
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
RUNNER_PREFIX_PATTERN = re.compile(
    rf"^\s*(?:(?:[-*+>]|\d+\.)?\s*[`$]?\s*|(?:用法|usage)\s*:\s*)"
    rf"{PYTHON_EXECUTABLE_PATTERN}"
    r"\s+(?:-X\s+\S+\s+)?scripts/test_process\.py\b.*(?<!\S)--\s*$",
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


def _unprotected_commands_in_source(source: str, label: str) -> list[str]:
    failures = []
    for line_number, line in enumerate(source.splitlines(), start=1):
        normalized = line.replace("\\", "/")
        for segment in COMMAND_SEPARATOR_PATTERN.split(normalized):
            child_starts = _automated_child_starts(segment)
            if any(not _runner_precedes_child(segment, start) for start in child_starts):
                failures.append(f"{label}:{line_number}: {line.strip()}")
                break
    return failures


def _unprotected_documented_test_commands() -> list[str]:
    failures = []
    for relative in _automated_test_documents():
        source = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
        failures.extend(_unprotected_commands_in_source(source, relative.as_posix()))
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
