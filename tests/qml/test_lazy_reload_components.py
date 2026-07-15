# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Headless 懒加载回归测试 — pageSources 冷跳页时序。

覆盖从主页直接跳到尚未加载的页 2：目标 Loader Ready 前，实际显示索引
``_displayIndex`` 必须保持旧页；加载完成后才切换。该脚本保留原历史场景的
第一拍判据，但只使用当前公开的 ``pageSources`` API。

判据:
  1. 启动后主页(0)Ready
  2. 切到未加载的页2: _displayIndex 必须等 page2 Ready 后才变为 2
     (修复前会立刻变 2, 此时 page2 尚未 Ready)
  3. 切走主页后主页仍 Ready（_loadOnce latch 生效，未被卸载）

用法: python scripts/test_process.py --qt-platform offscreen --timeout 180 -- python tests/qml/test_lazy_reload_components.py
退出码: 0=通过, 1=失败
"""
import sys
from pathlib import Path

from _test_process_bootstrap import configure_qml_test_process

configure_qml_test_process()

from PySide6.QtCore import QUrl, QTimer, QEventLoop, QTemporaryDir
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression

PKG_ROOT = Path(__file__).resolve().parents[2] / "prismqml"


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


def create_page_urls():
    temporary = QTemporaryDir()
    if not temporary.isValid():
        raise RuntimeError("无法创建临时页面目录")
    page_urls = []
    for index, color in enumerate(("#ffaaaa", "#aaffaa", "#aaaaff")):
        page_path = Path(temporary.path()) / f"Page{index}.qml"
        page_path.write_text(
            "import QtQuick\n"
            f'Rectangle {{ color: "{color}"; Text {{ text: "page{index}" }} }}\n',
            encoding="utf-8",
        )
        page_urls.append(QUrl.fromLocalFile(str(page_path)).toString())
    return temporary, page_urls


def create_stack(engine, page_urls):
    page_source_lines = ",\n        ".join(f'"{url}"' for url in page_urls)
    qml = f'''
import QtQuick
import PrismQML

StackedWidget {{
    width: 800; height: 600
    lazyLoading: true
    currentIndex: 0
    pageSources: [
        {page_source_lines}
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
        errors = "\n".join(error.toString() for error in comp.errors())
        raise RuntimeError(f"组件加载错误:\n{errors}")
    stack = comp.create()
    if stack is None:
        errors = "\n".join(error.toString() for error in comp.errors())
        raise RuntimeError(f"create() 返回 None:\n{errors}")
    return comp, stack


def validate_start(stack, failures):
    pump(500)
    if not is_loaded(stack, 0):
        failures.append("启动后主页(0)未加载完成, 测试前提不成立")
    if display_index(stack) != 0:
        failures.append(f"启动后 _displayIndex 应为 0, 实际 {display_index(stack)}")


def validate_cold_jump(stack, failures):
    # 第一拍必须保持旧页，Ready 后才切到目标页。
    stack.setProperty("currentIndex", 2)
    pump(1)
    if display_index(stack) == 2:
        failures.append(
            "切到未加载页2的第一拍 _displayIndex 立即变 2(未经 helper 等待) "
            "→ 未加载完就被推上来、旧页被移走 (bug 未修复)")
    pump(1500)
    if not is_loaded(stack, 2):
        failures.append("切到页2后页2未加载完成")
    if display_index(stack) != 2:
        failures.append(f"page2 加载完成后 _displayIndex 应为 2, 实际 {display_index(stack)}")


def validate_return_home(stack, failures):
    stack.setProperty("currentIndex", 0)
    pump(800)
    if display_index(stack) != 0:
        failures.append(f"切回主页后 _displayIndex 应为 0, 实际 {display_index(stack)}")
    if not is_loaded(stack, 0):
        failures.append("切回主页结束后主页仍未 Ready")


def report(failures):
    print(f"\n{'='*60}")
    if failures:
        print("RESULT: FAIL - pageSources 冷跳页懒加载回归测试失败")
        for f in failures:
            print("  [FAIL]", f)
        result = 1
    else:
        print("RESULT: PASS - pageSources 冷跳页等待加载完成, latch 生效")
        result = 0
    print(f"{'='*60}")
    return result


def main():
    app = QApplication(sys.argv)
    engine = QQmlEngine()
    engine.addImportPath(str(PKG_ROOT))
    try:
        temporary, page_urls = create_page_urls()
        component, stack = create_stack(engine, page_urls)
    except RuntimeError as error:
        print(f"[FAIL] {error}")
        return 1

    failures = []
    validate_start(stack, failures)
    validate_cold_jump(stack, failures)
    validate_return_home(stack, failures)
    result = report(failures)

    QTimer.singleShot(0, app.quit)
    app.exec()
    return result


if __name__ == "__main__":
    raise SystemExit(main())
