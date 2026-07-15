# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Acrylic blur structure contracts. 亚克力模糊结构合同。"""

import ast
import inspect
from pathlib import Path
from textwrap import dedent

from prismqml.python.window import mica_window


_SOURCE_PATH = Path(mica_window.__file__).resolve()
_FUNCTION_NAMES = {"_gaussian_blur_image", "_scale_acrylic_image"}
_FUNCTION_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)
_LOCAL_SCOPE_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
_SCALE_STATEMENTS = (
    "scale_factor = max(2, radius // 4)",
    "small_width = max(1, width // scale_factor)",
    "small_height = max(1, height // scale_factor)",
    "pixmap = QPixmap.fromImage(image)",
    '''\
        small = pixmap.scaled(
            small_width,
            small_height,
            qt_namespace.AspectRatioMode.IgnoreAspectRatio,
            qt_namespace.TransformationMode.SmoothTransformation,
        )
    ''',
    '''\
        result_pixmap = small.scaled(
            width,
            height,
            qt_namespace.AspectRatioMode.IgnoreAspectRatio,
            qt_namespace.TransformationMode.SmoothTransformation,
        )
    ''',
    "return result_pixmap.toImage()",
)
_BLUR_STATEMENTS = (
    "from PySide6.QtCore import Qt",
    '''\
        if image.isNull() or radius <= 0:
            return image
    ''',
    "converted = image.convertToFormat(QImage.Format.Format_ARGB32)",
    "width, height = converted.width(), converted.height()",
    '''\
        if width == 0 or height == 0:
            return image
    ''',
    "return _scale_acrylic_image(converted, width, height, radius, Qt)",
)
_EXPECTED_CONTRACTS = {
    "_scale_acrylic_image": (
        "def _scale_acrylic_image(image: QImage, width: int, height: int, "
        "radius: int, qt_namespace: Any) -> QImage: pass",
        _SCALE_STATEMENTS,
    ),
    "_gaussian_blur_image": (
        "def _gaussian_blur_image(image: QImage, radius: int) -> QImage: pass",
        _BLUR_STATEMENTS,
    ),
}


def _parse_source():
    source = _SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_SOURCE_PATH), feature_version=(3, 9))
    return source, tree


def _direct_functions(tree):
    return [node for node in tree.body if isinstance(node, _FUNCTION_NODES)]


def _parent_map(tree):
    return {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }


def _is_nested_scope(node, parents):
    current = parents.get(node)
    while current is not None:
        if isinstance(current, _LOCAL_SCOPE_NODES):
            return True
        current = parents.get(current)
    return False


def _module_target_bindings(tree):
    parents = _parent_map(tree)
    bindings = {name: [] for name in _FUNCTION_NAMES}
    for node in ast.walk(tree):
        if isinstance(node, ast.Global):
            for name in set(node.names) & _FUNCTION_NAMES:
                bindings[name].append(node)
            continue
        if _is_nested_scope(node, parents):
            continue
        if isinstance(node, (*_FUNCTION_NODES, ast.ClassDef)):
            if node.name in bindings:
                bindings[node.name].append(node)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            if node.id in bindings:
                bindings[node.id].append(node)
        elif isinstance(node, ast.alias):
            name = node.asname or node.name.split(".")[0]
            if name in bindings:
                bindings[name].append(node)
        elif isinstance(node, ast.ExceptHandler) and node.name in bindings:
            bindings[node.name].append(node)
    return bindings


def _assert_runtime_resolution(functions):
    for name, function in functions.items():
        runtime = getattr(mica_window, name, None)
        assert inspect.isfunction(runtime), name
        assert not inspect.iscoroutinefunction(runtime), name
        assert runtime.__name__ == name
        assert runtime.__code__.co_firstlineno == function.lineno, name


def _statement_dumps(sources):
    return [
        ast.dump(
            ast.parse(dedent(source), feature_version=(3, 9)).body[0],
            include_attributes=False,
        )
        for source in sources
    ]


def _body_dumps(node):
    assert ast.get_docstring(node, clean=False)
    return [
        ast.dump(statement, include_attributes=False)
        for statement in node.body[1:]
    ]


def _assert_signature(node, expected_source):
    expected = ast.parse(expected_source, feature_version=(3, 9)).body[0]
    assert ast.dump(node.args, include_attributes=False) == ast.dump(
        expected.args, include_attributes=False
    )
    assert ast.dump(node.returns, include_attributes=False) == ast.dump(
        expected.returns, include_attributes=False
    )


def test_acrylic_blur_functions_stay_unique_small_and_exact():
    source, tree = _parse_source()
    matching = [
        node for node in _direct_functions(tree) if node.name in _FUNCTION_NAMES
    ]
    functions = {node.name: node for node in matching}

    assert len(source.splitlines()) <= 500
    assert set(functions) == _FUNCTION_NAMES
    assert len(functions) == len(matching) == 2
    assert _module_target_bindings(tree) == {
        name: [function] for name, function in functions.items()
    }
    _assert_runtime_resolution(functions)
    for name, function in functions.items():
        signature_source, body_sources = _EXPECTED_CONTRACTS[name]
        assert type(function) is ast.FunctionDef, name
        assert function.end_lineno - function.lineno + 1 <= 30, name
        assert function.decorator_list == [], name
        _assert_signature(function, signature_source)
        assert _body_dumps(function) == _statement_dumps(body_sources)
