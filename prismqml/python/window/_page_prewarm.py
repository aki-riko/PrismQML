# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Low-priority page prewarming. 低优先级页面预热。"""

from typing import Any, Optional

from PySide6.QtCore import QTimer

from ..core.logger import exception


_PAGE_PREWARM_DELAY_MS = 250


def initialize_page_prewarm_state(owner: Any) -> None:
    """Initialize startup guard and prewarm queue state. 初始化启动保护与预热队列。"""
    owner._startup_page_guard_active = False
    owner._startup_page_index = 0
    owner._page_prewarm_queue = []
    owner._page_prewarm_scheduled = False
    owner._page_prewarm_in_flight = None
    owner._foreground_page_load_index = None


class PagePrewarmMixin:
    """Admission guard and idle scheduler for non-current pages."""

    def _begin_startup_page_guard(self) -> None:
        if not self._lazy_loading:
            return
        self._startup_page_guard_active = True
        self._startup_page_index = self._current_index

    def _startup_page_creation_blocked(self, index: int) -> bool:
        return bool(
            self._lazy_loading
            and getattr(self, "_startup_page_guard_active", False)
            and index != self._startup_page_index
        )

    def _complete_startup_page_guard(self, index: Optional[int] = None) -> None:
        if not getattr(self, "_startup_page_guard_active", False):
            return
        if index is not None and index != self._startup_page_index:
            return
        self._startup_page_guard_active = False
        self._schedule_page_prewarm()

    def _complete_startup_page_guard_if_ready(self) -> None:
        if self._startup_page_is_ready():
            self._complete_startup_page_guard()

    def _startup_page_is_ready(self) -> bool:
        page = self._pages.get(getattr(self, "_startup_page_index", 0))
        if page is None:
            return False
        if getattr(page, "_prismqml_async_page", False):
            return bool(getattr(page, "is_ready", False))
        return True

    def prewarmPage(self, index: int) -> bool:
        """Queue one non-current page for idle prewarming. 将非当前页加入空闲预热队列。"""
        total = len(self._nav_items) + len(self._bottom_nav_items)
        if not self._lazy_loading or not 0 <= index < total:
            return False
        if index == self._current_index or index in self._pages:
            return False
        queue = getattr(self, "_page_prewarm_queue", [])
        if index in queue or index == getattr(self, "_page_prewarm_in_flight", None):
            return False
        self._page_prewarm_queue = queue
        queue.append(index)
        self._schedule_page_prewarm()
        return True

    def _schedule_page_prewarm(self) -> None:
        if not getattr(self, "_window", None):
            return
        if getattr(self, "_startup_page_guard_active", False) or getattr(
            self, "_page_prewarm_scheduled", False
        ):
            return
        if getattr(self, "_foreground_page_load_index", None) is not None:
            return
        if getattr(self, "_page_prewarm_in_flight", None) is not None:
            return
        if not getattr(self, "_page_prewarm_queue", []):
            return
        self._page_prewarm_scheduled = True
        QTimer.singleShot(_PAGE_PREWARM_DELAY_MS, self._run_next_page_prewarm)

    def _run_next_page_prewarm(self) -> None:
        self._page_prewarm_scheduled = False
        if getattr(self, "_startup_page_guard_active", False):
            return
        if getattr(self, "_foreground_page_load_index", None) is not None:
            self._schedule_page_prewarm()
            return
        while getattr(self, "_page_prewarm_queue", []):
            index = self._page_prewarm_queue.pop(0)
            if index == self._current_index or index in self._pages:
                continue
            self._page_prewarm_in_flight = index
            try:
                self._create_page(index)
            except Exception as exc:
                self._page_prewarm_in_flight = None
                exception(f"页面预热失败: {type(exc).__name__}: {exc}")
                self._schedule_page_prewarm()
                return
            page = self._pages.get(index)
            if page is None or not getattr(page, "_prismqml_async_page", False):
                self._finish_page_prewarm(index)
            return

    def _finish_page_prewarm(self, index: int) -> None:
        if getattr(self, "_page_prewarm_in_flight", None) == index:
            self._page_prewarm_in_flight = None
        self._schedule_page_prewarm()

    def _mark_foreground_page_load_started(self, index: int) -> None:
        self._foreground_page_load_index = index

    def _mark_foreground_page_load_finished(self) -> None:
        self._foreground_page_load_index = None
        self._schedule_page_prewarm()

    def _discard_page_prewarm(self, index: int) -> None:
        queue = getattr(self, "_page_prewarm_queue", [])
        self._page_prewarm_queue = [
            queued_index
            for queued_index in queue
            if queued_index != index
        ]

    def _is_page_prewarming(self, index: int) -> bool:
        return getattr(self, "_page_prewarm_in_flight", None) == index
