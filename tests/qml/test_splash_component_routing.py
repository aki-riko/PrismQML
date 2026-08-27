# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Custom splash routing regression. 自定义启动组件分流回归。"""

from __future__ import annotations

import sys
from pathlib import Path

from _test_process_bootstrap import configure_qml_test_process

configure_qml_test_process()

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl, Slot
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtWidgets import QApplication

from prismqml.python.window.fast_splash import FastSplashController


ROOT = Path(__file__).resolve().parents[2]
PKG_ROOT = ROOT / "prismqml"


class StartupBridge(QObject):
    """Record QML startup-window registration calls for this runtime probe."""

    def __init__(self):
        super().__init__()
        self.windows = []

    @Slot(QObject, result=bool)
    def registerStartupWindow(self, window):
        self.windows.append(window)
        return True


def pump(milliseconds: int) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def main() -> int:
    app = QApplication(sys.argv)
    engine = QQmlEngine()
    engine.addImportPath(str(PKG_ROOT))
    startup_bridge = StartupBridge()
    engine.rootContext().setContextProperty("PrismQmlStartup", startup_bridge)
    default_source = """
import QtQuick
import PrismQML

NavigationWindowCore {
    visible: false
    splashEnabled: false
    property bool done: _usesDefaultSplashComponent
}
"""
    default_component = QQmlComponent(engine)
    default_component.setData(
        default_source.encode("utf-8"), QUrl("default-splash-routing")
    )
    default_window = default_component.create()
    if default_window is None or not default_window.property("done"):
        print("[FAIL] 默认 Splash 被误判为自定义组件")
        for error in default_component.errors():
            print("   ", error.toString())
        return 1
    if startup_bridge.windows != [default_window]:
        print("[FAIL] 默认 NavigationWindowCore 未自动注册启动窗口")
        return 1

    source = """
import QtQuick
import PrismQML

NavigationWindowCore {
    id: win
    width: 320
    height: 180
    visible: false
    splashEnabled: false
    splashMinimumVisibleDuration: 0

    property bool customMounted: false

    splashComponent: Component {
        Rectangle {
            objectName: "customSplash"
            anchors.fill: parent
            color: "transparent"

            Component.onCompleted: win.customMounted = true

            function finish() {}
        }
    }
}
"""
    component = QQmlComponent(engine)
    component.setData(source.encode("utf-8"), QUrl("custom-splash-routing"))
    for _ in range(60):
        if component.status() != QQmlComponent.Status.Loading:
            break
        pump(20)
    if component.isError():
        print("[FAIL] 自定义 Splash 场景加载失败:")
        for error in component.errors():
            print("   ", error.toString())
        return 1

    window = component.create()
    if window is None:
        print("[FAIL] 自定义 Splash 场景创建失败")
        return 1
    if startup_bridge.windows != [default_window, window]:
        print("[FAIL] 自定义 NavigationWindowCore 未自动注册启动窗口")
        return 1

    controller = FastSplashController(app)
    if not controller.restore_embedded_splash(window):
        print("[FAIL] 快速 Splash 回退控制器无法恢复内嵌启动页")
        return 1

    for _ in range(20):
        pump(20)
        if window.property("customMounted"):
            break

    failures = []
    if window.property("_usesDefaultSplashComponent"):
        failures.append("自定义 splashComponent 被误判为默认组件")
    if not window.property("customMounted"):
        failures.append("延迟启用后自定义 Splash 没有挂载")
    if not window.property("splashEnabled") or window.property("_splashInstance") is None:
        failures.append("延迟启用后 Splash 状态没有恢复")

    if failures:
        print("[FAIL] 自定义 Splash 自动分流失败")
        for failure in failures:
            print("  ", failure)
        return 1

    print("RESULT: PASS - 自定义 Splash 自动回退到内嵌生命周期")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
