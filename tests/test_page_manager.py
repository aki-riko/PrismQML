# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Page manager failure-boundary regressions. 页面管理失败边界回归。"""

from types import SimpleNamespace

import pytest
import shiboken6
from PySide6.QtQuick import QQuickItem


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_page_size_signal_process_control_propagates(error_type):
    from prismqml.python.window._page_manager import _emit_page_size_signals

    def stop_emit():
        raise error_type("stop")

    page_item = SimpleNamespace(
        widthChanged=SimpleNamespace(emit=stop_emit),
        heightChanged=SimpleNamespace(emit=lambda: None),
    )
    with pytest.raises(error_type, match="stop"):
        _emit_page_size_signals(page_item)


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_async_page_creation_process_control_propagates(error_type):
    from prismqml.python.window._page_manager import _create_async_page_boundary

    def stop_create():
        raise error_type("stop")

    item = SimpleNamespace(
        page_getter=stop_create,
        page_class=None,
        _page_instance=None,
    )
    with pytest.raises(error_type, match="stop"):
        _create_async_page_boundary(item, lambda _page: None)


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize(
    ("method_name", "args"),
    (
        ("_switch_to_index", (0,)),
        ("_start_async_page_load", (0,)),
        ("_finish_loading", ()),
    ),
)
def test_page_manager_invoke_process_control_propagates(
    monkeypatch, error_type, method_name, args
):
    from prismqml.python.window import _page_manager

    def stop_invoke(*_args):
        raise error_type("stop")

    monkeypatch.setattr(
        _page_manager,
        "QMetaObject",
        SimpleNamespace(invokeMethod=stop_invoke),
    )
    manager = _page_manager.PageManagerMixin()
    manager._window = object()
    with pytest.raises(error_type, match="stop"):
        getattr(manager, method_name)(*args)


def _destroyed_window():
    """返回一个 C++ 对象已被删除的 QQuickWindow 包装器。"""
    from PySide6.QtCore import QCoreApplication, QEvent
    from PySide6.QtQuick import QQuickWindow

    window = QQuickWindow()
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert not shiboken6.isValid(window)
    return window


def _spy_page_ready(monkeypatch):
    """记录真实 invokeMethod 调用与异常日志，不替换被测语义。"""
    from PySide6.QtCore import QMetaObject

    from prismqml.python.window import _page_manager

    calls = []
    errors = []
    real_invoke = QMetaObject.invokeMethod

    def record_invoke(target, method, *args):
        calls.append(method)
        return real_invoke(target, method, *args)

    monkeypatch.setattr(
        _page_manager,
        "QMetaObject",
        SimpleNamespace(invokeMethod=record_invoke),
    )
    monkeypatch.setattr(_page_manager, "exception", errors.append)
    return calls, errors


def test_python_page_ready_skips_window_deleted_during_shutdown(qapp, monkeypatch):
    """退出期窗口已析构：不得对已删除的 C++ 对象 invokeMethod，也不得报错。

    回归 2026-10-20 实测：退出清理在 aboutToQuit 销毁 QML 窗口后，仍排在
    定时器队列里的页面预热任务会继续走到这里。Python 包装器在 C++ 对象被
    删除后依然是真值，``if not self._window`` 挡不住，invokeMethod 抛
    ``libshiboken: Internal C++ object (QQuickWindow) already deleted``。
    """
    from prismqml.python.window import _page_manager

    calls, errors = _spy_page_ready(monkeypatch)
    manager = _page_manager.PageManagerMixin()
    manager._window = _destroyed_window()

    manager._mark_python_page_ready(0)

    assert calls == []
    assert errors == []


def test_python_page_ready_still_notifies_live_window(qapp, monkeypatch):
    """存活窗口必须照常收到就绪通知，守卫不得过度拦截。"""
    from PySide6.QtQuick import QQuickWindow

    from prismqml.python.window import _page_manager

    window = QQuickWindow()
    calls, errors = _spy_page_ready(monkeypatch)
    manager = _page_manager.PageManagerMixin()
    manager._window = window

    manager._mark_python_page_ready(7)

    assert calls == ["_markPythonPageReady"]
    assert errors == []
    window.deleteLater()


def _destroyed_container_tree():
    """返回随窗口一起析构的 (窗口, 页面容器, 页项)，三者 C++ 对象均已删除。"""
    from PySide6.QtCore import QCoreApplication, QEvent
    from PySide6.QtQuick import QQuickItem, QQuickWindow

    window = QQuickWindow()
    container = QQuickItem(window.contentItem())
    container.setObjectName("page_0")
    page_item = QQuickItem(container)
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert not shiboken6.isValid(window)
    assert not shiboken6.isValid(container)
    return window, container, page_item


def test_live_qt_object_keeps_none_and_plain_double_semantics(qapp):
    """守卫必须把 None 判为失效，且不得把普通测试替身误判为已析构。"""
    from prismqml.python.window._page_layout import _live_qt_object

    assert _live_qt_object(None) is None
    # shiboken6.isValid 对非 Qt 对象返回 True，替身必须原样放行。
    live_double = object()
    assert _live_qt_object(live_double) is live_double


def test_async_attach_skips_container_deleted_with_window(qapp, monkeypatch):
    """退出期页面容器/页项随窗口析构：异步挂载不得抛 already deleted。

    回归：``_resolve_async_page_target`` 在窗口存活时解析出容器，窗口随后被
    退出清理销毁，排队的异步建页任务才真正执行挂载。
    """
    from prismqml.python.window import _page_manager

    _, container, _page_item = _destroyed_container_tree()
    errors = []
    monkeypatch.setattr(_page_manager, "exception", errors.append)

    class _Page:
        _prismqml_async_page = False
        _deferred_queue = []

        def __init__(self, qml_item):
            self._qml_item = qml_item
            self._prismqml_layout_item = None

    manager = _page_manager.PageManagerMixin()
    manager._window = _destroyed_window()

    manager._attach_async_page_content(_Page(_page_item), container)

    assert errors == []


def test_async_batch_complete_skips_deleted_page_item(qapp, monkeypatch):
    """退出期批量完成回调不得对已析构页项 setOpacity。"""
    from prismqml.python.window import _page_manager

    _, _container, page_item = _destroyed_container_tree()
    errors = []
    monkeypatch.setattr(_page_manager, "exception", errors.append)

    class _Page:
        _prismqml_async_page = False
        _deferred_queue = []

        def __init__(self, qml_item):
            self._qml_item = qml_item

    manager = _page_manager.PageManagerMixin()
    manager._window = _destroyed_window()
    page = _Page(page_item)
    manager._pages = {0: page}
    manager._mark_python_page_ready = lambda index: None
    manager._mark_page_load_finished = lambda index: None
    manager._finish_loading_and_switch = lambda index: None

    manager._on_async_batch_complete(0, page)

    assert errors == []


def test_page_container_lookup_reuses_cache_until_window_changes(qapp):
    from prismqml.python.window._page_manager import PageManagerMixin

    root = QQuickItem()
    first_page = QQuickItem(root)
    first_page.setObjectName("page_0")

    class Window:
        def __init__(self, content_item):
            self._content_item = content_item

        def contentItem(self):
            return self._content_item

    manager = PageManagerMixin()
    first_window = Window(root)
    manager._window = first_window

    assert manager._find_child_by_name("page_0") is first_page
    assert manager._find_child_by_name("page_0") is first_page

    second_root = QQuickItem()
    second_page = QQuickItem(second_root)
    second_page.setObjectName("page_0")
    manager._window = Window(second_root)
    assert manager._find_child_by_name("page_0") is second_page

    first_page.deleteLater()
    second_page.deleteLater()
    root.deleteLater()
    second_root.deleteLater()
