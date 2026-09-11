# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Module ownership boundaries: persistence, config, notification, win32.
模块所有者边界门禁：外观持久化、配置单例、通知 helper 与 SetWindowPos 声明。"""

from python_architecture_shared import (
    CONFIG_PACKAGE,
    CORE_PACKAGE,
    PYTHON_PACKAGE,
    REPO_ROOT,
    WINDOW_PACKAGE,
    _function_names,
    _lazy_exports,
    _literal_assignment,
    _named_function_calls,
    _resolved_imports,
)


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
    assert "_apply_config_appearance" in _function_names(appearance)
    assert "configure_appearance_persistence" in _function_names(appearance)
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

    assert _named_function_calls(composition, "get_config_manager")
    for owner in (registry, window_registry):
        assert not _named_function_calls(owner, "configure_appearance_persistence")


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
        "prismqml.python.runtime.appearance.configure_appearance_persistence",
    }
    assert _named_function_calls(
        configuration, "configure_appearance_persistence"
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


def test_set_window_pos_signature_has_one_shared_owner():
    """SetWindowPos ctypes signature stays in one core declaration helper."""
    helper = CORE_PACKAGE / "_win32_api.py"
    helper_source = helper.read_text(encoding="utf-8")
    callsites = (
        CORE_PACKAGE / "shadow.py",
        CORE_PACKAGE / "_window_follower.py",
        CORE_PACKAGE / "_popup_owner.py",
        PYTHON_PACKAGE / "window" / "native_window.py",
    )

    assert helper.exists()
    assert helper_source.count("function.argtypes = [") == 1
    assert "def bind_set_window_pos(user32):" in helper_source
    for path in callsites:
        source = path.read_text(encoding="utf-8")
        assert "bind_set_window_pos" in source, path
        assert "SetWindowPos.argtypes" not in source, path
