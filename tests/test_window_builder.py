# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Window builder fallback-boundary regressions. 窗口构建回退边界回归。"""

from pathlib import Path
from types import SimpleNamespace

import pytest


class _EngineSetupContext:
    def __init__(self, calls):
        self._calls = calls

    def setContextProperty(self, name, value):
        self._calls.append(("context", name, value))


class _EngineSetupEngine:
    def __init__(self, calls):
        self._calls = calls
        self._context = _EngineSetupContext(calls)

    def rootContext(self):
        self._calls.append("rootContext")
        return self._context

    def addImageProvider(self, name, provider):
        self._calls.append(("image_provider", name, provider))


def _recording_factory(calls, name, value):
    def factory():
        calls.append(("factory", name))
        return value

    return factory


class _EngineSetupScenario:
    def __init__(self):
        self.calls = []
        self.engine = _EngineSetupEngine(self.calls)
        names = ("theme", "shadow", "config", "mica", "clipboard", "native")
        self.values = {name: object() for name in names}
        self.svg_provider = object()
        self.config_factory = self.factory("config")

    def factory(self, name):
        return _recording_factory(self.calls, name, self.values[name])

    def profile(self, label):
        self.calls.append(("profile", label))

    def get_engine(self):
        self.calls.append("get_engine")
        return self.engine

    @staticmethod
    def fail_set_engine(_engine):
        pytest.fail("existing engine must not be replaced")

    @staticmethod
    def fail_create_engine():
        pytest.fail("existing engine must be reused")

    def load_core(self, profile):
        self.calls.append("load_core_imports")
        profile("导入核心管理器")
        return (
            self.factory("theme"),
            self.factory("shadow"),
            self.config_factory,
        )

    def load_window(self, profile):
        self.calls.append("load_window_imports")
        profile("导入窗口依赖")
        return (
            self.factory("mica"),
            self.factory("native"),
            self.factory("clipboard"),
        )

    def patch_setup(self, monkeypatch, setup):
        from prismqml.python.core import incubation
        from prismqml.python.runtime import context_composition

        monkeypatch.setattr(
            setup, "get_or_create_qml_engine", self.get_engine
        )
        monkeypatch.setattr(
            context_composition,
            "load_core_window_managers",
            self.load_core,
        )
        monkeypatch.setattr(
            context_composition,
            "load_window_dependencies",
            self.load_window,
        )
        monkeypatch.setattr(
            incubation,
            "asynchronous_page_loader_enabled",
            _recording_factory(self.calls, "asynchronous_page_loader", False),
        )
        monkeypatch.setattr(
            setup,
            "get_svg_provider",
            _recording_factory(self.calls, "svg", self.svg_provider),
        )


def _expected_engine_setup_prefix():
    return [
        "load_core_imports",
        ("profile", "导入核心管理器"),
        "get_engine",
        ("profile", "获取/创建 QML Engine"),
        "load_window_imports",
        ("profile", "导入窗口依赖"),
        "rootContext",
    ]


def _expected_engine_context_calls(scenario):
    values = scenario.values
    return [
        ("factory", "theme"),
        ("context", "ThemeManager", values["theme"]),
        ("factory", "shadow"),
        ("context", "ShadowManager", values["shadow"]),
        ("factory", "config"),
        ("context", "ConfigManager", values["config"]),
        ("factory", "mica"),
        ("context", "MicaManager", values["mica"]),
        ("factory", "clipboard"),
        ("context", "ClipboardHelper", values["clipboard"]),
        ("context", "PrismQmlStartupProfileVerbose", True),
        ("factory", "asynchronous_page_loader"),
        ("context", "PrismQmlAsynchronousPageLoaderEnabled", False),
        ("factory", "native"),
        ("context", "NativeWindow", values["native"]),
        ("profile", "注入 ContextProperty"),
    ]


def _expected_engine_provider_calls(scenario):
    return [
        ("factory", "svg"),
        ("image_provider", "svg", scenario.svg_provider),
        ("profile", "注册 ImageProvider"),
    ]


def _expected_engine_reuse_prefix():
    return [
        "load_core_imports",
        ("profile", "导入核心管理器"),
        "get_engine",
        ("profile", "获取/创建 QML Engine"),
    ]


def test_window_engine_setup_preserves_context_provider_and_profile_order(monkeypatch):
    from prismqml.python.runtime import window_registry as setup

    scenario = _EngineSetupScenario()
    scenario.patch_setup(monkeypatch, setup)
    builder = SimpleNamespace()

    get_config_manager = setup.prepare_window_engine(
        builder, True, scenario.profile
    )

    expected = _expected_engine_setup_prefix()
    expected += _expected_engine_context_calls(scenario)
    expected += _expected_engine_provider_calls(scenario)
    assert builder._engine is scenario.engine
    assert get_config_manager is scenario.config_factory
    assert scenario.calls == expected


def test_window_dependency_loaders_preserve_real_identity_and_profile_order():
    from prismqml.python.core import ThemeManager
    from prismqml.python.runtime.configuration import get_config_manager
    from prismqml.python.runtime import context_composition as setup
    from prismqml.python.runtime.window_services import (
        get_clipboard_helper,
        get_mica_manager,
        get_native_window_hook,
        getShadowManager,
    )

    profiles = []
    core_managers = setup.load_core_window_managers(profiles.append)
    window_dependencies = setup.load_window_dependencies(profiles.append)

    assert core_managers == (ThemeManager, getShadowManager, get_config_manager)
    assert window_dependencies == (
        get_mica_manager,
        get_native_window_hook,
        get_clipboard_helper,
    )
    assert profiles == ["导入核心管理器", "导入窗口依赖"]


def test_window_engine_setup_assigns_runtime_engine(monkeypatch):
    from prismqml.python.runtime import window_registry as setup

    calls = []
    engine = object()
    monkeypatch.setattr(
        setup,
        "get_or_create_qml_engine",
        lambda: calls.append("get_or_create") or engine,
    )
    builder = SimpleNamespace()

    setup._ensure_window_engine(
        builder, lambda label: calls.append(("profile", label))
    )

    assert builder._engine is engine
    assert calls == [
        "get_or_create",
        ("profile", "获取/创建 QML Engine"),
    ]


def test_window_engine_setup_reuses_complete_context_registration(monkeypatch):
    from prismqml.python.runtime import context_registry
    from prismqml.python.runtime import context_composition
    from prismqml.python.runtime import window_registry as setup

    scenario = _EngineSetupScenario()
    scenario.patch_setup(monkeypatch, setup)
    context_registry.mark_context_registration(
        scenario.engine, context_registry.FULL_CONTEXT_REGISTRATION
    )
    monkeypatch.setattr(
        context_composition,
        "load_window_dependencies",
        lambda _profile: pytest.fail("complete context must be reused"),
    )
    builder = SimpleNamespace()

    get_config_manager = setup.prepare_window_engine(
        builder, True, scenario.profile
    )

    expected = _expected_engine_reuse_prefix()
    expected += [
        ("profile", "复用完整 ContextProperty"),
        ("factory", "svg"),
        ("image_provider", "svg", scenario.svg_provider),
        ("profile", "注册 ImageProvider"),
    ]
    assert get_config_manager is scenario.config_factory
    assert scenario.calls == expected


def test_window_engine_setup_reuses_window_context_registration(monkeypatch):
    from prismqml.python.runtime import context_registry
    from prismqml.python.runtime import context_composition
    from prismqml.python.runtime import window_registry as setup

    scenario = _EngineSetupScenario()
    scenario.patch_setup(monkeypatch, setup)
    context_registry.mark_context_registration(
        scenario.engine, context_registry.WINDOW_CONTEXT_REGISTRATION
    )
    monkeypatch.setattr(
        context_composition,
        "load_window_dependencies",
        lambda _profile: pytest.fail("window context must be reused"),
    )
    builder = SimpleNamespace()

    setup.prepare_window_engine(builder, True, scenario.profile)

    expected = _expected_engine_reuse_prefix()
    expected += [
        ("profile", "复用 ContextProperty"),
        ("factory", "svg"),
        ("image_provider", "svg", scenario.svg_provider),
        ("profile", "注册 ImageProvider"),
    ]
    assert scenario.calls == expected


@pytest.mark.parametrize("error_type", [ValueError, KeyboardInterrupt, SystemExit])
def test_window_engine_setup_propagates_non_runtime_errors(
    monkeypatch, error_type
):
    from prismqml.python.runtime import window_registry as setup

    failure = error_type("stop")
    monkeypatch.setattr(
        setup,
        "get_or_create_qml_engine",
        lambda: (_ for _ in ()).throw(failure),
    )

    with pytest.raises(error_type) as caught:
        setup._ensure_window_engine(
            SimpleNamespace(), lambda _label: pytest.fail("must fail fast")
        )

    assert caught.value is failure


class _FailingEngineSetupContext:
    def __init__(self, calls, error_type):
        self._calls = calls
        self._error_type = error_type

    def setContextProperty(self, name, _value):
        self._calls.append(("context", name))
        if name == "ConfigManager":
            raise self._error_type("stop")


def _unused_window_dependencies():
    return (
        lambda: object(),
        lambda: object(),
        lambda: object(),
    )


def _expected_context_failure_calls():
    return [
        ("factory", "theme"),
        ("context", "ThemeManager"),
        ("factory", "shadow"),
        ("context", "ShadowManager"),
        ("factory", "config"),
        ("context", "ConfigManager"),
    ]


@pytest.mark.parametrize("error_type", [RuntimeError, KeyboardInterrupt, SystemExit])
def test_window_context_setup_fail_fast(error_type):
    from prismqml.python.runtime import context_composition as setup

    calls = []
    context = _FailingEngineSetupContext(calls, error_type)
    engine = SimpleNamespace(rootContext=lambda: context)
    factories = tuple(
        _recording_factory(calls, name, object())
        for name in ("theme", "shadow", "config")
    )

    with pytest.raises(error_type, match="stop"):
        setup.register_window_engine_context(
            SimpleNamespace(_engine=engine),
            False,
            factories,
            _unused_window_dependencies(),
            lambda _label: pytest.fail("must fail fast"),
        )

    assert calls == _expected_context_failure_calls()


class _FailingProviderEngine:
    def __init__(self, calls, error_type, failure_stage):
        self._calls = calls
        self._error_type = error_type
        self._failure_stage = failure_stage

    def addImageProvider(self, name, provider):
        self._calls.append(("add", name, provider))
        if self._failure_stage == "add":
            raise self._error_type("stop")


@pytest.mark.parametrize("failure_stage", ["svg_factory", "add"])
@pytest.mark.parametrize("error_type", [RuntimeError, KeyboardInterrupt, SystemExit])
def test_window_svg_provider_setup_fail_fast(
    monkeypatch, error_type, failure_stage
):
    from prismqml.python.runtime import window_registry as setup

    calls = []
    provider = object()
    engine = _FailingProviderEngine(calls, error_type, failure_stage)

    def get_svg_provider():
        calls.append("get_svg")
        if failure_stage == "svg_factory":
            raise error_type("stop")
        return provider

    monkeypatch.setattr(setup, "get_svg_provider", get_svg_provider)
    with pytest.raises(error_type, match="stop"):
        setup._register_window_image_providers(
            SimpleNamespace(_engine=engine),
            lambda _label: pytest.fail("must fail fast"),
        )

    expected = ["get_svg"]
    if failure_stage == "add":
        expected.append(("add", "svg", provider))
    assert calls == expected


def test_generated_qml_helpers_empty_collections():
    from prismqml.python.window._window_builder import WindowBuilderMixin

    builder = WindowBuilderMixin()
    builder._nav_items = []
    builder._bottom_nav_items = []

    assert builder._render_navigation_items_qml() == ""
    assert builder._render_bottom_items_qml() == ""
    assert builder._render_page_containers_qml() == ""


def test_generated_qml_helpers_render_navigation_contract():
    from prismqml.python.window._window_builder import WindowBuilderMixin

    builder = WindowBuilderMixin()
    builder._resolve_icon_path = lambda name: f"icon://{name}"
    builder._nav_items = [
        SimpleNamespace(text='Top "one"', icon="home"),
        SimpleNamespace(text="Top two", icon="settings"),
    ]
    builder._bottom_nav_items = [
        SimpleNamespace(text="Default", icon="info"),
        SimpleNamespace(text="Action", icon="run", selectable=False),
    ]

    top = builder._render_navigation_items_qml()
    bottom = builder._render_bottom_items_qml()

    assert top == (
        '{ "text": "Top \\"one\\"", "icon": "icon://home" }, '
        '{ "text": "Top two", "icon": "icon://settings" }'
    )
    assert bottom == (
        '{ "text": "Default", "icon": "icon://info", '
        '"key": "page_2", "selectable": true }, '
        '{ "text": "Action", "icon": "icon://run", '
        '"key": "page_3", "selectable": false }'
    )


def test_generated_page_containers_keep_structure():
    from prismqml.python.window._window_builder import WindowBuilderMixin

    builder = WindowBuilderMixin()
    builder._nav_items = [object()]
    builder._bottom_nav_items = [object(), object()]

    pages = builder._render_page_containers_qml()

    assert pages.startswith("\n        Item {")
    assert pages.endswith("        }")
    assert pages.count('objectName: "page_') == 3
    assert [pages.index(f'objectName: "page_{i}"') for i in range(3)] == sorted(
        pages.index(f'objectName: "page_{i}"') for i in range(3)
    )
    assert pages.count("width: parent ? parent.width : 0") == 3
    assert pages.count("height: parent ? parent.height : 0") == 3


def test_window_template_preserves_dollar_values_and_boolean_literals():
    from prismqml.python.window._window_builder import WindowBuilderMixin

    builder = WindowBuilderMixin()
    builder._width = 640
    builder._height = 480
    builder._title = 'Dollar $HOME "quoted" {brace}\nline'
    builder._icon_colored = True
    builder._lazy_loading = True
    builder._caption_action_visible = True
    builder._caption_action_icon = "Bot"
    builder._caption_action_tool_tip = 'Ask "$" {context}\nnow'
    builder._caption_action_enabled = False

    source = builder._render_window_qml(
        Path("D:/Qml$Root"),
        "WindowsBar",
        "file:///D:/icon$1.svg",
        False,
        True,
        '{"text": "$nav"}',
        '{"text": "$bottom"}',
        "\n        Item {}",
    )

    assert 'import "file:///D:/Qml$Root"' in source
    assert 'windowTitle: "Dollar $HOME \\"quoted\\" \\u007Bbrace\\u007D\\nline"' in source
    assert 'windowIcon: "file:///D:/icon$1.svg"' in source
    assert "windowIconColored: true" in source
    assert "captionActionVisible: true" in source
    assert 'captionActionIcon: "Bot"' in source
    assert (
        'captionActionToolTip: "Ask \\"$\\" \\u007Bcontext\\u007D\\nnow"'
        in source
    )
    assert "captionActionEnabled: false" in source
    assert "startupProfilingVerbose: false" in source
    assert "lazyLoading: true" in source
    assert "micaEnabled: true\n    \n" in source
    assert 'navigationItems: [{"text": "$nav"}]' in source
    assert source.endswith("}\n")


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_generated_window_file_boundary_process_control_propagates(
    monkeypatch, error_type
):
    from prismqml.python.window._window_builder import WindowBuilderMixin

    def stop_load(_self, _qml, _component, _profile, _verbose):
        raise error_type("stop")

    monkeypatch.setattr(
        WindowBuilderMixin,
        "_load_generated_window_component",
        stop_load,
    )
    builder = WindowBuilderMixin()
    with pytest.raises(error_type, match="stop"):
        builder._load_generated_window_boundary("", "", lambda _label: None, False)
