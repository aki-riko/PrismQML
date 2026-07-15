# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SQL normalization structure contracts. SQL 归一化结构合同。"""

from __future__ import annotations

import ast
from pathlib import Path

from prismqml.python.models import _sql_lexing, _sql_query_tools


_SOURCE_PATH = Path(_sql_query_tools.__file__).resolve()
_LEXER_PATH = Path(_sql_lexing.__file__).resolve()
_TARGET_SIGNATURES = {
    "_copy_protected_span": ("sql", "index", "length", "out"),
    "_copy_single_quoted": ("sql", "index", "length", "out"),
    "_copy_double_quoted": ("sql", "index", "length", "out"),
    "_copy_backtick_quoted": ("sql", "index", "length", "out"),
    "_copy_bracket_quoted": ("sql", "index", "length", "out"),
    "_copy_line_comment": ("sql", "index", "length", "out"),
    "_copy_block_comment": ("sql", "index", "length", "out"),
    "_copy_plain_sql": ("sql", "index", "length", "out"),
    "_copy_protected_sql": ("sql", "index", "length", "out"),
    "_copy_unresolved_parameter": ("sql", "index", "end", "out"),
    "_normalize_dict_params": ("sql", "params"),
    "normalize_one": ("sql", "params"),
    "strip_strings_and_comments": ("sql",),
    "_has_named_placeholder": ("sql",),
}
_NORMALIZATION_TARGETS = set(_TARGET_SIGNATURES) - {
    "strip_strings_and_comments", "_has_named_placeholder",
}
_LEXER_SIGNATURES = {
    "_is_surrogate": ("char",),
    "_is_identifier_char": ("char",),
    "_is_identifier_start": ("char",),
    "_identifier_span_end": ("sql", "index", "length"),
    "_digit_span_end": ("sql", "index", "length", "hexadecimal"),
    "_numeric_exponent_end": ("sql", "index", "length"),
    "_numeric_span_end": ("sql", "index", "length"),
    "_numbered_parameter_span_end": ("sql", "index", "length"),
    "_bom_context_token_span": ("sql", "index", "length"),
    "_dollar_starts_parameter": ("sql", "start", "index"),
    "_dollar_is_embedded": ("sql", "start", "index"),
    "_quoted_span_end": ("sql", "index", "length", "closing", "doubled"),
    "_line_comment_span_end": ("sql", "index", "length"),
    "_block_comment_span_end": ("sql", "index", "length"),
    "_parenthesized_suffix_span": ("sql", "index", "length"),
    "protected_sql_span_end": ("sql", "index", "length"),
    "_extended_parameter_span": ("sql", "index", "length"),
    "named_parameter_span": ("sql", "index", "length", "scan_start"),
}
_SHARED_LEXER_NAMES = {
    "_SIMPLE_NAMED_PARAMETER", "named_parameter_span",
    "protected_sql_span_end",
}
_CONTROL_FLOW_NODES = (
    ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith,
)
_NESTED_FUNCTION_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
_MAX_FILE_LINES = 699
_MAX_FUNCTION_LINES = 30
_MAX_CONTROL_DEPTH = 2


def _parse_source(path: Path = _SOURCE_PATH) -> tuple[str, ast.Module]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path), feature_version=(3, 9))
    return source, tree


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


def _direct_name_calls(node: ast.FunctionDef) -> list[str]:
    calls = []

    def visit(current: ast.AST):
        if current is not node and isinstance(current, _NESTED_FUNCTION_NODES):
            return
        if isinstance(current, ast.Call) and isinstance(current.func, ast.Name):
            calls.append(current.func.id)
        for child in ast.iter_child_nodes(current):
            visit(child)

    visit(node)
    return calls


def _module_scope_nodes(tree: ast.Module) -> list[ast.AST]:
    nodes = []

    def visit(current: ast.AST):
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return
        nodes.append(current)
        for child in ast.iter_child_nodes(current):
            visit(child)

    for statement in tree.body:
        visit(statement)
    return nodes


def _assigned_names(tree: ast.Module) -> set[str]:
    return {
        node.id for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }


def _rebound_names(tree: ast.Module) -> set[str]:
    names = _assigned_names(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.add(node.name)
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            names.update(node.names)
    return names


def _module_name_aliases(tree: ast.Module, source_name: str) -> set[str]:
    aliases = {source_name}
    assignments = [
        node for node in _module_scope_nodes(tree)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
    ]
    while True:
        additions = set()
        for assignment in assignments:
            value = assignment.value
            if not isinstance(value, ast.Name) or value.id not in aliases:
                continue
            targets = (
                assignment.targets
                if isinstance(assignment, ast.Assign)
                else [assignment.target]
            )
            additions.update(
                target.id for target in targets if isinstance(target, ast.Name)
            )
        additions -= aliases
        if not additions:
            return aliases
        aliases.update(additions)


def _loaded_names(node: ast.FunctionDef) -> set[str]:
    return {
        child.id for child in ast.walk(node)
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load)
    }


def test_normalization_helpers_are_unique_small_top_level_functions():
    source, tree = _parse_source()
    all_functions = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    direct = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }

    assert len(source.splitlines()) <= _MAX_FILE_LINES
    assert set(_TARGET_SIGNATURES).isdisjoint(_assigned_names(tree))
    for name, signature in _TARGET_SIGNATURES.items():
        matches = [node for node in all_functions if node.name == name]
        assert matches == [direct[name]], name
        node = direct[name]
        assert [argument.arg for argument in node.args.args] == list(signature)
        assert node.decorator_list == []
        assert node.end_lineno - node.lineno + 1 <= _MAX_FUNCTION_LINES
        assert _control_depth(node) <= _MAX_CONTROL_DEPTH


def test_shared_lexer_helpers_are_unique_small_top_level_functions():
    source, tree = _parse_source(_LEXER_PATH)
    all_functions = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    direct = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }

    assert len(source.splitlines()) <= _MAX_FILE_LINES
    assert set(_LEXER_SIGNATURES).isdisjoint(_assigned_names(tree))
    for name, signature in _LEXER_SIGNATURES.items():
        matches = [node for node in all_functions if node.name == name]
        assert matches == [direct[name]], name
        node = direct[name]
        assert [argument.arg for argument in node.args.args] == list(signature)
        assert node.decorator_list == []
        assert node.end_lineno - node.lineno + 1 <= _MAX_FUNCTION_LINES
        assert _control_depth(node) <= _MAX_CONTROL_DEPTH


def test_shared_lexer_imports_are_exact_and_not_rebound():
    _source, tree = _parse_source()
    shared_imports = [
        (node.module, node.level, alias.name, alias.asname)
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
        if alias.name in _SHARED_LEXER_NAMES
        or alias.asname in _SHARED_LEXER_NAMES
    ]

    assert sorted(shared_imports) == [
        ("_sql_lexing", 1, "_SIMPLE_NAMED_PARAMETER", None),
        ("_sql_lexing", 1, "named_parameter_span", None),
        ("_sql_lexing", 1, "protected_sql_span_end", None),
    ]
    assert _SHARED_LEXER_NAMES.isdisjoint(_rebound_names(tree))


def test_normalization_pipeline_stays_separate_from_structural_masking():
    _source, tree = _parse_source()
    direct = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    target_calls = {
        name: _direct_name_calls(direct[name]) for name in _TARGET_SIGNATURES
    }

    assert target_calls["normalize_one"].count("_normalize_dict_params") == 1
    assert [
        name for name in target_calls["_normalize_dict_params"]
        if name in {
            "_copy_plain_sql", "_copy_protected_sql",
            "named_parameter_span", "_copy_unresolved_parameter",
        }
    ] == [
        "_copy_plain_sql", "_copy_protected_sql",
        "named_parameter_span", "_copy_unresolved_parameter",
    ]
    assert [
        name for name in target_calls["_copy_protected_sql"]
        if name.startswith("_copy_")
    ] == [
        "_copy_single_quoted", "_copy_double_quoted",
        "_copy_backtick_quoted", "_copy_bracket_quoted",
        "_copy_line_comment", "_copy_block_comment",
    ]
    assert target_calls["_copy_protected_span"].count(
        "protected_sql_span_end"
    ) == 1
    assert target_calls["strip_strings_and_comments"].count(
        "protected_sql_span_end"
    ) == 1
    assert _direct_name_calls(direct["_has_named_placeholder"]).count(
        "named_parameter_span"
    ) == 1
    assert _direct_name_calls(direct["_has_named_placeholder"]).count(
        "protected_sql_span_end"
    ) == 1
    assert "_SIMPLE_NAMED_PARAMETER" in _loaded_names(
        direct["_normalize_dict_params"]
    )

    _lexer_source, lexer_tree = _parse_source(_LEXER_PATH)
    lexer_direct = {
        node.name: node for node in lexer_tree.body
        if isinstance(node, ast.FunctionDef)
    }
    assert [
        name for name in _direct_name_calls(lexer_direct["protected_sql_span_end"])
        if name.endswith("_span_end")
    ] == [
        "_quoted_span_end", "_quoted_span_end", "_line_comment_span_end",
        "_block_comment_span_end",
    ]
    assert _direct_name_calls(lexer_direct["named_parameter_span"]).count(
        "_dollar_is_embedded"
    ) == 1
    assert _direct_name_calls(lexer_direct["named_parameter_span"]).count(
        "_extended_parameter_span"
    ) == 1
    assert "_SIMPLE_NAMED_PARAMETER" in _loaded_names(
        lexer_direct["named_parameter_span"]
    )
    assert _direct_name_calls(lexer_direct["_extended_parameter_span"]).count(
        "_is_identifier_char"
    ) == 1
    assert _direct_name_calls(lexer_direct["_extended_parameter_span"]).count(
        "_parenthesized_suffix_span"
    ) == 1


def test_normalization_helpers_do_not_borrow_structural_masking():
    _source, tree = _parse_source()
    direct = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    masking_aliases = _module_name_aliases(tree, "strip_strings_and_comments")

    assert all(
        "strip_strings_and_comments" not in _direct_name_calls(direct[name])
        for name in _NORMALIZATION_TARGETS
    )
    assert all(
        masking_aliases.isdisjoint(_loaded_names(direct[name]))
        for name in _NORMALIZATION_TARGETS
    )
