# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Window service composition. 窗口服务运行时装配。"""


def get_window_helper():
    """Return the runtime-owned WindowHelper singleton. 获取 runtime 持有的窗口辅助单例。"""
    from ..core.window_helper import get_window_helper as _get_window_helper

    return _get_window_helper()


def get_mica_manager():
    """Return the runtime-owned Mica manager. 获取 runtime 持有的云母管理器。"""
    from ..window.mica_window import get_mica_manager as _get_mica_manager

    return _get_mica_manager()
