# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""System tray architecture gates. 系统托盘架构门禁。"""

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SYSTEM_TRAY = REPO_ROOT / "prismqml" / "python" / "window" / "system_tray.py"
MENU_MIXIN = REPO_ROOT / "prismqml" / "python" / "window" / "_system_tray_menu.py"
MENU_METHODS = {
    "_ensureQmlMenu",
    "_create_qml_menu",
    "release_engine",
    "_qml_icon_value",
    "_action_options",
    "_submenu_payload",
    "_addActionToQml",
    "_onMenuActionTriggered",
    "addAction",
    "_build_action",
    "_warn_duplicate_action_id",
    "addActions",
    "addSeparator",
    "clearActions",
    "actions",
    "updateAction",
    "removeAction",
    "setActionChecked",
    "setActionEnabled",
    "setActionText",
    "addMenu",
    "_register_submenu_callbacks",
}


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _class_methods(tree: ast.Module, class_name: str) -> set[str]:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                child.name
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
    raise AssertionError(f"class {class_name} not found")


def test_system_tray_menu_protocol_is_extracted():
    system_tree = _tree(SYSTEM_TRAY)
    mixin_tree = _tree(MENU_MIXIN)

    system_methods = _class_methods(system_tree, "SystemTrayIcon")
    mixin_methods = _class_methods(mixin_tree, "SystemTrayMenuMixin")

    assert MENU_METHODS <= mixin_methods
    assert MENU_METHODS.isdisjoint(system_methods)

    tray_class = next(
        node
        for node in system_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "SystemTrayIcon"
    )
    assert [ast.unparse(base) for base in tray_class.bases] == [
        "SystemTrayMenuMixin",
        "QObject",
    ]


def test_system_tray_modules_stay_within_architecture_limit():
    for path in (SYSTEM_TRAY, MENU_MIXIN):
        assert len(path.read_text(encoding="utf-8").splitlines()) < 500
