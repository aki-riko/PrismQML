# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
"""Splash 默认挂载回归 — 验证 Window 默认创建启动画面并可关闭。

背景: PrismQML 框架(NavigationWindowCore)早有 _splashInstance + 首屏就绪
自动 finish 的机制,但 Python 端 WindowCore 从不创建 splash 实例,导致默认
窗口从未显示启动画面。本测试锁定"默认即挂载"这一行为。

判据:
  - 默认 Window(BAR) show 后,QML 根对象 _splashInstance 非 null,且
    Python 侧 self._splash_instance 持有引用(防 GC)。
  - setSplashEnabled(False) 后,根对象 _splashInstance 为 null。

用法: <venv>/python tests/qml/test_splash_default_mount.py
退出码: 0=通过, 1=失败
"""
import os
import sys
from pathlib import Path

# headless 离屏渲染,无需真实显示器
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PySide6.QtCore import QTimer, QEventLoop
from PySide6.QtWidgets import QApplication


def pump(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def main():
    app = QApplication.instance() or QApplication(sys.argv)

    from prismqml import Window, WindowType

    failures = []

    # --- 场景1: 默认开启 ---
    win = Window(window_type=WindowType.BAR)
    win.setWindowTitle("Splash 测试")
    win.addPage(None, "Home", "主页")
    win.show()
    pump(100)

    splash_qml = win._window.property("_splashInstance") if win._window else None
    if splash_qml is None:
        failures.append("默认窗口 _splashInstance 为 null(splash 未挂载)")
    if win._splash_instance is None:
        failures.append("Python 侧 _splash_instance 未持有引用(GC 风险)")

    # --- 场景2: 显式关闭 ---
    win2 = Window(window_type=WindowType.BAR)
    win2.setWindowTitle("Splash 关闭测试")
    win2.setSplashEnabled(False)
    win2.addPage(None, "Home", "主页")
    win2.show()
    pump(100)

    splash_qml2 = win2._window.property("_splashInstance") if win2._window else None
    if splash_qml2 is not None:
        failures.append("setSplashEnabled(False) 后 _splashInstance 仍非 null")
    if win2._splash_instance is not None:
        failures.append("setSplashEnabled(False) 后 Python 侧仍持有 splash 引用")

    print(f"\n{'=' * 60}")
    print(f"  默认挂载: qml={splash_qml is not None} py={win._splash_instance is not None}")
    print(f"  显式关闭: qml={splash_qml2 is not None} py={win2._splash_instance is not None}")
    if failures:
        print("RESULT: FAIL - splash 默认挂载测试失败")
        for f in failures:
            print("  [FAIL]", f)
        result = 1
    else:
        print("RESULT: PASS - splash 默认挂载/可关闭均正确")
        result = 0
    print(f"{'=' * 60}")

    # offscreen 平台下 QApplication 全局析构可能段错误(平台插件噪音),
    # 用 flush + os._exit 绕过 Qt 清理,保证退出码可靠供 CI 判定。
    sys.stdout.flush()
    os._exit(result)


if __name__ == "__main__":
    main()
