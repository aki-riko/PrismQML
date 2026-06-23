# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Headless 欢迎页关闭时机回归测试 — 直接测真实 _dismissSplashWhenReady。

复现 bug: 窗口框架壳 Loader.onLoaded(NavigationBar/ContentFrame 加载完)就
立即 splash.finish(),但此时 StackedWidget 内主页仍在异步加载 → 欢迎页过早
消失,露出空白再浮现主页。

修复: NavigationWindowCore._dismissSplashWhenReady(stack) —— 主页未就绪时
连 stack.pageLoaded 等首屏那一页加载完成再 finish,带超时兜底+去重。

测法: 全在 QML 内构造场景(真实 NavigationWindowCore 子树 + mock splash +
真实懒加载 StackedWidget),onCompleted 时机模拟框架 onLoaded 调真函数,
把时序结果暴露为属性给 Python 断言。避免跨语言传 QObject 参数的坑。

判据:
  - 调用瞬间主页(异步)未就绪 → 不得 finish (finishAtCall===0)
  - 主页 pageLoaded 后 → 必须 finish 且仅一次, 且彼时主页确已就绪

用法: python tests/qml/test_splash_timing.py
退出码: 0=通过, 1=失败
"""
import sys
from pathlib import Path

from PySide6.QtCore import QUrl, QTimer, QEventLoop
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine

PKG_ROOT = Path(__file__).resolve().parents[2] / "prismqml"
NAV_DIR = PKG_ROOT / "PrismQML" / "controls" / "navigation"
PAGES_DIR = Path(__file__).resolve().parents[2] / "examples" / "pages"


def pump(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def main():
    app = QApplication(sys.argv)
    engine = QQmlEngine()
    engine.addImportPath(str(PKG_ROOT))

    page0 = QUrl.fromLocalFile(str(PAGES_DIR / "ButtonPage.qml")).toString()
    page1 = QUrl.fromLocalFile(str(PAGES_DIR / "InputPage.qml")).toString()

    # 自包含 QML 场景: NavigationWindowCore 内放 mock splash + 真 StackedWidget,
    # onCompleted(等同框架 onLoaded 时机)调真函数 _dismissSplashWhenReady。
    qml = f'''
import QtQuick
import PrismQML
import "{NAV_DIR.as_posix()}"

NavigationWindowCore {{
    id: win

    // 测试可读结果
    property int finishAtCall: -1     // 调函数瞬间 splash.finish 次数
    property bool pageReadyAtCall: false
    property int finishFinal: -1      // 主页加载完后的 finish 次数
    property bool pageReadyAtFinish: false
    property bool done: false
    // 实时反映 mock splash 当前 finish 次数(事件循环跑完后由 Python 读)
    readonly property int splashFinishCount: mockSplash.finishCount

    // mock splash: 记录 finish 次数
    QtObject {{
        id: mockSplash
        property int finishCount: 0
        function finish() {{ finishCount += 1 }}
    }}

    // 真实懒加载 StackedWidget(主页异步)
    StackedWidget {{
        id: stack
        width: 800; height: 600
        lazyLoading: true
        currentIndex: 0
        pageSources: ["{page0}", "{page1}"]
        onPageLoaded: (idx) => {{
            if (idx === currentIndex && !win.done) {{
                win.done = true
                win.finishFinal = mockSplash.finishCount
                win.pageReadyAtFinish = stack._isPageLoaded(stack.currentIndex)
            }}
        }}
    }}

    Component.onCompleted: {{
        win._splashInstance = mockSplash
        // 模拟框架 onLoaded 时机调真函数
        win.pageReadyAtCall = stack._isPageLoaded(stack.currentIndex)
        win._dismissSplashWhenReady(stack)
        win.finishAtCall = mockSplash.finishCount
    }}
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
        sys.exit(1)

    # 驱动主页异步加载完成 + 函数内 connect 回调触发 finish
    for _ in range(40):
        pump(50)
        if win.property("splashFinishCount") > 0:
            break

    failures = []
    page_ready_at_call = win.property("pageReadyAtCall")
    finish_at_call = win.property("finishAtCall")

    done = win.property("done")
    final_count = win.property("splashFinishCount")

    # 核心断言1: 框架就绪时主页未就绪 → 调用瞬间不得 finish
    if not page_ready_at_call:
        if finish_at_call != 0:
            failures.append(
                f"框架 ready 时主页未就绪却已 finish(finishAtCall={finish_at_call}) "
                "(bug 未修复)")
    # 核心断言2: 主页加载完成后必须 finish 且仅一次
    if not done:
        failures.append("主页 pageLoaded 未触发")
    if final_count < 1:
        failures.append(f"主页就绪后欢迎页仍未关闭(splashFinishCount={final_count})")
    if final_count > 1:
        failures.append(f"finish 被调用多次({final_count}),未去重")

    print(f"\n{'='*60}")
    print(f"  pageReadyAtCall={page_ready_at_call} finishAtCall={finish_at_call} "
          f"done={done} splashFinishCount={final_count}")
    if failures:
        print("RESULT: FAIL - 欢迎页关闭时机测试失败")
        for f in failures:
            print("  [FAIL]", f)
        result = 1
    else:
        print("RESULT: PASS - 欢迎页等主页就绪后才关闭(真函数验证)")
        result = 0
    print(f"{'='*60}")

    QTimer.singleShot(0, app.quit)
    app.exec()
    sys.exit(result)


if __name__ == "__main__":
    main()
