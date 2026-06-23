# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是FluentQML的一部分，采用MIT许可证授权。
"""FluentQML 工具函数"""
import os
from pathlib import Path
from PySide6.QtQml import QQmlApplicationEngine


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


def register_types(engine: QQmlApplicationEngine):
    """
    注册QML类型到引擎 Register QML types to engine
    
    Note: 使用函数内导入以避免模块级循环依赖
    Note: Using in-function imports to avoid module-level circular dependencies
    """
    # 延迟导入以避免循环依赖 Lazy imports to avoid circular dependencies
    from .theme import getThemeManager
    from ..providers import get_qrcode_generator, get_qrcode_provider, get_screen_eyedropper_manager
    from ..window import get_mica_manager, get_acrylic_helper, get_native_window_hook

    # Register theme manager 注册主题管理器
    context = engine.rootContext()
    context.setContextProperty("ThemeManager", getThemeManager())

    # Register QRCode generator 注册二维码生成器
    context.setContextProperty("QRCodeGenerator", get_qrcode_generator())

    # Register QRCode image provider 注册二维码图片提供器
    engine.addImageProvider("qrcode", get_qrcode_provider())

    # Register Mica manager 注册云母效果管理器
    context.setContextProperty("MicaManager", get_mica_manager())

    # Register Acrylic helper 注册亚克力助手
    acrylic_helper = get_acrylic_helper()
    context.setContextProperty("AcrylicHelper", acrylic_helper)

    # Register NativeWindowHook 注册 frameless + DWM 动画 hook
    # WindowCore 在 Component.onCompleted 里调 NativeWindow.attach(window)
    # 让 frameless 窗口享受 DWM 原生 minimize/maximize/restore 动画
    context.setContextProperty("NativeWindow", get_native_window_hook())
    engine.addImageProvider("acrylic", acrylic_helper.imageProvider)
    
    # Register Screen Eyedropper manager 注册屏幕取色管理器
    context.setContextProperty("ScreenEyedropperManager", get_screen_eyedropper_manager())

    # Register Shadow manager 注册阴影管理器
    # Used by WindowCore / TipPopup to enable DWM native window shadows.
    # Missing this registration causes QML warnings:
    #   "ReferenceError: ShadowManager is not defined"
    # from any engine that loads a WindowCore-based QML.
    from .shadow import getShadowManager
    context.setContextProperty("ShadowManager", getShadowManager())

    # Register Window Helper 注册窗口辅助工具（任务栏图标等）
    from .window_helper import get_window_helper
    context.setContextProperty("WindowHelper", get_window_helper())

    # Add QML import path 添加QML导入路径
    # importPath 指向 module 根目录的**父**：Qt 会扫描 <importPath>/FluentQML/qmldir。
    # qml_path() 返回 prismqml/FluentQML（module 根本身），故传 .parent。
    engine.addImportPath(str(qml_path().parent))
