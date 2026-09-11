# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Singleton accessor and public facade owners.
单例访问器与公开入口所有者门禁（shadow、provider factories、icon provider、
window helper、DWM filter）。"""

from python_architecture_shared import (
    CORE_PACKAGE,
    PROVIDERS_PACKAGE,
    PYTHON_PACKAGE,
    REPO_ROOT,
    WINDOW_PACKAGE,
    _function_names,
    _lazy_exports,
    _literal_assignment,
    _resolved_imports,
)


def test_shadow_manager_access_has_one_runtime_owner():
    root_init = REPO_ROOT / "prismqml" / "__init__.py"
    core_init = CORE_PACKAGE / "__init__.py"
    core_shadow = CORE_PACKAGE / "shadow.py"
    runtime_init = PYTHON_PACKAGE / "runtime" / "__init__.py"
    runtime_services = PYTHON_PACKAGE / "runtime" / "window_services.py"
    runtime_composition = PYTHON_PACKAGE / "runtime" / "context_composition.py"
    root_exports = _lazy_exports(root_init)
    core_exports = _lazy_exports(core_init)
    core_public_names = set(_literal_assignment(core_init, "__all__"))
    runtime_exports = _lazy_exports(runtime_init)

    assert runtime_exports["getShadowManager"] == (
        ".window_services",
        "getShadowManager",
    )
    assert root_exports["getShadowManager"] == (
        ".python.runtime",
        "getShadowManager",
    )
    assert "getShadowManager" not in core_exports
    assert "getShadowManager" not in core_public_names
    assert "getShadowManager" in _function_names(runtime_services)
    service_imports = {target for _line, target in _resolved_imports(runtime_services)}
    assert "prismqml.python.core.shadow.getShadowManager" in service_imports

    composition_imports = {
        target for _line, target in _resolved_imports(runtime_composition)
    }
    assert "prismqml.python.runtime.window_services.getShadowManager" in (
        composition_imports
    )
    assert "prismqml.python.core.shadow.getShadowManager" not in composition_imports

    violations = []
    for path in sorted(PYTHON_PACKAGE.rglob("*.py")):
        if path in (core_shadow, runtime_services):
            continue
        for line, target in _resolved_imports(path):
            if target == "prismqml.python.core.shadow.getShadowManager":
                violations.append(f"{path.relative_to(REPO_ROOT)}:{line}: {target}")
    assert violations == []


def test_optional_provider_factories_have_one_runtime_owner():
    root_init = REPO_ROOT / "prismqml" / "__init__.py"
    runtime_init = PYTHON_PACKAGE / "runtime" / "__init__.py"
    provider_services = PYTHON_PACKAGE / "runtime" / "provider_services.py"
    lazy_context = PYTHON_PACKAGE / "runtime" / "lazy_context.py"
    window_registry = PYTHON_PACKAGE / "runtime" / "window_registry.py"
    providers_init = PROVIDERS_PACKAGE / "__init__.py"
    example = REPO_ROOT / "examples" / "main.py"
    root_exports = _lazy_exports(root_init)
    runtime_exports = _lazy_exports(runtime_init)
    providers_exports = _lazy_exports(providers_init)
    provider_names = (
        "get_qrcode_generator",
        "get_qrcode_provider",
        "get_screen_eyedropper_manager",
        "get_svg_provider",
    )

    for name in provider_names:
        assert root_exports[name] == (".python.runtime", name)
        assert runtime_exports[name] == (".provider_services", name)
        assert providers_exports[name] == ("..runtime", name)
        assert name in _function_names(provider_services)

    provider_imports = {
        target for _line, target in _resolved_imports(provider_services)
    }
    assert {
        "prismqml.python.providers.qrcode_generator.get_qrcode_generator",
        "prismqml.python.providers.qrcode_generator.get_qrcode_provider",
        "prismqml.python.providers.screen_eyedropper.get_screen_eyedropper_manager",
        "prismqml.python.providers.svg_provider.get_svg_provider",
    } <= provider_imports

    lazy_imports = {target for _line, target in _resolved_imports(lazy_context)}
    assert {
        "prismqml.python.runtime.provider_services.get_qrcode_generator",
        "prismqml.python.runtime.provider_services.get_qrcode_provider",
        "prismqml.python.runtime.provider_services.get_screen_eyedropper_manager",
    } <= lazy_imports
    assert not {
        "prismqml.python.providers.qrcode_generator.get_qrcode_generator",
        "prismqml.python.providers.qrcode_generator.get_qrcode_provider",
        "prismqml.python.providers.screen_eyedropper.get_screen_eyedropper_manager",
    } & lazy_imports

    window_imports = {
        target for _line, target in _resolved_imports(window_registry)
    }
    assert "prismqml.python.runtime.provider_services.get_svg_provider" in (
        window_imports
    )
    assert "prismqml.python.providers.svg_provider.get_svg_provider" not in (
        window_imports
    )

    example_imports = {target for _line, target in _resolved_imports(example)}
    assert "prismqml.python.runtime.get_svg_provider" in example_imports
    assert "prismqml.python.providers.get_svg_provider" not in example_imports
    assert "prismqml.python.core.register_types" not in example_imports


def test_icon_provider_access_has_one_runtime_owner():
    root_init = REPO_ROOT / "prismqml" / "__init__.py"
    core_init = CORE_PACKAGE / "__init__.py"
    core_icon_provider = CORE_PACKAGE / "icon_provider.py"
    runtime_init = PYTHON_PACKAGE / "runtime" / "__init__.py"
    runtime_icon_registry = PYTHON_PACKAGE / "runtime" / "icon_registry.py"
    root_exports = _lazy_exports(root_init)
    core_exports = _lazy_exports(core_init)
    runtime_exports = _lazy_exports(runtime_init)

    assert root_exports["get_icon_provider"] == (
        ".python.runtime",
        "get_icon_provider",
    )
    assert runtime_exports["get_icon_provider"] == (
        ".icon_registry",
        "get_icon_provider",
    )
    assert "get_icon_provider" not in _literal_assignment(core_init, "__all__")
    assert "get_icon_provider" not in core_exports
    assert "get_icon_provider" in _function_names(runtime_icon_registry)
    assert "get_icon_provider" in _function_names(core_icon_provider)

    runtime_imports = {
        target for _line, target in _resolved_imports(runtime_icon_registry)
    }
    assert "prismqml.python.core.icon_provider.get_icon_provider" in runtime_imports

    violations = []
    for path in sorted(PYTHON_PACKAGE.rglob("*.py")):
        if path in (core_icon_provider, runtime_icon_registry):
            continue
        for line, target in _resolved_imports(path):
            if target == "prismqml.python.core.icon_provider.get_icon_provider":
                violations.append(f"{path.relative_to(REPO_ROOT)}:{line}: {target}")
    assert violations == []


def test_window_helper_access_has_one_runtime_owner():
    root_init = REPO_ROOT / "prismqml" / "__init__.py"
    runtime_init = PYTHON_PACKAGE / "runtime" / "__init__.py"
    runtime_services = PYTHON_PACKAGE / "runtime" / "window_services.py"
    runtime_registry = PYTHON_PACKAGE / "runtime" / "registry.py"
    runtime_composition = PYTHON_PACKAGE / "runtime" / "context_composition.py"
    window_exports = _lazy_exports(WINDOW_PACKAGE / "__init__.py")
    providers_exports = _lazy_exports(PROVIDERS_PACKAGE / "__init__.py")
    window_core = WINDOW_PACKAGE / "window_core.py"
    application_icon = WINDOW_PACKAGE / "_application_icon_runtime.py"
    root_exports = _lazy_exports(root_init)
    runtime_exports = _lazy_exports(runtime_init)

    assert runtime_exports["get_window_helper"] == (
        ".window_services",
        "get_window_helper",
    )
    assert runtime_exports["get_mica_manager"] == (
        ".window_services",
        "get_mica_manager",
    )
    for name in (
        "get_acrylic_helper",
        "get_native_window_hook",
        "get_clipboard_helper",
    ):
        assert runtime_exports[name] == (".window_services", name)
    for name in ("get_mica_manager", "get_acrylic_helper", "get_clipboard_helper"):
        assert root_exports[name] == (".python.runtime", name)
    assert providers_exports["get_clipboard_helper"] == (
        "..runtime",
        "get_clipboard_helper",
    )
    for name in (
        "get_mica_manager",
        "get_acrylic_helper",
        "get_native_window_hook",
    ):
        assert window_exports[name] == ("..runtime", name)
    assert "get_window_helper" in _function_names(runtime_services)
    assert "get_mica_manager" in _function_names(runtime_services)
    assert {
        "get_acrylic_helper",
        "get_native_window_hook",
        "get_clipboard_helper",
    } <= _function_names(runtime_services)
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
        "prismqml.python.runtime.appearance.getThemeManager"
        in composition_imports
    )
    assert "prismqml.python.core.theme.getThemeManager" not in composition_imports
    assert (
        "prismqml.python.runtime.window_services.get_mica_manager"
        in composition_imports
    )
    assert (
        "prismqml.python.runtime.window_services.get_native_window_hook"
        in composition_imports
    )
    assert (
        "prismqml.python.runtime.window_services.get_clipboard_helper"
        in composition_imports
    )
    assert (
        "prismqml.python.runtime.window_services.get_acrylic_helper"
        in composition_imports
    )
    assert "prismqml.python.window.mica_window.get_mica_manager" not in composition_imports
    assert "prismqml.python.window.mica_window.get_acrylic_helper" not in composition_imports
    assert "prismqml.python.window.native_window.get_native_window_hook" not in composition_imports
    assert "prismqml.python.providers.clipboard.get_clipboard_helper" not in composition_imports
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


def test_public_dwm_filter_entrypoint_has_one_runtime_owner():
    root_init = REPO_ROOT / "prismqml" / "__init__.py"
    core_init = CORE_PACKAGE / "__init__.py"
    runtime_init = PYTHON_PACKAGE / "runtime" / "__init__.py"
    runtime_application = PYTHON_PACKAGE / "runtime" / "application.py"
    root_exports = _lazy_exports(root_init)
    core_exports = _lazy_exports(core_init)
    runtime_exports = _lazy_exports(runtime_init)

    assert root_exports["installDwmSyncFilter"] == (
        ".python.runtime",
        "installDwmSyncFilter",
    )
    assert runtime_exports["installDwmSyncFilter"] == (
        ".application",
        "installDwmSyncFilter",
    )
    assert "installDwmSyncFilter" not in _literal_assignment(core_init, "__all__")
    assert "installDwmSyncFilter" not in core_exports
    assert "installDwmSyncFilter" in _function_names(runtime_application)
    assert "return install_application_dwm_filter()" in runtime_application.read_text(
        encoding="utf-8"
    )
