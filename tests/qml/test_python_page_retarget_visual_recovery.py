# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Python page retarget visual recovery. Python 页面重定向视觉复位回归。

Navigating back to an already loaded page while a lazy target is still in flight
must leave exactly the displayed page visible: the collapse mask has to be
released and no abandoned target may stay on screen.
懒加载目标仍在飞行中时切回已加载页，必须只剩当前显示页可见：收紧遮罩要复位，
被放弃的目标不得留在屏幕上。
"""

import sys
import tempfile
from pathlib import Path

from _test_process_bootstrap import configure_qml_test_process

configure_qml_test_process()

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QTimer,
    Signal,
)
from PySide6.QtQuick import QQuickItem
from PySide6.QtWidgets import QApplication


class _ManagedPage(QObject):
    page_ready = Signal()
    page_failed = Signal(str)
    _prismqml_async_page = True

    def __init__(self):
        super().__init__()
        self._qml_item = QQuickItem()
        self._deferred_queue = []

    def start_loading(self):
        return None


class _PlainPage:
    def __init__(self):
        self._qml_item = QQuickItem()
        self._deferred_queue = []


def pump(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def wait_for(predicate, timeout_ms=3000):
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        pump(20)
        elapsed += 20
    return predicate()


def _dispose_window(window):
    qml_window = getattr(window, "_window", None)
    if qml_window is not None and shiboken6.isValid(qml_window):
        qml_window.setProperty("visible", False)
        qml_window.deleteLater()
        QCoreApplication.sendPostedEvents(qml_window, QEvent.DeferredDelete)
    window._window = None
    QApplication.processEvents()


def _visible_page_indexes(stack):
    container = stack.property("containerItem")
    children = container.childItems() if container is not None else []
    return [index for index, child in enumerate(children) if child.isVisible()]


def _click_navigation(window, index):
    """Mirror a real navigation click: QML writes currentIndex, then Python reacts.

    复刻真实导航点击：QML 先同步写 currentIndex，Python 随后响应。
    """
    window._window.setProperty("currentIndex", index)
    window._on_nav_changed(index)


def _exercise_retarget_recovery(temp_dir, prefix, ready_before_click):
    from prismqml import Window, WindowType

    class IsolatedWindow(Window):
        _GENERATED_QML_CACHE_DIR = Path(temp_dir) / f"{prefix}-windows"

    target_page = _ManagedPage()
    window = IsolatedWindow(window_type=WindowType.BAR)
    window.setSplashEnabled(False)
    window.setLazyLoading(True)
    window.addPage(lambda: _PlainPage(), "Home", "Home")
    window.addPage(lambda: target_page, "Target", "Target")
    try:
        window.show()
        pump(200)
        qml_window = window._window
        stack = qml_window.property("stackedWidget")
        assert _visible_page_indexes(stack) == [0]

        _click_navigation(window, 1)
        assert wait_for(lambda: 1 in window._pages)
        assert wait_for(
            lambda: qml_window.property("_pythonLazyCollapseComplete") is True
        )
        # The collapse hides the previously displayed page. 收紧阶段隐藏原显示页。
        assert _visible_page_indexes(stack) == []

        if ready_before_click:
            target_page.page_ready.emit()
            _click_navigation(window, 0)
        else:
            _click_navigation(window, 0)
            target_page.page_ready.emit()

        transition = stack.findChild(QObject, "lazyPageCircleTransition")
        assert transition is not None
        # Let any in-flight reveal settle before judging the final visual state.
        # 判定最终视觉状态前，先等在飞的揭幕动画结束。
        assert wait_for(
            lambda: transition.property("active") is False
            and transition.property("running") is False
        )
        assert wait_for(lambda: _visible_page_indexes(stack) == [0]), (
            f"ready_before_click={ready_before_click} left "
            f"visible={_visible_page_indexes(stack)}"
        )
        pump(400)

        assert transition.property("collapsed") is False
        assert stack.property("_pythonLazyTransitionTargetIndex") == -1
        assert stack.property("_displayIndex") == 0
        assert qml_window.property("_pythonPendingIndex") == -1
        assert qml_window.property("_pythonLoading") is False
        assert window._foreground_page_load_index is None
        assert _visible_page_indexes(stack) == [0]
    finally:
        _dispose_window(window)


def _exercise_uninterrupted_switch_still_reveals(temp_dir):
    """Guard the normal path: an undisturbed switch must show the target.

    守住正常路径：未被打断的切换必须显示目标页。
    """
    from prismqml import Window, WindowType

    class IsolatedWindow(Window):
        _GENERATED_QML_CACHE_DIR = Path(temp_dir) / "baseline-windows"

    target_page = _ManagedPage()
    window = IsolatedWindow(window_type=WindowType.BAR)
    window.setSplashEnabled(False)
    window.setLazyLoading(True)
    window.addPage(lambda: _PlainPage(), "Home", "Home")
    window.addPage(lambda: target_page, "Target", "Target")
    try:
        window.show()
        pump(200)
        qml_window = window._window
        stack = qml_window.property("stackedWidget")

        _click_navigation(window, 1)
        assert wait_for(lambda: 1 in window._pages)
        target_page.page_ready.emit()

        assert wait_for(lambda: _visible_page_indexes(stack) == [1])
        assert wait_for(lambda: qml_window.property("_pythonLoading") is False)
        assert stack.property("_displayIndex") == 1
        assert stack.property("_pythonLazyTransitionTargetIndex") == -1
        assert qml_window.property("_pythonPendingIndex") == -1
    finally:
        _dispose_window(window)


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    with tempfile.TemporaryDirectory() as temp_dir:
        _exercise_retarget_recovery(temp_dir, "click-first", ready_before_click=False)
        _exercise_retarget_recovery(temp_dir, "ready-first", ready_before_click=True)
        _exercise_uninterrupted_switch_still_reveals(temp_dir)
    assert app is QApplication.instance()
    return 0


if __name__ == "__main__":
    sys.exit(main())
