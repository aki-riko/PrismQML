# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Python dependency-direction architecture gates. Python 依赖方向架构门禁。"""

import ast
from importlib.util import resolve_name
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_PACKAGE = REPO_ROOT / "prismqml" / "python"
CORE_PACKAGE = PYTHON_PACKAGE / "core"
FORBIDDEN_CORE_DEPENDENCIES = (
    "prismqml.python.config",
    "prismqml.python.providers",
    "prismqml.python.runtime",
    "prismqml.python.window",
)


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


def test_core_does_not_depend_on_runtime_composition_layers():
    violations = []
    for path in sorted(CORE_PACKAGE.rglob("*.py")):
        for line, target in _resolved_imports(path):
            if any(
                target == forbidden or target.startswith(f"{forbidden}.")
                for forbidden in FORBIDDEN_CORE_DEPENDENCIES
            ):
                violations.append(f"{path.relative_to(REPO_ROOT)}:{line}: {target}")

    core_exports = _lazy_exports(CORE_PACKAGE / "__init__.py")
    for name, (module_name, _attribute) in core_exports.items():
        target = resolve_name(module_name, "prismqml.python.core")
        if any(
            target == forbidden or target.startswith(f"{forbidden}.")
            for forbidden in FORBIDDEN_CORE_DEPENDENCIES
        ):
            violations.append(f"prismqml/python/core/__init__.py: {name} -> {target}")

    assert violations == []


def test_runtime_registration_has_one_composition_owner():
    root_init = REPO_ROOT / "prismqml" / "__init__.py"
    core_init = CORE_PACKAGE / "__init__.py"
    runtime_init = PYTHON_PACKAGE / "runtime" / "__init__.py"
    root_exports = _lazy_exports(root_init)
    core_exports = _lazy_exports(core_init)
    runtime_exports = _lazy_exports(runtime_init)

    assert root_exports["register_types"] == (".python.runtime", "register_types")
    assert runtime_exports["register_types"] == (".registry", "register_types")
    assert "register_types" in _literal_assignment(root_init, "__all__")
    assert "register_types" in _literal_assignment(runtime_init, "__all__")
    assert "register_types" not in _literal_assignment(core_init, "__all__")
    assert "register_types" not in core_exports
    assert "register_types" not in _function_names(CORE_PACKAGE / "utils.py")
    assert "register_types" in _function_names(
        PYTHON_PACKAGE / "runtime" / "registry.py"
    )


def test_public_appearance_mutations_cross_the_runtime_boundary():
    root_exports = _lazy_exports(REPO_ROOT / "prismqml" / "__init__.py")

    for name in ("setTheme", "setSkin", "setAccentColor"):
        assert root_exports[name] == (".python.runtime.appearance", name)
