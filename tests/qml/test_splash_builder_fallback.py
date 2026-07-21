# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Real public SplashScreen loading regressions. 公共启动画面直载回归。"""

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


def _delete_qobject(obj):
    if obj is None or not shiboken6.isValid(obj):
        return
    obj.deleteLater()
    QCoreApplication.sendPostedEvents(obj, QEvent.DeferredDelete)
    assert not shiboken6.isValid(obj)


def _dispose_window(window):
    qml_window = getattr(window, "_window", None)
    splash = getattr(window, "_splash_instance", None)
    component = getattr(window, "_splash_component", None)
    if qml_window is not None and shiboken6.isValid(qml_window):
        qml_window.setProperty("_splashInstance", None)
        qml_window.setProperty("visible", False)
    if splash is not None and shiboken6.isValid(splash):
        splash.setParentItem(None)
    _delete_qobject(splash)
    _delete_qobject(component)
    _delete_qobject(qml_window)
    window._splash_instance = None
    window._splash_component = None
    window._window = None
    QApplication.processEvents()


def _new_window(window_type, window_class):
    window = window_class(window_type=window_type)
    window.addPage(None, "Home", "Home")
    return window


def _exercise_public_component_mount():
    from prismqml import Window, WindowType

    window = _new_window(WindowType.BAR, Window)
    window.resize(1111, 777)
    window.showSplash(":/icons/splash.svg", 'Title "quoted" {brace}\nline', "Loading")
    try:
        window.show()
        pump(120)
        splash = window._window.property("_splashInstance")
        assert splash is window._splash_instance
        assert window._splash_component is not None
        assert splash.property("iconSource") == "qrc:/icons/splash.svg"
        assert splash.property("title") == 'Title "quoted" {brace}\nline'
        assert splash.property("subtitle") == "Loading"
        assert splash.findChild(QObject, "splashProgressRing") is not None
        assert splash.parentItem() == window._window.contentItem()
        assert splash.width() == 1111
        assert splash.height() == 777
    finally:
        _dispose_window(window)


def _exercise_deleted_window_mount_failure():
    from prismqml import Window, WindowType

    window = _new_window(WindowType.BAR, Window)
    window.setSplashEnabled(False)
    try:
        window.show()
        pump(60)
        qml_window = window._window
        qml_window.deleteLater()
        QCoreApplication.sendPostedEvents(qml_window, QEvent.DeferredDelete)
        QApplication.processEvents()
        assert not shiboken6.isValid(qml_window)

        window.setSplashEnabled(True)
        window._create_splash()
        assert window._splash_instance is None
    finally:
        _dispose_window(window)


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    _exercise_public_component_mount()
    _exercise_deleted_window_mount_failure()
    assert app is QApplication.instance()
    return 0


if __name__ == "__main__":
    sys.exit(main())
