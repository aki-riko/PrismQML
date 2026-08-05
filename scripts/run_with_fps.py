# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""带实时 FPS 叠加层的 gallery 启动脚本.

用法: python scripts/run_with_fps.py
显示: 窗口右上角实时 fps + 最近 1 秒最差帧 ms.

完全不改业务 QML/Python: 复用 examples/main.py 的初始化路径,
在 QML 加载完成后从 Python 侧程序化创建 FpsOverlay (scripts/FpsOverlay.qml)
并 setParentItem 到 windowInstance.contentItem.
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


def _inject_fps_overlay(engine):
    """QML 加载完成后, 找 windowInstance.contentItem 并注入 FpsOverlay."""
    from PySide6.QtCore import QCoreApplication, QTimer, QUrl
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

        actual_api = win.rendererInterface().graphicsApi()
        actual_api_name = getattr(actual_api, "name", str(actual_api))
        if actual_api_name != "Direct3D11":
            print(
                "[fps-overlay] 只接受 Direct3D11，"
                f"实际为 {actual_api_name}"
            )
            state["injected"] = True
            QCoreApplication.exit(5)
            return
        print(f"[fps-overlay] graphics backend = {actual_api_name}")

        # win 是 QQuickWindow, 取它的 contentItem 作为 overlay parent
        content_item = win.contentItem()

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
    from PySide6.QtQml import QQmlApplicationEngine

    import examples.main as gallery

    class _FpsOverlayEngine(QQmlApplicationEngine):
        def load(self, url) -> None:
            super().load(url)
            if self.rootObjects():
                _inject_fps_overlay(self)

    gallery.QQmlApplicationEngine = _FpsOverlayEngine
    return int(gallery.main())


if __name__ == "__main__":
    sys.exit(main())
