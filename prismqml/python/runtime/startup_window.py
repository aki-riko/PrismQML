# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""QML startup-window registration bridge. 纯 QML 启动窗口注册桥。"""

from __future__ import annotations

import weakref

from PySide6.QtCore import QObject, Property, Slot

from ..core.logger import exception
from .context_registry import register_context_property
from .startup_defaults import DEFAULT_SPLASH_SUBTITLE


class StartupWindowRegistrar(QObject):
    """Expose the App startup-window contract to QML. 向 QML 暴露启动窗口合同。"""

    def __init__(self, owner, parent: QObject) -> None:
        super().__init__(parent)
        try:
            self._owner = weakref.ref(owner)
        except TypeError:
            # Test doubles and a few QObject facades may not expose weak refs.
            self._owner = lambda: owner

    @Property(str, constant=True)
    def splashSubtitle(self) -> str:
        """Expose the App-level subtitle default to pure-QML windows."""
        owner = self._owner()
        return str(getattr(owner, "splash_subtitle", DEFAULT_SPLASH_SUBTITLE))

    @Slot(QObject, result=bool)
    def registerStartupWindow(self, main_window: QObject) -> bool:
        """Attach one QML-created window through the public App API."""
        owner = self._owner()
        if owner is None or main_window is None:
            return False
        try:
            return bool(owner.attach_startup_window(main_window))
        except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
            exception(
                "QML 启动窗口注册失败: "
                f"{type(exc).__name__}: {exc}"
            )
            return False


def register_startup_window_context(engine, owner) -> StartupWindowRegistrar:
    """Install and retain the QML startup-window registration bridge."""
    registrar = StartupWindowRegistrar(owner, engine)
    register_context_property(
        engine.rootContext(), "PrismQmlStartup", registrar
    )
    setattr(engine, "_prismqml_startup_window_registrar", registrar)
    return registrar
