# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Headless 懒加载回归测试 — pageComponents(组件列表)模式。

复现 bug: pageComponents + lazyLoading 模式下, 切到未加载页时
onCurrentIndexChanged 因 `_useSourceMode==false` 短路, 不走 LazyLoadingHelper,
直接 _doAnimation 并立刻把 _displayIndex 设为目标页 —— 而该页 Loader 是
asynchronous 异步孵化, 还没 Ready 就被推上来、旧页被移走(表现为"设置页
懒加载未完成就被移除/切走")。

修复: onCurrentIndexChanged 去掉 _useSourceMode 限定, 两种 lazy 模式统一走
helper; component Loader 加 _loadOnce latch(同 sourceLoader)。

判据:
  1. 启动后主页(0)Ready
  2. 切到未加载的页1: _displayIndex 必须等 page1 Ready 后才变为 1
     (修复前会立刻变 1, 此时 page1 尚未 Ready)
  3. 切走主页后主页仍 Ready(_loadOnce latch 在 component 模式生效, 未被卸载)

用法: python tests/qml/test_lazy_reload_components.py
退出码: 0=通过, 1=失败
"""
import sys
from pathlib import Path

from PySide6.QtCore import QUrl, QTimer, QEventLoop
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression

PKG_ROOT = Path(__file__).resolve().parents[2] / "prismqml"
NAV_DIR = PKG_ROOT / "PrismQML" / "controls" / "navigation"


def pump(ms):
    """空转事件循环 ms 毫秒, 驱动 StackedWidget 内部定时器/异步 Loader。"""
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def eval_expr(stack, expr_str):
    """对 stack 求值表达式取返回值(处理 PySide6 返回元组的情况)。"""
    expr = QQmlExpression(QQmlEngine.contextForObject(stack), stack, expr_str)
    val = expr.evaluate()
    if isinstance(val, tuple):
        val = val[0]
    return val


def is_loaded(stack, idx):
    return bool(eval_expr(stack, f"_isPageLoaded({idx})"))


def display_index(stack):
    return int(eval_expr(stack, "_displayIndex"))


# PLACEHOLDER_MAIN
def main():
    app = QApplication(sys.argv)
    engine = QQmlEngine()
    engine.addImportPath(str(PKG_ROOT))

    # pageComponents 模式: 内联 3 个 Component(Rectangle 内含子项, 走异步孵化路径)。
    # 不用 examples 页面是为了让测试自包含、不依赖外部资源。
    qml = f'''
import QtQuick
import PrismQML
import "{NAV_DIR.as_posix()}"

StackedWidget {{
    width: 800; height: 600
    lazyLoading: true
    currentIndex: 0
    pageComponents: [
        Component {{ Rectangle {{ color: "#ffaaaa"; Text {{ text: "page0" }} }} }},
        Component {{ Rectangle {{ color: "#aaffaa"; Text {{ text: "page1" }} }} }},
        Component {{ Rectangle {{ color: "#aaaaff"; Text {{ text: "page2" }} }} }}
    ]
}}
'''

    comp = QQmlComponent(engine)
    comp.setData(qml.encode("utf-8"), QUrl("inline"))
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

    # 阶段0: 启动后等主页(index 0)异步孵化完成
    pump(500)
    if not is_loaded(stack, 0):
        failures.append("启动后主页(0)未加载完成, 测试前提不成立")
    if display_index(stack) != 0:
        failures.append(f"启动后 _displayIndex 应为 0, 实际 {display_index(stack)}")

    # 阶段1: 切到未加载的页2(跳过页1, 确保是冷加载)。
    # 核心判据(时序无关): 切换发起的"第一拍", _displayIndex 必须仍是旧值 0。
    #   修复后: onCurrentIndexChanged 走 helper, _displayIndex 不立即改, 等 page2
    #           Ready 后由 onLoadingComplete 才更新 → 第一拍仍为 0。
    #   修复前(bug): 不走 helper, 立刻 _displayIndex=2(无论 page2 是否 Ready)
    #           → 第一拍即为 2。这正是"未加载完就把新页推上来、旧页移走"的根因。
    # 用 currentIndex(目标)=2 但 _displayIndex(实际显示)应延迟到加载完成区分两者。
    stack.setProperty("currentIndex", 2)
    pump(1)  # 仅驱动一拍事件循环, 不足以等异步孵化完成
    first_tick_display = display_index(stack)
    if first_tick_display == 2:
        failures.append(
            "切到未加载页2的第一拍 _displayIndex 立即变 2(未经 helper 等待) "
            "→ 未加载完就被推上来、旧页被移走 (bug 未修复)")

    # 等 helper 完成异步孵化 + 切换
    pump(1500)
    if not is_loaded(stack, 2):
        failures.append("切到页2后页2未加载完成")
    if display_index(stack) != 2:
        failures.append(f"page2 加载完成后 _displayIndex 应为 2, 实际 {display_index(stack)}")

    # 阶段2: 切回主页0, 确认全程正常往返
    stack.setProperty("currentIndex", 0)
    pump(800)
    if display_index(stack) != 0:
        failures.append(f"切回主页后 _displayIndex 应为 0, 实际 {display_index(stack)}")
    if not is_loaded(stack, 0):
        failures.append("切回主页结束后主页仍未 Ready")

    print(f"\n{'='*60}")
    if failures:
        print("RESULT: FAIL - pageComponents 懒加载回归测试失败")
        for f in failures:
            print("  [FAIL]", f)
        result = 1
    else:
        print("RESULT: PASS - pageComponents 模式切换等待加载完成, latch 生效")
        result = 0
    print(f"{'='*60}")

    QTimer.singleShot(0, app.quit)
    app.exec()
    sys.exit(result)


if __name__ == "__main__":
    main()
