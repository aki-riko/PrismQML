# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SQL query tool architecture gates. SQL 查询工具架构门禁。"""

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUERY_TOOLS = REPO_ROOT / "prismqml" / "python" / "models" / "_sql_query_tools.py"
KEYSET_BUILDER = (
    REPO_ROOT / "prismqml" / "python" / "models" / "_sql_keyset_builder.py"
)
BUILDER_HELPERS = {
    "_normalize_cursor_directions",
    "_build_row_value_predicate",
    "_build_null_branch_predicate",
    "_wrap_keyset_branch",
    "_build_desc_nullable_union",
    "_cursor_column_equal",
    "_cursor_column_after",
    "_build_expanded_keyset_predicate",
    "_build_guarded_expanded_query",
    "_build_uniform_keyset_query",
    "_try_build_guarded_subquery",
    "build_keyset_query",
}


def _functions(path: Path) -> dict[str, ast.FunctionDef]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }


def test_keyset_builder_has_one_module_owner():
    query_functions = _functions(QUERY_TOOLS)
    builder_functions = _functions(KEYSET_BUILDER)

    assert "inject_keyset_predicate" in query_functions
    assert BUILDER_HELPERS <= builder_functions.keys()
    assert BUILDER_HELPERS.isdisjoint(query_functions)

    wrapper = query_functions["inject_keyset_predicate"]
    calls = {
        node.func.id
        for node in ast.walk(wrapper)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "build_keyset_query" in calls


def test_sql_query_modules_stay_within_architecture_limit():
    for path in (QUERY_TOOLS, KEYSET_BUILDER):
        assert len(path.read_text(encoding="utf-8").splitlines()) < 500
