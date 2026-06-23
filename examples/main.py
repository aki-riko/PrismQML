# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是FluentQML的一部分，采用MIT许可证授权。
"""
FluentQML Gallery - 组件展示应用

运行方式：python examples/main.py
"""

import sys
import os
import time

# 禁用 Qt 字体数据库警告（OpenType support missing）
# Disable Qt font database warnings
os.environ["QT_LOGGING_RULES"] = "qt.text.font.db=false"

# 允许 QML XMLHttpRequest 读取本地文件（Translator 加载 i18n JSON 所需）
# Allow QML XMLHttpRequest to read local files (needed by Translator for i18n JSON)
os.environ["QML_XHR_ALLOW_FILE_READ"] = "1"

# 启动计时由 core/logger.py 加载时自动开始

# 添加项目根目录到路径(main.py 在 examples/,上 2 层到项目根)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fluentqml.python.core import log_time
log_time("Python启动与核心库导入完成")

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow, QSGRendererInterface
from PySide6.QtCore import Qt, QUrl, QResource

from fluentqml.python.core import ThemeManager, getShadowManager, installDwmSyncFilter, install_qt_message_handler
from fluentqml.python.config import getConfigManager, applyDpiScale
from fluentqml.python.providers import (
    get_qrcode_generator, get_qrcode_provider,
    get_screen_eyedropper_manager,
    get_clipboard_helper,
    get_svg_provider,
)
from fluentqml.python.window import get_mica_manager, get_acrylic_helper

# 注册二进制资源文件(QML 通过 qrc:/ 访问图片等)
# 用 .rcc 二进制资源代替编译成 .py 的资源(体积更小,不污染代码仓库)
_rcc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "gallery.rcc")
if not QResource.registerResource(_rcc_path):
    print(f"警告: 资源注册失败 {_rcc_path}")

log_time("全部模块导入完成")

def main():
    log_time("main()开始")
    # 必须在创建QApplication之前应用DPI缩放和高DPI策略
    # Must apply DPI scale and high DPI policy before creating QApplication
    
    # 设置高DPI缩放策略（PassThrough = 精确缩放，避免模糊）
    # Set high DPI scale factor rounding policy (PassThrough = exact scaling, avoid blur)
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # 强制使用OpenGL后端，避免 D3D11 device lost 问题
    # Force OpenGL backend to avoid D3D11 device-lost crashes on some Windows drivers
    QQuickWindow.setGraphicsApi(QSGRendererInterface.OpenGL)

    applyDpiScale()
    log_time("DPI缩放应用完成")
    
    app = QApplication(sys.argv)
    log_time("QApplication创建完成")
    
    # 安装DWM同步过滤器（解决resize撕裂问题）
    # Install DWM sync filter (fix resize tearing)
    installDwmSyncFilter()
    log_time("DWM同步过滤器安装完成")
    
    # 将QML/Qt日志重定向到项目logger
    install_qt_message_handler()
    log_time("Qt消息处理器安装完成")
    
    # 初始化主题管理器、阴影管理器和配置管理器
    theme_manager = ThemeManager()
    shadow_manager = getShadowManager()
    config_manager = getConfigManager()
    mica_manager = get_mica_manager()
    acrylic_helper = get_acrylic_helper()
    screen_eyedropper_manager = get_screen_eyedropper_manager()
    log_time("管理器初始化完成")
    
    engine = QQmlApplicationEngine()
    log_time("QML引擎创建完成")

    # 安装异步孵化控制器: 让 asynchronous Loader(StackedWidget 懒加载)分帧切片
    # 实例化, 避免切到未加载页时单帧建整棵页面树阻塞 GUI 线程造成掉帧。
    # 注: 走 fluentqml.App 的应用会自动安装; 此处直接裸建 engine 故需显式调用。
    from fluentqml.python.core.incubation import install_incubation_controller
    install_incubation_controller(engine)
    
    # 资源已通过 QResource.registerResource(gallery.rcc) 在模块加载时注册
    
    # 注册管理器到QML
    engine.rootContext().setContextProperty("ThemeManager", theme_manager)
    engine.rootContext().setContextProperty("ShadowManager", shadow_manager)
    engine.rootContext().setContextProperty("ConfigManager", config_manager)
    engine.rootContext().setContextProperty("MicaManager", mica_manager)
    engine.rootContext().setContextProperty("AcrylicHelper", acrylic_helper)
    engine.rootContext().setContextProperty("QRCodeGenerator", get_qrcode_generator())
    engine.rootContext().setContextProperty("ScreenEyedropperManager", screen_eyedropper_manager)
    engine.rootContext().setContextProperty("ClipboardHelper", get_clipboard_helper())
    
    # 注册窗口辅助工具（任务栏图标同步等）
    from fluentqml.python.core.window_helper import get_window_helper
    engine.rootContext().setContextProperty("WindowHelper", get_window_helper())
    
    # 注册二维码图片提供器
    engine.addImageProvider("qrcode", get_qrcode_provider())
    # 注册亚克力图片提供器
    engine.addImageProvider("acrylic", acrylic_helper.imageProvider)
    # 注册SVG图片提供器（高质量SVG渲染）
    engine.addImageProvider("svg", get_svg_provider())
    log_time("上下文属性注册完成")
    
    # 添加QML导入路径
    # importPath 指向 fluentqml/ 父级，Qt 会扫描其中的 PrismQML/qmldir
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fluentqml_root = os.path.join(project_root, "fluentqml")
    engine.addImportPath(fluentqml_root)
    qml_dir = os.path.join(fluentqml_root, "PrismQML")

    # 添加组件子目录（用于 main.qml 中的字面量 subdir import 兼容）
    for subdir in ["controls/buttons", "controls/inputs", "controls/data",
                   "controls/containers", "controls/feedback", "controls/menus",
                   "controls/dialogs", "controls/icons", "controls/utils",
                   "navigation", "controls/navigation", "controls/settings"]:
        engine.addImportPath(os.path.join(qml_dir, subdir))
    
    # 加载QML
    qml_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.qml")
    log_time("开始加载QML")
    engine.load(QUrl.fromLocalFile(qml_file))
    log_time("QML加载完成")
    
    if not engine.rootObjects():
        print("[ERROR] 加载QML失败，请检查组件路径或QML语法")
        return -1
    
    log_time("窗口准备就绪，进入事件循环")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
