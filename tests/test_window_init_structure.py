# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""WindowCore.__init__ structure contracts. 窗口状态初始化结构合同。"""

from __future__ import annotations

import ast
from pathlib import Path

from prismqml.python.window import _window_init, window_core


_CORE_PATH = Path(window_core.__file__).resolve()
_HELPER_PATH = Path(_window_init.__file__).resolve()
_EXPECTED_HELPERS = {"initialize_splash_state", "initialize_window_state"}
_EXPECTED_INIT_STATEMENTS = (
    "super().__init__(parent)",
    "initialize_window_state(self, window_type)",
    "from ..runtime import get_config_manager",
    "self._lazy_loading = get_config_manager().lazyLoading",
    "initialize_splash_state(self)",
)
_EXPECTED_WINDOW_STATE = (
    "owner._window_type = window_type",
    "owner._engine: Optional[QQmlApplicationEngine] = None",
    "owner._window: Optional[QQuickWindow] = None",
    "owner._content_area: Optional[QQuickItem] = None",
    "owner._pending_props: Dict[str, Any] = {}",
    "owner._pending_calls: List[tuple[str, Any]] = []",
    'owner._title = "PrismQML App"',
    "owner._width, owner._height = resolve_initial_window_size()",
    'owner._icon = ""',
    "owner._icon_colored = True",
    'owner._nav_items: List["NavigationItem"] = []',
    'owner._bottom_nav_items: List["NavigationItem"] = []',
    "owner._current_index = 0",
    "owner._pages: Dict[int, Any] = {}",
    "initialize_page_prewarm_state(owner)",
)
_EXPECTED_SPLASH_STATE = (
    "owner._splash_enabled = True",
    'owner._splash_icon = ""',
    'owner._splash_title = ""',
    "owner._splash_subtitle = DEFAULT_SPLASH_SUBTITLE",
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


def _unique_function(nodes, name):
    matches = [node for node in _direct_function_nodes(nodes) if node.name == name]
    assert len(matches) == 1
    return matches[0]


def _window_core_init(tree: ast.Module) -> ast.FunctionDef:
    classes = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "WindowCore"
    ]
    assert len(classes) == 1
    return _unique_function(classes[0].body, "__init__")


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
            ast.parse(source, feature_version=(3, 9)).body[0],
            include_attributes=False,
        )
        for source in sources
    ]


def _body_dumps(node: ast.FunctionDef):
    assert ast.get_docstring(node, clean=False)
    return [
        ast.dump(statement, include_attributes=False)
        for statement in node.body[1:]
    ]


def _optional_dump(node):
    if node is None:
        return None
    return ast.dump(node, include_attributes=False)


def _assert_signature(node, expected_source):
    expected = ast.parse(expected_source, feature_version=(3, 9)).body[0]
    assert ast.dump(node.args, include_attributes=False) == ast.dump(
        expected.args, include_attributes=False
    )
    assert node.decorator_list == []
    assert _optional_dump(node.returns) == _optional_dump(expected.returns)


def test_window_core_init_stays_exact_and_delegated():
    core_source, core_tree = _parse_source(_CORE_PATH)
    init_method = _window_core_init(core_tree)

    assert len(core_source.splitlines()) <= 699
    assert init_method.end_lineno - init_method.lineno + 1 <= 30
    assert _control_depth(init_method) == 0
    _assert_signature(
        init_method,
        "def __init__(self, window_type: int = WindowType.BAR, "
        "parent: Optional[QObject] = None): pass",
    )
    assert _body_dumps(init_method) == _statement_dumps(_EXPECTED_INIT_STATEMENTS)


def test_window_init_helpers_stay_exact_and_flat():
    helper_source, helper_tree = _parse_source(_HELPER_PATH)
    helper_nodes = _direct_function_nodes(helper_tree.body)
    helpers = {node.name: node for node in helper_nodes}

    assert len(helper_source.splitlines()) <= 100
    assert len(helpers) == len(helper_nodes)
    assert set(helpers) == _EXPECTED_HELPERS
    state_helper = helpers["initialize_window_state"]
    splash_helper = helpers["initialize_splash_state"]
    _assert_signature(
        state_helper,
        "def initialize_window_state(owner: Any, window_type: int) -> None: pass",
    )
    _assert_signature(
        splash_helper,
        "def initialize_splash_state(owner: Any) -> None: pass",
    )
    assert _body_dumps(state_helper) == _statement_dumps(_EXPECTED_WINDOW_STATE)
    assert _body_dumps(splash_helper) == _statement_dumps(_EXPECTED_SPLASH_STATE)
    for name, helper in helpers.items():
        assert helper.end_lineno - helper.lineno + 1 <= 30, name
        assert _control_depth(helper) == 0, name
