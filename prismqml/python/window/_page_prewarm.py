# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Low-priority page prewarming. 低优先级页面预热。"""

from time import perf_counter
from typing import Any, Dict, Optional

from PySide6.QtCore import QTimer

from ..core.logger import debug, exception


_PAGE_PREWARM_DELAY_MS = 250
_PAGE_PREWARM_BUDGET_MS = 5.0
_PAGE_PREWARM_OVERRUN_BACKOFF_MS = 500


def initialize_page_prewarm_state(owner: Any) -> None:
    """Initialize startup guard and prewarm queue state. 初始化启动保护与预热队列。"""
    owner._startup_page_guard_active = False
    owner._startup_page_index = 0
    owner._page_prewarm_queue = []
    owner._page_prewarm_scheduled = False
    owner._page_prewarm_in_flight = None
    owner._page_prewarm_generation = 0
    owner._page_prewarm_status = "idle"
    owner._page_prewarm_started_at = None
    owner._page_prewarm_creation_elapsed_ms = 0.0
    owner._page_prewarm_last_index = None
    owner._page_prewarm_last_elapsed_ms = 0.0
    owner._page_prewarm_last_result = "none"
    owner._page_prewarm_last_over_budget = False
    owner._page_prewarm_overrun_count = 0
    owner._page_prewarm_budget_ms = _PAGE_PREWARM_BUDGET_MS
    owner._page_loads_in_flight = set()
    owner._foreground_page_load_index = None


class PagePrewarmMixin:
    """Admission guard and idle scheduler for non-current pages."""

    def _begin_startup_page_guard(self) -> None:
        if not getattr(self, "_lazy_loading", False):
            return
        self._startup_page_guard_active = True
        self._startup_page_index = getattr(self, "_current_index", 0)

    def _startup_page_creation_blocked(self, index: int) -> bool:
        return bool(
            getattr(self, "_lazy_loading", False)
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
        if not getattr(self, "_lazy_loading", False) or not 0 <= index < total:
            return False
        if index == self._current_index or index in self._pages:
            return False
        queue = getattr(self, "_page_prewarm_queue", [])
        if index in queue or index == getattr(self, "_page_prewarm_in_flight", None):
            return False
        self._page_prewarm_queue = queue
        queue.append(index)
        self._page_prewarm_status = "queued"
        self._schedule_page_prewarm()
        return True

    def pagePrewarmState(self) -> Dict[str, Any]:
        """Return a copy of the prewarm state for diagnostics. 返回预热状态快照。"""
        return {
            "status": getattr(self, "_page_prewarm_status", "idle"),
            "queued": list(getattr(self, "_page_prewarm_queue", [])),
            "scheduled": bool(
                getattr(self, "_page_prewarm_scheduled", False)
            ),
            "inFlight": getattr(self, "_page_prewarm_in_flight", None),
            "lastIndex": getattr(self, "_page_prewarm_last_index", None),
            "lastElapsedMs": getattr(
                self, "_page_prewarm_last_elapsed_ms", 0.0
            ),
            "budgetMs": getattr(
                self, "_page_prewarm_budget_ms", _PAGE_PREWARM_BUDGET_MS
            ),
            "lastResult": getattr(
                self, "_page_prewarm_last_result", "none"
            ),
            "lastOverBudget": bool(
                getattr(self, "_page_prewarm_last_over_budget", False)
            ),
            "overrunCount": getattr(
                self, "_page_prewarm_overrun_count", 0
            ),
        }

    def _drop_queued_prewarm(self, index: int) -> None:
        """Drop one index from the queued prewarm list. 从预热队列移除指定索引。"""
        self._page_prewarm_queue = [
            queued_index
            for queued_index in getattr(self, "_page_prewarm_queue", [])
            if queued_index != index
        ]

    def _release_prewarm_ownership(self, index: int) -> None:
        """Release in-flight prewarm ownership. 解除进行中的预热所有权。"""
        self._page_prewarm_in_flight = None
        self._page_prewarm_started_at = None
        self._page_prewarm_status = "cancelled"
        self._page_prewarm_last_index = index
        self._page_prewarm_last_result = "cancelled"

    def cancelPagePrewarm(self, index: int) -> bool:
        """Cancel a queued prewarm request without touching foreground pages.

        取消排队的页面预热请求，不影响前台页面；已经开始的异步页面仅解除
        预热所有权，保留其加载流程，以便用户随后导航时可以直接复用。
        """
        queued = index in getattr(self, "_page_prewarm_queue", [])
        if queued:
            self._drop_queued_prewarm(index)

        in_flight = getattr(self, "_page_prewarm_in_flight", None) == index
        if in_flight:
            self._release_prewarm_ownership(index)

        if not queued and not in_flight:
            return False
        self._invalidate_page_prewarm_timer()
        if getattr(self, "_page_prewarm_queue", []):
            self._schedule_page_prewarm()
        elif not in_flight:
            self._page_prewarm_status = "idle"
        debug(
            f"取消页面预热 index={index} queued={queued} "
            f"in_flight={in_flight}",
            tag="PagePrewarm",
        )
        return True

    def _page_prewarm_blocker(self) -> Optional[str]:
        if getattr(self, "_startup_page_guard_active", False):
            return "startup_guard"
        if getattr(self, "_foreground_page_load_index", None) is not None:
            return "foreground_load"
        if getattr(self, "_page_loads_in_flight", set()):
            return "page_load"
        if getattr(self, "_page_prewarm_in_flight", None) is not None:
            return "prewarm_load"
        return None

    def _invalidate_page_prewarm_timer(self) -> None:
        if not getattr(self, "_page_prewarm_scheduled", False):
            return
        self._page_prewarm_generation = (
            getattr(self, "_page_prewarm_generation", 0) + 1
        )
        self._page_prewarm_scheduled = False
        if getattr(self, "_page_prewarm_in_flight", None) is None:
            self._page_prewarm_status = (
                "queued"
                if getattr(self, "_page_prewarm_queue", [])
                else "idle"
            )

    def _schedule_page_prewarm(self, delay_ms: Optional[int] = None) -> None:
        if not getattr(self, "_window", None):
            return
        if getattr(self, "_page_prewarm_scheduled", False):
            return
        if self._page_prewarm_blocker() is not None:
            self._page_prewarm_status = "blocked"
            return
        if not getattr(self, "_page_prewarm_queue", []):
            if getattr(self, "_page_prewarm_in_flight", None) is None:
                self._page_prewarm_status = "idle"
            return
        if delay_ms is None:
            delay_ms = _PAGE_PREWARM_DELAY_MS
        self._page_prewarm_scheduled = True
        self._page_prewarm_status = "scheduled"
        generation = getattr(self, "_page_prewarm_generation", 0)
        QTimer.singleShot(
            max(0, int(delay_ms)),
            lambda: self._run_next_page_prewarm(generation),
        )

    def _pop_next_page_prewarm(self) -> Optional[int]:
        while getattr(self, "_page_prewarm_queue", []):
            index = self._page_prewarm_queue.pop(0)
            if index == self._current_index or index in self._pages:
                self._page_prewarm_last_index = index
                self._page_prewarm_last_result = "skipped"
                continue
            return index
        return None

    def _record_page_prewarm_result(
        self, index: int, elapsed_ms: float, result: str
    ) -> None:
        budget_ms = float(
            getattr(self, "_page_prewarm_budget_ms", _PAGE_PREWARM_BUDGET_MS)
        )
        over_budget = elapsed_ms > budget_ms
        self._page_prewarm_last_index = index
        self._page_prewarm_last_elapsed_ms = elapsed_ms
        self._page_prewarm_last_result = result
        self._page_prewarm_last_over_budget = over_budget
        if over_budget:
            self._page_prewarm_overrun_count = (
                getattr(self, "_page_prewarm_overrun_count", 0) + 1
            )
        debug(
            f"页面预热完成 index={index} result={result} "
            f"elapsed_ms={elapsed_ms:.3f} budget_ms={budget_ms:.3f} "
            f"over_budget={over_budget}",
            tag="PagePrewarm",
        )

    def _next_page_prewarm_delay(self) -> int:
        if getattr(self, "_page_prewarm_last_over_budget", False):
            return _PAGE_PREWARM_OVERRUN_BACKOFF_MS
        return _PAGE_PREWARM_DELAY_MS

    def _prewarm_elapsed_ms(self) -> float:
        """Milliseconds elapsed since the prewarm started. 预热已耗时（毫秒）。"""
        return (perf_counter() - self._page_prewarm_started_at) * 1000

    def _abort_page_prewarm(self, index: int, exc: Exception) -> None:
        """Record a failed prewarm creation and back off. 记录预热创建失败并退避。"""
        elapsed_ms = self._prewarm_elapsed_ms()
        self._record_page_prewarm_result(index, elapsed_ms, "failed")
        self._page_prewarm_in_flight = None
        self._page_prewarm_started_at = None
        self._page_prewarm_status = "failed"
        exception(f"页面预热失败: {type(exc).__name__}: {exc}")
        self._schedule_page_prewarm(_PAGE_PREWARM_OVERRUN_BACKOFF_MS)

    def _run_next_page_prewarm(self, generation: Optional[int] = None) -> None:
        if generation is not None and generation != getattr(
            self, "_page_prewarm_generation", 0
        ):
            return
        self._page_prewarm_scheduled = False
        blocker = self._page_prewarm_blocker()
        if blocker is not None:
            self._page_prewarm_status = "blocked"
            return
        index = self._pop_next_page_prewarm()
        if index is None:
            self._page_prewarm_status = "idle"
            return
        self._page_prewarm_in_flight = index
        self._page_prewarm_started_at = perf_counter()
        self._page_prewarm_status = "running"
        try:
            self._create_page(index)
        except Exception as exc:
            self._abort_page_prewarm(index, exc)
            return
        elapsed_ms = self._prewarm_elapsed_ms()
        page = self._pages.get(index)
        if page is None or not getattr(page, "_prismqml_async_page", False):
            self._finish_page_prewarm(index, elapsed_ms=elapsed_ms)
            return
        self._page_prewarm_creation_elapsed_ms = elapsed_ms
        self._page_prewarm_status = "loading"

    def _finish_page_prewarm(
        self, index: int, *, elapsed_ms: Optional[float] = None
    ) -> None:
        if getattr(self, "_page_prewarm_in_flight", None) != index:
            return
        if elapsed_ms is None:
            started_at = getattr(self, "_page_prewarm_started_at", None)
            elapsed_ms = (
                (perf_counter() - started_at) * 1000
                if started_at is not None
                else 0.0
            )
        self._record_page_prewarm_result(index, elapsed_ms, "completed")
        self._page_prewarm_in_flight = None
        self._page_prewarm_started_at = None
        self._page_prewarm_status = "completed"
        self._schedule_page_prewarm(self._next_page_prewarm_delay())

    def _mark_foreground_page_load_started(self, index: int) -> None:
        self._foreground_page_load_index = index
        self._invalidate_page_prewarm_timer()

    def _mark_foreground_page_load_finished(self) -> None:
        self._foreground_page_load_index = None
        self._schedule_page_prewarm()

    def _mark_page_load_started(self, index: int) -> None:
        loads = getattr(self, "_page_loads_in_flight", set())
        self._page_loads_in_flight = loads
        loads.add(index)
        self._invalidate_page_prewarm_timer()

    def _mark_page_load_finished(self, index: int) -> None:
        loads = getattr(self, "_page_loads_in_flight", set())
        loads.discard(index)
        if not loads:
            self._schedule_page_prewarm()

    def _is_page_load_in_flight(self, index: int) -> bool:
        return index in getattr(self, "_page_loads_in_flight", set())

    def _discard_page_prewarm(self, index: int) -> None:
        self._drop_queued_prewarm(index)
        if not self._page_prewarm_queue:
            self._invalidate_page_prewarm_timer()

    def _is_page_prewarming(self, index: int) -> bool:
        return getattr(self, "_page_prewarm_in_flight", None) == index
