# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Real QML-owned Splash configuration regressions. QML 持有的启动画面配置回归。"""

import os
import sys
from pathlib import Path

os.environ["QML_DISABLE_DISK_CACHE"] = "1"
os.environ.pop("QML_FORCE_DISK_CACHE", None)

from _test_process_bootstrap import configure_qml_test_process

configure_qml_test_process()

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer
from PySide6.QtWidgets import QApplication


def pump(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def _dispose_window(window):
    qml_window = getattr(window, "_window", None)
    if qml_window is not None and shiboken6.isValid(qml_window):
        qml_window.setProperty("visible", False)
        qml_window.deleteLater()
        QCoreApplication.sendPostedEvents(qml_window, QEvent.DeferredDelete)
    window._window = None
    QApplication.processEvents()


def main():
    app = QApplication.instance() or QApplication(sys.argv)

    from prismqml import Window, WindowType

    window = Window(window_type=WindowType.BAR)
    window.resize(1111, 777)
    window.addPage(None, "Home", "Home")
    window.showSplash("/icons/splash.svg", 'Title "quoted" {brace}\nline', "Loading")
    try:
        window.show()
        pump(120)
        root = window._window
        splash = root.property("_splashInstance")
        loader = root.findChild(QObject, "windowSplashLoader")
        assert splash is not None
        assert loader is not None
        assert not hasattr(window, "_splash_instance")
        assert splash.property("iconSource").endswith("/icons/splash.svg")
        assert splash.property("title") == 'Title "quoted" {brace}\nline'
        assert splash.property("subtitle") == "Loading"
        assert splash.findChild(QObject, "splashProgressRing") is not None
        assert splash.parentItem() == loader
        assert loader.parentItem() == root.contentItem()
        assert splash.property("width") == 1111
        assert splash.property("height") == 777
    finally:
        _dispose_window(window)

    assert app is QApplication.instance()
    return 0


if __name__ == "__main__":
    sys.exit(main())
