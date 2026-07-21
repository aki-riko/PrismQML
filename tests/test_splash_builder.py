# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Splash builder boundary regressions. 启动画面构建边界回归。"""

from pathlib import Path
from types import SimpleNamespace

import pytest


_DEFAULT_SPLASH = object()


class _FakeError:
    def __init__(self, text):
        self._text = text

    def toString(self):
        return self._text


class _FakeSplash:
    def __init__(self, trace=None, parent_error=None):
        self.trace = trace if trace is not None else []
        self.parent_error = parent_error
        self.parent = None
        self.properties = {}

    def setParentItem(self, parent):
        self.trace.append("splash.setParentItem")
        if self.parent_error is not None:
            raise self.parent_error
        self.parent = parent

    def setProperty(self, name, value):
        self.trace.append(f"splash.setProperty:{name}")
        self.properties[name] = value


class _FakeEngine:
    def __init__(self, trace=None):
        self.trace = trace if trace is not None else []

    def rootContext(self):
        self.trace.append("engine.rootContext")
        return object()


class _FakeComponent:
    def __init__(
        self,
        splash=_DEFAULT_SPLASH,
        errors=(),
        trace=None,
        begin_error=None,
    ):
        self.trace = trace if trace is not None else []
        self.splash = _FakeSplash(self.trace) if splash is _DEFAULT_SPLASH else splash
        self._errors = [_FakeError(text) for text in errors]
        self.begin_error = begin_error
        self.begin_calls = 0
        self.complete_calls = 0

    def isError(self):
        return bool(self._errors)

    def errors(self):
        return self._errors

    def beginCreate(self, context):
        self.trace.append("component.beginCreate")
        self.begin_calls += 1
        if self.begin_error is not None:
            raise self.begin_error
        return self.splash

    def completeCreate(self):
        self.trace.append("component.completeCreate")
        self.complete_calls += 1


class _FakeWindow:
    def __init__(self, trace=None, failures=None):
        self.trace = trace if trace is not None else []
        self.failures = failures or {}
        self.content = object()
        self.properties = {}

    def _fail(self, stage):
        error = self.failures.get(stage)
        if error is not None:
            raise error

    def contentItem(self):
        self.trace.append("window.contentItem")
        self._fail("content")
        return self.content

    def width(self):
        self.trace.append("window.width")
        return 1111

    def height(self):
        self.trace.append("window.height")
        return 777

    def setProperty(self, name, value):
        self.trace.append(f"window.setProperty:{name}")
        self._fail("publish")
        self.properties[name] = value


class _RecordingBuilder(SimpleNamespace):
    def __setattr__(self, name, value):
        trace = getattr(self, "_trace", None)
        if trace is not None and name in {"_splash_instance", "_splash_component"}:
            trace.append(f"builder.{name}")
        super().__setattr__(name, value)


def _new_builder(trace=None, **overrides):
    resolve_calls = []

    def resolve_icon(name):
        resolve_calls.append(name)
        return "qrc" + name if name.startswith(":/") else name

    values = {
        "_splash_enabled": True,
        "_window": _FakeWindow(trace),
        "_splash_icon": ":/icons/splash.svg",
        "_icon": "fallback-icon",
        "_splash_title": 'Title "quoted" {brace}\nline',
        "_title": "Fallback title",
        "_splash_subtitle": "Sub $ value",
        "_resolve_icon_path": resolve_icon,
        "_engine": _FakeEngine(trace),
        "_splash_instance": None,
        "_splash_component": None,
    }
    values.update(overrides)
    builder = _RecordingBuilder(**values)
    builder._resolve_calls = resolve_calls
    builder._trace = trace
    return builder


def _install_loader(monkeypatch, component):
    from prismqml.python.window import _splash_builder

    monkeypatch.setattr(
        _splash_builder,
        "_load_splash_component",
        lambda builder, profile: component,
    )


@pytest.mark.parametrize(
    "builder",
    [
        SimpleNamespace(_splash_enabled=False),
        SimpleNamespace(_splash_enabled=True, _window=None),
    ],
)
def test_create_splash_guards_before_setup(monkeypatch, builder):
    from prismqml.python.window import _splash_builder

    setup_calls = []
    monkeypatch.setattr(
        _splash_builder, "_make_splash_profile", lambda: setup_calls.append("profile")
    )
    monkeypatch.setattr(
        _splash_builder,
        "_prepare_splash_profile",
        lambda *_args: setup_calls.append("prepare"),
    )
    _splash_builder.create_splash(builder)
    assert setup_calls == []


def test_load_splash_component_uses_public_component_file(monkeypatch):
    from prismqml.python.core import utils
    from prismqml.python.window import _splash_builder

    captured = {}

    class CapturingComponent:
        def __init__(self, engine, url):
            captured["engine"] = engine
            captured["url"] = url.toLocalFile()

        def isError(self):
            return False

    monkeypatch.setattr(utils, "qml_path", lambda: Path("D:/Fixed/Qml"))
    monkeypatch.setattr(_splash_builder, "QQmlComponent", CapturingComponent)
    builder = _new_builder()
    assert _splash_builder._load_splash_component(builder, lambda _label: None) is not None
    actual_url = captured["url"].replace("\\", "/")
    if actual_url.startswith("/D:/"):
        actual_url = actual_url[1:]
    assert captured["engine"] is builder._engine
    assert actual_url == "D:/Fixed/Qml/controls/feedback/SplashScreen/SplashScreen.qml"


def test_create_splash_injects_initial_properties_before_complete(monkeypatch):
    from prismqml.python.window import _splash_builder

    trace = []
    component = _FakeComponent(trace=trace)
    _install_loader(monkeypatch, component)
    builder = _new_builder(trace)
    _splash_builder.create_splash(builder)

    assert trace.index("component.beginCreate") < trace.index(
        "splash.setProperty:iconSource"
    )
    assert trace.index("splash.setProperty:subtitle") < trace.index(
        "component.completeCreate"
    )
    assert component.begin_calls == 1
    assert component.complete_calls == 1
    assert component.splash.properties == {
        "iconSource": "qrc:/icons/splash.svg",
        "title": 'Title "quoted" {brace}\nline',
        "subtitle": "Sub $ value",
        "width": 1111,
        "height": 777,
    }
    assert builder._splash_instance is component.splash
    assert builder._splash_component is component


@pytest.mark.parametrize(
    ("overrides", "expected_values", "expected_resolves"),
    [
        (
            {"_splash_icon": "", "_icon": ":/fallback.svg", "_splash_title": ""},
            ("qrc:/fallback.svg", "Fallback title", "Sub $ value"),
            [":/fallback.svg"],
        ),
        (
            {
                "_splash_icon": "",
                "_icon": "",
                "_splash_title": "",
                "_title": "",
                "_splash_subtitle": "",
            },
            ("", "", ""),
            [],
        ),
    ],
)
def test_create_splash_resolves_fallback_values(
    monkeypatch, overrides, expected_values, expected_resolves
):
    from prismqml.python.window import _splash_builder

    _install_loader(monkeypatch, _FakeComponent())
    builder = _new_builder(**overrides)
    _splash_builder.create_splash(builder)

    assert tuple(
        builder._splash_instance.properties[name]
        for name in ("iconSource", "title", "subtitle")
    ) == expected_values
    assert builder._resolve_calls == expected_resolves


@pytest.mark.parametrize(
    ("component", "expected_warning"),
    [
        (None, None),
        (
            _FakeComponent(splash=None),
            "[Splash] beginCreate() 返回 None,跳过启动画面",
        ),
    ],
)
def test_create_splash_rejects_invalid_component_results(
    monkeypatch, component, expected_warning
):
    from prismqml.python.window import _splash_builder

    warnings = []
    monkeypatch.setattr(_splash_builder, "warning", warnings.append)
    if component is None:
        monkeypatch.setattr(
            _splash_builder,
            "_load_splash_component",
            lambda builder, profile: None,
        )
    else:
        _install_loader(monkeypatch, component)
    builder = _new_builder()
    _splash_builder.create_splash(builder)

    assert warnings == ([] if expected_warning is None else [expected_warning])
    assert builder._splash_instance is None
    assert builder._splash_component is None


def test_create_splash_mount_and_publish_order(monkeypatch):
    from prismqml.python.window import _splash_builder

    trace = []
    splash = _FakeSplash(trace)
    component = _FakeComponent(splash=splash, trace=trace)
    _install_loader(monkeypatch, component)
    builder = _new_builder(trace)
    _splash_builder.create_splash(builder)

    assert trace.index("component.beginCreate") < trace.index("component.completeCreate")
    assert trace.index("component.completeCreate") < trace.index("window.contentItem")
    assert splash.parent is builder._window.content
    assert splash.properties["width"] == 1111
    assert splash.properties["height"] == 777
    assert builder._window.properties["_splashInstance"] is splash


def test_create_splash_mount_failure_is_nonfatal_and_keeps_old_refs(monkeypatch):
    from prismqml.python.window import _splash_builder

    old_instance, old_component = object(), object()
    window = _FakeWindow(failures={"content": RuntimeError("deleted window")})
    _install_loader(monkeypatch, _FakeComponent())
    messages = []
    monkeypatch.setattr(_splash_builder, "exception", messages.append)
    builder = _new_builder(
        _window=window,
        _splash_instance=old_instance,
        _splash_component=old_component,
    )

    _splash_builder.create_splash(builder)

    assert messages == [
        "[Splash] 创建启动画面失败(不影响启动): RuntimeError: deleted window"
    ]
    assert builder._splash_instance is old_instance
    assert builder._splash_component is old_component
    assert window.properties == {}


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("stage", ["create", "mount"])
def test_create_splash_late_process_control_propagates(
    monkeypatch, stage, error_type
):
    from prismqml.python.window import _splash_builder

    error = error_type(f"stop at {stage}")
    splash = _FakeSplash(parent_error=error if stage == "mount" else None)
    component = _FakeComponent(
        splash=splash,
        begin_error=error if stage == "create" else None,
    )
    _install_loader(monkeypatch, component)
    builder = _new_builder()

    with pytest.raises(error_type, match=f"stop at {stage}"):
        _splash_builder.create_splash(builder)


def test_create_splash_profile_uses_shared_elapsed_time(monkeypatch):
    from prismqml.python.window import _splash_builder

    times = iter((1.0, 2.0, 4.0, 7.0, 11.0, 16.0))
    messages = []
    monkeypatch.setattr(_splash_builder.time, "perf_counter", lambda: next(times))

    def record_profile(message):
        if message.startswith("[启动剖析]"):
            messages.append(message)

    monkeypatch.setattr(_splash_builder, "debug", record_profile)
    _install_loader(monkeypatch, _FakeComponent())

    _splash_builder.create_splash(_new_builder())

    assert [message.split(" PrismQML._create_splash ", 1)[1].split(":", 1)[0] for message in messages] == [
        "导入/准备",
        "component.beginCreate(public)",
        "component.completeCreate(public)",
        "挂载到窗口",
    ]


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_create_splash_process_control_propagates(monkeypatch, error_type):
    from prismqml.python.window import _splash_builder

    def stop_creation():
        raise error_type("stop")

    monkeypatch.setattr(_splash_builder.time, "perf_counter", stop_creation)
    builder = SimpleNamespace(_splash_enabled=True, _window=object())
    with pytest.raises(error_type, match="stop"):
        _splash_builder.create_splash(builder)
