# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Window startup orchestration regressions. 窗口启动编排回归。"""

from pathlib import Path
from types import SimpleNamespace

import pytest


class _FakeStandardPaths:
    class StandardLocation:
        CacheLocation = object()

    calls = []

    @classmethod
    def writableLocation(cls, location):
        cls.calls.append(location)
        return "D:/cache"


class _CreateWindowScenario:
    def __init__(self):
        self.calls = []
        self.profile = object()
        self.get_config = object()
        self.qml_dir = Path("D:/qml")
        self.icon_dir = self.qml_dir / "controls" / "icons" / "fluent"
        self.rendered = ("source", "WindowsBar", "qrc:/icon.svg", False)

    def prepare_profile(self):
        self.calls.append("profile")
        return self.profile, True

    def prepare_engine(self, builder, verbose, profile):
        self.calls.append(("engine", builder, verbose, profile))
        return self.get_config

    def resolve_paths(self, profile):
        self.calls.append(("paths", profile))
        return self.qml_dir, self.icon_dir

    def compose(self, qml_dir, icon_dir, verbose, get_config, profile):
        self.calls.append(
            ("compose", qml_dir, icon_dir, verbose, get_config, profile)
        )
        return self.rendered

    def finish(self, builder, rendered, profile, verbose):
        self.calls.append(("finish", builder, rendered, profile, verbose))

    def patch(self, monkeypatch, module):
        monkeypatch.setattr(
            module, "prepare_window_startup_profile", self.prepare_profile
        )
        monkeypatch.setattr(module, "prepare_window_engine", self.prepare_engine)
        monkeypatch.setattr(module, "resolve_window_qml_paths", self.resolve_paths)
        monkeypatch.setattr(module, "finish_window_startup", self.finish)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("", False),
        ("0", False),
        (" true ", False),
        ("1", True),
        ("TRUE", True),
        ("Yes", True),
        ("on", True),
    ],
)
def test_startup_profile_verbose_contract(monkeypatch, value, expected):
    from prismqml.python.window import _window_startup as startup

    monkeypatch.setenv("PRISMQML_STARTUP_PROFILE_VERBOSE", value)
    assert startup._startup_profile_verbose() is expected


@pytest.mark.parametrize("verbose", [False, True])
def test_prepare_window_startup_profile_preserves_order(monkeypatch, verbose):
    from prismqml.python.window import _window_startup as startup

    calls = []
    profile = object()

    def make_profile():
        calls.append("make")
        return profile

    monkeypatch.setattr(startup, "_make_window_profile", make_profile)
    monkeypatch.setattr(
        startup,
        "_startup_profile_verbose",
        lambda: calls.append("verbose") or verbose,
    )
    monkeypatch.setattr(
        startup,
        "_log_window_cache_environment",
        lambda: calls.append("cache"),
    )

    assert startup.prepare_window_startup_profile() == (profile, verbose)
    assert calls == ["make", "verbose"] + (["cache"] if verbose else [])


def test_window_profile_keeps_shared_elapsed_state(monkeypatch):
    from prismqml.python.window import _window_startup as startup

    moments = iter((10.0, 10.125, 10.5))
    records = []
    monkeypatch.setattr(startup.time, "perf_counter", lambda: next(moments))
    monkeypatch.setattr(
        startup,
        "debug",
        lambda message, tag=None: records.append((message, tag)),
    )

    profile = startup._make_window_profile()
    profile("first")
    profile("second")

    assert records == [
        (
            "[启动剖析] PrismQML._create_window first: +125ms / total 125ms",
            "WindowBuilder",
        ),
        (
            "[启动剖析] PrismQML._create_window second: +375ms / total 500ms",
            "WindowBuilder",
        ),
    ]


def test_window_cache_environment_log_preserves_inputs(monkeypatch):
    from prismqml.python.window import _window_startup as startup

    records = []
    _FakeStandardPaths.calls = []
    monkeypatch.setattr(startup, "QStandardPaths", _FakeStandardPaths)
    monkeypatch.setattr(
        startup,
        "debug",
        lambda message, tag=None: records.append((message, tag)),
    )
    monkeypatch.setenv("QML_DISK_CACHE_PATH", "D:/qml-cache")
    monkeypatch.setenv("QML_DISABLE_DISK_CACHE", "0")
    monkeypatch.setenv("QML_FORCE_DISK_CACHE", "1")

    startup._log_window_cache_environment()

    assert _FakeStandardPaths.calls == [_FakeStandardPaths.StandardLocation.CacheLocation]
    assert records == [
        (
            "[启动剖析] PrismQML QML cache env: "
            "QML_DISK_CACHE_PATH='D:/qml-cache', "
            "QML_DISABLE_DISK_CACHE='0', QML_FORCE_DISK_CACHE='1', "
            "QtCacheLocation='D:/cache'",
            "WindowBuilder",
        )
    ]


def test_resolve_window_qml_paths_preserves_dynamic_boundary(monkeypatch):
    from prismqml.python.core import utils
    from prismqml.python.window import _window_startup as startup

    calls = []
    qml_dir = Path("D:/qml-root")
    monkeypatch.setattr(utils, "qml_path", lambda: calls.append("qml_path") or qml_dir)

    result = startup.resolve_window_qml_paths(
        lambda label: calls.append(("profile", label))
    )

    assert result == (qml_dir, qml_dir / "controls" / "icons" / "fluent")
    assert calls == ["qml_path", ("profile", "解析 QML 路径")]


def test_create_window_keeps_five_phase_orchestration(monkeypatch):
    from prismqml.python.window import _window_builder as module

    scenario = _CreateWindowScenario()
    scenario.patch(monkeypatch, module)
    builder = SimpleNamespace(_compose_window_qml=scenario.compose)

    module.WindowBuilderMixin._create_window(builder)

    assert scenario.calls == [
        "profile",
        ("engine", builder, True, scenario.profile),
        ("paths", scenario.profile),
        (
            "compose",
            scenario.qml_dir,
            scenario.icon_dir,
            True,
            scenario.get_config,
            scenario.profile,
        ),
        ("finish", builder, scenario.rendered, scenario.profile, True),
    ]
