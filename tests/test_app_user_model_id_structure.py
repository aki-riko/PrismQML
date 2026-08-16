# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""AUMID derivation structure contracts. AUMID 派生结构合同。"""

from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

from prismqml.python import window as window_module


_SOURCE_PATH = Path(window_module.__file__).resolve()
_PYTHON_ROOT = _SOURCE_PATH.parents[1]
_TARGET_FUNCTIONS = {
    "_derive_executable_app_user_model_id",
    "_derive_current_script_app_user_model_id",
    "_derive_app_user_model_id",
}
_CONTROL_FLOW_NODES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Try,
    ast.With,
    ast.AsyncWith,
)
_NESTED_FUNCTION_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
_MAX_FILE_LINES = 699
_MAX_FUNCTION_LINES = 30
_MAX_CONTROL_DEPTH = 2
_MAX_LONG_FUNCTIONS = 14
_MAX_LONG_FUNCTIONS_BY_AREA = {
    "core": 7,
    "models": 0,
    "providers": 2,
    "runtime": 2,
    "state": 0,
    "window": 5,
}


def _parse_source(path: Path) -> tuple[str, ast.Module]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path), feature_version=(3, 9))
    return source, tree


def _function_nodes(tree: ast.Module):
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def _direct_functions(nodes, name):
    return [
        node
        for node in nodes
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    ]


def _control_depth(node: ast.AST) -> int:
    def visit(current: ast.AST, depth: int) -> int:
        if current is not node and isinstance(current, _NESTED_FUNCTION_NODES):
            return depth
        current_depth = depth + int(isinstance(current, _CONTROL_FLOW_NODES))
        child_depths = [
            visit(child, current_depth) for child in ast.iter_child_nodes(current)
        ]
        return max([current_depth, *child_depths])

    return visit(node, 0)


def _direct_name_calls(node: ast.FunctionDef):
    calls = set()

    def visit(current: ast.AST):
        if current is not node and isinstance(current, _NESTED_FUNCTION_NODES):
            return
        if isinstance(current, ast.Call) and isinstance(current.func, ast.Name):
            calls.add(current.func.id)
        for child in ast.iter_child_nodes(current):
            visit(child)

    visit(node)
    return calls


def _long_production_functions():
    offenders = []
    for path in sorted(_PYTHON_ROOT.rglob("*.py")):
        _source, tree = _parse_source(path)
        for node in _function_nodes(tree):
            line_count = node.end_lineno - node.lineno + 1
            if line_count > _MAX_FUNCTION_LINES:
                relative = path.relative_to(_PYTHON_ROOT).as_posix()
                offenders.append((relative, node.name, line_count))
    return offenders


def test_app_user_model_id_pipeline_stays_small_and_delegated():
    source, tree = _parse_source(_SOURCE_PATH)
    targets = {
        name: _direct_functions(tree.body, name) for name in _TARGET_FUNCTIONS
    }

    assert len(source.splitlines()) <= _MAX_FILE_LINES
    assert all(len(nodes) == 1 for nodes in targets.values()), targets
    target_nodes = {name: nodes[0] for name, nodes in targets.items()}
    for name, node in target_nodes.items():
        assert node.end_lineno - node.lineno + 1 <= _MAX_FUNCTION_LINES, name
        assert _control_depth(node) <= _MAX_CONTROL_DEPTH, name

    main_calls = _direct_name_calls(target_nodes["_derive_app_user_model_id"])
    assert "_derive_executable_app_user_model_id" in main_calls
    assert "_derive_current_script_app_user_model_id" in main_calls


def test_module_initialization_derives_before_applying_app_user_model_id():
    _source, tree = _parse_source(_SOURCE_PATH)
    assignments = [
        (index, node)
        for index, node in enumerate(tree.body)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "APP_USER_MODEL_ID"
            for target in node.targets
        )
    ]

    assert len(assignments) == 1
    index, assignment = assignments[0]
    assert isinstance(assignment.value, ast.Call)
    assert isinstance(assignment.value.func, ast.Name)
    assert assignment.value.func.id == "_derive_app_user_model_id"

    apply_statement = tree.body[index + 1]
    assert isinstance(apply_statement, ast.Expr)
    assert isinstance(apply_statement.value, ast.Call)
    assert isinstance(apply_statement.value.func, ast.Name)
    assert apply_statement.value.func.id == "_apply_app_user_model_id"
    assert len(apply_statement.value.args) == 1
    assert isinstance(apply_statement.value.args[0], ast.Name)
    assert apply_statement.value.args[0].id == "APP_USER_MODEL_ID"


def test_python_long_function_inventory_does_not_regress():
    offenders = _long_production_functions()
    counts = Counter(path.split("/", 1)[0] for path, _name, _lines in offenders)

    assert len(offenders) <= _MAX_LONG_FUNCTIONS, offenders
    assert set(counts) <= set(_MAX_LONG_FUNCTIONS_BY_AREA), counts
    for area, maximum in _MAX_LONG_FUNCTIONS_BY_AREA.items():
        assert counts[area] <= maximum, (area, counts[area], offenders)
