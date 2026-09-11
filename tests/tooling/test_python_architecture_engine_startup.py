# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QML engine and application startup owners. 引擎与启动装配所有者门禁。"""

from python_architecture_shared import (
    PYTHON_PACKAGE,
    REPO_ROOT,
    WINDOW_PACKAGE,
    _attribute_function_calls,
    _function_names,
    _lazy_exports,
    _named_function_calls,
    _resolved_imports,
)


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
