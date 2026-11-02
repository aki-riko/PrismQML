# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""PrismQML 工具函数"""
import os
from pathlib import Path

QML_XHR_ALLOW_FILE_READ_ENV = "QML_XHR_ALLOW_FILE_READ"


def _enable_quick_window_alpha_buffer() -> None:
    """Enable translucent child windows before their native surfaces exist.

    在原生表面创建前启用透明子窗口所需的 alpha buffer。
    """
    from PySide6.QtQuick import QQuickWindow

    QQuickWindow.setDefaultAlphaBuffer(True)


def configure_qml_environment(allow_file_read: bool = True) -> None:
    """Configure process-wide QML rendering before engine creation.

    在引擎创建前配置进程级 QML 渲染环境。

    普通 ``import prismqml`` 不修改该进程环境。使用裸 ``QQmlEngine`` 且需要
    Translator 加载本地 i18n JSON 时，必须在创建引擎前显式调用本函数。
    """
    os.environ[QML_XHR_ALLOW_FILE_READ_ENV] = "1" if allow_file_read else "0"
    _enable_quick_window_alpha_buffer()


def is_app_thread() -> bool:
    """Report whether the caller runs on the Qt application thread.

    报告调用方是否运行在 Qt 应用线程上。

    Qt signals, timers and thread affinity all key off this thread, so callers that
    must decide whether the event loop can deliver work use this instead of comparing
    ``QThread.currentThread()`` against the application instance by hand. Returns
    ``False`` when no ``QCoreApplication`` exists, because nothing can deliver events
    then either.
    Qt 的信号、定时器与线程亲和性都以该线程为准, 因此需要判断事件循环能否投递任务的调用方
    应使用本函数, 而不是自行比较 ``QThread.currentThread()`` 与应用实例。没有
    ``QCoreApplication`` 时返回 ``False``, 因为那时同样无法投递事件。
    """
    from PySide6.QtCore import QCoreApplication, QThread

    app = QCoreApplication.instance()
    if app is None:
        return False
    return QThread.currentThread() is app.thread()


def qml_path(relative_path: str = "") -> Path:
    """获取QML文件路径

    返回的目录即 QML module 根（`module PrismQML` 在其 qmldir 中声明）。
    Qt 6 QML 要求 importPath 指向该目录的**父**（见 register_types 中的 addImportPath）。
    """
    base = Path(__file__).parent.parent.parent / "PrismQML"
    if relative_path:
        return base / relative_path
    return base


def init_style():
    """
    初始化QML控件样式为Basic，禁用原生平台样式
    必须在创建QGuiApplication之前调用
    """
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
