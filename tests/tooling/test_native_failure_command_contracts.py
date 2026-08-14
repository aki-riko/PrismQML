# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Native failure command-boundary contracts. 原生失败命令边界契约。"""

from __future__ import annotations

import ast
import re
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
NATIVE_FAILURE_TARGETS = {
    "prism_native_failure_helper",
    "prism_native_failure_loader",
    "prism_native_failure_companion",
}
NATIVE_FAILURE_PATTERN = re.compile(
    r"\bprism_native_failure_(?:helper|loader|companion)\b"
)
NATIVE_FAILURE_CMAKE_REFERENCES = (
    (
        "add_library",
        "prism_native_failure_companion SHARED "
        "tests/native_failure_companion.cpp",
    ),
    (
        "add_executable",
        "prism_native_failure_loader tests/native_failure_loader.cpp",
    ),
    (
        "target_link_libraries",
        "prism_native_failure_loader PRIVATE prism_native_failure_companion",
    ),
    (
        "set_target_properties",
        "prism_native_failure_companion PROPERTIES "
        'RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/'
        'native-failure-companion"',
    ),
    (
        "set_target_properties",
        "prism_native_failure_loader PROPERTIES "
        'RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/'
        'native-failure-loader"',
    ),
    (
        "add_executable",
        "prism_native_failure_helper tests/native_failure_helper.cpp",
    ),
    (
        "target_link_libraries",
        "prism_native_failure_helper PRIVATE Qt6::Core",
    ),
    (
        "set_target_properties",
        "prism_native_failure_helper PROPERTIES "
        'RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/'
        'native-failure-helper"',
    ),
    (
        "foreach",
        "_native_failure_target IN ITEMS prism_native_failure_companion "
        "prism_native_failure_loader prism_native_failure_helper",
    ),
)


def _cmake_blocks(content: str, command: str) -> list[str]:
    return re.findall(rf"\b{command}\s*\((.*?)\)", content, re.DOTALL)


def _only_block(blocks: list[str], label: str) -> str:
    assert len(blocks) == 1, f"expected one {label}, got {len(blocks)}"
    return blocks[0]


def _assert_fixture_targets(content: str) -> None:
    targets = set(
        re.findall(
            r"\badd_(?:executable|library)\(\s*"
            r"(prism_native_failure_(?:helper|loader|companion))",
            content,
        )
    )
    assert targets == NATIVE_FAILURE_TARGETS


def _assert_runner_binding(content: str) -> None:
    bindings = [
        " ".join(block.split())
        for block in _cmake_blocks(content, "set")
        if block.lstrip().startswith("PRISM_TEST_PROCESS_RUNNER")
    ]
    assert bindings == [
        "PRISM_TEST_PROCESS_RUNNER "
        '"${CMAKE_CURRENT_SOURCE_DIR}/../scripts/test_process.py"'
    ]


def _matrix_block(content: str) -> tuple[str, list[str]]:
    blocks = _cmake_blocks(content, "add_test")
    matrices = [
        block
        for block in blocks
        if re.search(r"\bNAME\s+prism_native_failure_matrix\b", block)
    ]
    return _only_block(matrices, "native matrix"), blocks


def _assert_matrix_chain(matrix_block: str) -> None:
    matrix = " ".join(matrix_block.split())
    chain = (
        'COMMAND "${Python3_EXECUTABLE}" "${PRISM_TEST_PROCESS_RUNNER}" '
        '--qt-platform offscreen '
        '--timeout "${PRISM_NATIVE_FAILURE_MATRIX_TIMEOUT_SECONDS}" -- '
        '"${Python3_EXECUTABLE}" '
        '"${CMAKE_CURRENT_SOURCE_DIR}/tests/verify_native_failures.py" '
        '--runner "${PRISM_TEST_PROCESS_RUNNER}"'
    )
    assert chain in matrix
    assert (
        '--case-timeout "${PRISM_NATIVE_FAILURE_CASE_TIMEOUT_SECONDS}"'
        in matrix
    )
    target_pattern = re.compile(
        r"\$<TARGET_FILE:(prism_native_failure_(?:helper|loader|companion))>"
    )
    assert set(target_pattern.findall(matrix)) == NATIVE_FAILURE_TARGETS


def _assert_matrix_timeout(content: str) -> None:
    blocks = [
        " ".join(block.split())
        for block in _cmake_blocks(content, "set_tests_properties")
        if block.lstrip().startswith("prism_native_failure_matrix")
    ]
    block = _only_block(blocks, "native matrix properties")
    assert 'TIMEOUT "${PRISM_NATIVE_FAILURE_CTEST_TIMEOUT_SECONDS}"' in block


def _fixture_references(content: str) -> list[tuple[str, str]]:
    return [
        (match.group("command"), " ".join(match.group("body").split()))
        for match in re.finditer(
            r"\b(?P<command>[A-Za-z_][A-Za-z0-9_]*)\s*"
            r"\((?P<body>.*?)\)",
            content,
            re.DOTALL,
        )
        if NATIVE_FAILURE_PATTERN.search(match.group("body"))
    ]


def _assert_exact_fixture_references(content: str, matrix_block: str) -> None:
    expected = (
        *NATIVE_FAILURE_CMAKE_REFERENCES,
        ("add_test", " ".join(matrix_block.split())),
    )
    assert Counter(_fixture_references(content)) == Counter(expected)


def test_native_failure_cmake_chain_is_fail_closed():
    content = (PROJECT_ROOT / "cpp" / "CMakeLists.txt").read_text(
        encoding="utf-8"
    )
    _assert_fixture_targets(content)
    _assert_runner_binding(content)
    matrix_block, _add_test_blocks = _matrix_block(content)
    _assert_matrix_chain(matrix_block)
    _assert_matrix_timeout(content)
    _assert_exact_fixture_references(content, matrix_block)


def _parent_nodes(module: ast.Module) -> dict[ast.AST, ast.AST]:
    return {
        child: parent
        for parent in ast.walk(module)
        for child in ast.iter_child_nodes(parent)
    }


def _enclosing_function(node: ast.AST, parents: dict) -> str | None:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current.name
    return None


def _assert_subprocess_import(module: ast.Module) -> None:
    imports = [
        alias
        for node in ast.walk(module)
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.name == "subprocess"
    ]
    assert [(alias.name, alias.asname) for alias in imports] == [
        ("subprocess", None)
    ]
    assert not any(
        isinstance(node, ast.ImportFrom) and node.module == "subprocess"
        for node in ast.walk(module)
    )


def _only_process_call(module: ast.Module) -> ast.Call:
    _assert_subprocess_import(module)
    attributes = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "subprocess"
    ]
    assert {item.attr for item in attributes} <= {"run", "CompletedProcess"}
    run_attributes = [item for item in attributes if item.attr == "run"]
    assert len(run_attributes) == 1
    parents = _parent_nodes(module)
    call = parents[run_attributes[0]]
    assert isinstance(call, ast.Call) and call.func is run_attributes[0]
    assert _enclosing_function(call, parents) == "_run_case"
    assert len(call.args) == 1
    assert all(keyword.arg is not None for keyword in call.keywords)
    keywords = {keyword.arg for keyword in call.keywords}
    assert not {"shell", "executable"} & keywords
    return call


def _assert_no_alternative_process_calls(module: ast.Module) -> None:
    forbidden = re.compile(
        r"^(?:os\.(?:system|popen|startfile|spawn\w*|exec\w*)|"
        r"asyncio\.create_subprocess_\w+|multiprocessing\.Process)$"
    )
    calls = [
        ast.unparse(node.func)
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
    ]
    assert [name for name in calls if forbidden.match(name)] == []


def _runner_command_list(module: ast.Module) -> ast.List:
    function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "_runner_command"
    )
    returns = [node for node in ast.walk(function) if isinstance(node, ast.Return)]
    assert len(returns) == 1
    assert isinstance(returns[0].value, ast.List)
    return returns[0].value


def _assert_runner_command_shape(module: ast.Module, call: ast.Call) -> None:
    assert ast.unparse(call.args[0]) == (
        "_runner_command(runner, command, case_timeout)"
    )
    command = _runner_command_list(module)
    assert ast.unparse(command.elts[0]) == "sys.executable"
    assert ast.unparse(command.elts[1]) == "str(runner)"
    separator = next(
        index
        for index, element in enumerate(command.elts)
        if isinstance(element, ast.Constant) and element.value == "--"
    )
    assert separator > 1
    assert isinstance(command.elts[separator + 1], ast.Starred)
    assert ast.unparse(command.elts[separator + 1].value) == "command"


def test_native_failure_verifier_only_spawns_through_runner():
    source = (
        PROJECT_ROOT / "cpp" / "tests" / "verify_native_failures.py"
    ).read_text(encoding="utf-8")
    module = ast.parse(source)

    _assert_runner_command_shape(module, _only_process_call(module))
    _assert_no_alternative_process_calls(module)
