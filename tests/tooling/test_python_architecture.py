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


def test_window_helper_access_has_one_runtime_owner():
    runtime_init = PYTHON_PACKAGE / "runtime" / "__init__.py"
    runtime_services = PYTHON_PACKAGE / "runtime" / "window_services.py"
    runtime_registry = PYTHON_PACKAGE / "runtime" / "registry.py"
    runtime_composition = PYTHON_PACKAGE / "runtime" / "context_composition.py"
    window_core = WINDOW_PACKAGE / "window_core.py"
    application_icon = WINDOW_PACKAGE / "_application_icon_runtime.py"
    runtime_exports = _lazy_exports(runtime_init)

    assert runtime_exports["get_window_helper"] == (
        ".window_services",
        "get_window_helper",
    )
    assert runtime_exports["get_mica_manager"] == (
        ".window_services",
        "get_mica_manager",
    )
    assert "get_window_helper" in _function_names(runtime_services)
    assert "get_mica_manager" in _function_names(runtime_services)
    assert (
        "prismqml.python.core.window_helper.get_window_helper"
        in {
            target for _line, target in _resolved_imports(runtime_services)
        }
    )

    registry_imports = {
        target for _line, target in _resolved_imports(runtime_registry)
    }
    composition_imports = {
        target for _line, target in _resolved_imports(runtime_composition)
    }
    assert (
        "prismqml.python.runtime.window_services.get_window_helper"
        in composition_imports
    )
    assert (
        "prismqml.python.window.mica_window.get_mica_manager"
        in {
            target for _line, target in _resolved_imports(runtime_services)
        }
    )
    for owner in (window_core, application_icon):
        imports = {target for _line, target in _resolved_imports(owner)}
        assert "prismqml.python.runtime.get_window_helper" in imports
        assert "prismqml.python.core.window_helper.get_window_helper" not in imports
    window_core_imports = {
        target for _line, target in _resolved_imports(window_core)
    }
    assert "prismqml.python.runtime.get_mica_manager" in window_core_imports
    assert "prismqml.python.window.mica_window.get_mica_manager" not in window_core_imports
    assert "prismqml.python.core.window_helper.get_window_helper" not in registry_imports
    assert "prismqml.python.core.window_helper.get_window_helper" not in composition_imports


def test_qml_engine_composition_has_one_runtime_owner():
    app = WINDOW_PACKAGE / "app.py"
    window_registry = PYTHON_PACKAGE / "runtime" / "window_registry.py"
    runtime_engine = PYTHON_PACKAGE / "runtime" / "engine.py"
    runtime_init = PYTHON_PACKAGE / "runtime" / "__init__.py"
    runtime_exports = _lazy_exports(runtime_init)
    app_imports = {target for _line, target in _resolved_imports(app)}
    window_imports = {
        target for _line, target in _resolved_imports(window_registry)
    }

    for name in (
        "create_qml_engine",
        "publish_qml_engine",
        "is_published_qml_engine",
        "get_published_qml_engine",
        "register_qml_engine_binding",
        "release_qml_engine_bindings",
        "reset_qml_engine",
        "get_or_create_qml_engine",
        "configure_application_engine",
    ):
        assert runtime_exports[name] == (".engine", name)
        assert name in _function_names(runtime_engine)

    for name in (
        "create_qml_engine",
        "publish_qml_engine",
        "configure_application_engine",
    ):
        assert f"prismqml.python.runtime.{name}" in app_imports
    assert (
        "prismqml.python.runtime.engine.get_or_create_qml_engine"
        in window_imports
    )

    violations = []
    for path in sorted(PYTHON_PACKAGE.rglob("*.py")):
        if path == runtime_engine:
            continue
        for line in _named_function_calls(path, "QQmlApplicationEngine"):
            violations.append(
                f"{path.relative_to(REPO_ROOT)}:{line}: QQmlApplicationEngine()"
            )
        for line in _attribute_function_calls(path, "EngineManager", "set_engine"):
            violations.append(
                f"{path.relative_to(REPO_ROOT)}:{line}: EngineManager.set_engine()"
            )
        for name in ("_release_engine_bindings", "reset"):
            for line in _attribute_function_calls(path, "EngineManager", name):
                violations.append(
                    f"{path.relative_to(REPO_ROOT)}:{line}: "
                    f"EngineManager.{name}()"
                )

    assert violations == []

    window_engine_violations = []
    for path in sorted(WINDOW_PACKAGE.rglob("*.py")):
        for name in ("get_engine", "register_engine_binding"):
            for line in _attribute_function_calls(path, "EngineManager", name):
                window_engine_violations.append(
                    f"{path.relative_to(REPO_ROOT)}:{line}: "
                    f"EngineManager.{name}()"
                )
    assert window_engine_violations == []


def test_application_startup_composition_has_one_runtime_owner():
    app = WINDOW_PACKAGE / "app.py"
    runtime_application = PYTHON_PACKAGE / "runtime" / "application.py"
    runtime_init = PYTHON_PACKAGE / "runtime" / "__init__.py"
    runtime_exports = _lazy_exports(runtime_init)
    app_imports = {target for _line, target in _resolved_imports(app)}

    runtime_names = (
        "prepare_application_environment",
        "create_qt_application",
        "install_application_input_filter",
        "install_application_dwm_filter",
        "reset_application_input_filter",
        "reset_application_dwm_filter",
    )
    for name in runtime_names:
        assert runtime_exports[name] == (".application", name)
        assert name in _function_names(runtime_application)
        assert f"prismqml.python.runtime.{name}" in app_imports

    violations = []
    owned_calls = (
        "QApplication",
        "configure_qml_environment",
        "applyDpiScale",
        "install_qt_message_handler",
        "install_input_focus_filter",
        "installDwmSyncFilter",
        "reset_input_focus_filter",
        "reset_dwm_sync_filter",
    )
    owned_implementation_paths = {
        PYTHON_PACKAGE / "core" / "input_focus_filter.py",
        PYTHON_PACKAGE / "core" / "shadow.py",
    }
    for path in sorted(PYTHON_PACKAGE.rglob("*.py")):
        if path == runtime_application or path in owned_implementation_paths:
            continue
        for name in owned_calls:
            for line in _named_function_calls(path, name):
                violations.append(
                    f"{path.relative_to(REPO_ROOT)}:{line}: {name}()"
                )
        for line in _attribute_function_calls(
            path, "QQuickWindow", "setGraphicsApi"
        ):
            violations.append(
                f"{path.relative_to(REPO_ROOT)}:{line}: "
                "QQuickWindow.setGraphicsApi()"
            )

    assert violations == []
    assert _attribute_function_calls(
        runtime_application, "QQuickWindow", "setGraphicsApi"
    )
    assert "QSGRendererInterface.GraphicsApi.Direct3D11" in (
        runtime_application.read_text(encoding="utf-8")
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


def test_appearance_persistence_has_one_runtime_composition_owner():
    appearance = PYTHON_PACKAGE / "runtime" / "appearance.py"
    appearance_defaults = CORE_PACKAGE / "appearance_defaults.py"
    config_manager = PYTHON_PACKAGE / "config" / "config_manager.py"
    registry = PYTHON_PACKAGE / "runtime" / "registry.py"
    window_registry = PYTHON_PACKAGE / "runtime" / "window_registry.py"
    composition = PYTHON_PACKAGE / "runtime" / "context_composition.py"

    appearance_imports = {target for _line, target in _resolved_imports(appearance)}
    config_imports = {target for _line, target in _resolved_imports(config_manager)}

    assert (
        "prismqml.python.core.theme._bind_appearance_persistence"
        in appearance_imports
    )
    assert "_persist_appearance_change" in _function_names(appearance)
    assert "install_appearance_persistence" in _function_names(appearance)
    assert "_apply_config_appearance" in _function_names(appearance)
    assert "install_config_appearance_runtime" in _function_names(appearance)
    assert (
        "prismqml.python.core.theme._bind_appearance_persistence"
        not in config_imports
    )
    assert "prismqml.python.core.theme.getThemeManager" not in config_imports
    assert "_persist_appearance_change" not in _function_names(config_manager)
    assert "_bind_appearance_runtime" in _function_names(config_manager)
    assert _literal_assignment(appearance_defaults, "DEFAULT_ACCENT") == "#0e5a9c"

    accent_literal_owners = [
        path
        for path in sorted(PYTHON_PACKAGE.rglob("*.py"))
        if "#0e5a9c" in path.read_text(encoding="utf-8")
    ]
    assert accent_literal_owners == [appearance_defaults]

    runtime_factory_violations = []
    for path in sorted(CONFIG_PACKAGE.rglob("*.py")):
        for line, target in _resolved_imports(path):
            if target.endswith((".getThemeManager", ".ThemeManager")):
                runtime_factory_violations.append(
                    f"{path.relative_to(REPO_ROOT)}:{line}: {target}"
                )
    assert runtime_factory_violations == []

    composition_imports = {
        target for _line, target in _resolved_imports(composition)
    }
    assert (
        "prismqml.python.runtime.appearance.install_appearance_persistence"
        in composition_imports
    )
    assert _named_function_calls(composition, "install_appearance_persistence")
    for owner in (registry, window_registry):
        assert not _named_function_calls(owner, "install_appearance_persistence")


def test_configuration_singleton_has_one_runtime_composition_owner():
    configuration = PYTHON_PACKAGE / "runtime" / "configuration.py"
    runtime_init = PYTHON_PACKAGE / "runtime" / "__init__.py"
    runtime_exports = _lazy_exports(runtime_init)
    configuration_imports = {
        target for _line, target in _resolved_imports(configuration)
    }

    assert runtime_exports["get_config_manager"] == (
        ".configuration",
        "get_config_manager",
    )
    assert "get_config_manager" in _function_names(configuration)
    assert configuration_imports == {
        "prismqml.python.config.getConfigManager",
        "prismqml.python.runtime.appearance.install_config_appearance_runtime",
    }
    assert _named_function_calls(
        configuration, "install_config_appearance_runtime"
    )

    for owner in (
        WINDOW_PACKAGE / "app.py",
        WINDOW_PACKAGE / "window_core.py",
    ):
        imports = {target for _line, target in _resolved_imports(owner)}
        assert "prismqml.python.runtime.get_config_manager" in imports
        assert (
            "prismqml.python.runtime.configuration.get_config_manager"
            not in imports
        )

    violations = []
    for path in sorted(PYTHON_PACKAGE.rglob("*.py")):
        if path == configuration or path.is_relative_to(PYTHON_PACKAGE / "config"):
            continue
        for line, target in _resolved_imports(path):
            if target == "prismqml.python.config.getConfigManager":
                violations.append(f"{path.relative_to(REPO_ROOT)}:{line}: {target}")

    assert violations == []


def test_notification_qml_helper_has_one_runtime_composition_owner():
    core_notification = CORE_PACKAGE / "notification.py"
    runtime_notification = PYTHON_PACKAGE / "runtime" / "notification.py"
    core_init = CORE_PACKAGE / "__init__.py"
    runtime_init = PYTHON_PACKAGE / "runtime" / "__init__.py"
    core_exports = _lazy_exports(core_init)
    runtime_exports = _lazy_exports(runtime_init)
    runtime_imports = {
        target for _line, target in _resolved_imports(runtime_notification)
    }

    assert not core_notification.exists()
    assert runtime_notification.exists()
    assert "NotificationPosition" not in core_exports
    assert "NotificationSeverity" not in core_exports
    assert "showDesktopInfo" not in core_exports
    assert runtime_exports["NotificationPosition"] == (
        ".notification",
        "Position",
    )
    assert runtime_exports["showDesktopInfo"] == (
        ".notification",
        "showDesktopInfo",
    )
    assert "prismqml.python.runtime.engine.get_published_qml_engine" in runtime_imports
    assert "prismqml.python.core.logger.getLogger" in runtime_imports
