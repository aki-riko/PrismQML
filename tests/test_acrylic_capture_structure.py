# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Acrylic capture structure contracts. 亚克力截图结构合同。"""

import ast
from pathlib import Path
from textwrap import dedent

from prismqml.python.window import mica_window


_SOURCE_PATH = Path(mica_window.__file__).resolve()
_HELPER_NAMES = {
    "_grab_acrylic_region",
    "_publish_acrylic_capture",
    "_resolve_acrylic_screen",
}
_GRAB_STATEMENTS = (
    '''\
        if not window or width <= 0 or height <= 0:
            warning("Invalid parameters for grabAndBlur")
            return ""
    ''',
    '''\
        try:
            screen = _resolve_acrylic_screen(window)
            if screen is _NO_ACRYLIC_SCREEN:
                return ""
            pixmap = _grab_acrylic_region(window, screen, x, y, width, height)
            if pixmap.isNull():
                error("Failed to grab screen")
                return ""
            return _publish_acrylic_capture(self, pixmap, width, height)
        except (ValueError, OSError, RuntimeError) as e:
            error(f"Failed to grab and blur: {e}")
            return ""
    ''',
)
_RESOLVE_STATEMENTS = (
    "screen = window.screen()",
    '''\
        if not screen:
            screens = QApplication.screens()
            if screens:
                screen = screens[0]
            else:
                error("No screen available")
                return _NO_ACRYLIC_SCREEN
    ''',
    "return screen",
)
_GRAB_REGION_STATEMENTS = (
    "win_x = window.x()",
    "win_y = window.y()",
    "global_x = win_x + x",
    "global_y = win_y + y",
    "screen_geo = screen.geometry()",
    "grab_x = global_x - screen_geo.x()",
    "grab_y = global_y - screen_geo.y()",
    "return screen.grabWindow(0, grab_x, grab_y, width, height)",
)
_PUBLISH_STATEMENTS = (
    "image = pixmap.toImage()",
    "blurred = _gaussian_blur_image(image, owner._blur_radius)",
    "owner._image_state.set_image(blurred)",
    'image_url = f"image://acrylic/{owner._image_state.image_id}"',
    "owner.imageReady.emit(image_url)",
    'debug(f"Acrylic image ready: {width}x{height}")',
    "return image_url",
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


def _parse_source():
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


def _acrylic_class(tree):
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "AcrylicHelper"
    ]
    assert len(matches) == 1
    return matches[0]


def _control_depth(node):
    def visit(current, depth):
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


def test_grab_and_blur_stays_small_and_delegated():
    source, tree = _parse_source()
    method = _unique_function(_acrylic_class(tree).body, "grabAndBlur")

    assert len(source.splitlines()) <= 699
    assert method.end_lineno - method.lineno + 1 <= 30
    assert _control_depth(method) <= 2
    _assert_signature(
        method,
        "def grabAndBlur(self, window: QWindow, x: int, y: int, "
        "width: int, height: int) -> str: pass",
    )
    assert _body_dumps(method) == _statement_dumps(_GRAB_STATEMENTS)


def test_acrylic_capture_helpers_stay_exact_and_flat():
    _source, tree = _parse_source()
    functions = _direct_functions(tree.body)
    helper_nodes = [node for node in functions if node.name in _HELPER_NAMES]
    helpers = {node.name: node for node in helper_nodes}

    assert set(helpers) == _HELPER_NAMES
    assert len(helpers) == len(helper_nodes) == 3
    expected_bodies = {
        "_resolve_acrylic_screen": _RESOLVE_STATEMENTS,
        "_grab_acrylic_region": _GRAB_REGION_STATEMENTS,
        "_publish_acrylic_capture": _PUBLISH_STATEMENTS,
    }
    expected_signatures = {
        "_resolve_acrylic_screen":
            "def _resolve_acrylic_screen(window: QWindow) -> Any: pass",
        "_grab_acrylic_region":
            "def _grab_acrylic_region(window: QWindow, screen: QScreen, x: int, "
            "y: int, width: int, height: int) -> QPixmap: pass",
        "_publish_acrylic_capture":
            "def _publish_acrylic_capture(owner: Any, pixmap: QPixmap, width: int, "
            "height: int) -> str: pass",
    }
    for name, helper in helpers.items():
        assert helper.end_lineno - helper.lineno + 1 <= 30, name
        assert _control_depth(helper) <= 2, name
        assert helper.decorator_list == [], name
        _assert_signature(helper, expected_signatures[name])
        assert _body_dumps(helper) == _statement_dumps(expected_bodies[name])
