# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""DPI 启动输入、配置候选与 Windows 系统 DPI 合同回归测试。"""

import json
import os
import re
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from prismqml.python.config.app_config import AppConfig
import prismqml.python.config.dpi as dpi_module


_QT_DPI_ENVIRONMENT = (
    "QT_AUTO_SCREEN_SCALE_FACTOR",
    "QT_SCREEN_SCALE_FACTORS",
    "QT_ENABLE_HIGHDPI_SCALING",
    "QT_SCALE_FACTOR",
)


def _dirty_qt_dpi_environment(monkeypatch):
    for name in _QT_DPI_ENVIRONMENT:
        monkeypatch.setenv(name, "dirty")


def _assert_follow_system_environment():
    assert os.environ["QT_ENABLE_HIGHDPI_SCALING"] == "1"
    assert "QT_AUTO_SCREEN_SCALE_FACTOR" not in os.environ
    assert "QT_SCREEN_SCALE_FACTORS" not in os.environ
    assert "QT_SCALE_FACTOR" not in os.environ


@pytest.mark.parametrize("scale", [0, 100, 125, 150, 175, 200])
def test_apply_dpi_scale_accepts_only_declared_values(
    tmp_path, monkeypatch, scale
):
    path = tmp_path / "app.json"
    path.write_text(json.dumps({"Window": {"DpiScale": scale}}), encoding="utf-8")
    _dirty_qt_dpi_environment(monkeypatch)
    monkeypatch.setattr(dpi_module, "getSystemDpiScale", lambda: 150)

    assert dpi_module.applyDpiScale(path) == scale

    if scale == 0:
        _assert_follow_system_environment()
    else:
        assert os.environ["QT_ENABLE_HIGHDPI_SCALING"] == "0"
        assert os.environ["QT_SCALE_FACTOR"] == str(scale / 100)
        assert "QT_AUTO_SCREEN_SCALE_FACTOR" not in os.environ
        assert "QT_SCREEN_SCALE_FACTORS" not in os.environ


@pytest.mark.parametrize(
    "payload",
    [
        '{"Window":{"DpiScale":"150"}}',
        '{"Window":{"DpiScale":[150]}}',
        '{"Window":{"DpiScale":{"value":150}}}',
        '{"Window":{"DpiScale":true}}',
        '{"Window":{"DpiScale":125.5}}',
        '{"Window":{"DpiScale":NaN}}',
        '{"Window":{"DpiScale":Infinity}}',
        '{"Window":{"DpiScale":-Infinity}}',
        '{"Window":{"DpiScale":-1}}',
        '{"Window":{"DpiScale":999}}',
        '{"Window":{"DpiScale":null}}',
        '{"Window":{}}',
        '{"Window":[]}',
        '[]',
        '{',
    ],
)
def test_apply_dpi_scale_invalid_real_json_follows_system_without_pollution(
    tmp_path, monkeypatch, payload
):
    path = tmp_path / "app.json"
    path.write_text(payload, encoding="utf-8")
    _dirty_qt_dpi_environment(monkeypatch)
    monkeypatch.setattr(dpi_module, "getSystemDpiScale", lambda: 175)

    assert dpi_module.applyDpiScale(path) == 0
    _assert_follow_system_environment()


def test_apply_dpi_scale_missing_file_follows_system(tmp_path, monkeypatch):
    _dirty_qt_dpi_environment(monkeypatch)
    monkeypatch.setattr(dpi_module, "getSystemDpiScale", lambda: 100)

    assert dpi_module.applyDpiScale(tmp_path / "missing.json") == 0
    _assert_follow_system_environment()


def test_apply_dpi_scale_rejects_valid_dpi_when_peer_window_field_is_invalid(
    tmp_path, monkeypatch
):
    path = tmp_path / "app.json"
    path.write_text(
        '{"Window":{"DpiScale":150,"WindowType":3}}', encoding="utf-8"
    )
    _dirty_qt_dpi_environment(monkeypatch)
    monkeypatch.setattr(dpi_module, "getSystemDpiScale", lambda: 125)

    assert dpi_module.applyDpiScale(path) == 0
    _assert_follow_system_environment()

    config = AppConfig()
    config.file = path
    assert config.load() is False
    assert config.dpi_scale.value == 0
    assert config.window_type.value == 1


def test_app_config_options_are_the_python_runtime_contract():
    assert AppConfig.dpi_scale.options == [0, 100, 125, 150, 175, 200]
    assert AppConfig.window_type.options == [0, 1, 2]


def test_ms_style_window_is_the_default_window_type():
    assert AppConfig.window_type.default_value == 1


def _read_cpp_int_array(symbol):
    header = (
        Path(__file__).resolve().parents[1]
        / "cpp"
        / "include"
        / "prism"
        / "ConfigContracts.h"
    ).read_text(encoding="utf-8")
    pattern = re.compile(
        rf"inline\s+constexpr\s+std::array<int,\s*(\d+)>\s+"
        rf"{re.escape(symbol)}\s*=\s*\{{(.*?)\}}\s*;",
        re.DOTALL,
    )
    matches = list(pattern.finditer(header))
    assert len(matches) == 1, f"expected one C++ array named {symbol}"
    declared_count = int(matches[0].group(1))
    body = re.sub(r"/\*.*?\*/", "", matches[0].group(2), flags=re.DOTALL)
    body = re.sub(r"//[^\r\n]*", "", body)
    tokens = [token.strip() for token in body.split(",")]
    if tokens and not tokens[-1]:
        tokens.pop()
    assert tokens and all(re.fullmatch(r"-?\d+", token) for token in tokens)
    assert len(tokens) == declared_count
    return [int(token) for token in tokens]


def test_cpp_config_options_strictly_mirror_python_runtime_contract():
    assert _read_cpp_int_array("kValidDpiScales") == AppConfig.dpi_scale.options
    assert _read_cpp_int_array("kValidWindowTypes") == AppConfig.window_type.options


def test_settings_page_maps_runtime_options_by_value_not_raw_index():
    source = (
        Path(__file__).resolve().parents[1]
        / "examples"
        / "pages"
        / "SettingsPage.qml"
    ).read_text(encoding="utf-8")
    normalized = " ".join(source.split())

    assert "ConfigManager.windowTypeOptions" in normalized
    assert "windowTypeValues.indexOf(ConfigManager.windowType)" in normalized
    assert "ConfigManager.setWindowType(windowTypeValues[idx])" in normalized
    assert "ConfigManager.dpiScaleOptions" in normalized
    assert "dpiValues.indexOf(ConfigManager.dpiScale)" in normalized
    assert "ConfigManager.setDpiScale(dpiValues[idx])" in normalized
    assert "property var dpiValues: [0, 100, 125, 150, 175, 200]" not in source


def test_app_config_invalid_choice_load_is_atomic(tmp_path):
    config = AppConfig()
    config.file = tmp_path / "app.json"
    assert config.set(config.lazy_loading, False, save=False) is True
    assert config.set(config.dpi_scale, 150, save=False) is True
    assert config.set(config.window_type, 2, save=False) is True
    config.file.write_text(
        json.dumps(
            {
                "Window": {
                    "LazyLoading": True,
                    "DpiScale": 999,
                    "WindowType": 0,
                }
            }
        ),
        encoding="utf-8",
    )
    changes = []
    lazy_updates = []
    dpi_updates = []
    window_updates = []
    config.configChanged.connect(lambda: changes.append(True))
    config.lazy_loading.valueUpdated.connect(lazy_updates.append)
    config.dpi_scale.valueUpdated.connect(dpi_updates.append)
    config.window_type.valueUpdated.connect(window_updates.append)

    assert config.load() is False
    assert config.lazy_loading.value is False
    assert config.dpi_scale.value == 150
    assert config.window_type.value == 2
    assert changes == []
    assert lazy_updates == []
    assert dpi_updates == []
    assert window_updates == []


def test_app_config_rejects_non_object_window_group_atomically(tmp_path):
    config = AppConfig()
    config.file = tmp_path / "app.json"
    assert config.set(config.dpi_scale, 150, save=False) is True
    config.file.write_text('{"Window":[]}', encoding="utf-8")
    changes = []
    dpi_updates = []
    config.configChanged.connect(lambda: changes.append(True))
    config.dpi_scale.valueUpdated.connect(dpi_updates.append)

    assert config.load() is False
    assert config.dpi_scale.value == 150
    assert changes == []
    assert dpi_updates == []


class _RegistryKey:
    def __init__(self, owner, path):
        self.owner = owner
        self.path = path

    def __enter__(self):
        self.owner.entered.append(self.path)
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.owner.exited.append(self.path)


class _FakeWinreg:
    HKEY_CURRENT_USER = object()

    def __init__(self, outcomes):
        self.outcomes = outcomes
        self.entered = []
        self.exited = []

    def OpenKey(self, _root, path):
        outcome = self.outcomes.get((path, "__open__"))
        if isinstance(outcome, BaseException):
            raise outcome
        return _RegistryKey(self, path)

    def QueryValueEx(self, key, name):
        outcome = self.outcomes[(key.path, name)]
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome, 1

    def CloseKey(self, key):
        self.exited.append(key.path)


def test_registry_query_failure_closes_handle_before_fallback(monkeypatch):
    metrics = r"Control Panel\Desktop\WindowMetrics"
    desktop = r"Control Panel\Desktop"
    fake = _FakeWinreg(
        {
            (metrics, "AppliedDPI"): OSError("query failed"),
            (desktop, "LogPixels"): 120,
        }
    )
    monkeypatch.setattr(dpi_module.sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "winreg", fake)
    monkeypatch.setattr(
        dpi_module,
        "_get_dpi_for_system_scale",
        lambda: pytest.fail("registry success must precede awareness-dependent API"),
        raising=False,
    )

    assert dpi_module.getSystemDpiScale() == 125
    assert fake.entered == [metrics, desktop]
    assert fake.exited == [metrics, desktop]


def test_registry_failures_fall_back_to_system_api(monkeypatch):
    metrics = r"Control Panel\Desktop\WindowMetrics"
    desktop = r"Control Panel\Desktop"
    fake = _FakeWinreg(
        {
            (metrics, "__open__"): FileNotFoundError("missing"),
            (desktop, "__open__"): OSError("denied"),
        }
    )
    monkeypatch.setattr(dpi_module.sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "winreg", fake)
    monkeypatch.setattr(
        dpi_module, "_get_dpi_for_system_scale", lambda: 150, raising=False
    )

    assert dpi_module.getSystemDpiScale() == 150
    assert fake.entered == []
    assert fake.exited == []


def test_all_windows_dpi_sources_failing_returns_default(monkeypatch):
    fake = _FakeWinreg(
        {
            (r"Control Panel\Desktop\WindowMetrics", "__open__"): OSError("no metrics"),
            (r"Control Panel\Desktop", "__open__"): OSError("no desktop"),
        }
    )
    monkeypatch.setattr(dpi_module.sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "winreg", fake)
    monkeypatch.setattr(
        dpi_module, "_get_dpi_for_system_scale", lambda: None, raising=False
    )

    assert dpi_module.getSystemDpiScale() == 100


class _SystemDpiCall:
    def __init__(self, outcome):
        self.outcome = outcome

    def __call__(self):
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome


@pytest.mark.parametrize(
    ("outcome", "expected"),
    [
        (96, 100),
        (144, 150),
        (0, None),
        (True, None),
        (144.0, None),
        (OSError("API failed"), None),
    ],
)
def test_get_dpi_for_system_api_contract(monkeypatch, outcome, expected):
    fake_ctypes = ModuleType("ctypes")
    fake_ctypes.windll = SimpleNamespace(
        user32=SimpleNamespace(GetDpiForSystem=_SystemDpiCall(outcome))
    )
    monkeypatch.setitem(sys.modules, "ctypes", fake_ctypes)

    assert dpi_module._get_dpi_for_system_scale() == expected


def test_get_dpi_for_system_missing_api_returns_none(monkeypatch):
    monkeypatch.setitem(sys.modules, "ctypes", ModuleType("ctypes"))

    assert dpi_module._get_dpi_for_system_scale() is None
