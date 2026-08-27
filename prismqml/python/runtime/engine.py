# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""QML engine runtime composition. QML 引擎运行时装配。"""

from PySide6.QtQml import QQmlApplicationEngine

from ..core.engine import EngineManager


def create_qml_engine() -> QQmlApplicationEngine:
    """Create an unpublished QML engine. 创建尚未发布的 QML 引擎。"""
    return QQmlApplicationEngine()


def publish_qml_engine(engine: QQmlApplicationEngine) -> None:
    """Publish the process QML engine. 发布进程级 QML 引擎。"""
    EngineManager.set_engine(engine)


def is_published_qml_engine(engine: QQmlApplicationEngine) -> bool:
    """Check whether the process engine is this instance. 检查进程引擎身份。"""
    return EngineManager._engine is engine


def get_published_qml_engine() -> QQmlApplicationEngine:
    """Return the published QML engine. 获取已发布的 QML 引擎。"""
    return EngineManager.get_engine()


def register_qml_engine_binding(engine: QQmlApplicationEngine, binding) -> None:
    """Keep one binding alive with the QML engine. 保活引擎绑定对象。"""
    EngineManager.register_engine_binding(engine, binding)


def release_qml_engine_bindings(
    engine: QQmlApplicationEngine, *, include_lazy: bool = True
) -> None:
    """Release Python bindings owned by the QML engine. 释放引擎绑定对象。"""
    EngineManager._release_engine_bindings(engine, include_lazy=include_lazy)


def reset_qml_engine() -> None:
    """Reset the published QML engine and its bindings. 重置进程 QML 引擎。"""
    EngineManager.reset()


def get_or_create_qml_engine() -> QQmlApplicationEngine:
    """Reuse or create and publish the process engine. 复用或创建并发布引擎。"""
    try:
        return EngineManager.get_engine()
    except RuntimeError:
        engine = create_qml_engine()
        publish_qml_engine(engine)
        return engine


def configure_application_engine(
    engine: QQmlApplicationEngine,
    *,
    config_path=None,
    persist_appearance: bool = None,
) -> None:
    """Install App-owned QML integrations. 安装 App 使用的 QML 集成。"""
    from ..core.incubation import install_default_incubation_controller
    from . import register_types

    install_default_incubation_controller(engine)
    if config_path is None and persist_appearance is None:
        register_types(engine)
    else:
        register_types(
            engine,
            config_path=config_path,
            persist_appearance=persist_appearance,
        )


def register_startup_window_context(engine, owner):
    """Expose the App-owned startup-window bridge to QML."""
    from .startup_window import register_startup_window_context as register

    return register(engine, owner)
