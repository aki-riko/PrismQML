# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Managed asynchronous page lifecycle. 受管异步页面生命周期。"""

from functools import partial


class ManagedPageLifecycleMixin:
    """Coordinate managed page completion and failure callbacks."""

    def _start_managed_async_page(
        self, index, item, page_instance, *, finish_loading=True
    ):
        self._mark_page_load_started(index)
        on_ready, on_failed = self._managed_page_callbacks(
            index, item, page_instance, finish_loading
        )
        page_instance.page_ready.connect(on_ready)
        page_instance.page_failed.connect(on_failed)
        try:
            page_instance.start_loading()
        except Exception as exc:
            self._log_managed_page_exception(
                "异步 QML 页面启动失败: "
                f"{type(exc).__name__}: {exc}"
            )
            self._handle_managed_page_start_failure(
                index, item, page_instance, finish_loading, str(exc)
            )

    def _handle_managed_page_start_failure(
        self, index, item, page_instance, finish_loading, message
    ):
        if self._is_page_prewarming(index):
            self._on_prewarm_managed_page_failed(
                index, item, page_instance, message
            )
        elif not finish_loading:
            self._on_initial_managed_page_failed(
                index, item, page_instance, message
            )
        else:
            self._on_managed_page_failed(
                index, item, page_instance, message
            )

    def _on_managed_async_page_ready(self, index, page_instance):
        if self._pages.get(index) is not page_instance:
            return
        self._mark_python_page_ready(index)
        self._mark_page_load_finished(index)
        self._finish_loading_and_switch(index)

    def _on_initial_managed_async_page_ready(self, index, page_instance):
        if self._pages.get(index) is not page_instance:
            return
        self._mark_python_page_ready(index)
        self._mark_page_load_finished(index)
        self._complete_startup_page_guard(index)

    def _managed_page_callbacks(self, index, item, page_instance, finish_loading):
        if self._is_page_prewarming(index):
            return self._prewarm_managed_page_callbacks(
                index, item, page_instance
            )
        if finish_loading:
            return self._foreground_managed_page_callbacks(
                index, item, page_instance
            )
        return self._initial_managed_page_callbacks(
            index, item, page_instance
        )

    def _prewarm_managed_page_callbacks(self, index, item, page_instance):
        return (
            partial(
                self._on_prewarm_managed_page_ready,
                index,
                page_instance,
            ),
            partial(
                self._on_prewarm_managed_page_failed,
                index,
                item,
                page_instance,
            ),
        )

    def _foreground_managed_page_callbacks(self, index, item, page_instance):
        return (
            partial(
                self._on_managed_async_page_ready,
                index,
                page_instance,
            ),
            partial(
                self._on_managed_page_failed,
                index,
                item,
                page_instance,
            ),
        )

    def _initial_managed_page_callbacks(self, index, item, page_instance):
        return (
            partial(
                self._on_initial_managed_async_page_ready,
                index,
                page_instance,
            ),
            partial(
                self._on_initial_managed_page_failed,
                index,
                item,
                page_instance,
            ),
        )

    def _on_managed_page_failed(self, index, item, page_instance, message):
        self._log_managed_page_warning(f"异步 QML 页面加载失败: {message}")
        self._clear_managed_page(index, item, page_instance)
        self._mark_page_load_finished(index)
        self._complete_startup_page_guard(index)
        if self._is_active_foreground_target(index):
            self._finish_loading()

    def _on_initial_managed_page_failed(
        self, index, item, page_instance, message
    ):
        self._log_managed_page_warning(f"异步 QML 页面加载失败: {message}")
        self._clear_managed_page(index, item, page_instance)
        self._mark_page_load_finished(index)
        self._complete_startup_page_guard(index)
        self._finish_loading()

    def _clear_managed_page(self, index, item, page_instance):
        if self._pages.get(index) is page_instance:
            self._pages.pop(index)
        if item._page_instance is page_instance:
            item._page_instance = None

    def _on_prewarm_managed_page_ready(self, index, page_instance):
        if self._pages.get(index) is not page_instance:
            return
        self._mark_python_page_ready(index)
        self._mark_page_load_finished(index)
        promoted = self._foreground_page_load_index == index
        self._finish_page_prewarm(index)
        if promoted:
            self._finish_loading_and_switch(index)

    def _on_prewarm_managed_page_failed(
        self, index, item, page_instance, message
    ):
        self._log_managed_page_warning(f"异步 QML 页面预热失败: {message}")
        self._clear_managed_page(index, item, page_instance)
        self._mark_page_load_finished(index)
        promoted = self._foreground_page_load_index == index
        self._finish_page_prewarm(index)
        if promoted and self._is_active_foreground_target(index):
            self._finish_loading()
