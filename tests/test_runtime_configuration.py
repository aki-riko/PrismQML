# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Runtime configuration composition contracts. 运行时配置装配合同。"""

import json

import pytest

from prismqml.python import config
from prismqml.python.config.config_manager import ConfigManager
from prismqml.python.runtime import appearance
from prismqml.python.runtime.configuration import get_config_manager


class _ManagerProbe:
    def __init__(self):
        self.bindings = []
        self.appearancePersistenceEnabled = True

    def _bind_appearance_runtime(self, callback, *, apply_persisted=True):
        self.bindings.append((callback, apply_persisted))


class _AppearanceProbe:
    def __init__(self, failure=None):
        self.calls = []
        self.failure = failure

    def _apply_theme_from_qml(self, value):
        self.calls.append(("theme", value))

    def _apply_skin_from_qml(self, value):
        self.calls.append(("skin", value))
        if self.failure is not None:
            raise self.failure

    def _apply_accent_color(self, value):
        self.calls.append(("accent_color", value))


@pytest.fixture
def isolated_config_manager():
    previous = ConfigManager._instance
    ConfigManager._instance = None
    try:
        yield
    finally:
        ConfigManager._instance = previous


def test_get_config_manager_preserves_no_argument_call_shape(monkeypatch):
    manager = _ManagerProbe()
    calls = []

    def factory():
        calls.append(())
        return manager

    monkeypatch.setattr(config, "getConfigManager", factory)

    assert get_config_manager() is manager
    assert calls == [()]
    assert len(manager.bindings) == 1
    assert callable(manager.bindings[0][0])
    assert manager.bindings[0][1] is True


def test_get_config_manager_forwards_explicit_path(monkeypatch):
    manager = _ManagerProbe()
    calls = []

    def factory(config_path):
        calls.append(config_path)
        return manager

    monkeypatch.setattr(config, "getConfigManager", factory)

    assert get_config_manager("custom-config.json") is manager
    assert calls == ["custom-config.json"]
    assert len(manager.bindings) == 1
    assert callable(manager.bindings[0][0])
    assert manager.bindings[0][1] is True


def test_config_manager_rejects_a_second_explicit_path(
    tmp_path, isolated_config_manager
):
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"

    manager = get_config_manager(str(first_path))

    with pytest.raises(RuntimeError, match="different configuration path"):
        get_config_manager(str(second_path))

    assert manager.getConfigPath() == str(first_path.resolve())


def test_config_manager_rejects_a_second_appearance_policy(
    tmp_path, isolated_config_manager
):
    get_config_manager(str(tmp_path / "app.json"), persist_appearance=True)

    with pytest.raises(RuntimeError, match="appearance persistence policy"):
        get_config_manager(persist_appearance=False)


def test_config_manager_rejects_non_boolean_appearance_policy(
    tmp_path, isolated_config_manager
):
    with pytest.raises(TypeError, match="must be a bool or None"):
        get_config_manager(
            str(tmp_path / "app.json"), persist_appearance="false"
        )

    assert ConfigManager._instance is None


def test_runtime_binding_applies_loaded_appearance_once(
    qapp, tmp_path, monkeypatch, isolated_config_manager
):
    path = tmp_path / "app.json"
    path.write_text(
        json.dumps(
            {
                "Appearance": {
                    "Theme": "dark",
                    "Skin": "vintage_ticket",
                    "AccentColor": "#123456",
                }
            }
        ),
        encoding="utf-8",
    )
    runtime = _AppearanceProbe()
    monkeypatch.setattr(appearance, "getThemeManager", lambda: runtime)

    manager = get_config_manager(str(path))

    assert runtime.calls == [
        ("theme", "dark"),
        ("skin", "vintage_ticket"),
        ("accent_color", "#123456"),
    ]
    assert get_config_manager() is manager
    assert len(runtime.calls) == 3


@pytest.mark.parametrize("error_type", [RuntimeError, KeyboardInterrupt, SystemExit])
def test_runtime_binding_failure_is_retryable(
    qapp, tmp_path, monkeypatch, error_type, isolated_config_manager
):
    path = tmp_path / "app.json"
    failure = error_type("stop")
    failing_runtime = _AppearanceProbe(failure)
    recovered_runtime = _AppearanceProbe()
    monkeypatch.setattr(
        appearance, "getThemeManager", lambda: failing_runtime
    )

    with pytest.raises(error_type) as caught:
        get_config_manager(str(path))

    assert caught.value is failure
    manager = ConfigManager._instance
    assert manager._appearance_runtime is None
    monkeypatch.setattr(
        appearance, "getThemeManager", lambda: recovered_runtime
    )

    assert get_config_manager() is manager
    assert recovered_runtime.calls == [
        ("theme", "auto"),
        ("skin", "fluent"),
        ("accent_color", "#0e5a9c"),
    ]
