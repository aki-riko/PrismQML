# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
"""孵化控制器回归测试 — 防止异步懒加载掉帧修复被回退。

背景: 切到未加载页时, 异步 Loader 实例化整棵页面树。若引擎未装
QQmlIncubationController, 这棵树在单帧内同步建完, 与导航指示器动画
(GUI 线程 NumberAnimation)抢帧 → 掉帧。装 controller 后按帧切片孵化。

本测试不依赖 GPU 帧率(headless 无渲染循环不可靠), 而是验证两个**结构性**
不变量, 它们是修复生效的前提:
  1. App 创建后, engine 已装 FluentIncubationController(自动安装未被删)。
  2. controller 真的在推进孵化: 加载一个含 asynchronous Loader 的场景,
     controller 的 incubateFor 被驱动后, 异步对象最终完成孵化(对象出现)。

用法: <venv>/python tests/qml/test_incubation_controller.py
退出码: 0=通过, 1=失败
"""
import sys
from pathlib import Path

from PySide6.QtCore import QUrl, QTimer, QEventLoop
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from fluentqml.python.core.incubation import (  # noqa: E402
    FluentIncubationController, install_incubation_controller)
from fluentqml.python.core.utils import register_types  # noqa: E402


def pump(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def main():
    from PySide6.QtGui import QGuiApplication
    app = QGuiApplication(sys.argv)
    failures = []

    # 不变量1: install 后 engine 装上 FluentIncubationController + 幂等
    engine = QQmlApplicationEngine()
    register_types(engine)
    c1 = install_incubation_controller(engine)
    if not isinstance(engine.incubationController(), FluentIncubationController):
        failures.append("install 后 engine 未装 FluentIncubationController")
    if install_incubation_controller(engine) is not c1:
        failures.append("install 非幂等(重复安装产生了新 controller)")

    # 不变量2: controller 真的推进异步孵化 — 用 asynchronous Loader 场景
    qml = '''
import QtQuick
Item {
    width: 100; height: 100
    property alias loaderStatus: ld.status
    property bool itemReady: ld.item !== null
    Loader {
        id: ld
        asynchronous: true
        sourceComponent: Rectangle { width: 50; height: 50; color: "red" }
    }
}
'''
    comp = QQmlComponent(engine)
    comp.setData(qml.encode("utf-8"), QUrl("inline"))
    obj = comp.create()
    if obj is None:
        failures.append("测试场景 create() 返回 None")
    else:
        # 异步 Loader 初始通常未就绪; controller 被定时器驱动后应推进到就绪
        ready = False
        for _ in range(40):
            pump(50)
            if obj.property("itemReady"):
                ready = True
                break
        if not ready:
            failures.append("装了 controller 但异步 Loader 始终未孵化完成"
                            "(controller 未推进孵化)")

    out = []
    if failures:
        out.append("RESULT: FAIL - 孵化控制器回归失败")
        out += ["  [FAIL] " + f for f in failures]
        result = 1
    else:
        out.append("RESULT: PASS - 孵化控制器已装且推进异步孵化")
        result = 0
    sys.stderr.write("\n".join(out) + "\n")
    QTimer.singleShot(0, app.quit)
    app.exec()
    sys.exit(result)


if __name__ == "__main__":
    main()
