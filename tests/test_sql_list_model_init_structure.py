# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SqlListModel init structure contracts. SQL 模型构造结构合同。"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from textwrap import dedent

from prismqml.python.models import sql_list_model


_SOURCE_PATH = Path(sql_list_model.__file__).resolve()
_HELPER_NAME = "_initialize_empty_query_state"
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
_EXPECTED_INIT_STATEMENTS = (
    "super().__init__(parent)",
    """
    if isinstance(db_path_or_router, (str, Path)):
        self._router: DbRouter = _SingleDbRouter(str(db_path_or_router))
        self._db_path: str = str(db_path_or_router)
    elif isinstance(db_path_or_router, DbRouter):
        self._router = db_path_or_router
        self._db_path = ""
    else:
        raise TypeError(
            f"db_path_or_router 必须是 str/Path/DbRouter,got {type(db_path_or_router)}"
        )
    """,
    "self._page_size: int = max(1, int(page_size))",
    "self._lru_capacity: int = max(1, int(lru_capacity))",
    "_initialize_empty_query_state(self)",
)
_EXPECTED_HELPER_STATEMENTS = (
    'owner._sql: str = ""',
    'owner._count_sql: str = ""',
    "owner._params: list = []",
    "owner._count_params: list = []",
    "owner._formatters: dict[str, callable] = {}",
    "owner._cursor_columns: list[str] = []",
    "owner._cursor_nullable_index: Optional[int] = None",
    "owner._cursor_col_indices: list[int] = []",
    "owner._cursor_directions: list[str] = []",
    "owner._row_count: int = 0",
    "owner._columns: list[str] = []",
    "owner._role_to_col: dict[int, int] = {}",
    "owner._role_names: dict[int, QByteArray] = {}",
    "owner._cache = PageCache(owner._lru_capacity)",
)


def _parse_source() -> tuple[str, ast.Module]:
    source = _SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_SOURCE_PATH), feature_version=(3, 9))
    return source, tree


def _direct_functions(nodes):
    return [
        node
        for node in nodes
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def _unique_function(nodes, name):
    matches = [node for node in _direct_functions(nodes) if node.name == name]
    assert len(matches) == 1
    return matches[0]


def _model_class(tree):
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "SqlListModel"
    ]
    assert len(matches) == 1
    return matches[0]


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


def _statement_dumps(sources):
    return [
        ast.dump(
            ast.parse(dedent(source), feature_version=(3, 9)).body[0],
            include_attributes=False,
        )
        for source in sources
    ]


def _body_dumps(node):
    return [ast.dump(item, include_attributes=False) for item in node.body]


def _assert_signature(node, expected_source):
    expected = ast.parse(expected_source, feature_version=(3, 9)).body[0]
    assert ast.dump(node.args, include_attributes=False) == ast.dump(
        expected.args, include_attributes=False
    )
    assert ast.dump(node.returns, include_attributes=False) == ast.dump(
        expected.returns, include_attributes=False
    )
    assert node.decorator_list == []


def test_init_pipeline_stays_exact_and_delegated():
    source, tree = _parse_source()
    model_class = _model_class(tree)
    init_method = _unique_function(model_class.body, "__init__")
    helper = _unique_function(tree.body, _HELPER_NAME)

    assert len(source.splitlines()) < 700
    assert init_method.end_lineno - init_method.lineno + 1 <= 30
    assert helper.end_lineno - helper.lineno + 1 <= 30
    assert _control_depth(init_method) <= 2
    assert _control_depth(helper) == 0
    _assert_signature(
        init_method,
        "def __init__(self, db_path_or_router: Union[str, Path, DbRouter], "
        "parent=None, page_size: int=PAGE_SIZE_DEFAULT, "
        "lru_capacity: int=LRU_CAPACITY_DEFAULT) -> None: pass",
    )
    _assert_signature(
        helper,
        "def _initialize_empty_query_state(owner: Any) -> None: pass",
    )
    assert _body_dumps(init_method) == _statement_dumps(_EXPECTED_INIT_STATEMENTS)
    assert _body_dumps(helper) == _statement_dumps(_EXPECTED_HELPER_STATEMENTS)


def test_init_helper_runtime_binding_matches_source():
    _source, tree = _parse_source()
    helper = _unique_function(tree.body, _HELPER_NAME)
    runtime = getattr(sql_list_model, _HELPER_NAME)

    assert inspect.isfunction(runtime)
    assert not inspect.iscoroutinefunction(runtime)
    assert runtime.__name__ == _HELPER_NAME
    assert runtime.__code__.co_firstlineno == helper.lineno
