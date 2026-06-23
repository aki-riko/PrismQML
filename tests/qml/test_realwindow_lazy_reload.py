# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of FluentQML, licensed under MIT.
"""真机路径懒加载复现 — 经完整 WindowsBar 链路, 而非顶层 StackedWidget。

为什么需要这个: test_lazy_reload.py 直接实例化顶层 StackedWidget, 但真机
(example/Gitora)走的是:
    WindowsBar.content -> asynchronous mainLoader -> contentComponent
      -> StackedWidget(嵌套在异步 Loader 里, 由 startupTimer 50ms 后才 active)
这条嵌套异步路径与顶层直接实例化的时序完全不同, 顶层测试 PASS 不代表真机不复现。

判据: 启动→切到页1→切回页0, 全程主页(0)的 Loader 必须始终保持 Ready
(未被卸载)。主页被卸载正是"切回重新懒加载/再次显示 loading"的根因。

用法: <venv>/python tests/qml/test_realwindow_lazy_reload.py
退出码: 0=通过(主页未被卸载), 1=失败(主页被卸载=会重新懒加载)
"""
import sys
from pathlib import Path

from PySide6.QtCore import QUrl, QTimer, QEventLoop
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression

PKG_ROOT = Path(__file__).resolve().parents[2] / "fluentqml"
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from fluentqml.python.core.utils import register_types  # noqa: E402

PAGES_DIR = Path(__file__).resolve().parents[2] / "examples" / "pages"


def pump(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def eval_on(obj, expr_str):
    expr = QQmlExpression(QQmlEngine.contextForObject(obj), obj, expr_str)
    val = expr.evaluate()
    if isinstance(val, tuple):
        val = val[0]
    return val


def main():
    app = QApplication(sys.argv)
    from PySide6.QtQml import QQmlApplicationEngine
    engine = QQmlApplicationEngine()
    register_types(engine)

    page0 = QUrl.fromLocalFile(str(PAGES_DIR / "ButtonPage.qml")).toString()
    page1 = QUrl.fromLocalFile(str(PAGES_DIR / "InputPage.qml")).toString()

    qml = f'''
import QtQuick
import FluentQML as Fluent

Fluent.Windows {{
    width: 900; height: 650
    lazyLoading: true
    navigationItems: [
        {{ "text": "页0", "icon": "" }},
        {{ "text": "页1", "icon": "" }}
    ]
    pageSources: ["{page0}", "{page1}"]
}}
'''

    comp = QQmlComponent(engine)
    comp.setData(qml.encode("utf-8"), QUrl("inline"))
    for _ in range(60):
        if comp.status() != QQmlComponent.Status.Loading:
            break
        pump(50)
    if comp.isError():
        print("[FAIL] 组件加载错误:")
        for e in comp.errors():
            print("   ", e.toString())
        sys.exit(1)

    win = comp.create()
    if win is None:
        print("[FAIL] create() 返回 None")
        for e in comp.errors():
            print("   ", e.toString())
        sys.exit(1)

    # 等 mainLoader(startupTimer 50ms) + 内部 StackedWidget 建好 + 主页异步加载
    stack = None
    for _ in range(40):
        pump(50)
        sw = win.property("stackedWidget")
        if sw is not None:
            stack = sw
            if eval_on(stack, "_isPageLoaded(0)"):
                break

    if stack is None:
        Path(__file__).with_suffix(".result.txt").write_text(
            "RESULT: ERROR - 等待超时: window.stackedWidget 仍为 None", encoding="utf-8")
        sys.stderr.write("\n>>>RESULT_BEGIN>>>\nstack is None\n<<<RESULT_END<<<\n")
        sys.exit(1)

    failures = []

    if not eval_on(stack, "_isPageLoaded(0)"):
        failures.append("启动后主页(0)未加载完成, 测试前提不成立")

    # 切到页1
    win.setProperty("currentIndex", 1)
    pump(1000)
    if not eval_on(stack, "_isPageLoaded(1)"):
        failures.append("切到页1后页1未加载完成")

    # 核心断言: 切走后主页是否仍 Ready
    home_still_loaded = eval_on(stack, "_isPageLoaded(0)")
    if not home_still_loaded:
        failures.append("切走主页后主页被卸载 → 切回必重新懒加载 (bug 复现)")

    # 切回主页
    win.setProperty("currentIndex", 0)
    pump(600)
    if not eval_on(stack, "_isPageLoaded(0)"):
        failures.append("切回主页结束后主页仍未 Ready")

    lines = [f"切走后主页是否仍Ready(未卸载) = {home_still_loaded}"]
    if failures:
        lines.append("RESULT: FAIL - 真机路径懒加载复现/回归失败")
        for f in failures:
            lines.append("  [FAIL] " + f)
        result = 1
    else:
        lines.append("RESULT: PASS - 真机路径下切走再切回主页未重新懒加载")
        result = 0
    out = "\n".join(lines)
    sys.stderr.write("\n>>>RESULT_BEGIN>>>\n" + out + "\n<<<RESULT_END<<<\n")
    sys.stderr.flush()
    Path(__file__).with_suffix(".result.txt").write_text(out, encoding="utf-8")

    QTimer.singleShot(0, app.quit)
    app.exec()
    sys.exit(result)


if __name__ == "__main__":
    main()
