# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Configuration runtime composition. 配置运行时装配。"""


def get_config_manager(config_path: str = None):
    """Return the process configuration singleton. 获取进程配置单例。"""
    from ..config import getConfigManager
    from .appearance import install_config_appearance_runtime

    if config_path is None:
        manager = getConfigManager()
    else:
        manager = getConfigManager(config_path)
    install_config_appearance_runtime(manager)
    return manager
