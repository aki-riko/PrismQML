# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""SettingsCore 持久化失败与加载边界回归测试。"""

import json
import sys

import pytest

from prismqml.python.config.config_item import SettingEntry
from prismqml.python.config.config_manager import ConfigManager
from prismqml.python.config.settings_core import SettingsCore
import prismqml.python.config.settings_core as settings_core_module


class _PersistenceConfig(SettingsCore):
    normal = SettingEntry("General", "Normal", "old")
    restart = SettingEntry("General", "Restart", False, restart=True)


class _ExplodingEncodeEntry(SettingEntry):
    def encode(self, _value):
        raise RuntimeError("encode hook failed")


class _DumpFailureConfig(SettingsCore):
    broken = _ExplodingEncodeEntry("General", "Broken", "value")


class _ExplodingValidator:
    def coerce(self, value):
        if value == "boom":
            raise RuntimeError("validator failed")
        return value


class _AtomicLoadConfig(SettingsCore):
    first = SettingEntry("Group", "First", "old")
    second = SettingEntry(
        "Group", "Second", "safe", validator=_ExplodingValidator()
    )


class _IsolatedConfig(SettingsCore):
    value = SettingEntry("General", "Value", "default")


class _InheritanceBase(SettingsCore):
    value = SettingEntry("General", "Value", "base")


class _InheritanceMiddle(_InheritanceBase):
    value = SettingEntry("General", "Value", "middle")


class _InheritanceLeaf(_InheritanceMiddle):
    pass


class _DottedKeyConfig(SettingsCore):
    dotted_group = SettingEntry("A.B", "C", "group-default")
    dotted_name = SettingEntry("A", "B.C", "name-default")


class _MutableDefaultConfig(SettingsCore):
    items = SettingEntry("General", "Items", [])


def _raise_disk_full(_source, _target):
    raise OSError("disk full")


@pytest.fixture
def config(tmp_path):
    _PersistenceConfig.normal._value = _PersistenceConfig.normal.default_value
    _PersistenceConfig.restart._value = _PersistenceConfig.restart.default_value
    instance = _PersistenceConfig()
    instance.file = tmp_path / "settings.json"
    return instance


def test_set_rolls_back_when_atomic_replace_fails(config, monkeypatch):
    baseline = {"General": {"Normal": "old", "Restart": False}}
    config.file.write_text(json.dumps(baseline), encoding="utf-8")
    diagnostics = []
    config_changes = []
    restart_requests = []
    value_updates = []
    entry = config.restart

    monkeypatch.setattr(settings_core_module.os, "replace", _raise_disk_full)
    monkeypatch.setattr(
        settings_core_module, "exception", diagnostics.append, raising=False
    )
    config.configChanged.connect(lambda: config_changes.append(True))
    config.restartRequested.connect(lambda: restart_requests.append(True))
    entry.valueUpdated.connect(value_updates.append)
    try:
        result = config.set(entry, True)
    finally:
        entry.valueUpdated.disconnect(value_updates.append)

    assert result is False
    assert config.get(entry) is False
    assert json.loads(config.file.read_text(encoding="utf-8")) == baseline
    assert list(config.file.parent.glob("*.tmp")) == []
    assert value_updates == []
    assert restart_requests == []
    assert config_changes == []
    assert diagnostics == ["保存失败 Save failed: disk full"]


@pytest.mark.parametrize("control_error", [KeyboardInterrupt, SystemExit])
def test_set_rolls_back_and_propagates_process_control_errors(
    config, monkeypatch, control_error
):
    config_changes = []
    restart_requests = []
    value_updates = []
    entry = config.restart

    def interrupt_replace(_source, _target):
        raise control_error()

    monkeypatch.setattr(settings_core_module.os, "replace", interrupt_replace)
    config.configChanged.connect(lambda: config_changes.append(True))
    config.restartRequested.connect(lambda: restart_requests.append(True))
    entry.valueUpdated.connect(value_updates.append)
    try:
        with pytest.raises(control_error):
            config.set(entry, True)
    finally:
        entry.valueUpdated.disconnect(value_updates.append)

    assert config.get(entry) is False
    assert value_updates == []
    assert restart_requests == []
    assert config_changes == []
    assert list(config.file.parent.glob("*.tmp")) == []


def test_save_reports_encode_hook_failure_with_traceback_boundary(
    tmp_path, monkeypatch
):
    config = _DumpFailureConfig()
    config.file = tmp_path / "settings.json"
    diagnostics = []
    monkeypatch.setattr(
        settings_core_module, "exception", diagnostics.append, raising=False
    )

    assert config.save() is False
    assert diagnostics == ["保存失败 Save failed: encode hook failed"]
    assert not config.file.exists()
    assert list(tmp_path.glob("*.tmp")) == []


def test_save_returns_true_after_atomic_persistence(config):
    assert config.save() is True
    assert json.loads(config.file.read_text(encoding="utf-8")) == {
        "General": {"Normal": "old", "Restart": False}
    }


def test_save_without_file_returns_false():
    assert _PersistenceConfig().save() is False


def test_set_without_file_rolls_back_and_suppresses_global_signals():
    _PersistenceConfig.normal._value = _PersistenceConfig.normal.default_value
    config = _PersistenceConfig()
    entry = config.normal
    config_changes = []
    config.configChanged.connect(lambda: config_changes.append(True))

    assert config.set(entry, "new") is False
    assert config.get(entry) == "old"
    assert config_changes == []


def test_set_rolls_back_on_real_parent_path_failure(config, tmp_path, monkeypatch):
    blocker = tmp_path / "blocked-parent"
    blocker.write_text("not a directory", encoding="utf-8")
    config.file = blocker / "settings.json"
    diagnostics = []
    config_changes = []
    monkeypatch.setattr(settings_core_module, "exception", diagnostics.append)
    config.configChanged.connect(lambda: config_changes.append(True))

    assert config.set(config.normal, "new") is False
    assert config.get(config.normal) == "old"
    assert blocker.read_text(encoding="utf-8") == "not a directory"
    assert config_changes == []
    assert len(diagnostics) == 1


def test_set_without_persistence_keeps_memory_signal_contract(config):
    config_changes = []
    restart_requests = []
    config.configChanged.connect(lambda: config_changes.append(True))
    config.restartRequested.connect(lambda: restart_requests.append(True))

    assert config.set(config.restart, True, save=False) is True
    assert config.get(config.restart) is True
    assert restart_requests == [True]
    assert config_changes == [True]
    assert not config.file.exists()


def test_set_unchanged_value_is_success_without_side_effects(config):
    config_changes = []
    config.configChanged.connect(lambda: config_changes.append(True))

    assert config.set(config.normal, "old") is True
    assert config_changes == []
    assert not config.file.exists()


@pytest.mark.parametrize(
    "payload",
    [b'{"General":', b"\xff\xfe\xfa"],
)
def test_load_known_file_errors_keep_defaults_and_suppress_signal(
    config, payload
):
    config.file.write_bytes(payload)
    config_changes = []
    config.configChanged.connect(lambda: config_changes.append(True))

    assert config.load() is False

    assert config.get(config.normal) == "old"
    assert config.get(config.restart) is False
    assert config_changes == []


def test_load_propagates_unknown_json_loader_failure(config, monkeypatch):
    config.file.write_text("{}", encoding="utf-8")

    def fail_load(_stream):
        raise RuntimeError("json loader defect")

    monkeypatch.setattr(settings_core_module.json, "load", fail_load)

    with pytest.raises(RuntimeError, match="json loader defect"):
        config.load()


def test_load_os_error_keeps_defaults_and_suppresses_signal(config, monkeypatch):
    config.file.write_text("{}", encoding="utf-8")
    config_changes = []
    config.configChanged.connect(lambda: config_changes.append(True))

    def fail_open(*_args, **_kwargs):
        raise PermissionError("access denied")

    monkeypatch.setattr(settings_core_module, "open", fail_open, raising=False)

    assert config.load() is False

    assert config.get(config.normal) == "old"
    assert config.get(config.restart) is False
    assert config_changes == []


def test_successful_set_notifies_only_after_persistence(config):
    value_updates = []
    config_changes = []
    entry = config.normal
    entry.valueUpdated.connect(value_updates.append)
    config.configChanged.connect(lambda: config_changes.append(True))

    assert config.set(entry, "new") is True
    assert config.get(entry) == "new"
    assert json.loads(config.file.read_text(encoding="utf-8"))["General"] == {
        "Normal": "new",
        "Restart": False,
    }
    assert value_updates == ["new"]
    assert config_changes == [True]


def test_success_log_failure_cannot_roll_back_committed_value(config, monkeypatch):
    value_updates = []
    entry = config.normal
    entry.valueUpdated.connect(value_updates.append)

    def fail_info(_message):
        raise RuntimeError("success logger failed")

    monkeypatch.setattr(settings_core_module, "info", fail_info)

    assert config.set(entry, "new") is True
    assert config.get(entry) == "new"
    assert json.loads(config.file.read_text(encoding="utf-8"))["General"][
        "Normal"
    ] == "new"
    assert value_updates == ["new"]


def test_instances_have_independent_values_and_signals():
    _IsolatedConfig.value._value = _IsolatedConfig.value.default_value
    first = _IsolatedConfig()
    second = _IsolatedConfig()
    first_updates = []
    second_updates = []
    first.value.valueUpdated.connect(first_updates.append)
    second.value.valueUpdated.connect(second_updates.append)

    assert first.value is not second.value
    assert first.set(_IsolatedConfig.value, "first", save=False) is True
    assert first.get(_IsolatedConfig.value) == "first"
    assert second.get(_IsolatedConfig.value) == "default"
    assert first_updates == ["first"]
    assert second_updates == []


def test_nearest_inherited_entry_override_wins():
    config = _InheritanceLeaf()
    entries = dict(config._iter_entries())

    assert entries["value"].default_value == "middle"
    assert config.get(_InheritanceLeaf.value) == "middle"


def test_c3_left_base_override_wins():
    class _Left(_InheritanceBase):
        value = SettingEntry("General", "Value", "left")

    class _Right(_InheritanceBase):
        value = SettingEntry("General", "Value", "right")

    class _Diamond(_Left, _Right):
        pass

    config = _Diamond()
    assert config.get(_Diamond.value) == "left"


def test_duplicate_persistence_key_is_rejected_at_class_definition():
    with pytest.raises(TypeError, match="General.Value"):

        class _DuplicateKeyConfig(SettingsCore):
            first = SettingEntry("General", "Value", 1)
            second = SettingEntry("General", "Value", 2)


def test_flat_and_nested_group_conflict_is_rejected_at_class_definition():
    with pytest.raises(TypeError, match="General"):

        class _ConflictingGroupConfig(SettingsCore):
            flat = SettingEntry("General", "", 1)
            nested = SettingEntry("General", "Value", 2)


def test_inherited_duplicate_key_is_rejected_at_class_definition():
    with pytest.raises(TypeError, match="General.Value"):

        class _InheritedDuplicateConfig(_InheritanceBase):
            duplicate = SettingEntry("General", "Value", "duplicate")


def test_mutable_defaults_are_isolated_between_instances_and_prototype():
    first = _MutableDefaultConfig()
    second = _MutableDefaultConfig()

    first.items.value.append("first")

    assert first.items.value == ["first"]
    assert second.items.value == []
    assert _MutableDefaultConfig.items.value == []


def test_load_is_all_or_none_when_validator_fails(tmp_path):
    config = _AtomicLoadConfig()
    config.file = tmp_path / "settings.json"
    config.file.write_text(
        json.dumps({"Group": {"First": "new", "Second": "boom"}}),
        encoding="utf-8",
    )
    first_updates = []
    config_changes = []
    config.first.valueUpdated.connect(first_updates.append)
    config.configChanged.connect(lambda: config_changes.append(True))

    with pytest.raises(RuntimeError, match="validator failed"):
        config.load()

    assert config.get(config.first) == "old"
    assert config.get(config.second) == "safe"
    assert first_updates == []
    assert config_changes == []


def test_load_commits_all_values_before_first_entry_signal(tmp_path):
    config = _AtomicLoadConfig()
    config.file = tmp_path / "settings.json"
    config.file.write_text(
        json.dumps({"Group": {"First": "new", "Second": "ready"}}),
        encoding="utf-8",
    )
    second_values_seen = []
    config.first.valueUpdated.connect(
        lambda _value: second_values_seen.append(config.second.value)
    )

    assert config.load() is True
    assert config.first.value == "new"
    assert config.second.value == "ready"
    assert second_values_seen == ["ready"]


def test_load_overlong_json_integer_is_known_bad_file_input(config):
    digit_limit = getattr(sys, "get_int_max_str_digits", lambda: 4300)()
    digits = "9" * max(5000, digit_limit + 100)
    config.file.write_text(
        '{"General":{"Normal":' + digits + "}}", encoding="utf-8"
    )
    config_changes = []
    config.configChanged.connect(lambda: config_changes.append(True))

    assert config.load() is False

    assert config.get(config.normal) == "old"
    assert config_changes == []


def test_load_excessive_nesting_is_known_bad_file_input(config):
    depth = 5000
    nested = "[" * depth + "0" + "]" * depth
    config.file.write_text(
        '{"General":{"Normal":' + nested + "}}", encoding="utf-8"
    )
    config_changes = []
    config.configChanged.connect(lambda: config_changes.append(True))

    assert config.load() is False

    assert config.get(config.normal) == "old"
    assert config_changes == []


def test_dotted_group_and_name_keys_load_without_collision(tmp_path):
    config = _DottedKeyConfig()
    config.file = tmp_path / "settings.json"
    config.file.write_text(
        json.dumps({"A.B": {"C": "group"}, "A": {"B.C": "name"}}),
        encoding="utf-8",
    )

    assert config.load() is True
    assert config.dotted_group.value == "group"
    assert config.dotted_name.value == "name"


def test_config_manager_property_signal_is_silent_on_save_failure(
    tmp_path, monkeypatch
):
    blocker = tmp_path / "blocked-parent"
    blocker.write_text("not a directory", encoding="utf-8")
    original_instance = ConfigManager._instance
    ConfigManager._instance = None
    diagnostics = []
    monkeypatch.setattr(settings_core_module, "exception", diagnostics.append)
    try:
        manager = ConfigManager(str(blocker / "settings.json"))
        property_changes = []
        config_changes = []
        manager.micaEnabledChanged.connect(lambda: property_changes.append(True))
        manager.configChanged.connect(lambda: config_changes.append(True))

        manager.setMicaEnabled(True)

        assert manager.micaEnabled is False
        assert property_changes == []
        assert config_changes == []
        assert len(diagnostics) == 1
    finally:
        ConfigManager._instance = original_instance
