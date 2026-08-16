# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Configuration runtime composition. 配置运行时装配。"""


def get_config_manager(
    config_path: str = None, *, persist_appearance: bool = None
):
    """Return the process configuration singleton. 获取进程配置单例。"""
    from ..config import getConfigManager
    from .appearance import configure_appearance_persistence

    if config_path is None and persist_appearance is None:
        manager = getConfigManager()
    elif config_path is None:
        manager = getConfigManager(
            persist_appearance=persist_appearance
        )
    elif persist_appearance is None:
        manager = getConfigManager(config_path)
    else:
        manager = getConfigManager(
            config_path, persist_appearance=persist_appearance
        )
    configure_appearance_persistence(manager)
    return manager
