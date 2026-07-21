# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Window root setup regressions. 窗口根对象装配回归。"""

from types import SimpleNamespace

import pytest


class _RootEngine:
    def __init__(self, calls, roots):
        self._calls = calls
        self._roots = roots

    def loadData(self, source):
        self._calls.append(("loadData", source))

    def rootObjects(self):
        self._calls.append("rootObjects")
        return self._roots


class _ForbiddenRootEngine:
    @staticmethod
    def loadData(_source):
        pytest.fail("file root must skip inline load")

    @staticmethod
    def rootObjects():
        pytest.fail("file root must skip rootObjects")


class _RootBuilder:
    def __init__(self, calls, static_root, file_root, engine):
        self._calls = calls
        self._static_root = static_root
        self._file_root = file_root
        self._engine = engine

    def _load_static_window_boundary(
        self, qml_dir, component, icon, mica, profile, verbose
    ):
        self._calls.append(
            ("static", qml_dir, component, icon, mica, profile, verbose)
        )
        return self._static_root

    def _load_generated_window_boundary(self, source, component, profile, verbose):
        self._calls.append(("file", source, component, profile, verbose))
        return self._file_root


class _PendingBuilder:
    def __init__(self, pending_props, pending_calls):
        self._title = "Title"
        self._icon_colored = False
        self._pending_props = pending_props
        self._pending_calls = pending_calls
        self.calls = []

    def _apply_pending_state(self):
        self.calls.append(
            ("apply", dict(self._pending_props), list(self._pending_calls))
        )


class _FinishScenario:
    def __init__(self):
        self.calls = []
        self.root = object()

    def load(
        self, builder, qml_dir, source, component, icon, mica, profile, verbose
    ):
        self.calls.append(
            (
                "load",
                builder,
                qml_dir,
                source,
                component,
                icon,
                mica,
                profile,
                verbose,
            )
        )
        return self.root

    def install(self, builder, root, profile):
        self.calls.append(("install", builder, root, profile))

    def apply(self, builder, icon, mica, profile):
        self.calls.append(("pending", builder, icon, mica, profile))

    def finalize(self, builder, profile):
        self.calls.append(("splash", builder, profile))

    def patch(self, monkeypatch, module):
        monkeypatch.setattr(module, "load_window_root", self.load)
        monkeypatch.setattr(module, "install_window_root", self.install)
        monkeypatch.setattr(module, "apply_window_pending_state", self.apply)
        monkeypatch.setattr(module, "finalize_window_startup", self.finalize)


def test_window_root_loader_prefers_static_root():
    from prismqml.python.window import _window_root_setup as setup

    calls = []
    root = object()
    profile = object()
    builder = _RootBuilder(calls, root, object(), _ForbiddenRootEngine())

    result = setup.load_window_root(
        builder,
        "qml-dir",
        "source",
        "Component",
        "qrc:/icon.svg",
        True,
        profile,
        True,
    )

    assert result is root
    assert calls == [
        (
            "static",
            "qml-dir",
            "Component",
            "qrc:/icon.svg",
            True,
            profile,
            True,
        )
    ]


def test_window_root_loader_uses_file_root_after_static_failure():
    from prismqml.python.window import _window_root_setup as setup

    calls = []
    root = object()
    profile = object()
    builder = _RootBuilder(calls, None, root, _ForbiddenRootEngine())

    result = setup.load_window_root(
        builder,
        "qml-dir",
        "source",
        "Component",
        "qrc:/icon.svg",
        False,
        profile,
        True,
    )

    assert result is root
    assert calls == [
        (
            "static",
            "qml-dir",
            "Component",
            "qrc:/icon.svg",
            False,
            profile,
            True,
        ),
        ("file", "source", "Component", profile, True),
    ]


def test_window_root_loader_uses_inline_last_root():
    from prismqml.python.window import _window_root_setup as setup

    calls = []
    roots = [object(), object()]
    profile = lambda label: calls.append(("profile", label))
    builder = _RootBuilder(calls, None, None, _RootEngine(calls, roots))

    result = setup.load_window_root(
        builder,
        "qml-dir",
        "源码",
        "Component",
        "qrc:/icon.svg",
        False,
        profile,
        False,
    )

    assert result is roots[-1]
    assert calls == [
        (
            "static",
            "qml-dir",
            "Component",
            "qrc:/icon.svg",
            False,
            profile,
            False,
        ),
        ("file", "源码", "Component", profile, False),
        ("loadData", "源码".encode("utf-8")),
        ("profile", "engine.loadData fallback"),
        "rootObjects",
        "rootObjects",
    ]


def test_window_root_loader_rejects_missing_root():
    from prismqml.python.window import _window_root_setup as setup

    calls = []
    profile = lambda label: calls.append(("profile", label))
    builder = _RootBuilder(calls, None, None, _RootEngine(calls, []))

    with pytest.raises(RuntimeError, match="^Failed to create window$"):
        setup.load_window_root(
            builder,
            "qml-dir",
            "source",
            "Component",
            "qrc:/icon.svg",
            False,
            profile,
            False,
        )

    assert calls == [
        (
            "static",
            "qml-dir",
            "Component",
            "qrc:/icon.svg",
            False,
            profile,
            False,
        ),
        ("file", "source", "Component", profile, False),
        ("loadData", b"source"),
        ("profile", "engine.loadData fallback"),
        "rootObjects",
    ]


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_window_root_loader_process_control_propagates(error_type):
    from prismqml.python.window import _window_root_setup as setup

    def stop_file_load(*_args):
        raise error_type("stop")

    engine = _ForbiddenRootEngine()
    builder = SimpleNamespace(
        _load_static_window_boundary=stop_file_load,
        _engine=engine,
    )
    with pytest.raises(error_type, match="stop"):
        setup.load_window_root(
            builder,
            "qml-dir",
            "source",
            "Component",
            "qrc:/icon.svg",
            False,
            object(),
            False,
        )


def test_install_window_root_preserves_publish_find_connect_order():
    from prismqml.python.window import _window_root_setup as setup

    calls = []
    root = object()
    builder = SimpleNamespace(_window=None)
    builder._find_content_area = lambda: calls.append(("find", builder._window))
    builder._connect_signals = lambda: calls.append(("connect", builder._window))
    profile = lambda label: calls.append(("profile", label, builder._window))

    setup.install_window_root(builder, root, profile)

    assert calls == [
        ("profile", "获取 rootObject", root),
        ("find", root),
        ("profile", "查找 content area", root),
        ("connect", root),
        ("profile", "连接 QML 信号", root),
    ]


def test_window_pending_state_logs_residual_before_apply(monkeypatch):
    from prismqml.python.window import _window_root_setup as setup

    pending_props = {
        "windowTitle": "Title",
        "windowIcon": ":/icons/app.svg",
        "windowIconColored": False,
        "micaEnabled": False,
        "extra": 7,
    }
    builder = _PendingBuilder(pending_props, [("navigate", 1)])
    monkeypatch.setattr(
        setup,
        "debug",
        lambda message, tag=None: builder.calls.append(("debug", message, tag)),
    )
    profile = lambda label: builder.calls.append(("profile", label))

    setup.apply_window_pending_state(builder, "qrc:/icons/app.svg", False, profile)

    assert builder.calls == [
        (
            "debug",
            "[启动剖析] PrismQML._create_window pending state: "
            "props=['extra'], calls=1",
            "WindowBuilder",
        ),
        ("apply", {"extra": 7}, [("navigate", 1)]),
        ("profile", "应用 pending state"),
    ]


@pytest.mark.parametrize(
    ("pending_icon", "rendered_icon"),
    [(":/icons/app.svg", "qrc:/icons/app.svg"), ("qrc:/icons/app.svg", ":/icons/app.svg")],
)
def test_deduplicated_pending_state_skips_log_but_still_applies(
    monkeypatch, pending_icon, rendered_icon
):
    from prismqml.python.window import _window_root_setup as setup

    builder = _PendingBuilder({"windowIcon": pending_icon}, [])
    monkeypatch.setattr(
        setup,
        "debug",
        lambda _message, tag=None: pytest.fail(
            f"deduplicated state must not log with tag {tag}"
        ),
    )
    profile = lambda label: builder.calls.append(("profile", label))

    setup.apply_window_pending_state(builder, rendered_icon, False, profile)

    assert builder.calls == [
        ("apply", {}, []),
        ("profile", "应用 pending state"),
    ]


@pytest.mark.parametrize("error_type", [RuntimeError, KeyboardInterrupt, SystemExit])
def test_pending_apply_failure_propagates(monkeypatch, error_type):
    from prismqml.python.window import _window_root_setup as setup

    def stop_apply():
        raise error_type("stop")

    builder = SimpleNamespace(
        _title="Title",
        _icon_colored=False,
        _pending_props={},
        _pending_calls=[],
        _apply_pending_state=stop_apply,
    )
    monkeypatch.setattr(setup, "debug", lambda _message, tag=None: None)
    with pytest.raises(error_type, match="stop"):
        setup.apply_window_pending_state(
            builder, "qrc:/icon.svg", False, lambda _label: pytest.fail("stop")
        )


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_window_splash_process_control_propagates(error_type):
    from prismqml.python.window import _window_root_setup as setup

    def stop_splash():
        raise error_type("stop")

    builder = SimpleNamespace(_create_splash=stop_splash)
    with pytest.raises(error_type, match="stop"):
        setup.finalize_window_startup(
            builder, lambda _label: pytest.fail("must fail fast")
        )


def test_finish_window_startup_preserves_root_pending_splash_order(monkeypatch):
    from prismqml.python.window import _window_root_setup as setup

    scenario = _FinishScenario()
    scenario.patch(monkeypatch, setup)
    builder = object()
    profile = object()
    rendered = ("qml-dir", "source", "Component", "qrc:/icon.svg", True)

    setup.finish_window_startup(builder, rendered, profile, False)

    assert scenario.calls == [
        (
            "load",
            builder,
            "qml-dir",
            "source",
            "Component",
            "qrc:/icon.svg",
            True,
            profile,
            False,
        ),
        ("install", builder, scenario.root, profile),
        ("pending", builder, "qrc:/icon.svg", True, profile),
        ("splash", builder, profile),
    ]
