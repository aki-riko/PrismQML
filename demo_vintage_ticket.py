# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Launch the standalone vintage-ticket preview. 启动独立复古票据预览。"""

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow, QSGRendererInterface
from PySide6.QtWidgets import QApplication

from prismqml import Skin, configure_qml_environment, register_types, setSkin
from prismqml.python.config import applyDpiScale
from prismqml.python.core import install_qt_message_handler
from prismqml.python.core.logger import error, info


PREVIEW_QML = Path(__file__).resolve().parent / "examples" / "vintage_ticket_preview.qml"


def _configure_graphics_backend() -> None:
    """Configure the only supported Windows backend. 配置 Windows 唯一受支持后端。"""
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    if sys.platform == "win32":
        QQuickWindow.setGraphicsApi(
            QSGRendererInterface.GraphicsApi.Direct3D11
        )


def _create_preview_engine() -> QQmlApplicationEngine:
    """Create and load the standalone preview engine. 创建并加载独立预览引擎。"""
    engine = QQmlApplicationEngine()
    register_types(engine)
    engine.addImportPath(str(PREVIEW_QML.parents[1] / "prismqml"))
    engine.load(QUrl.fromLocalFile(str(PREVIEW_QML)))
    return engine


def main() -> int:
    """Create the real D3D11 preview window. 创建真实 D3D11 预览窗口。"""
    configure_qml_environment()
    _configure_graphics_backend()
    applyDpiScale()
    app = QApplication(sys.argv)
    install_qt_message_handler()
    setSkin(Skin.VINTAGE_TICKET)

    engine = _create_preview_engine()
    if not engine.rootObjects():
        error(f"复古票据预览加载失败: {PREVIEW_QML}", tag="VintageTicket")
        return 1

    window = engine.rootObjects()[0]
    actual_api = window.rendererInterface().graphicsApi().name
    if sys.platform == "win32" and actual_api != "Direct3D11":
        error(f"图形后端不符合要求: {actual_api}", tag="VintageTicket")
        window.close()
        return 1

    info(f"复古票据预览已启动，图形后端={actual_api}", tag="VintageTicket")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
