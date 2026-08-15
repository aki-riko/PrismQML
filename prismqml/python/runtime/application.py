# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Qt application runtime composition. Qt 应用运行时装配。"""

import os
from typing import List, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication


def _configure_windows_graphics_api() -> None:
    """Select the required Windows Qt Quick backend. 选择 Windows 强制图形后端。"""
    from PySide6.QtQuick import QQuickWindow, QSGRendererInterface

    QQuickWindow.setGraphicsApi(
        QSGRendererInterface.GraphicsApi.Direct3D11
    )


def prepare_application_environment(allow_qml_file_read: bool) -> None:
    """Prepare process-wide Qt settings before QApplication. 在创建应用前准备 Qt。"""
    from ..config import applyDpiScale
    from ..core import configure_qml_environment, install_qt_message_handler

    configure_qml_environment(allow_qml_file_read)
    if os.name == "nt":
        _configure_windows_graphics_api()
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    applyDpiScale()
    install_qt_message_handler()


def create_qt_application(argv: List[str]) -> Tuple[QApplication, bool]:
    """Create QApplication and report ownership. 创建应用并返回所有权。"""
    owns_application = QApplication.instance() is None
    return QApplication(argv or []), owns_application


def install_application_input_filter(app: QApplication):
    """Install the process input filter. 安装进程输入过滤器。"""
    from ..core.input_focus_filter import install_input_focus_filter

    return install_input_focus_filter(app)


def install_application_dwm_filter() -> bool:
    """Install the Windows DWM synchronization filter. 安装 Windows DWM 同步过滤器。"""
    from ..core.shadow import installDwmSyncFilter

    return installDwmSyncFilter()
