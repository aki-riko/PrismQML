# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Splash builder boundary regressions. 启动画面构建边界回归。"""

from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest


_DEFAULT_SPLASH = object()
_MOUNT_TRACE = [
    "file.load",
    "component.create",
    "profile.create",
    "window.contentItem",
    "splash.setParentItem",
    "window.width",
    "splash.setProperty:width",
    "window.height",
    "splash.setProperty:height",
    "window.setProperty:_splashInstance",
    "profile.mount",
    "builder._splash_instance",
    "builder._splash_component",
    "debug",
]


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


class _FakeComponent:
    def __init__(
        self,
        splash=_DEFAULT_SPLASH,
        errors=(),
        trace=None,
        create_error=None,
    ):
        self.trace = trace if trace is not None else []
        self.splash = _FakeSplash(self.trace) if splash is _DEFAULT_SPLASH else splash
        self._errors = [_FakeError(text) for text in errors]
        self.create_error = create_error
        self.create_calls = 0
        self.inline_data = None
        self.inline_url = None

    def isError(self):
        return bool(self._errors)

    def errors(self):
        return self._errors

    def create(self):
        self.trace.append("component.create")
        self.create_calls += 1
        if self.create_error is not None:
            raise self.create_error
        return self.splash

    def setData(self, data, url):
        self.trace.append("component.setData")
        self.inline_data = data
        self.inline_url = url


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
    from prismqml.python.window._window_builder import WindowBuilderMixin

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
        "_escape_qml": WindowBuilderMixin._escape_qml,
        "_resolve_icon_path": resolve_icon,
        "_engine": object(),
        "_splash_instance": None,
        "_splash_component": None,
    }
    values.update(overrides)
    builder = _RecordingBuilder(**values)
    builder._resolve_calls = resolve_calls
    builder._trace = trace
    return builder


def _install_file_loader(monkeypatch, component, trace=None):
    from prismqml.python.core import utils
    from prismqml.python.window import _splash_builder

    captured = {}

    def load(builder, splash_qml, profile, verbose, profile_values):
        if trace is not None:
            trace.append("file.load")
        captured.update(
            qml=splash_qml,
            profile=profile,
            verbose=verbose,
            profile_values=profile_values,
        )
        return component

    monkeypatch.setattr(utils, "qml_path", lambda: Path("D:/Fixed/Qml"))
    monkeypatch.setattr(_splash_builder, "_load_splash_file_component", load)
    return captured


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
        "_prepare_splash_qml",
        lambda *_args: setup_calls.append("prepare"),
    )
    _splash_builder.create_splash(builder)
    assert setup_calls == []


def test_create_splash_fixed_qml_bytes_and_file_fast_path(monkeypatch):
    from prismqml.python.window import _splash_builder

    component, inline_calls = _FakeComponent(), []
    captured = _install_file_loader(monkeypatch, component)
    monkeypatch.setenv("PRISMQML_STARTUP_PROFILE_VERBOSE", "YES")

    def record_inline(*args):
        inline_calls.append(args)
        return _FakeComponent()

    monkeypatch.setattr(_splash_builder, "QQmlComponent", record_inline)
    builder = _new_builder()
    _splash_builder.create_splash(builder)

    qml_bytes = captured["qml"].encode("utf-8")
    assert len(qml_bytes) == 3455
    assert sha256(qml_bytes).hexdigest().upper() == (
        "2FB0C01D9B0E69109BCAADD7F12F55D03F3D7B3964190D7EF53209E318BE3661"
    )
    assert captured["qml"].count("\n") == 126
    assert captured["profile_values"] == (
        "qrc:/icons/splash.svg",
        'Title "quoted" {brace}\nline',
        "Sub $ value",
    )
    assert captured["verbose"] is True
    assert builder._resolve_calls == [":/icons/splash.svg"]
    assert inline_calls == []
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

    captured = _install_file_loader(monkeypatch, _FakeComponent())
    builder = _new_builder(**overrides)
    _splash_builder.create_splash(builder)

    assert captured["profile_values"] == expected_values
    assert builder._resolve_calls == expected_resolves


def test_create_splash_inline_fallback_uses_exact_source(monkeypatch):
    from prismqml.python.window import _splash_builder

    component = _FakeComponent()
    captured = _install_file_loader(monkeypatch, None)
    created_with = []
    profile_messages = []

    def make_component(engine):
        created_with.append(engine)
        return component

    monkeypatch.setattr(_splash_builder, "QQmlComponent", make_component)
    monkeypatch.setattr(_splash_builder, "info", profile_messages.append)
    builder = _new_builder()
    _splash_builder.create_splash(builder)

    assert created_with == [builder._engine]
    assert component.inline_data == captured["qml"].encode("utf-8")
    assert component.inline_url.toString() == "inline-splash"
    assert any("component.setData fallback" in msg for msg in profile_messages)
    assert any("component.create(inline)" in msg for msg in profile_messages)


@pytest.mark.parametrize(
    ("case", "expected_warning", "expected_create_calls"),
    [
        ("error", "[Splash] 组件加载失败: ['broken qml']", 0),
        ("none", "[Splash] create() 返回 None,跳过启动画面", 1),
    ],
)
def test_create_splash_rejects_invalid_component_results(
    monkeypatch, case, expected_warning, expected_create_calls
):
    from prismqml.python.window import _splash_builder

    component = (
        _FakeComponent(errors=("broken qml",))
        if case == "error"
        else _FakeComponent(splash=None)
    )
    _install_file_loader(monkeypatch, component)
    warnings = []
    monkeypatch.setattr(_splash_builder, "warning", warnings.append)
    builder = _new_builder()
    _splash_builder.create_splash(builder)

    assert warnings == [expected_warning]
    assert component.create_calls == expected_create_calls
    assert builder._splash_instance is None
    assert builder._splash_component is None
    assert builder._window.properties == {}


def test_create_splash_mount_and_publish_order(monkeypatch):
    from prismqml.python.window import _splash_builder

    trace = []
    splash = _FakeSplash(trace)
    component = _FakeComponent(splash=splash, trace=trace)
    _install_file_loader(monkeypatch, component, trace)

    def record_profile(message):
        if "component.create(" in message:
            trace.append("profile.create")
        elif "挂载到窗口:" in message:
            trace.append("profile.mount")

    monkeypatch.setattr(_splash_builder, "info", record_profile)
    monkeypatch.setattr(_splash_builder, "debug", lambda _msg: trace.append("debug"))
    builder = _new_builder(trace)
    _splash_builder.create_splash(builder)

    assert trace == _MOUNT_TRACE
    assert splash.parent is builder._window.content
    assert splash.properties == {"width": 1111, "height": 777}
    assert builder._window.properties["_splashInstance"] is splash
    assert builder._splash_instance is splash
    assert builder._splash_component is component


def test_create_splash_mount_failure_is_nonfatal_and_keeps_old_refs(monkeypatch):
    from prismqml.python.window import _splash_builder

    old_instance, old_component = object(), object()
    window = _FakeWindow(failures={"content": RuntimeError("deleted window")})
    _install_file_loader(monkeypatch, _FakeComponent())
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
        create_error=error if stage == "create" else None,
    )
    _install_file_loader(monkeypatch, component)
    builder = _new_builder()

    with pytest.raises(error_type, match=f"stop at {stage}"):
        _splash_builder.create_splash(builder)


def test_create_splash_profile_uses_shared_elapsed_time(monkeypatch):
    from prismqml.python.window import _splash_builder

    times = iter((1.0, 2.0, 4.0, 7.0, 11.0))
    messages = []
    monkeypatch.setattr(_splash_builder.time, "perf_counter", lambda: next(times))
    monkeypatch.setattr(_splash_builder, "info", messages.append)
    _install_file_loader(monkeypatch, _FakeComponent())

    _splash_builder.create_splash(_new_builder())

    assert messages == [
        "[启动剖析] PrismQML._create_splash 导入/准备: +1000ms / total 1000ms",
        "[启动剖析] PrismQML._create_splash 拼接 Splash QML: +2000ms / total 3000ms",
        "[启动剖析] PrismQML._create_splash component.create(file): +3000ms / total 6000ms",
        "[启动剖析] PrismQML._create_splash 挂载到窗口: +4000ms / total 10000ms",
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


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_splash_file_component_process_control_propagates(error_type):
    from prismqml.python.window import _splash_builder

    def stop_file_load(_source):
        raise error_type("stop")

    builder = SimpleNamespace(_write_generated_splash_qml=stop_file_load)
    with pytest.raises(error_type, match="stop"):
        _splash_builder._load_splash_file_component(
            builder,
            "",
            lambda _label: None,
            False,
            ("", "", ""),
        )
