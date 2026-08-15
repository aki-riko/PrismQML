# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Qt application runtime composition contracts. Qt 应用运行时装配合同。"""

import sys
from types import ModuleType, SimpleNamespace

import pytest

import prismqml.python.config as config
import prismqml.python.core as core
import prismqml.python.core.input_focus_filter as input_focus_filter
import prismqml.python.core.shadow as shadow
import prismqml.python.runtime as runtime
import prismqml.python.runtime.application as runtime_application
from prismqml.python.window import app as app_module


def _install_prepare_spies(monkeypatch, calls, failure_stage=None, failure=None):
    def invoke(label, value=None):
        calls.append(label if value is None else (label, value))
        if failure_stage is not None and label == failure_stage:
            raise failure

    monkeypatch.setattr(
        runtime_application, "os", SimpleNamespace(name="nt")
    )
    monkeypatch.setattr(
        core,
        "configure_qml_environment",
        lambda value: invoke("qml", value),
    )
    monkeypatch.setattr(
        runtime_application,
        "_configure_windows_graphics_api",
        lambda: invoke("graphics"),
    )
    monkeypatch.setattr(
        runtime_application,
        "QGuiApplication",
        SimpleNamespace(
            setHighDpiScaleFactorRoundingPolicy=lambda value: invoke(
                "rounding", value
            )
        ),
    )
    monkeypatch.setattr(config, "applyDpiScale", lambda: invoke("dpi"))
    monkeypatch.setattr(
        core, "install_qt_message_handler", lambda: invoke("messages")
    )


def test_prepare_application_environment_preserves_startup_order(monkeypatch):
    calls = []
    _install_prepare_spies(monkeypatch, calls)

    runtime_application.prepare_application_environment(False)

    assert calls == [
        ("qml", False),
        "graphics",
        (
            "rounding",
            runtime_application.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough,
        ),
        "dpi",
        "messages",
    ]


def test_prepare_application_environment_keeps_non_windows_graphics_default(
    monkeypatch,
):
    calls = []
    _install_prepare_spies(monkeypatch, calls)
    monkeypatch.setattr(runtime_application, "os", SimpleNamespace(name="posix"))
    monkeypatch.setattr(
        runtime_application,
        "_configure_windows_graphics_api",
        lambda: pytest.fail("must keep the platform default"),
    )

    runtime_application.prepare_application_environment(True)

    assert calls == [
        ("qml", True),
        (
            "rounding",
            runtime_application.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough,
        ),
        "dpi",
        "messages",
    ]


def test_windows_graphics_backend_is_direct3d11(monkeypatch):
    calls = []
    direct3d11 = object()
    qt_quick = ModuleType("PySide6.QtQuick")
    qt_quick.QQuickWindow = SimpleNamespace(
        setGraphicsApi=lambda value: calls.append(value)
    )
    qt_quick.QSGRendererInterface = SimpleNamespace(
        GraphicsApi=SimpleNamespace(Direct3D11=direct3d11)
    )
    monkeypatch.setitem(sys.modules, "PySide6.QtQuick", qt_quick)

    runtime_application._configure_windows_graphics_api()

    assert calls == [direct3d11]


@pytest.mark.parametrize("stage", ["qml", "graphics", "rounding", "dpi", "messages"])
@pytest.mark.parametrize("error_type", [RuntimeError, KeyboardInterrupt, SystemExit])
def test_prepare_application_environment_propagates_stage_failures(
    monkeypatch, stage, error_type
):
    failure = error_type(stage)
    calls = []
    _install_prepare_spies(
        monkeypatch, calls, failure_stage=stage, failure=failure
    )

    with pytest.raises(error_type) as caught:
        runtime_application.prepare_application_environment(True)

    assert caught.value is failure
    labels = [call[0] if isinstance(call, tuple) else call for call in calls]
    expected = ["qml", "graphics", "rounding", "dpi", "messages"]
    assert labels == expected[: expected.index(stage) + 1]


@pytest.mark.parametrize("existing", [None, object()])
def test_create_qt_application_reports_ownership(monkeypatch, existing):
    calls = []
    application = object()

    def factory(argv):
        calls.append(argv)
        return application

    factory.instance = lambda: existing
    monkeypatch.setattr(runtime_application, "QApplication", factory)

    created, owns_application = runtime_application.create_qt_application(
        ["prism", "--flag"]
    )

    assert created is application
    assert owns_application is (existing is None)
    assert calls == [["prism", "--flag"]]


def test_application_filter_installers_delegate_to_core(monkeypatch):
    application = object()
    input_filter = object()
    calls = []
    monkeypatch.setattr(
        input_focus_filter,
        "install_input_focus_filter",
        lambda value: calls.append(("input", value)) or input_filter,
    )
    monkeypatch.setattr(
        shadow,
        "installDwmSyncFilter",
        lambda: calls.append("dwm") or True,
    )

    assert (
        runtime_application.install_application_input_filter(application)
        is input_filter
    )
    assert runtime_application.install_application_dwm_filter() is True
    assert calls == [("input", application), "dwm"]


@pytest.mark.parametrize("stage", ["input", "dwm"])
def test_app_marks_filter_rollback_before_runtime_install(monkeypatch, stage):
    application = object()
    failure = RuntimeError(stage)
    calls = []
    owner = SimpleNamespace(
        _app=None,
        _owns_app=False,
        _input_filter_started=False,
        _dwm_filter_started=False,
    )

    def invoke(label, value=None):
        calls.append(label if value is None else (label, value))
        if label == stage:
            raise failure

    monkeypatch.setattr(
        runtime,
        "create_qt_application",
        lambda argv: invoke("create", argv) or (application, True),
    )
    monkeypatch.setattr(
        runtime,
        "install_application_input_filter",
        lambda value: invoke("input", value),
    )
    monkeypatch.setattr(
        runtime,
        "install_application_dwm_filter",
        lambda: invoke("dwm"),
    )

    with pytest.raises(RuntimeError) as caught:
        app_module._create_qt_application(owner, ["prism"])

    assert caught.value is failure
    assert owner._app is application
    assert owner._owns_app is True
    assert owner._input_filter_started is True
    assert owner._dwm_filter_started is (stage == "dwm")
    expected = [("create", ["prism"]), ("input", application)]
    if stage == "dwm":
        expected.append("dwm")
    assert calls == expected
