# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Engine-level appearance persistence. 引擎级外观持久化回归。"""

import json
from pathlib import Path
import threading
import time

from prismqml import Skin, Theme, setAccentColor, setSkin, setTheme
from prismqml.python.config.config_manager import ConfigManager
from prismqml.python.core.theme import ThemeManager


ROOT = Path(__file__).resolve().parents[1]


def _new_manager(path):
    ConfigManager._instance = None
    return ConfigManager(str(path))


def _wait_persistence(manager):
    assert manager.waitForPersistence(5000)


def test_appearance_settings_round_trip_and_restore_runtime(qapp, tmp_path):
    path = tmp_path / "app.json"
    original_config = ConfigManager._instance
    theme_manager = ThemeManager()
    previous = (
        theme_manager.theme,
        theme_manager.skin,
        theme_manager.accentColor,
    )
    try:
        manager = _new_manager(path)
        manager.setTheme("dark")
        manager.setSkin("vintage_ticket")
        manager.setLanguage("zh_CN")
        manager.setAccentColor("#123456")
        _wait_persistence(manager)

        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["Appearance"] == {
            "Theme": "dark",
            "Skin": "vintage_ticket",
            "Language": "zh_CN",
            "AccentColor": "#123456",
        }
        assert theme_manager.theme == "dark"
        assert theme_manager.skin == "vintage_ticket"
        assert theme_manager.accentColor == "#123456"

        theme_manager._apply_theme_from_qml("light")
        theme_manager._apply_skin_from_qml("fluent")
        theme_manager._apply_accent_color("#abcdef")
        restored = _new_manager(path)

        assert restored.theme == "dark"
        assert restored.skin == "vintage_ticket"
        assert restored.language == "zh_CN"
        assert restored.accentColor == "#123456"
        assert theme_manager.theme == "dark"
        assert theme_manager.skin == "vintage_ticket"
        assert theme_manager.accentColor == "#123456"
    finally:
        theme_manager._apply_theme_from_qml(previous[0])
        theme_manager._apply_skin_from_qml(previous[1])
        theme_manager._apply_accent_color(previous[2])
        ConfigManager._instance = original_config


def test_public_theme_api_persists_and_restores_without_stale_runtime(
    qapp, tmp_path, monkeypatch
):
    """Public engine setters must persist without replaying an older request."""
    path = tmp_path / "app.json"
    original_config = ConfigManager._instance
    theme_manager = ThemeManager()
    previous = (
        theme_manager.theme,
        theme_manager.skin,
        theme_manager.accentColor,
    )
    observed_themes = []
    try:
        manager = _new_manager(path)
        original_write = manager.cfg._write_mapping_file

        def delayed_write(file_path, mapping):
            time.sleep(0.05)
            original_write(file_path, mapping)

        monkeypatch.setattr(manager.cfg, "_write_mapping_file", delayed_write)
        theme_manager.themeChanged.connect(observed_themes.append)

        setTheme(Theme.DARK)
        setTheme(Theme.LIGHT)
        setSkin(Skin.VINTAGE_TICKET)
        setAccentColor("#123456")

        assert theme_manager.theme == "light"
        assert theme_manager.skin == "vintage_ticket"
        assert theme_manager.accentColor == "#123456"
        assert observed_themes == ["dark", "light"]
        _wait_persistence(manager)
        assert observed_themes == ["dark", "light"]

        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["Appearance"] == {
            "Theme": "light",
            "Skin": "vintage_ticket",
            "Language": "auto",
            "AccentColor": "#123456",
        }

        theme_manager.setThemeFromQml("dark")
        theme_manager.setSkinFromQml("neobrutalism")
        theme_manager.setAccentColor("#abcdef")
        _wait_persistence(manager)
        restored = _new_manager(path)

        assert restored.theme == "dark"
        assert restored.skin == "neobrutalism"
        assert restored.accentColor == "#abcdef"
        assert theme_manager.theme == "dark"
        assert theme_manager.skin == "neobrutalism"
        assert theme_manager.accentColor == "#abcdef"
    finally:
        theme_manager._apply_theme_from_qml(previous[0])
        theme_manager._apply_skin_from_qml(previous[1])
        theme_manager._apply_accent_color(previous[2])
        if ConfigManager._instance is not None:
            ConfigManager._instance.waitForPersistence(5000)
        ConfigManager._instance = original_config


def test_legacy_window_only_config_uses_appearance_defaults(tmp_path):
    path = tmp_path / "app.json"
    path.write_text(
        json.dumps({"Window": {"MicaEnabled": True}}), encoding="utf-8"
    )
    original_config = ConfigManager._instance
    try:
        manager = _new_manager(path)
        assert manager.micaEnabled is True
        assert manager.theme == "auto"
        assert manager.skin == "fluent"
        assert manager.language == "auto"
        assert manager.accentColor == ThemeManager.DEFAULT_ACCENT
    finally:
        ConfigManager._instance = original_config


def test_invalid_appearance_setters_do_not_persist_or_change_runtime(qapp, tmp_path):
    path = tmp_path / "app.json"
    original_config = ConfigManager._instance
    theme_manager = ThemeManager()
    previous = (
        theme_manager.theme,
        theme_manager.skin,
        theme_manager.accentColor,
    )
    try:
        manager = _new_manager(path)
        manager.setMicaEnabled(True)
        _wait_persistence(manager)
        baseline = path.read_bytes()
        manager.setTheme("missing")
        manager.setSkin("missing")
        manager.setLanguage("missing")
        manager.setAccentColor("#xyzxyz")

        assert path.read_bytes() == baseline
        assert manager.theme == "auto"
        assert manager.skin == "fluent"
        assert manager.language == "auto"
        assert manager.accentColor == ThemeManager.DEFAULT_ACCENT
        assert theme_manager.theme == "auto"
        assert theme_manager.skin == "fluent"
        assert theme_manager.accentColor == ThemeManager.DEFAULT_ACCENT
    finally:
        theme_manager._apply_theme_from_qml(previous[0])
        theme_manager._apply_skin_from_qml(previous[1])
        theme_manager._apply_accent_color(previous[2])
        ConfigManager._instance = original_config


def test_qml_setter_persists_off_main_thread(qapp, tmp_path, monkeypatch):
    path = tmp_path / "app.json"
    original_config = ConfigManager._instance
    theme_manager = ThemeManager()
    previous = theme_manager.theme
    try:
        manager = _new_manager(path)
        worker_threads = []
        original_write = manager.cfg._write_mapping_file

        def delayed_write(file_path, mapping):
            worker_threads.append(threading.get_ident())
            time.sleep(0.05)
            original_write(file_path, mapping)

        monkeypatch.setattr(manager.cfg, "_write_mapping_file", delayed_write)
        started = time.perf_counter()
        manager.setTheme("dark")
        callback_ms = (time.perf_counter() - started) * 1000

        assert callback_ms < 8
        assert manager.persistencePending
        assert manager.theme == "auto"
        assert theme_manager.theme == "dark"
        _wait_persistence(manager)
        assert manager.theme == "dark"
        assert worker_threads and worker_threads[0] != threading.get_ident()
    finally:
        theme_manager._apply_theme_from_qml(previous)
        ConfigManager._instance = original_config


def test_runtime_appearance_is_applied_before_public_notification(
    qapp, tmp_path
):
    path = tmp_path / "app.json"
    original_config = ConfigManager._instance
    theme_manager = ThemeManager()
    previous = theme_manager.theme
    observed = []
    try:
        manager = _new_manager(path)
        manager.themeChanged.connect(
            lambda: observed.append((manager.theme, theme_manager.theme))
        )
        manager.setTheme("dark")
        _wait_persistence(manager)

        assert observed == [("dark", "dark")]
    finally:
        theme_manager._apply_theme_from_qml(previous)
        ConfigManager._instance = original_config


def test_failed_background_save_keeps_committed_appearance(
    qapp, tmp_path, monkeypatch
):
    path = tmp_path / "app.json"
    original_config = ConfigManager._instance
    theme_manager = ThemeManager()
    previous = theme_manager.theme
    try:
        manager = _new_manager(path)

        def fail_write(_file_path, _mapping):
            raise OSError("forced persistence failure")

        monkeypatch.setattr(manager.cfg, "_write_mapping_file", fail_write)
        manager.setTheme("dark")
        _wait_persistence(manager)

        assert manager.theme == "auto"
        assert theme_manager.theme == "auto"
        assert not path.exists()
    finally:
        theme_manager._apply_theme_from_qml(previous)
        ConfigManager._instance = original_config


def test_gallery_startup_does_not_override_persisted_appearance():
    qml_source = (ROOT / "examples" / "main.qml").read_text(encoding="utf-8")
    cpp_source = (ROOT / "cpp" / "gallery" / "main.cpp").read_text(
        encoding="utf-8"
    )

    assert "Fluent.Translator.setLanguage(" not in qml_source
    assert "ConfigManager.setLanguage(" not in qml_source
    assert "setSkin(" not in cpp_source
    assert "setTheme(" not in cpp_source
    assert "setAccentColor(" not in cpp_source
