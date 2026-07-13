# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""SettingsCore 事务、扩展 hook 与 schema 边界回归。"""

import json

import pytest
from PySide6.QtCore import QObject

from prismqml.python.config.app_config import AppConfig
from prismqml.python.config.config_item import SettingEntry
from prismqml.python.config.config_manager import ConfigManager
from prismqml.python.config.settings_core import SettingsCore
import prismqml.python.config.settings_core as settings_core_module


class _FlatDictConfig(SettingsCore):
    data = SettingEntry("Data", "", {"default": True})


class _MutableSignalConfig(SettingsCore):
    items = SettingEntry("General", "Items", [])


class _SerializationConfig(SettingsCore):
    value = SettingEntry("General", "Value", "old")


class _TaggedEntry(SettingEntry):
    def __init__(self, group, name, default, *, tag, parent=None):
        super().__init__(group, name, default, parent=parent)
        self.tag = tag

    def clone(self, parent=None):
        cloned = type(self)(
            self.group,
            self.name,
            self.default_value,
            tag=self.tag,
            parent=parent,
        )
        cloned._replace_value(self.value, False)
        return cloned

    def encode(self, value):
        return {"value": value, "tag": self.tag}

    def decode(self, raw):
        if raw["tag"] != self.tag:
            raise ValueError("tag mismatch")
        return self.prepare(raw["value"])


class _TaggedConfig(SettingsCore):
    tagged = _TaggedEntry("General", "Tagged", "default", tag="blue")


class _ExplodingCopy:
    def __deepcopy__(self, _memo):
        raise RuntimeError("copy boom")


class _CopyFailingEntry(SettingEntry):
    def prepare(self, incoming):
        if incoming == "poison":
            return _ExplodingCopy()
        return super().prepare(incoming)

    def encode(self, value):
        if isinstance(value, _ExplodingCopy):
            return "encoded"
        return value

    def decode(self, raw):
        return self.prepare(raw)


class _CommitFailureConfig(SettingsCore):
    first = SettingEntry("General", "First", "old-first")
    second = _CopyFailingEntry("General", "Second", "old-second")


class _QObjectEntry(SettingEntry):
    def __init__(
        self,
        group,
        name,
        default,
        validator=None,
        *,
        restart=False,
        parent=None,
    ):
        super().__init__(
            group,
            name,
            default,
            validator,
            restart=restart,
            parent=parent,
        )
        self.setObjectName("bound-entry")
        self.helper = QObject(self)
        self.internal_updates = 0
        self.valueUpdated.connect(self._record_update)

    def _record_update(self, _value):
        self.internal_updates += 1


class _QObjectConfig(SettingsCore):
    value = _QObjectEntry("General", "Value", "default")


class _TextDecodeEntry(SettingEntry):
    def prepare(self, incoming):
        if not isinstance(incoming, str):
            raise TypeError("prepare expects external text")
        return int(incoming)

    def decode(self, raw):
        return self.prepare(raw)


def test_flat_dict_value_round_trips_by_schema_shape(tmp_path):
    path = tmp_path / "settings.json"
    writer = _FlatDictConfig()
    writer.file = path
    reader = _FlatDictConfig()
    reader.file = path

    assert writer.set(writer.data, {"saved": [1, 2]}) is True
    assert reader.load() is True
    assert reader.data.value == {"saved": [1, 2]}


def test_non_entry_shadow_does_not_revive_in_grandchild():
    class _Base(SettingsCore):
        value = SettingEntry("General", "Value", "base")

    class _Masked(_Base):
        value = None

    class _Leaf(_Masked):
        pass

    assert _Leaf.value is None
    assert dict(_Leaf()._iter_entries()) == {}


def test_custom_constructor_and_load_state_survive_instance_binding(tmp_path):
    path = tmp_path / "settings.json"
    config = _TaggedConfig()
    config.file = path

    assert config.tagged.tag == "blue"
    assert config.set(config.tagged, "saved") is True
    path.write_text(
        json.dumps(
            {"General": {"Tagged": {"value": "loaded", "tag": "blue"}}}
        ),
        encoding="utf-8",
    )
    assert config.load() is True
    assert config.tagged.value == "loaded"
    assert config.tagged.tag == "blue"


def test_default_clone_runs_custom_qobject_constructor_per_instance():
    first = _QObjectConfig()
    second = _QObjectConfig()

    assert first.value.objectName() == "bound-entry"
    assert first.value.helper is not second.value.helper
    assert first.value.helper.parent() is first.value
    assert second.value.helper.parent() is second.value
    assert first.set(first.value, "new", save=False) is True
    assert first.value.internal_updates == 1
    assert second.value.internal_updates == 0


def test_custom_constructor_without_clone_override_is_rejected():
    class _MissingCloneEntry(SettingEntry):
        def __init__(self, group, name, default, *, tag, parent=None):
            super().__init__(group, name, default, parent=parent)
            self.tag = tag

    class _MissingCloneConfig(SettingsCore):
        value = _MissingCloneEntry("General", "Value", "default", tag="x")

    with pytest.raises(TypeError, match="clone"):
        _MissingCloneConfig()


def test_direct_load_commits_decoded_value_without_second_prepare():
    entry = _TextDecodeEntry("General", "Value", 1)
    updates = []
    entry.valueUpdated.connect(updates.append)

    entry.load("2")

    assert entry.value == 2
    assert updates == [2]


def test_set_signal_argument_cannot_mutate_committed_value(tmp_path):
    config = _MutableSignalConfig()
    config.file = tmp_path / "settings.json"
    config.items.valueUpdated.connect(lambda value: value.append("listener"))

    assert config.set(config.items, ["saved"]) is True
    assert config.items.value == ["saved"]
    assert json.loads(config.file.read_text(encoding="utf-8"))["General"][
        "Items"
    ] == ["saved"]


def test_load_signal_argument_cannot_mutate_committed_value(tmp_path):
    config = _MutableSignalConfig()
    config.file = tmp_path / "settings.json"
    config.file.write_text(
        json.dumps({"General": {"Items": ["loaded"]}}), encoding="utf-8"
    )
    config.items.valueUpdated.connect(lambda value: value.append("listener"))

    assert config.load() is True
    assert config.items.value == ["loaded"]


def test_config_manager_initialization_failure_allows_clean_retry(
    tmp_path, monkeypatch
):
    original_instance = ConfigManager._instance
    original_load = AppConfig.load
    ConfigManager._instance = None
    calls = []

    def fail_once(config, file=None):
        calls.append(file)
        if len(calls) == 1:
            raise RuntimeError("load defect")
        return original_load(config, file)

    monkeypatch.setattr(AppConfig, "load", fail_once)
    try:
        with pytest.raises(RuntimeError, match="load defect"):
            ConfigManager(str(tmp_path / "settings.json"))
        assert ConfigManager._instance is None

        manager = ConfigManager(str(tmp_path / "settings.json"))
        assert manager._initialized is True
        assert len(calls) == 2
    finally:
        ConfigManager._instance = original_instance


def test_existing_directory_target_is_real_replace_failure(tmp_path, monkeypatch):
    config = _SerializationConfig()
    config.file = tmp_path / "settings-target"
    config.file.mkdir()
    diagnostics = []
    changes = []
    monkeypatch.setattr(settings_core_module, "exception", diagnostics.append)
    config.value.valueUpdated.connect(changes.append)

    assert config.set(config.value, "new") is False
    assert config.value.value == "old"
    assert config.file.is_dir()
    assert list(tmp_path.glob("*.tmp")) == []
    assert changes == []
    assert len(diagnostics) == 1


@pytest.mark.parametrize("value", [object(), "\ud800"])
def test_non_serializable_values_leave_no_partial_commit(
    tmp_path, monkeypatch, value
):
    config = _SerializationConfig()
    config.file = tmp_path / "settings.json"
    diagnostics = []
    changes = []
    monkeypatch.setattr(settings_core_module, "exception", diagnostics.append)
    config.value.valueUpdated.connect(changes.append)

    assert config.set(config.value, value) is False
    assert config.value.value == "old"
    assert not config.file.exists()
    assert list(tmp_path.glob("*.tmp")) == []
    assert changes == []
    assert len(diagnostics) == 1


def test_value_signal_observes_already_committed_disk(tmp_path):
    config = _SerializationConfig()
    config.file = tmp_path / "settings.json"
    disk_values = []
    config.value.valueUpdated.connect(
        lambda _value: disk_values.append(
            json.loads(config.file.read_text(encoding="utf-8"))["General"][
                "Value"
            ]
        )
    )

    assert config.set(config.value, "new") is True
    assert disk_values == ["new"]


def test_set_prepares_extension_state_before_disk_commit(tmp_path):
    config = _CommitFailureConfig()
    config.file = tmp_path / "settings.json"
    changes = []
    config.second.valueUpdated.connect(changes.append)

    with pytest.raises(RuntimeError, match="copy boom"):
        config.set(config.second, "poison")

    assert config.second.value == "old-second"
    assert not config.file.exists()
    assert changes == []


def test_load_prepares_all_extension_states_before_any_commit(tmp_path):
    config = _CommitFailureConfig()
    config.file = tmp_path / "settings.json"
    config.file.write_text(
        json.dumps(
            {"General": {"First": "new-first", "Second": "poison"}}
        ),
        encoding="utf-8",
    )
    first_changes = []
    config.first.valueUpdated.connect(first_changes.append)

    with pytest.raises(RuntimeError, match="copy boom"):
        config.load()

    assert config.first.value == "old-first"
    assert config.second.value == "old-second"
    assert first_changes == []
