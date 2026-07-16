# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SVG rewrite structure contracts. SVG 重写结构合同。"""

import ast
from collections import Counter
from pathlib import Path

from prismqml.python.core import icon_core


_SOURCE_PATH = Path(icon_core.__file__).resolve()
_TARGETS = {
    "_qfile_svg_path",
    "_read_svg_text",
    "_prepare_svg_rewrite",
    "_create_svg_stream",
    "_write_namespace_declarations",
    "_write_start_element",
    "_is_svg_path",
    "_merged_path_attributes",
    "_write_svg_start_element",
    "_write_start_document",
    "_write_characters",
    "_copy_svg_token",
    "_finish_svg_rewrite",
    "_rewrite_svg_stream",
    "_rewrite_svg_attrs",
}
_EXPECTED_CALLS = {
    "_read_svg_text": {"_qfile_svg_path": 1},
    "_write_start_element": {"_write_namespace_declarations": 1},
    "_write_svg_start_element": {
        "_is_svg_path": 1,
        "_merged_path_attributes": 1,
        "_write_start_element": 1,
    },
    "_copy_svg_token": {"_write_start_document": 1, "_write_characters": 1},
    "_rewrite_svg_stream": {
        "_create_svg_stream": 1,
        "_write_svg_start_element": 1,
        "_copy_svg_token": 1,
        "_finish_svg_rewrite": 1,
    },
    "_rewrite_svg_attrs": {
        "_read_svg_text": 1,
        "_prepare_svg_rewrite": 1,
        "_rewrite_svg_stream": 1,
    },
}


def _parse_source():
    source = _SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_SOURCE_PATH), feature_version=(3, 9))
    return source, tree


def _target_nodes(tree):
    return {
        name: [
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == name
        ]
        for name in _TARGETS
    }


def _direct_name_calls(node):
    return Counter(
        child.func.id
        for child in ast.walk(node)
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
    )


def _target_name_rebindings(tree):
    rebindings = []
    for statement in tree.body:
        if isinstance(statement, ast.FunctionDef) and statement.name in _TARGETS:
            continue
        for child in ast.walk(statement):
            if isinstance(child, ast.Name) and child.id in _TARGETS:
                if isinstance(child.ctx, (ast.Store, ast.Del)):
                    rebindings.append((child.lineno, child.id))
            if isinstance(child, ast.alias):
                bound = child.asname or child.name.rsplit(".", 1)[-1]
                if bound in _TARGETS:
                    rebindings.append((statement.lineno, bound))
    return rebindings


def test_svg_rewrite_pipeline_stays_small_and_delegated():
    """Keep the rewrite pipeline mechanically split. 保持重写流水线机械拆分。"""
    source, tree = _parse_source()
    targets = _target_nodes(tree)

    assert len(source.splitlines()) <= 500
    assert all(len(nodes) == 1 for nodes in targets.values()), targets
    functions = {name: nodes[0] for name, nodes in targets.items()}
    for name, node in functions.items():
        assert node.end_lineno - node.lineno + 1 <= 30, name
    for caller, expected in _EXPECTED_CALLS.items():
        calls = _direct_name_calls(functions[caller])
        assert all(calls[name] == count for name, count in expected.items()), calls
    entry = functions["_rewrite_svg_attrs"]
    assert not any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(entry))
    assert _target_name_rebindings(tree) == []
