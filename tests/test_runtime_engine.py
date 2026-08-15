# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Runtime QML engine composition contracts. QML 引擎运行时装配合同。"""

from types import SimpleNamespace

import pytest

import prismqml.python.core.incubation as incubation
import prismqml.python.runtime as runtime
import prismqml.python.runtime.engine as runtime_engine


def test_get_or_create_qml_engine_reuses_published_engine(monkeypatch):
    engine = object()
    calls = []
    manager = SimpleNamespace(
        get_engine=lambda: calls.append("get") or engine,
        set_engine=lambda _engine: pytest.fail("must not republish"),
    )
    monkeypatch.setattr(runtime_engine, "EngineManager", manager)
    monkeypatch.setattr(
        runtime_engine,
        "QQmlApplicationEngine",
        lambda: pytest.fail("must not create"),
    )

    assert runtime_engine.get_or_create_qml_engine() is engine
    assert calls == ["get"]


def test_engine_lifecycle_ports_delegate_to_engine_manager(monkeypatch):
    engine = object()
    calls = []
    manager = SimpleNamespace(
        _engine=engine,
        _release_engine_bindings=lambda value, include_lazy=True: calls.append(
            ("release", value, include_lazy)
        ),
        reset=lambda: calls.append("reset"),
    )
    monkeypatch.setattr(runtime_engine, "EngineManager", manager)

    assert runtime_engine.is_published_qml_engine(engine) is True
    assert runtime_engine.is_published_qml_engine(object()) is False
    runtime_engine.release_qml_engine_bindings(engine, include_lazy=False)
    runtime_engine.reset_qml_engine()

    assert calls == [("release", engine, False), "reset"]


def test_engine_access_ports_delegate_to_engine_manager(monkeypatch):
    engine = object()
    binding = object()
    calls = []
    manager = SimpleNamespace(
        get_engine=lambda: calls.append("get") or engine,
        register_engine_binding=lambda value, item: calls.append(
            ("register", value, item)
        ),
    )
    monkeypatch.setattr(runtime_engine, "EngineManager", manager)

    assert runtime_engine.get_published_qml_engine() is engine
    runtime_engine.register_qml_engine_binding(engine, binding)

    assert calls == ["get", ("register", engine, binding)]


def test_get_or_create_qml_engine_creates_and_publishes_missing_engine(
    monkeypatch,
):
    engine = object()
    calls = []

    def get_engine():
        calls.append("get")
        raise RuntimeError("missing")

    manager = SimpleNamespace(
        get_engine=get_engine,
        set_engine=lambda value: calls.append(("publish", value)),
    )
    monkeypatch.setattr(runtime_engine, "EngineManager", manager)
    monkeypatch.setattr(
        runtime_engine,
        "QQmlApplicationEngine",
        lambda: calls.append("create") or engine,
    )

    assert runtime_engine.get_or_create_qml_engine() is engine
    assert calls == ["get", "create", ("publish", engine)]


@pytest.mark.parametrize("error_type", [ValueError, KeyboardInterrupt, SystemExit])
def test_get_or_create_qml_engine_propagates_non_runtime_errors(
    monkeypatch, error_type
):
    failure = error_type("stop")
    manager = SimpleNamespace(get_engine=lambda: (_ for _ in ()).throw(failure))
    monkeypatch.setattr(runtime_engine, "EngineManager", manager)
    monkeypatch.setattr(
        runtime_engine,
        "QQmlApplicationEngine",
        lambda: pytest.fail("must not create"),
    )

    with pytest.raises(error_type) as caught:
        runtime_engine.get_or_create_qml_engine()

    assert caught.value is failure


def test_configure_application_engine_preserves_registration_order(monkeypatch):
    engine = object()
    calls = []
    monkeypatch.setattr(
        incubation,
        "install_default_incubation_controller",
        lambda value: calls.append(("incubation", value)),
    )
    monkeypatch.setattr(
        runtime,
        "register_types",
        lambda value: calls.append(("register", value)),
    )

    runtime_engine.configure_application_engine(engine)

    assert calls == [("incubation", engine), ("register", engine)]


@pytest.mark.parametrize("stage", ["incubation", "register"])
@pytest.mark.parametrize("error_type", [RuntimeError, KeyboardInterrupt, SystemExit])
def test_configure_application_engine_propagates_failures(
    monkeypatch, stage, error_type
):
    engine = object()
    failure = error_type("stop")
    calls = []

    def invoke(label, value):
        calls.append((label, value))
        if stage == label:
            raise failure

    monkeypatch.setattr(
        incubation,
        "install_default_incubation_controller",
        lambda value: invoke("incubation", value),
    )
    monkeypatch.setattr(
        runtime, "register_types", lambda value: invoke("register", value)
    )

    with pytest.raises(error_type) as caught:
        runtime_engine.configure_application_engine(engine)

    assert caught.value is failure
    expected = [("incubation", engine)]
    if stage == "register":
        expected.append(("register", engine))
    assert calls == expected
