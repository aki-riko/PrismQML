# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""WindowCore.show structure contracts. 窗口显示编排结构合同。"""

from __future__ import annotations

import ast
from pathlib import Path

from prismqml.python.window import _window_show, window_core


_CORE_PATH = Path(window_core.__file__).resolve()
_HELPER_PATH = Path(_window_show.__file__).resolve()
_HELPER_FUNCTIONS = {
    "ensure_initial_pages",
    "invoke_optional_startup_hook",
    "make_show_profile",
    "show_window_root",
}
_EXPECTED_SHOW_STATEMENTS = (
    "profile = make_show_profile(debug)",
    "if not show_window_root(self, profile):\n    return",
    "WindowCore._current_window_instance = self",
    'invoke_optional_startup_hook(self, "_begin_startup_page_guard")',
    "ensure_initial_pages(self, profile)",
)
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


def _parse_source(path: Path) -> tuple[str, ast.Module]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path), feature_version=(3, 9))
    return source, tree


def _direct_function_nodes(nodes):
    return [
        node
        for node in nodes
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def _direct_functions(nodes):
    return {node.name: node for node in _direct_function_nodes(nodes)}


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


def _statement_dump(source: str) -> str:
    statement = ast.parse(source, feature_version=(3, 9)).body[0]
    return ast.dump(statement, include_attributes=False)


def _assert_show_signature(node: ast.FunctionDef) -> None:
    assert [argument.arg for argument in node.args.args] == ["self"]
    assert node.args.posonlyargs == []
    assert node.args.kwonlyargs == []
    assert node.args.vararg is None
    assert node.args.kwarg is None
    assert node.args.defaults == []
    assert node.decorator_list == []
    assert node.returns is None


def _window_core_show(tree: ast.Module) -> ast.FunctionDef:
    classes = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "WindowCore"
    ]
    assert len(classes) == 1
    methods = [
        node
        for node in _direct_function_nodes(classes[0].body)
        if node.name == "show"
    ]
    assert len(methods) == 1
    return methods[0]


def test_show_pipeline_stays_small_and_delegated():
    core_source, core_tree = _parse_source(_CORE_PATH)
    helper_source, helper_tree = _parse_source(_HELPER_PATH)
    show_method = _window_core_show(core_tree)
    helper_nodes = _direct_function_nodes(helper_tree.body)
    helper_functions = _direct_functions(helper_tree.body)

    assert len(core_source.splitlines()) <= 699
    assert len(helper_source.splitlines()) <= 120
    assert len(helper_functions) == len(helper_nodes)
    assert set(helper_functions) == _HELPER_FUNCTIONS
    assert show_method.end_lineno - show_method.lineno + 1 <= 10
    assert _control_depth(show_method) <= 1
    _assert_show_signature(show_method)
    assert ast.get_docstring(show_method, clean=False)
    actual_statements = [
        ast.dump(statement, include_attributes=False)
        for statement in show_method.body[1:]
    ]
    expected_statements = [
        _statement_dump(source) for source in _EXPECTED_SHOW_STATEMENTS
    ]
    assert actual_statements == expected_statements
    for name, function in helper_functions.items():
        assert function.end_lineno - function.lineno + 1 <= 30, name
        assert _control_depth(function) <= 2, name
