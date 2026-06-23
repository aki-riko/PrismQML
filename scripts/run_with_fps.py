# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是PrismQML的一部分，采用MIT许可证授权。
"""带实时 FPS 叠加层的 gallery 启动脚本.

用法: python scripts/run_with_fps.py
显示: 窗口右上角实时 fps + 最近 1 秒最差帧 ms.

完全不改业务 QML/Python: 复用 examples/main.py 的初始化路径,
在 QML 加载完成后从 Python 侧程序化创建 FpsOverlay (scripts/FpsOverlay.qml)
并 setParentItem 到 windowInstance.contentItem.
"""
import os
import sys

# 让 examples/ 能 import resources
GALLERY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "examples")
sys.path.insert(0, GALLERY_DIR)
os.chdir(GALLERY_DIR)


def _inject_fps_overlay(engine):
    """QML 加载完成后, 找 windowInstance.contentItem 并注入 FpsOverlay."""
    from PySide6.QtCore import QTimer, QUrl
    from PySide6.QtQml import QQmlComponent

    overlay_qml = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "FpsOverlay.qml")

    state = {"injected": False, "tries": 0}

    def try_inject():
        if state["injected"]:
            return
        state["tries"] += 1
        roots = engine.rootObjects()
        if not roots:
            if state["tries"] < 50:
                QTimer.singleShot(100, try_inject)
            else:
                print("[fps-overlay] 找不到 rootObjects, 放弃注入")
            return

        root = roots[0]
        win = root.property("windowInstance")
        if win is None:
            # main.qml 启动后 0ms 就 createObject 了 windowInstance, 但可能还没设回
            if state["tries"] < 50:
                QTimer.singleShot(100, try_inject)
            else:
                print("[fps-overlay] windowInstance 始终为 None, 放弃")
            return

        # win 是 QQuickWindow, 取它的 contentItem 作为 overlay parent
        try:
            content_item = win.contentItem()
        except Exception as e:
            print(f"[fps-overlay] 取 contentItem 失败: {e}")
            return

        comp = QQmlComponent(engine, QUrl.fromLocalFile(overlay_qml))
        if comp.isError():
            print(f"[fps-overlay] FpsOverlay.qml 加载失败:\n{comp.errorString()}")
            return

        overlay = comp.create()
        if overlay is None:
            print(f"[fps-overlay] FpsOverlay 创建失败:\n{comp.errorString()}")
            return

        # 监听窗口的 frameSwapped (overlay 内部 Connections target = watchWindow)
        overlay.setProperty("watchWindow", win)
        # 父级设到 contentItem (visual parent), QObject parent 也一起
        overlay.setParent(content_item)
        if hasattr(overlay, "setParentItem"):
            overlay.setParentItem(content_item)

        state["injected"] = True
        print(f"[fps-overlay] 已注入到窗口 {win.width()}x{win.height()}")

    # 等 main.qml 的 Component.onCompleted 跑完 (windowInstance = createObject)
    QTimer.singleShot(300, try_inject)


def main():
    # 复用 gallery main 的全部初始化, 但需要在 engine.load 后插一个钩子
    # 最简方式: 直接复制 main() 的代码并在 engine.load 后加一行 _inject_fps_overlay
    import time as _t  # noqa
    os.environ.setdefault("QT_LOGGING_RULES", "qt.text.font.db=false")
    os.environ.setdefault("QML_XHR_ALLOW_FILE_READ", "1")

    # 项目根加入 sys.path (与 main.py 一致)
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, PROJECT_ROOT)

    from prismqml.python.core import (ThemeManager, getShadowManager,
                                       installDwmSyncFilter,
                                       install_qt_message_handler)
    from prismqml.python.config import getConfigManager, applyDpiScale
    from prismqml.python.providers import (get_qrcode_generator,
                                            get_qrcode_provider,
                                            get_screen_eyedropper_manager,
                                            get_clipboard_helper,
                                            get_svg_provider)
    from prismqml.python.window import get_mica_manager, get_acrylic_helper
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuick import QQuickWindow, QSGRendererInterface
    from PySide6.QtCore import Qt, QUrl

    from resources import gallery_rc  # noqa: F401

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QQuickWindow.setGraphicsApi(QSGRendererInterface.OpenGL)
    applyDpiScale()

    app = QApplication(sys.argv)
    installDwmSyncFilter()
    install_qt_message_handler()

    tm = ThemeManager(); sm = getShadowManager(); cm = getConfigManager()
    mm = get_mica_manager(); ah = get_acrylic_helper()
    scpm = get_screen_eyedropper_manager()

    engine = QQmlApplicationEngine()
    ctx = engine.rootContext()
    ctx.setContextProperty("ThemeManager", tm)
    ctx.setContextProperty("ShadowManager", sm)
    ctx.setContextProperty("ConfigManager", cm)
    ctx.setContextProperty("MicaManager", mm)
    ctx.setContextProperty("AcrylicHelper", ah)
    ctx.setContextProperty("QRCodeGenerator", get_qrcode_generator())
    ctx.setContextProperty("ScreenEyedropperManager", scpm)
    ctx.setContextProperty("ClipboardHelper", get_clipboard_helper())
    from prismqml.python.core.window_helper import get_window_helper
    ctx.setContextProperty("WindowHelper", get_window_helper())
    engine.addImageProvider("qrcode", get_qrcode_provider())
    engine.addImageProvider("acrylic", ah.imageProvider)
    engine.addImageProvider("svg", get_svg_provider())

    prismqml_root = os.path.join(PROJECT_ROOT, "prismqml")
    engine.addImportPath(prismqml_root)
    qml_dir = os.path.join(prismqml_root, "PrismQML")
    for subdir in ["controls/buttons", "controls/inputs", "controls/data",
                   "controls/containers", "controls/feedback", "controls/menus",
                   "controls/dialogs", "controls/icons", "controls/utils",
                   "navigation", "controls/navigation", "controls/settings"]:
        engine.addImportPath(os.path.join(qml_dir, subdir))

    qml_file = os.path.join(GALLERY_DIR, "main.qml")
    engine.load(QUrl.fromLocalFile(qml_file))
    if not engine.rootObjects():
        print("[ERROR] QML 加载失败")
        return -1

    _inject_fps_overlay(engine)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
