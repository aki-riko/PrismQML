# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

from prismqml.python.window import _derive_app_user_model_id


def test_explicit_app_user_model_id_wins():
    app_id = _derive_app_user_model_id(
        executable="C:/Python/python.exe",
        argv0="D:/Apps/Gitora/main.py",
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
