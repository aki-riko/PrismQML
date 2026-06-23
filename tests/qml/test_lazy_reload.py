# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
# 本文件是 FluentQML 的一部分，采用 MIT 许可证授权。
"""Headless 懒加载回归测试 — 切走再切回主页不应重新懒加载。

复现 bug: 初始当前页(主页 index 0)启动时 Loader.active 默认即 true,
绑定算出 true 但值未变化 → onActiveChanged 不触发 → _loadOnce 漏锁 →
切走时 active 绑定算出 false 主页被卸载 → 切回 _isPageLoaded(0)==false →
onCurrentIndexChanged 再次走 showLoadingAndSwitch(主页又懒加载一次)。

修复: sourceLoader.onLoaded 里补 _loadOnce = true。

判据: 模拟 启动→切到页1→切回页0, 全程主页(0)必须始终保持 Ready
(即未被卸载), 才说明切回不会重新懒加载。

用法: python tests/qml/test_lazy_reload.py
退出码: 0=通过, 1=失败
"""
import sys
from pathlib import Path

from PySide6.QtCore import QUrl, QTimer, QEventLoop
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression

PKG_ROOT = Path(__file__).resolve().parents[2] / "prismqml"
NAV_DIR = PKG_ROOT / "FluentQML" / "controls" / "navigation"
PAGES_DIR = Path(__file__).resolve().parents[2] / "examples" / "pages"


def pump(ms):
    """空转事件循环 ms 毫秒, 驱动 StackedWidget 内部定时器/异步 Loader。"""
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def is_loaded(stack, idx):
    """对 stack 求值 _isPageLoaded(idx) 取布尔返回值。
    注意: PySide6 QQmlExpression.evaluate() 返回 (值, 是否undefined) 元组,
    必须取 [0], 否则非空元组恒为 True 会让断言失去区分力。"""
    expr = QQmlExpression(QQmlEngine.contextForObject(stack), stack,
                          f"_isPageLoaded({idx})")
    val = expr.evaluate()
    if isinstance(val, tuple):
        val = val[0]
    return bool(val)


def main():
    app = QApplication(sys.argv)
    engine = QQmlEngine()
    engine.addImportPath(str(PKG_ROOT))

    page0 = QUrl.fromLocalFile(str(PAGES_DIR / "ButtonPage.qml")).toString()
    page1 = QUrl.fromLocalFile(str(PAGES_DIR / "InputPage.qml")).toString()

    qml = f'''
import QtQuick
import FluentQML
import "{NAV_DIR.as_posix()}"

StackedWidget {{
    width: 800; height: 600
    lazyLoading: true
    currentIndex: 0
    pageSources: ["{page0}", "{page1}"]
}}
'''

    comp = QQmlComponent(engine)
    comp.setData(qml.encode("utf-8"), QUrl("inline"))
    # StackedWidget 内含 asynchronous Loader, 组件编译为异步, 等到 Ready 再 create
    for _ in range(50):
        if comp.status() != QQmlComponent.Status.Loading:
            break
        pump(50)
    if comp.isError():
        print("[FAIL] 组件加载错误:")
        for e in comp.errors():
            print("   ", e.toString())
        sys.exit(1)

    stack = comp.create()
    if stack is None:
        print("[FAIL] create() 返回 None:")
        for e in comp.errors():
            print("   ", e.toString())
        sys.exit(1)

    failures = []

    # 阶段0: 启动后等主页(index 0)异步加载完成
    pump(500)
    if not is_loaded(stack, 0):
        failures.append("启动后主页(0)未加载完成, 测试前提不成立")

    # 阶段1: 切到页1, 等懒加载完成
    stack.setProperty("currentIndex", 1)
    pump(900)
    if not is_loaded(stack, 1):
        failures.append("切到页1后页1未加载完成")

    # 核心断言: 切走主页后, 主页是否仍保持 Ready(未被卸载)
    # 修复前: 主页 _loadOnce 漏锁 → active 变 false → 主页被卸载 → not Ready
    # 修复后: 主页 _loadOnce 已锁 → active 保持 true → 主页仍 Ready
    # 这是区分 bug 的关键点: 主页被卸载正是"切回会重新懒加载"的根因。
    if not is_loaded(stack, 0):
        failures.append("切走主页后主页被卸载 → 切回必重新懒加载 (bug 未修复)")

    # 阶段2: 切回主页0, 确认全程正常
    stack.setProperty("currentIndex", 0)
    pump(500)
    if not is_loaded(stack, 0):
        failures.append("切回主页结束后主页仍未 Ready")

    print(f"\n{'='*60}")
    if failures:
        print("RESULT: FAIL - 懒加载回归测试失败")
        for f in failures:
            print("  [FAIL]", f)
        result = 1
    else:
        print("RESULT: PASS - 切走再切回主页未重新懒加载")
        result = 0
    print(f"{'='*60}")

    QTimer.singleShot(0, app.quit)
    app.exec()
    sys.exit(result)


if __name__ == "__main__":
    main()
