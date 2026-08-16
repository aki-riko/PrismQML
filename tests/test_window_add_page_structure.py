# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""WindowCore.addPage structure contracts. 页面注册结构合同。"""

from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

from prismqml.python.window import window_core


_SOURCE_PATH = Path(window_core.__file__).resolve()
_PYTHON_ROOT = _SOURCE_PATH.parents[1]
_TARGET_FUNCTIONS = {"_make_navigation_item", "addPage"}
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
_MAX_LONG_FUNCTIONS = 39
_MAX_LONG_FUNCTIONS_BY_AREA = {
    "core": 17,
    "models": 1,
    "providers": 4,
    "runtime": 2,
    "state": 1,
    "window": 14,
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


def test_add_page_pipeline_stays_small_and_delegated():
    source, tree = _parse_source(_SOURCE_PATH)
    helpers = _direct_functions(tree.body, "_make_navigation_item")
    window_classes = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "WindowCore"
    ]

    assert len(source.splitlines()) <= _MAX_FILE_LINES
    assert len(helpers) == 1
    assert len(window_classes) == 1
    add_page_methods = _direct_functions(window_classes[0].body, "addPage")
    assert len(add_page_methods) == 1
    targets = {
        "_make_navigation_item": helpers[0],
        "addPage": add_page_methods[0],
    }
    assert targets.keys() == _TARGET_FUNCTIONS
    for name, node in targets.items():
        assert node.end_lineno - node.lineno + 1 <= _MAX_FUNCTION_LINES, name
        assert _control_depth(node) <= _MAX_CONTROL_DEPTH, name
    assert "_make_navigation_item" in _direct_name_calls(targets["addPage"])


def test_python_long_function_inventory_does_not_regress():
    offenders = _long_production_functions()
    counts = Counter(path.split("/", 1)[0] for path, _name, _lines in offenders)

    assert len(offenders) <= _MAX_LONG_FUNCTIONS, offenders
    assert set(counts) <= set(_MAX_LONG_FUNCTIONS_BY_AREA), counts
    for area, maximum in _MAX_LONG_FUNCTIONS_BY_AREA.items():
        assert counts[area] <= maximum, (area, counts[area], offenders)
