# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

import pytest

from prismqml.python import window as window_module
from prismqml.python.window import _derive_app_user_model_id


class _RaisingPath:
    def __init__(self, error_type):
        self._error_type = error_type

    def __fspath__(self):
        raise self._error_type("stop")


def test_explicit_app_user_model_id_wins():
    app_id = _derive_app_user_model_id(
        executable="C:/Python/python.exe",
        argv0="D:/Apps/Gitora/main.py",
        environ={"PRISMQML_APP_USER_MODEL_ID": "AkiRiko.Gitora"},
    )

    assert app_id == "AkiRiko.Gitora"


@pytest.mark.parametrize("error_type", [OSError, KeyboardInterrupt, SystemExit])
def test_explicit_app_user_model_id_short_circuits_automatic_sources(error_type):
    app_id = _derive_app_user_model_id(
        executable=_RaisingPath(error_type),
        argv0=_RaisingPath(error_type),
        environ={"PRISMQML_APP_USER_MODEL_ID": "AkiRiko.Gitora"},
    )

    assert app_id == "AkiRiko.Gitora"


def test_packaged_executable_uses_exe_stem():
    app_id = _derive_app_user_model_id(
        executable="D:/Apps/Gitora/Gitora.exe",
        argv0="D:/Apps/Gitora/main.py",
        environ={},
    )

    assert app_id == "PrismQML.Gitora"


def test_packaged_executable_short_circuits_script_derivation():
    app_id = _derive_app_user_model_id(
        executable="D:/Apps/Gitora/Gitora.exe",
        argv0=_RaisingPath(KeyboardInterrupt),
        environ={},
    )

    assert app_id == "PrismQML.Gitora"


@pytest.mark.parametrize("host_stem", ["python", "PYTHONW", "Py"])
def test_python_host_names_fall_through_to_script_path(host_stem):
    app_id = _derive_app_user_model_id(
        executable=f"C:/Python/{host_stem}.exe",
        argv0="D:/Apps/Gitora/main.py",
        environ={},
    )

    assert app_id.startswith("PrismQML.Gitora.main.")


def test_python_host_uses_script_path_to_avoid_taskbar_grouping_collision():
    first = _derive_app_user_model_id(
        executable="C:/Python/python.exe",
        argv0="D:/Apps/Gitora/main.py",
        environ={},
    )
    second = _derive_app_user_model_id(
        executable="C:/Python/python.exe",
        argv0="D:/Apps/Kaleidos/main.py",
        environ={},
    )

    assert first.startswith("PrismQML.Gitora.main.")
    assert second.startswith("PrismQML.Kaleidos.main.")
    assert first != second


def test_python_host_without_script_uses_stable_default():
    app_id = _derive_app_user_model_id(
        executable="C:/Python/python.exe",
        argv0="",
        environ={},
    )

    assert app_id == "PrismQML.App"

def test_python_module_entry_uses_parent_without_main_component():
    app_id = _derive_app_user_model_id(
        executable="C:/Python/python.exe",
        argv0="D:/Apps/Gitora/__main__.py",
        environ={},
    )

    assert app_id.startswith("PrismQML.Gitora.")
    assert ".main." not in app_id


@pytest.mark.parametrize("error_type", [OSError, TypeError, ValueError])
def test_executable_resolution_errors_fall_back_to_script(error_type):
    app_id = _derive_app_user_model_id(
        executable=_RaisingPath(error_type),
        argv0="D:/Apps/Gitora/main.py",
        environ={},
    )

    assert app_id.startswith("PrismQML.Gitora.main.")


@pytest.mark.parametrize("error_type", [OSError, TypeError, ValueError])
def test_script_resolution_errors_fall_back_to_stable_default(error_type):
    app_id = _derive_app_user_model_id(
        executable="C:/Python/python.exe",
        argv0=_RaisingPath(error_type),
        environ={},
    )

    assert app_id == "PrismQML.App"


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_executable_process_control_errors_propagate(error_type):
    with pytest.raises(error_type, match="stop"):
        _derive_app_user_model_id(
            executable=_RaisingPath(error_type),
            argv0="D:/Apps/Gitora/main.py",
            environ={},
        )


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_script_process_control_errors_propagate(error_type):
    with pytest.raises(error_type, match="stop"):
        _derive_app_user_model_id(
            executable="C:/Python/python.exe",
            argv0=_RaisingPath(error_type),
            environ={},
        )


def test_missing_process_argv_uses_stable_default(monkeypatch):
    monkeypatch.setattr(window_module.sys, "argv", [])

    app_id = _derive_app_user_model_id(
        executable="C:/Python/python.exe",
        argv0=None,
        environ={},
    )

    assert app_id == "PrismQML.App"


def test_default_arguments_read_current_process_sources(monkeypatch):
    monkeypatch.delenv("PRISMQML_APP_USER_MODEL_ID", raising=False)
    monkeypatch.setattr(window_module.sys, "executable", "C:/Python/python.exe")
    monkeypatch.setattr(window_module.sys, "argv", ["D:/Apps/Gitora/main.py"])

    app_id = _derive_app_user_model_id()

    assert app_id.startswith("PrismQML.Gitora.main.")


def test_default_arguments_read_environment_before_process_sources(monkeypatch):
    monkeypatch.setenv("PRISMQML_APP_USER_MODEL_ID", "AkiRiko.Gitora")
    monkeypatch.setattr(
        window_module.sys, "executable", _RaisingPath(KeyboardInterrupt)
    )
    monkeypatch.setattr(
        window_module.sys, "argv", [_RaisingPath(KeyboardInterrupt)]
    )

    app_id = _derive_app_user_model_id()

    assert app_id == "AkiRiko.Gitora"


def test_default_arguments_read_executable_before_process_argv(monkeypatch):
    monkeypatch.delenv("PRISMQML_APP_USER_MODEL_ID", raising=False)
    monkeypatch.setattr(
        window_module.sys, "executable", "D:/Apps/Gitora/Gitora.exe"
    )
    monkeypatch.setattr(
        window_module.sys, "argv", [_RaisingPath(KeyboardInterrupt)]
    )

    app_id = _derive_app_user_model_id()

    assert app_id == "PrismQML.Gitora"
