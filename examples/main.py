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

from prismqml import App, Updater
from prismqml.python.core import Logger, getLogger, log_time

# Keep normal Gallery runs at INFO; diagnostics can still be enabled explicitly.
# Gallery默认只输出INFO及以上；需要诊断时仍可显式开启DEBUG。
getLogger().set_level(Logger.INFO)

log_time("Python启动与核心库导入完成")

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import QUrl

from prismqml.python.config import DEFAULT_APP_CONFIG
from prismqml.python.config._app_config_schema import resolve_app_config_path
from prismqml.python.runtime import get_svg_provider
from examples.resources import GALLERY_RCC_PATH, register_gallery_resources

GALLERY_CONFIG_PATH = resolve_app_config_path(default=DEFAULT_APP_CONFIG)
GALLERY_APPLICATION_ICON = "qrc:/app_icon.svg"

# 注册二进制资源文件(QML 通过 qrc:/ 访问图片等)
# 用 .rcc 二进制资源代替编译成 .py 的资源(体积更小,不污染代码仓库)
if not register_gallery_resources():
    print(f"警告: 资源注册失败 {GALLERY_RCC_PATH}")

log_time("全部模块导入完成")

def main():
    log_time("main()开始")
    # App owns QApplication, the QML engine, and the early fast splash.
    # App 统一持有 QApplication、QML 引擎和早期快速启动页。
    app = App(
        argv=sys.argv,
        application_icon=GALLERY_APPLICATION_ICON,
        config_path=GALLERY_CONFIG_PATH,
        persist_appearance=True,
    )
    log_time("QApplication创建完成")
    log_time("快速独立 Splash 创建完成")
    engine = app.engine
    log_time("QML引擎创建完成")

    # Install safe sliced incubation for lazy pages. 为懒加载页面安装安全的分片孵化。
    # Known-unsafe Qt builds fall back automatically. 已知不安全的 Qt 构建会自动回退。
    from prismqml.python.core.incubation import (
        asynchronous_page_loader_enabled,
    )

    engine.rootContext().setContextProperty(
        "PrismQmlAsynchronousPageLoaderEnabled",
        asynchronous_page_loader_enabled(),
    )
    
    # 资源已通过 QResource.registerResource(gallery.rcc) 在模块加载时注册
    
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
        app.shutdown()
        return -1

    root = engine.rootObjects()[0]
    main_window = root.property("windowInstance")
    if main_window is not None:
        app._attach_fast_splash(main_window)
    
    log_time("窗口准备就绪，进入事件循环")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
