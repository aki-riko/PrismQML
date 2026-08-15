# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Runtime configuration composition contracts. 运行时配置装配合同。"""

from prismqml.python import config
from prismqml.python.runtime.configuration import get_config_manager


def test_get_config_manager_preserves_no_argument_call_shape(monkeypatch):
    manager = object()
    calls = []

    def factory():
        calls.append(())
        return manager

    monkeypatch.setattr(config, "getConfigManager", factory)

    assert get_config_manager() is manager
    assert calls == [()]


def test_get_config_manager_forwards_explicit_path(monkeypatch):
    manager = object()
    calls = []

    def factory(config_path):
        calls.append(config_path)
        return manager

    monkeypatch.setattr(config, "getConfigManager", factory)

    assert get_config_manager("custom-config.json") is manager
    assert calls == ["custom-config.json"]
