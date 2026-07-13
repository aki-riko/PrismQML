# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Window builder fallback-boundary regressions. 窗口构建回退边界回归。"""

import pytest


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_generated_window_file_boundary_process_control_propagates(
    monkeypatch, error_type
):
    from prismqml.python.window._window_builder import WindowBuilderMixin

    def stop_load(_self, _qml, _component, _profile, _verbose):
        raise error_type("stop")

    monkeypatch.setattr(
        WindowBuilderMixin,
        "_load_generated_window_component",
        stop_load,
    )
    builder = WindowBuilderMixin()
    with pytest.raises(error_type, match="stop"):
        builder._load_generated_window_boundary("", "", lambda _label: None, False)
