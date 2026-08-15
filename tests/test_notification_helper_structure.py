# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Notification helper structure contracts. 通知 helper 结构合同。"""

import ast
from pathlib import Path

from prismqml.python.runtime import notification


_SOURCE_PATH = Path(notification.__file__).resolve()
_TARGETS = {
    "_cached_helper_for",
    "_create_helper",
    "_get_helper",
}


def _target_nodes():
    tree = ast.parse(
        _SOURCE_PATH.read_text(encoding="utf-8"),
        filename=str(_SOURCE_PATH),
        feature_version=(3, 9),
    )
    return {
        name: [
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == name
        ]
        for name in _TARGETS
    }


def _direct_name_calls(node):
    return [
        child.func.id
        for child in ast.walk(node)
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
    ]


def _helper_store_count(node):
    return sum(
        isinstance(child, ast.Name)
        and child.id == "_helper"
        and isinstance(child.ctx, ast.Store)
        for child in ast.walk(node)
    )


def _target_name_rebindings():
    tree = ast.parse(
        _SOURCE_PATH.read_text(encoding="utf-8"),
        filename=str(_SOURCE_PATH),
        feature_version=(3, 9),
    )
    rebindings = []
    for statement in tree.body:
        if isinstance(statement, ast.FunctionDef) and statement.name in _TARGETS:
            continue
        if isinstance(statement, (ast.AsyncFunctionDef, ast.ClassDef)):
            if statement.name in _TARGETS:
                rebindings.append((statement.lineno, statement.name))
        for child in ast.walk(statement):
            if isinstance(child, ast.Name) and child.id in _TARGETS:
                if isinstance(child.ctx, (ast.Store, ast.Del)):
                    rebindings.append((child.lineno, child.id))
            if isinstance(child, ast.alias):
                bound = child.asname or child.name.rsplit(".", 1)[-1]
                if bound in _TARGETS:
                    rebindings.append((statement.lineno, bound))
    return rebindings


def test_notification_helper_pipeline_stays_small_and_delegated():
    functions = _target_nodes()

    assert all(len(nodes) == 1 for nodes in functions.values()), functions
    for name, nodes in functions.items():
        node = nodes[0]
        assert node.end_lineno - node.lineno + 1 <= 30, name

    get_node = functions["_get_helper"][0]
    calls = _direct_name_calls(get_node)
    assert calls.count("_cached_helper_for") == 1, calls
    assert calls.count("_create_helper") == 1, calls
    assert _helper_store_count(get_node) == 0
    assert _helper_store_count(functions["_create_helper"][0]) == 1
    assert _target_name_rebindings() == []
