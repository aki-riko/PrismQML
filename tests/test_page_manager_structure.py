# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""PageManager structure contracts. 页面管理器结构合同。"""

from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

from prismqml.python.window import _page_manager


_SOURCE_PATH = Path(_page_manager.__file__).resolve()
_PYTHON_ROOT = _SOURCE_PATH.parents[1]
_REQUIRED_ENTRY_METHODS = {"_create_page", "_start_async_page_load"}
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
_MAX_FILE_LINES = 499
_MAX_FUNCTION_LINES = 30
_MAX_CONTROL_DEPTH = 2
_MAX_LONG_FUNCTIONS = 40
_MAX_LONG_FUNCTIONS_BY_AREA = {
    "core": 17,
    "models": 3,
    "providers": 4,
    "state": 1,
    "window": 15,
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


def test_page_manager_functions_stay_within_structure_budget():
    source, tree = _parse_source(_SOURCE_PATH)
    functions = _function_nodes(tree)
    names = {node.name for node in functions}
    line_offenders = [
        (node.name, node.end_lineno - node.lineno + 1)
        for node in functions
        if node.end_lineno - node.lineno + 1 > _MAX_FUNCTION_LINES
    ]
    depth_offenders = [
        (node.name, _control_depth(node))
        for node in functions
        if _control_depth(node) > _MAX_CONTROL_DEPTH
    ]

    assert len(source.splitlines()) <= _MAX_FILE_LINES
    assert _REQUIRED_ENTRY_METHODS <= names
    assert line_offenders == []
    assert depth_offenders == []


def test_python_long_function_inventory_does_not_regress():
    offenders = _long_production_functions()
    counts = Counter(path.split("/", 1)[0] for path, _name, _lines in offenders)

    assert len(offenders) <= _MAX_LONG_FUNCTIONS, offenders
    assert set(counts) <= set(_MAX_LONG_FUNCTIONS_BY_AREA), counts
    for area, maximum in _MAX_LONG_FUNCTIONS_BY_AREA.items():
        assert counts[area] <= maximum, (area, counts[area], offenders)
