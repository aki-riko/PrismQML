# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""QML runtime registry composition. QML 运行时注册装配。"""

from PySide6.QtQml import QQmlApplicationEngine

from ..core.utils import _enable_quick_window_alpha_buffer, qml_path
from .context_registry import (
    FULL_CONTEXT_REGISTRATION,
    mark_context_registration,
)
from .context_composition import (
    register_lazy_context,
    register_primary_context,
    register_support_context,
    register_window_context,
)


def register_types(
    engine: QQmlApplicationEngine,
    *,
    config_path=None,
    persist_appearance: bool = None,
) -> None:
    """Register public QML context and providers. 注册公开 QML 上下文与 provider。"""
    _enable_quick_window_alpha_buffer()
    context = engine.rootContext()
    register_primary_context(
        context,
        config_path=config_path,
        persist_appearance=persist_appearance,
    )
    register_lazy_context(engine, context)
    register_window_context(engine, context)
    register_support_context(context)
    engine.addImportPath(str(qml_path().parent))
    mark_context_registration(engine, FULL_CONTEXT_REGISTRATION)
