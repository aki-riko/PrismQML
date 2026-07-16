# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Screen eyedropper paint structure gates. 屏幕取色器绘制结构门禁。"""

from __future__ import annotations

import ast
from pathlib import Path

from prismqml.python.providers import screen_eyedropper as eyedropper


_SOURCE_PATH = Path(eyedropper.__file__).resolve()
_HELPERS = {
    "_paint_eyedropper_background",
    "_paint_eyedropper_crosshair",
    "_paint_eyedropper_preview",
    "_paint_eyedropper_label",
}
_MAX_FUNCTION_LINES = 30


def _parse_source():
    source = _SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_SOURCE_PATH), feature_version=(3, 9))
    return source, tree


def _module_helper_nodes(tree):
    nodes = {}
    for name in _HELPERS:
        direct = [
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == name
        ]
        matches = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == name
        ]
        assert len(direct) == len(matches) == 1, (name, direct, matches)
        nodes[name] = direct[0]
    return nodes


def _paint_method_node(tree):
    classes = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "ScreenEyedropperWindow"
    ]
    assert len(classes) == 1, classes
    direct = [
        node
        for node in classes[0].body
        if isinstance(node, ast.FunctionDef) and node.name == "paintEvent"
    ]
    matches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "paintEvent"
    ]
    assert len(direct) == len(matches) == 1, (direct, matches)
    return direct[0]


def _target_nodes(tree):
    nodes = _module_helper_nodes(tree)
    nodes["paintEvent"] = _paint_method_node(tree)
    return nodes


def _direct_name_calls(node):
    calls = []

    def visit(current):
        if current is not node and isinstance(current, ast.FunctionDef):
            return
        if isinstance(current, ast.Call) and isinstance(current.func, ast.Name):
            calls.append(current.func.id)
        for child in ast.iter_child_nodes(current):
            visit(child)

    visit(node)
    return calls


def _direct_attribute_calls(node):
    return [
        child.func.attr
        for child in ast.walk(node)
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute)
    ]


def _top_level_name_calls(statements):
    return [
        (index, statement.value.func.id)
        for index, statement in enumerate(statements)
        if isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Call)
        and isinstance(statement.value.func, ast.Name)
    ]


def _assigned_name_indices(statements):
    return {
        statement.targets[0].id: index
        for index, statement in enumerate(statements)
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
    }


def _top_level_painter_calls(statements):
    return [
        statement.value.func.attr
        for statement in statements
        if isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Call)
        and isinstance(statement.value.func, ast.Attribute)
        and isinstance(statement.value.func.value, ast.Name)
        and statement.value.func.value.id == "painter"
    ]


def test_paint_targets_stay_owned_small_and_unique():
    source, tree = _parse_source()
    nodes = _target_nodes(tree)

    assert len(source.splitlines()) < 500
    for name, node in nodes.items():
        assert node.end_lineno - node.lineno + 1 <= _MAX_FUNCTION_LINES, name


def test_paint_pipeline_uses_ordered_top_level_delegation():
    _source, tree = _parse_source()
    nodes = _target_nodes(tree)
    paint = nodes["paintEvent"]
    calls = _top_level_name_calls(paint.body)
    assert [name for _index, name in calls] == [
        "_paint_eyedropper_background",
        "_paint_eyedropper_preview",
        "_paint_eyedropper_label",
    ]
    indices = dict((name, index) for index, name in calls)
    assignments = _assigned_name_indices(paint.body)
    color_indices = [assignments[name] for name in ("bg_color", "border_color", "text_color")]
    assert max(color_indices) < indices["_paint_eyedropper_background"]
    assert assignments["preview_rect"] < indices["_paint_eyedropper_preview"]
    between = paint.body[
        indices["_paint_eyedropper_preview"] + 1:indices["_paint_eyedropper_label"]
    ]
    assert _top_level_painter_calls(between) == ["setPen", "setBrush", "drawRoundedRect"]

    paint_calls = _direct_name_calls(nodes["paintEvent"])
    for helper in _HELPERS - {"_paint_eyedropper_crosshair"}:
        assert paint_calls.count(helper) == 1, (helper, paint_calls)
    assert "_paint_eyedropper_crosshair" not in paint_calls


def test_crosshair_stays_in_captured_preview_branch():
    _source, tree = _parse_source()
    preview = _target_nodes(tree)["_paint_eyedropper_preview"]
    branches = [statement for statement in preview.body if isinstance(statement, ast.If)]

    assert len(branches) == 1, branches
    assert [name for _index, name in _top_level_name_calls(branches[0].body)] == [
        "_paint_eyedropper_crosshair"
    ]
    preview_calls = _direct_name_calls(preview)
    assert preview_calls.count("_paint_eyedropper_crosshair") == 1


def test_paint_override_preserves_signature_and_raw_failure_flow():
    _source, tree = _parse_source()
    nodes = _target_nodes(tree)
    paint = nodes["paintEvent"]

    assert [argument.arg for argument in paint.args.args] == ["self", "event"]
    for name, node in nodes.items():
        assert not any(isinstance(child, ast.Try) for child in ast.walk(node)), name
        calls = _direct_attribute_calls(node)
        assert "save" not in calls, name
        assert "restore" not in calls, name
    assert "paintEvent" not in _direct_attribute_calls(paint)
