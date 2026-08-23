# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""
PrismQML Gallery - 组件展示应用

运行方式：python examples/main.py
"""

import sys
import os
import time

# 禁用 Qt 字体数据库警告（OpenType support missing）
# Disable Qt font database warnings
os.environ["QT_LOGGING_RULES"] = "qt.text.font.db=false"

# 启动计时由 core/logger.py 加载时自动开始

# 添加项目根目录到路径(main.py 在 examples/,上 2 层到项目根)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import prismqml

from prismqml import Updater, configure_qml_environment
from prismqml.python.core import Logger, getLogger, log_time

# Keep normal Gallery runs at INFO; diagnostics can still be enabled explicitly.
# Gallery默认只输出INFO及以上；需要诊断时仍可显式开启DEBUG。
getLogger().set_level(Logger.INFO)

# Enable local QML XHR before creating the engine. 在创建引擎前启用本地 QML XHR。
configure_qml_environment()
log_time("Python启动与核心库导入完成")

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import Qt, QUrl
from PySide6.QtQuick import QQuickWindow, QSGRendererInterface

from prismqml import register_types
from prismqml.python.core import install_qt_message_handler
from prismqml.python.config import DEFAULT_APP_CONFIG, applyDpiScale
from prismqml.python.config._app_config_schema import resolve_app_config_path
from prismqml.python.runtime import (
    get_svg_provider,
    install_application_dwm_filter,
)
from prismqml.python.window.fast_splash import FastSplashController
from examples.resources import GALLERY_RCC_PATH, register_gallery_resources

GALLERY_CONFIG_PATH = resolve_app_config_path(default=DEFAULT_APP_CONFIG)

# 注册二进制资源文件(QML 通过 qrc:/ 访问图片等)
# 用 .rcc 二进制资源代替编译成 .py 的资源(体积更小,不污染代码仓库)
if not register_gallery_resources():
    print(f"警告: 资源注册失败 {GALLERY_RCC_PATH}")

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

    if sys.platform == "win32":
        # Use the only supported Windows graphics backend. 使用唯一受支持的 Windows 图形后端。
        QQuickWindow.setGraphicsApi(
            QSGRendererInterface.GraphicsApi.Direct3D11
        )

    applyDpiScale(GALLERY_CONFIG_PATH)
    log_time("DPI缩放应用完成")
    
    app = QApplication(sys.argv)
    log_time("QApplication创建完成")

    # Show the lightweight independent splash before the main QML engine is
    # created. The main window is revealed through its outward ring once the
    # first page has swapped frames.
    # 在创建主 QML 引擎前显示轻量独立启动页；首页完成首帧后通过向外圆环揭幕。
    fast_splash = FastSplashController(app)
    fast_splash_enabled = fast_splash.show()
    log_time("快速独立 Splash 创建完成")
    
    # 安装DWM同步过滤器（解决resize撕裂问题）
    # Install DWM sync filter (fix resize tearing)
    install_application_dwm_filter()
    log_time("DWM同步过滤器安装完成")
    
    # 将QML/Qt日志重定向到项目logger
    install_qt_message_handler()
    log_time("Qt消息处理器安装完成")
    
    engine = QQmlApplicationEngine()
    log_time("QML引擎创建完成")

    # Install safe sliced incubation for lazy pages. 为懒加载页面安装安全的分片孵化。
    # Known-unsafe Qt builds fall back automatically. 已知不安全的 Qt 构建会自动回退。
    from prismqml.python.core.incubation import (
        asynchronous_page_loader_enabled,
        install_default_incubation_controller,
    )

    engine.rootContext().setContextProperty(
        "PrismQmlAsynchronousPageLoaderEnabled",
        asynchronous_page_loader_enabled(),
    )
    engine.rootContext().setContextProperty(
        "PrismQmlFastStartupSplashEnabled",
        fast_splash_enabled,
    )
    install_default_incubation_controller(engine)
    
    # 资源已通过 QResource.registerResource(gallery.rcc) 在模块加载时注册
    
    # Register the complete public QML runtime, including NativeWindow.
    # 注册完整公共 QML 运行时，包括 NativeWindow。
    register_types(
        engine,
        config_path=GALLERY_CONFIG_PATH,
        persist_appearance=True,
    )
    # 注册SVG图片提供器（高质量SVG渲染）
    engine.addImageProvider("svg", get_svg_provider())

    # Gallery 使用真实的 GitHub Releases 更新后端，供“自动更新”页面演示。
    # Gallery wires the same backend contract as an application host, but does
    # not start a network check until the user presses the check button.
    gallery_repository = os.environ.get(
        "PRISMQML_GALLERY_UPDATE_REPOSITORY", "aki-riko/PrismQML"
    ).strip() or "aki-riko/PrismQML"
    gallery_asset_keyword = os.environ.get(
        "PRISMQML_GALLERY_UPDATE_ASSET_KEYWORD", "Setup"
    ).strip() or "Setup"
    gallery_updater = Updater(
        gallery_repository, prismqml.__version__, gallery_asset_keyword
    )
    gallery_updater.set_require_artifact_digest(True)
    engine.rootContext().setContextProperty("appUpdater", gallery_updater)
    log_time("上下文属性注册完成")
    
    # 添加QML导入路径
    # importPath 指向 prismqml/ 父级，Qt 会扫描其中的 PrismQML/qmldir
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prismqml_root = os.path.join(project_root, "prismqml")
    engine.addImportPath(prismqml_root)
    qml_dir = os.path.join(prismqml_root, "PrismQML")

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
        fast_splash.close()
        return -1

    root = engine.rootObjects()[0]
    main_window = root.property("windowInstance")
    if fast_splash_enabled and main_window is not None:
        attached = fast_splash.attach_and_reveal(engine, main_window)
        if not attached:
            # Keep the existing in-window fallback if the native owner cannot
            # be established on a particular Qt/Windows build.
            # 若特定 Qt/Windows 构建无法建立原生 owner，则恢复原内嵌兜底。
            main_window.setProperty("splashEnabled", True)
            fast_splash.close()
    else:
        fast_splash.close()
    app.aboutToQuit.connect(fast_splash.close)
    
    log_time("窗口准备就绪，进入事件循环")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
