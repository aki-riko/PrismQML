# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""PrismQML Page Manager - 页面生命周期管理

负责懒加载、页面创建、异步加载等页面管理逻辑。
从 window_core.py 抽取，作为 Mixin 注入 WindowCore。
"""

from functools import partial
import time
from typing import Any, Dict, Optional, Type

from PySide6.QtCore import QTimer, QMetaObject, Q_ARG
from PySide6.QtQuick import QQuickItem

from ..core.logger import debug, exception, warning, info
from ._page_prewarm import PagePrewarmMixin


_PAGE_LOAD_RENDER_DELAY_MS = 16
_PAGE_SIZE_BIND_DELAY_MS = 50
_PAGE_SIZE_RETRY_DELAY_MS = 200
_NO_PAGE_TARGET = object()


def _emit_page_size_signals(page_item: Any) -> None:
    try:
        page_item.widthChanged.emit()
        page_item.heightChanged.emit()
    except Exception as exc:
        exception(f"页面尺寸信号触发失败: {type(exc).__name__}: {exc}")


def _resolve_async_page_instance(item: Any):
    if getattr(item, "page_getter", None):
        return item.page_getter()
    if item.page_class:
        return item.page_class()
    if item._page_instance:
        return item._page_instance
    return None


def _create_async_page_boundary(item: Any, on_page_ready) -> None:
    try:
        on_page_ready(_resolve_async_page_instance(item))
    except Exception as exc:
        exception(f"页面创建失败: {type(exc).__name__}: {exc}")
        on_page_ready(None)


def _make_page_profile(index: int):
    profile_start = time.perf_counter()
    profile_last = profile_start

    def profile(label: str):
        nonlocal profile_last
        now = time.perf_counter()
        debug(
            f"[启动剖析] PageManager._create_page[{index}] {label}: "
            f"+{int((now - profile_last) * 1000)}ms / "
            f"total {int((now - profile_start) * 1000)}ms"
        )
        profile_last = now

    return profile


def _resolve_sync_page_instance(item: Any):
    if item._page_instance is not None:
        return item._page_instance, "existing_instance"
    if getattr(item, "page_getter", None):
        page_instance = item.page_getter()
        item._page_instance = page_instance
        return page_instance, "page_getter"
    if item.page_class:
        page_instance = item.page_class()
        item._page_instance = page_instance
        return page_instance, "page_class"
    return None, None


def _resolve_page_layout_item(page_instance: Any):
    layout_item = getattr(page_instance, "_prismqml_layout_item", None)
    return layout_item if layout_item is not None else page_instance._qml_item


def _make_page_size_binder(
    page_instance: Any, page_container: Any, emit_signals: bool
):
    from shiboken6 import isValid

    def bind_size():
        page_item = _resolve_page_layout_item(page_instance)
        if not isValid(page_item) or not isValid(page_container):
            return
        width = page_container.width()
        height = page_container.height()
        if width > 0 and height > 0:
            page_item.setWidth(width)
            page_item.setHeight(height)
            if emit_signals:
                _emit_page_size_signals(page_item)

    return bind_size


def _connect_page_size_binding(page_container: Any, bind_size, delays) -> None:
    page_container.widthChanged.connect(bind_size)
    page_container.heightChanged.connect(bind_size)
    for delay in delays:
        QTimer.singleShot(delay, bind_size)


def _has_deferred_queue(page_instance: Any):
    return (
        hasattr(page_instance, "_deferred_queue")
        and page_instance._deferred_queue
    )


def _is_managed_async_page(page_instance: Any) -> bool:
    return bool(getattr(page_instance, "_prismqml_async_page", False))


class PageManagerMixin(PagePrewarmMixin):
    """页面管理器 Mixin，提供懒加载和页面生命周期管理"""

    # ==================== 懒加载管理（统一入口） ====================
    # Lazy loading is fully managed by Python side
    # QML side only provides animation and UI rendering
    # 懒加载完全由Python侧管理，QML侧只负责动画和UI渲染

    def _ensure_page_created(self, index: int):
        """确保指定索引的页面已创建（同步）"""
        if not self._admit_page_creation(index):
            return False
        if index not in self._pages:
            return self._create_page(index) is not False
        return True

    def _create_page(self, index: int):
        """创建页面内容"""
        if not self._admit_page_creation(index):
            return False
        profile = _make_page_profile(index)
        item, page_container = self._resolve_sync_page_target(index, profile)
        if item is _NO_PAGE_TARGET:
            return
        page_instance, page_source = _resolve_sync_page_instance(item)
        if page_source is None:
            profile("无页面构建器")
            return
        profile(f"创建页面实例 ({page_source})")
        self._attach_sync_page_content(
            index, page_instance, page_container, profile
        )
        self._finalize_sync_page(index, item, page_instance, profile)

    def _admit_page_creation(self, index: int) -> bool:
        if not self._startup_page_creation_blocked(index):
            return True
        warning(
            f"启动阶段拒绝预建非当前页 index={index}; "
            "请使用 prewarmPage() 排入低优先级队列"
        )
        return False

    def _resolve_sync_page_target(self, index: int, profile):
        all_items = self._nav_items + self._bottom_nav_items
        if index >= len(all_items):
            profile("索引越界")
            return _NO_PAGE_TARGET, None
        item = all_items[index]
        if self._window is None:
            profile("窗口未创建")
            return _NO_PAGE_TARGET, None
        page_container = self._find_child_by_name(f"page_{index}")
        profile("查找页面容器")
        if page_container is None:
            warning(f"未找到页面容器: page_{index}")
            return _NO_PAGE_TARGET, None
        return item, page_container

    def _attach_sync_page_content(
        self, index, page_instance, page_container, profile
    ):
        page_item = _resolve_page_layout_item(page_instance)
        if page_item:
            page_item.setParentItem(page_container)
            profile("setParentItem")
            bind_size = _make_page_size_binder(
                page_instance, page_container, False
            )
            profile("导入 shiboken")
            _connect_page_size_binding(
                page_container, bind_size, (_PAGE_SIZE_BIND_DELAY_MS,)
            )
            profile("绑定尺寸信号")
        else:
            warning(f"[_create_page] page_{index} _qml_item 为 None!")
            profile("_qml_item 为空")

    def _finalize_sync_page(self, index, item, page_instance, profile):
        self._pages[index] = page_instance
        info(f"创建页面: {item.text}")
        profile("登记页面实例")
        if _is_managed_async_page(page_instance):
            self._start_managed_async_page(
                index, item, page_instance, finish_loading=False
            )
            profile("启动异步 QML 页面")
            return
        if _has_deferred_queue(page_instance):
            profile("发现 deferred queue")
            page_instance.startBatchCreation()
            profile("启动 deferred queue")
        else:
            profile("无 deferred queue")
        if _resolve_page_layout_item(page_instance) is not None:
            self._mark_python_page_ready(index)
        if self._is_page_prewarming(index):
            self._finish_page_prewarm(index)
        elif index == getattr(self, "_startup_page_index", None):
            self._complete_startup_page_guard(index)

    def _mark_python_page_ready(self, index: int) -> None:
        """Tell the generated QML stack that a Python page is renderable."""
        if not self._window:
            return
        try:
            QMetaObject.invokeMethod(
                self._window,
                "_markPythonPageReady",
                Q_ARG("QVariant", index),
            )
        except RuntimeError as exc:
            exception(
                "Python 页面就绪通知失败: "
                f"{type(exc).__name__}: {exc}"
            )

    def _find_child_by_name(self, name: str) -> Optional[QQuickItem]:
        """根据objectName查找子项"""
        if self._window is None:
            return None

        def find_recursive(item: QQuickItem) -> Optional[QQuickItem]:
            if item.objectName() == name:
                return item
            for child in item.childItems():
                result = find_recursive(child)
                if result:
                    return result
            return None

        return find_recursive(self._window.contentItem())

    def _on_nav_changed(self, index: int):
        """导航项切换回调（QML触发）"""
        self._current_index = index
        self._discard_page_prewarm(index)

        # Python侧懒加载：页面未创建时异步加载并显示loading
        if self._is_page_prewarming(index):
            self._mark_foreground_page_load_started(index)
            self._start_loading_overlay(index)
        elif self._lazy_loading and index not in self._pages:
            self._start_async_page_load(index)
        else:
            self._switch_to_index(index)

        self.currentIndexChanged.emit(index)

    def _switch_to_index(self, index: int):
        """触发QML侧页面切换"""
        if self._window:
            try:
                QMetaObject.invokeMethod(
                    self._window, "navigateTo", Q_ARG("QVariant", index)
                )
            except RuntimeError as exc:
                exception(f"页面切换失败: {type(exc).__name__}: {exc}")

    def _start_async_page_load(self, index: int):
        """异步加载页面（显示loading动画）

        流程：
        1. 显示QML侧的_pythonLoading覆盖层
        2. 延迟16ms让loading动画先渲染
        3. 创建页面实例
        4. 如果页面有_deferred_queue，启动分批创建
        5. 完成后隐藏loading覆盖层
        """
        self._mark_foreground_page_load_started(index)
        self._start_loading_overlay(index)
        item, page_container = self._resolve_async_page_target(index)
        if item is _NO_PAGE_TARGET:
            self._finish_loading()
            return
        on_page_ready = partial(
            self._on_async_page_ready, index, item, page_container
        )
        self._schedule_async_page_creation(item, on_page_ready)

    def _resolve_async_page_target(self, index: int):
        all_items = self._nav_items + self._bottom_nav_items
        if index >= len(all_items):
            return _NO_PAGE_TARGET, None
        item = all_items[index]
        page_container = self._find_child_by_name(f"page_{index}")
        has_loader = (
            item.page_class is not None
            or getattr(item, "page_getter", None) is not None
            or item._page_instance is not None
        )
        if page_container is None or not has_loader:
            return _NO_PAGE_TARGET, None
        return item, page_container

    def _on_async_page_ready(
        self, index, item, page_container, page_instance
    ):
        if page_instance is None:
            self._finish_loading()
            return
        item._page_instance = page_instance
        self._attach_async_page_content(page_instance, page_container)
        self._finalize_async_page(index, item, page_instance)

    def _attach_async_page_content(self, page_instance, page_container):
        page_item = _resolve_page_layout_item(page_instance)
        if not page_item:
            return
        page_item.setParentItem(page_container)
        bind_size = _make_page_size_binder(page_instance, page_container, True)
        _connect_page_size_binding(
            page_container,
            bind_size,
            (_PAGE_SIZE_BIND_DELAY_MS, _PAGE_SIZE_RETRY_DELAY_MS),
        )
        if _has_deferred_queue(page_instance):
            page_instance._qml_item.setOpacity(0)

    def _finalize_async_page(self, index, item, page_instance):
        self._pages[index] = page_instance
        info(f"异步创建页面: {item.text}")
        if _is_managed_async_page(page_instance):
            self._start_managed_async_page(index, item, page_instance)
            return
        if _has_deferred_queue(page_instance):
            on_complete = partial(
                self._on_async_batch_complete, index, page_instance
            )
            page_instance.startBatchCreation(on_complete=on_complete)
            return
        self._mark_python_page_ready(index)
        self._finish_loading_and_switch(index)

    def _start_managed_async_page(
        self, index, item, page_instance, *, finish_loading=True
    ):
        on_ready, on_failed = self._managed_page_callbacks(
            index, item, page_instance, finish_loading
        )
        page_instance.page_ready.connect(on_ready)
        page_instance.page_failed.connect(on_failed)
        try:
            page_instance.start_loading()
        except Exception as exc:
            exception(
                "异步 QML 页面启动失败: "
                f"{type(exc).__name__}: {exc}"
            )
            if self._is_page_prewarming(index):
                self._on_prewarm_managed_page_failed(
                    index, item, page_instance, str(exc)
                )
            else:
                self._on_managed_page_failed(index, item, page_instance, str(exc))

    def _on_managed_async_page_ready(self, index):
        self._mark_python_page_ready(index)
        self._finish_loading_and_switch(index)

    def _on_initial_managed_async_page_ready(self, index):
        self._mark_python_page_ready(index)
        self._complete_startup_page_guard(index)

    def _managed_page_callbacks(self, index, item, page_instance, finish_loading):
        if self._is_page_prewarming(index):
            return (
                partial(self._on_prewarm_managed_page_ready, index),
                partial(
                    self._on_prewarm_managed_page_failed,
                    index,
                    item,
                    page_instance,
                ),
            )
        if finish_loading:
            return (
                partial(self._on_managed_async_page_ready, index),
                partial(self._on_managed_page_failed, index, item, page_instance),
            )
        return (
            partial(self._on_initial_managed_async_page_ready, index),
            partial(self._on_managed_page_failed, index, item, page_instance),
        )

    def _on_managed_page_failed(self, index, item, page_instance, message):
        warning(f"异步 QML 页面加载失败: {message}")
        self._clear_managed_page(index, item, page_instance)
        self._complete_startup_page_guard(index)
        self._finish_loading()

    def _clear_managed_page(self, index, item, page_instance):
        if self._pages.get(index) is page_instance:
            self._pages.pop(index)
        if item._page_instance is page_instance:
            item._page_instance = None

    def _on_prewarm_managed_page_ready(self, index):
        self._mark_python_page_ready(index)
        promoted = self._foreground_page_load_index == index
        self._finish_page_prewarm(index)
        if promoted:
            self._finish_loading_and_switch(index)

    def _on_prewarm_managed_page_failed(self, index, item, page_instance, message):
        warning(f"异步 QML 页面预热失败: {message}")
        self._clear_managed_page(index, item, page_instance)
        promoted = self._foreground_page_load_index == index
        self._finish_page_prewarm(index)
        if promoted:
            self._finish_loading()

    def _on_async_batch_complete(self, index, page_instance):
        if page_instance._qml_item:
            page_instance._qml_item.setOpacity(1)
        self._mark_python_page_ready(index)
        self._finish_loading_and_switch(index)

    def _schedule_async_page_creation(self, item, on_page_ready):
        create_page = partial(_create_async_page_boundary, item, on_page_ready)
        QTimer.singleShot(_PAGE_LOAD_RENDER_DELAY_MS, create_page)

    def _start_loading_overlay(self, index: int) -> None:
        if not self._window:
            return
        try:
            QMetaObject.invokeMethod(
                self._window, "_startPythonLoading", Q_ARG("QVariant", index)
            )
        except RuntimeError as exc:
            exception(
                "页面 loading 启动方法不可用: "
                f"{type(exc).__name__}: {exc}"
            )

    def _finish_loading_and_switch(self, index: int):
        """完成加载并切换到目标页面"""
        self._finish_loading()
        self._switch_to_index(index)

    def _finish_loading(self):
        """完成加载，隐藏loading动画"""
        self._mark_foreground_page_load_finished()
        if self._window:
            try:
                QMetaObject.invokeMethod(self._window, "_finishPythonLoading")
            except RuntimeError as exc:
                # Method may not exist, ignore 方法可能不存在
                exception(
                    "页面 loading 结束方法不可用: "
                    f"{type(exc).__name__}: {exc}"
                )
