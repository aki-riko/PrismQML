# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Window service composition. 窗口服务运行时装配。"""


def getShadowManager():
    """Return the runtime-owned shadow manager. 获取 runtime 持有的阴影管理器。"""
    from ..core.shadow import getShadowManager as _get_shadow_manager

    return _get_shadow_manager()


def get_window_helper():
    """Return the runtime-owned WindowHelper singleton. 获取 runtime 持有的窗口辅助单例。"""
    from ..core.window_helper import get_window_helper as _get_window_helper

    return _get_window_helper()


def get_mica_manager():
    """Return the runtime-owned Mica manager. 获取 runtime 持有的云母管理器。"""
    from ..window.mica_window import get_mica_manager as _get_mica_manager

    return _get_mica_manager()


def get_acrylic_helper():
    """Return the runtime-owned Acrylic helper. 获取 runtime 持有的亚克力助手。"""
    from ..window.mica_window import get_acrylic_helper as _get_acrylic_helper

    return _get_acrylic_helper()


def get_native_window_hook():
    """Return the runtime-owned native window hook. 获取 runtime 持有的原生窗口钩子。"""
    from ..window.native_window import get_native_window_hook as _get_native_window_hook

    return _get_native_window_hook()


def get_clipboard_helper():
    """Return the runtime-owned clipboard helper. 获取 runtime 持有的剪贴板助手。"""
    from ..providers.clipboard import get_clipboard_helper as _get_clipboard_helper

    return _get_clipboard_helper()
