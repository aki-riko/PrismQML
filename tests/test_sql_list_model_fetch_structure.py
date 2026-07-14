# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SqlListModel fetch structure contracts. SQL 分页结构合同。"""

from __future__ import annotations

import ast
from pathlib import Path

from prismqml.python.models import sql_list_model


_SOURCE_PATH = Path(sql_list_model.__file__).resolve()
_FETCH_HELPERS = {
    "_route_page",
    "_plan_page",
    "_fetch_fan_out_page",
    "_fetch_rust_page",
    "_fetch_sqlite_page",
    "_dispatch_page",
    "_fetch_page",
    "_install_resolved_columns",
    "_resolve_columns",
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
_MAX_HELPER_LINES = 30
_MAX_CONTROL_DEPTH = 2
_MAX_MODEL_LONG_FUNCTIONS = 3


def _parse_source(path: Path) -> tuple[str, ast.Module]:
    source = path.read_text(encoding="utf-8")
    return source, ast.parse(source, filename=str(path), feature_version=(3, 9))


def _method_map(tree: ast.Module) -> dict[str, ast.FunctionDef]:
    model_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "SqlListModel"
    )
    return {
        node.name: node
        for node in model_class.body
        if isinstance(node, ast.FunctionDef)
    }


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


def _direct_self_calls(node: ast.FunctionDef) -> list[str]:
    calls = []
    for child in ast.walk(node):
        if not isinstance(child, ast.Call) or not isinstance(child.func, ast.Attribute):
            continue
        owner = child.func.value
        if isinstance(owner, ast.Name) and owner.id == "self":
            calls.append(child.func.attr)
    return calls


def _long_model_functions() -> list[tuple[str, str, int]]:
    offenders = []
    for path in sorted(_SOURCE_PATH.parent.rglob("*.py")):
        _, tree = _parse_source(path)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            line_count = node.end_lineno - node.lineno + 1
            if line_count > _MAX_HELPER_LINES:
                relative_path = path.relative_to(_SOURCE_PATH.parent).as_posix()
                offenders.append((relative_path, node.name, line_count))
    return offenders


class _FetchPipelineSpy:
    def __init__(self, model):
        self.model = model
        self.previous_cursor = [9, 7]
        self.planned = ("SELECT planned", [4, 9, 7], 0, True, [1, 0])
        self.rows = [[7, 9], [6, 8]]
        self.end_cursor = [8, 6]
        self.events = []

    def route(self, page_idx, cursor):
        self.events.append(("route", page_idx, list(cursor)))
        return ["unused.sqlite"], False

    def plan(self, page_idx, cursor):
        self.events.append(("plan", page_idx, list(cursor)))
        return self.planned

    def dispatch(self, paths, is_multi_shard, *actual_plan):
        self.events.append(("dispatch", list(paths), is_multi_shard, actual_plan))
        return ["id", "ID"], self.rows, self.end_cursor

    def install(self, columns, *, validate_unique=True):
        self.events.append(("install", list(columns), validate_unique))
        type(self.model)._install_resolved_columns(
            self.model, columns, validate_unique=validate_unique
        )

    def format_rows(self, actual_rows):
        self.events.append(("format", [list(row) for row in actual_rows]))
        actual_rows[0][1] = 90

    def install_on(self, monkeypatch):
        monkeypatch.setattr(self.model, "_route_page", self.route)
        monkeypatch.setattr(self.model, "_plan_page", self.plan)
        monkeypatch.setattr(self.model, "_dispatch_page", self.dispatch)
        monkeypatch.setattr(self.model, "_install_resolved_columns", self.install)
        monkeypatch.setattr(self.model, "_apply_formatters", self.format_rows)


def test_fetch_page_pipeline_preserves_order_and_duplicate_column_boundary(
    monkeypatch,
):
    model = sql_list_model.SqlListModel("unused.sqlite", page_size=2)
    spy = _FetchPipelineSpy(model)
    spy.install_on(monkeypatch)

    result = model._fetch_page(3, spy.previous_cursor)

    assert spy.events == [
        ("route", 3, [9, 7]),
        ("plan", 3, [9, 7]),
        ("dispatch", ["unused.sqlite"], False, spy.planned),
        ("install", ["id", "ID"], False),
        ("format", [[7, 9], [6, 8]]),
    ]
    assert result == {"rows": [[7, 90], [6, 8]], "end_cursor": spy.end_cursor}
    assert result["rows"] is spy.rows
    assert result["end_cursor"] is spy.end_cursor
    assert model._columns == ["id", "ID"]
    assert [
        bytes(name).decode("utf-8") for name in model.roleNames().values()
    ] == ["id", "ID"]


def test_fetch_page_helpers_stay_small_and_reused():
    source, tree = _parse_source(_SOURCE_PATH)
    methods = _method_map(tree)

    assert len(source.splitlines()) < 700
    assert _FETCH_HELPERS <= methods.keys()
    for name in sorted(_FETCH_HELPERS):
        method = methods[name]
        assert method.end_lineno - method.lineno + 1 <= _MAX_HELPER_LINES, name
        assert _control_depth(method) <= _MAX_CONTROL_DEPTH, name

    assert {
        "_fetch_fan_out_page",
        "_fetch_rust_page",
        "_fetch_sqlite_page",
    } <= set(_direct_self_calls(methods["_dispatch_page"]))
    assert "_install_resolved_columns" in _direct_self_calls(
        methods["_resolve_columns"]
    )
    assert len(_long_model_functions()) <= _MAX_MODEL_LONG_FUNCTIONS
