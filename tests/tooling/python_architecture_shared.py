# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Shared layer paths and AST readers for Python dependency-direction gates.
Python 依赖方向门禁共用的层级路径与 AST 读取器；被 test_python_architecture*.py 引用。"""

import ast
from importlib.util import resolve_name
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_PACKAGE = REPO_ROOT / "prismqml" / "python"
CORE_PACKAGE = PYTHON_PACKAGE / "core"
CONFIG_PACKAGE = PYTHON_PACKAGE / "config"
PROVIDERS_PACKAGE = PYTHON_PACKAGE / "providers"
WINDOW_PACKAGE = PYTHON_PACKAGE / "window"
FORBIDDEN_CORE_DEPENDENCIES = (
    "prismqml.python.config",
    "prismqml.python.providers",
    "prismqml.python.runtime",
    "prismqml.python.window",
)
WINDOW_RUNTIME_CONTEXT_NAMES = {
    "ThemeManager",
    "ShadowManager",
    "ConfigManager",
    "MicaManager",
    "ClipboardHelper",
    "PrismQmlStartupProfileVerbose",
    "PrismQmlAsynchronousPageLoaderEnabled",
    "NativeWindow",
}


def _module_context(path: Path) -> tuple[str, str]:
    relative = path.relative_to(REPO_ROOT).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
        module = ".".join(parts)
        return module, module
    module = ".".join(parts)
    return module, ".".join(parts[:-1])


def _resolved_imports(path: Path) -> list[tuple[int, str]]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path), feature_version=(3, 9))
    _module, package = _module_context(path)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            target = node.module or ""
            if node.level:
                target = resolve_name("." * node.level + target, package)
            imports.extend(
                (node.lineno, f"{target}.{alias.name}" if target else alias.name)
                for alias in node.names
            )
        elif isinstance(node, ast.Call) and node.args:
            function = node.func
            is_dynamic_import = (
                isinstance(function, ast.Name)
                and function.id in {"__import__", "_import_module", "import_module"}
            ) or (
                isinstance(function, ast.Attribute)
                and function.attr == "import_module"
            )
            candidate = node.args[0]
            if not is_dynamic_import or not isinstance(candidate, ast.Constant):
                continue
            if not isinstance(candidate.value, str):
                continue
            target = candidate.value
            if target.startswith("."):
                base = module if path.name == "__init__.py" else package
                target = resolve_name(target, base)
            imports.append((node.lineno, target))
    return imports


def _literal_assignment(path: Path, name: str):
    tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
        feature_version=(3, 9),
    )
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} not found in {path}")


def _lazy_exports(path: Path) -> dict[str, tuple[str, str]]:
    return _literal_assignment(path, "_LAZY_EXPORTS")


def _function_names(path: Path) -> set[str]:
    tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
        feature_version=(3, 9),
    )
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _named_function_calls(path: Path, name: str) -> list[int]:
    tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
        feature_version=(3, 9),
    )
    return [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == name
    ]


def _attribute_function_calls(path: Path, owner: str, name: str) -> list[int]:
    tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
        feature_version=(3, 9),
    )
    return [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == name
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == owner
    ]


def _class_names(path: Path) -> set[str]:
    tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
        feature_version=(3, 9),
    )
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    }


def _literal_method_calls(path: Path) -> list[tuple[int, str, str]]:
    tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
        feature_version=(3, 9),
    )
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        first_argument = node.args[0]
        if not isinstance(first_argument, ast.Constant):
            continue
        if not isinstance(first_argument.value, str):
            continue
        calls.append((node.lineno, node.func.attr, first_argument.value))
    return calls
