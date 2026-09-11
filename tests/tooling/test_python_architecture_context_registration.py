# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Context / provider registration owners.
context 与 provider 注册所有者门禁（图标 context、appUpdater、lazy provider、
window runtime composition）。"""

from python_architecture_shared import (
    CORE_PACKAGE,
    PROVIDERS_PACKAGE,
    PYTHON_PACKAGE,
    REPO_ROOT,
    WINDOW_PACKAGE,
    WINDOW_RUNTIME_CONTEXT_NAMES,
    _attribute_function_calls,
    _class_names,
    _function_names,
    _lazy_exports,
    _literal_assignment,
    _literal_method_calls,
    _resolved_imports,
)


def test_icon_context_registration_has_one_composition_owner():
    root_init = REPO_ROOT / "prismqml" / "__init__.py"
    core_init = CORE_PACKAGE / "__init__.py"
    core_icon_provider = CORE_PACKAGE / "icon_provider.py"
    runtime_init = PYTHON_PACKAGE / "runtime" / "__init__.py"
    runtime_icon_registry = PYTHON_PACKAGE / "runtime" / "icon_registry.py"
    root_exports = _lazy_exports(root_init)
    core_exports = _lazy_exports(core_init)
    runtime_exports = _lazy_exports(runtime_init)
    icon_registry_imports = {
        target for _line, target in _resolved_imports(runtime_icon_registry)
    }

    assert root_exports["register_icon_provider"] == (
        ".python.runtime",
        "register_icon_provider",
    )
    assert runtime_exports["register_icon_provider"] == (
        ".icon_registry",
        "register_icon_provider",
    )
    assert "register_icon_provider" not in _literal_assignment(core_init, "__all__")
    assert "register_icon_provider" not in core_exports
    assert "register_icon_provider" not in _function_names(core_icon_provider)
    assert "register_icon_provider" in _function_names(runtime_icon_registry)

    core_icon_calls = _literal_method_calls(core_icon_provider)
    assert ("setContextProperty", "Icon") not in {
        (method, name) for _line, method, name in core_icon_calls
    }
    assert (
        "prismqml.python.runtime.context_registry.register_context_property"
        in icon_registry_imports
    )
    assert ("setContextProperty", "Icon") not in {
        (method, name)
        for _line, method, name in _literal_method_calls(runtime_icon_registry)
    }


def test_app_updater_composition_has_one_runtime_owner():
    app_path = WINDOW_PACKAGE / "app.py"
    runtime_init = PYTHON_PACKAGE / "runtime" / "__init__.py"
    runtime_auto_update = PYTHON_PACKAGE / "runtime" / "auto_update.py"
    runtime_exports = _lazy_exports(runtime_init)
    app_imports = {target for _line, target in _resolved_imports(app_path)}
    auto_update_imports = {
        target for _line, target in _resolved_imports(runtime_auto_update)
    }

    assert runtime_exports["enable_auto_update"] == (
        ".auto_update",
        "enable_auto_update",
    )
    assert "prismqml.python.runtime.enable_auto_update" in app_imports
    assert "prismqml.python.core.Updater" not in app_imports
    assert "enable_auto_update" in _function_names(runtime_auto_update)

    window_calls = {
        (method, name)
        for path in sorted(WINDOW_PACKAGE.rglob("*.py"))
        for _line, method, name in _literal_method_calls(path)
    }
    assert ("setContextProperty", "appUpdater") not in window_calls
    assert (
        "prismqml.python.runtime.context_registry.register_context_property"
        in auto_update_imports
    )
    assert ("setContextProperty", "appUpdater") not in {
        (method, name)
        for _line, method, name in _literal_method_calls(runtime_auto_update)
    }


def test_lazy_provider_registration_has_one_runtime_owner():
    runtime_registry = PYTHON_PACKAGE / "runtime" / "registry.py"
    runtime_composition = PYTHON_PACKAGE / "runtime" / "context_composition.py"
    runtime_lazy_context = PYTHON_PACKAGE / "runtime" / "lazy_context.py"
    registry_imports = {
        target for _line, target in _resolved_imports(runtime_registry)
    }
    composition_imports = {
        target for _line, target in _resolved_imports(runtime_composition)
    }
    lazy_context_imports = {
        target for _line, target in _resolved_imports(runtime_lazy_context)
    }

    assert not (PROVIDERS_PACKAGE / "lazy_context.py").exists()
    assert (
        "prismqml.python.runtime.lazy_context.LazyQRCodeGenerator"
        in composition_imports
    )
    assert (
        "prismqml.python.runtime.lazy_context.LazyScreenEyedropperManager"
        in composition_imports
    )
    assert not any(
        target.startswith("prismqml.python.runtime.lazy_context.")
        for target in registry_imports
    )
    assert "LazyQRCodeGenerator" in _class_names(runtime_lazy_context)
    assert "LazyScreenEyedropperManager" in _class_names(runtime_lazy_context)

    violations = []
    for path in sorted(PROVIDERS_PACKAGE.rglob("*.py")):
        for line, method, name in _literal_method_calls(path):
            if method in {"setContextProperty", "addImageProvider"}:
                violations.append(
                    f"{path.relative_to(REPO_ROOT)}:{line}: {method}({name!r})"
                )
    assert violations == []
    assert (
        "prismqml.python.runtime.context_registry.register_image_provider_once"
        in lazy_context_imports
    )
    assert ("addImageProvider", "qrcode") not in {
        (method, name)
        for _line, method, name in _literal_method_calls(runtime_lazy_context)
    }


def test_window_runtime_composition_has_one_owner():
    builder = WINDOW_PACKAGE / "_window_builder.py"
    runtime_registry_owner = PYTHON_PACKAGE / "runtime" / "registry.py"
    runtime_registry = PYTHON_PACKAGE / "runtime" / "window_registry.py"
    runtime_composition = PYTHON_PACKAGE / "runtime" / "context_composition.py"
    runtime_init = PYTHON_PACKAGE / "runtime" / "__init__.py"
    runtime_context = PYTHON_PACKAGE / "runtime" / "context_registry.py"
    builder_imports = {target for _line, target in _resolved_imports(builder)}
    runtime_exports = _lazy_exports(runtime_init)
    registry_imports = {
        target for _line, target in _resolved_imports(runtime_registry_owner)
    }
    window_registry_imports = {
        target for _line, target in _resolved_imports(runtime_registry)
    }

    assert (
        "prismqml.python.runtime.prepare_window_engine"
        in builder_imports
    )
    assert runtime_exports["prepare_window_engine"] == (
        ".window_registry",
        "prepare_window_engine",
    )
    assert not (WINDOW_PACKAGE / "_window_engine_setup.py").exists()
    assert "prepare_window_engine" in _function_names(runtime_registry)
    assert "register_context_property" in _function_names(runtime_context)
    assert "register_context_properties" in _function_names(runtime_context)
    assert "register_image_provider_once" in _function_names(runtime_context)
    assert {
        "load_core_window_managers",
        "load_window_dependencies",
        "register_primary_context",
        "register_lazy_context",
        "register_window_context",
        "register_support_context",
        "register_window_engine_context",
    } <= _function_names(runtime_composition)
    for name in (
        "register_primary_context",
        "register_lazy_context",
        "register_window_context",
        "register_support_context",
    ):
        assert (
            f"prismqml.python.runtime.context_composition.{name}"
            in registry_imports
        )
    assert (
        "prismqml.python.runtime.context_composition"
        in window_registry_imports
    )
    for name in ("load_core_window_managers", "load_window_dependencies"):
        assert _attribute_function_calls(runtime_registry, "context_composition", name)
    assert _attribute_function_calls(
        runtime_registry, "context_composition", "register_window_engine_context"
    )

    violations = []
    for path in sorted(WINDOW_PACKAGE.rglob("*.py")):
        relative_path = path.relative_to(REPO_ROOT)
        if "prepare_window_engine" in _function_names(path):
            violations.append(f"{relative_path}: defines prepare_window_engine")
        for line, method, name in _literal_method_calls(path):
            owns_runtime_context = (
                method == "setContextProperty"
                and name in WINDOW_RUNTIME_CONTEXT_NAMES
            )
            owns_svg_provider = method == "addImageProvider" and name == "svg"
            if owns_runtime_context or owns_svg_provider:
                violations.append(f"{relative_path}:{line}: {method}({name!r})")

    assert violations == []

    for owner in (runtime_registry_owner, runtime_registry):
        assert not {
            "load_core_window_managers",
            "load_window_dependencies",
            "register_primary_context",
            "register_lazy_context",
            "register_window_context",
            "register_support_context",
            "register_window_engine_context",
        } & _function_names(owner)

    shared_context_owners = (
        runtime_registry_owner,
        runtime_registry,
    )
    for owner in shared_context_owners:
        assert not {
            (method, name)
            for _line, method, name in _literal_method_calls(owner)
            if method == "setContextProperty"
            and name
            in {
                "ThemeManager",
                "ShadowManager",
                "ConfigManager",
                "MicaManager",
                "ClipboardHelper",
                "NativeWindow",
                "PrismQmlStartupProfileVerbose",
                "PrismQmlAsynchronousPageLoaderEnabled",
            }
        }
