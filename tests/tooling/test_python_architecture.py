# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Python dependency-direction architecture gates. Python 依赖方向架构门禁。

门禁主体：core 层禁止依赖 config/providers/window/runtime、动态导入封堵、根包装配
入口与 appearance 公开边界；其余领域分片见同目录 test_python_architecture_*.py，
共用 AST 读取器在 python_architecture_shared.py。
"""

from importlib.util import resolve_name

from python_architecture_shared import (
    CORE_PACKAGE,
    FORBIDDEN_CORE_DEPENDENCIES,
    PYTHON_PACKAGE,
    REPO_ROOT,
    _function_names,
    _lazy_exports,
    _literal_assignment,
    _resolved_imports,
)


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

    for name in (
        "setTheme",
        "getTheme",
        "setSkin",
        "getSkin",
        "isDark",
        "setAccentColor",
        "getAccentColor",
        "accentQColor",
        "getThemeManager",
    ):
        assert root_exports[name] == (".python.runtime.appearance", name)


def test_core_does_not_expose_runtime_owned_appearance_facades():
    core_init = CORE_PACKAGE / "__init__.py"
    core_exports = _lazy_exports(core_init)
    core_public_names = set(_literal_assignment(core_init, "__all__"))
    runtime_owned_names = {
        "setTheme",
        "getTheme",
        "setSkin",
        "getSkin",
        "isDark",
        "setAccentColor",
        "getAccentColor",
        "accentQColor",
        "getThemeManager",
    }

    assert runtime_owned_names.isdisjoint(core_public_names)
    assert runtime_owned_names.isdisjoint(core_exports)
