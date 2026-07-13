# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Splash builder boundary regressions. 启动画面构建边界回归。"""

from types import SimpleNamespace

import pytest


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_create_splash_process_control_propagates(monkeypatch, error_type):
    from prismqml.python.window import _splash_builder

    def stop_creation():
        raise error_type("stop")

    monkeypatch.setattr(_splash_builder.time, "perf_counter", stop_creation)
    builder = SimpleNamespace(_splash_enabled=True, _window=object())
    with pytest.raises(error_type, match="stop"):
        _splash_builder.create_splash(builder)


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_splash_file_component_process_control_propagates(error_type):
    from prismqml.python.window import _splash_builder

    def stop_file_load(_source):
        raise error_type("stop")

    builder = SimpleNamespace(_write_generated_splash_qml=stop_file_load)
    with pytest.raises(error_type, match="stop"):
        _splash_builder._load_splash_file_component(
            builder,
            "",
            lambda _label: None,
            False,
            ("", "", ""),
        )
