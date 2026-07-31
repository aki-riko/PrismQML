# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Heavy sliced-incubation runtime loaded only when needed. 按需加载的分片孵化实现。"""

from time import perf_counter

from PySide6.QtCore import QTimer, Qt
from PySide6.QtQml import QQmlIncubationController

from . import incubation as facade


_DIAGNOSTIC_TAG = "Incubation"


class PrismIncubationController(QQmlIncubationController):
    """Drive asynchronous QML incubation in bounded slices. 分片驱动异步 QML 孵化。"""

    def __init__(
        self,
        owner,
        budget_ms: int = 5,
        active_interval: int = 16,
        idle_interval: int = 250,
    ):
        super().__init__()
        self._budget_ms = max(1, int(budget_ms))
        self._active_interval = max(1, int(active_interval))
        self._idle_interval = max(self._active_interval, int(idle_interval))
        self._diagnostics_enabled = facade.startup_profile_verbose_enabled()
        self._diagnostic_sequence = 0

        # owner(QObject) is the parent because the controller is not a QObject.
        # controller 不是 QObject，因此由 owner 持有定时器生命周期。
        self._timer = QTimer(owner)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(self._idle_interval)

    def incubatingObjectCountChanged(self, incubating_object_count: int) -> None:
        """Promote polling as soon as Qt queues work. Qt 入队后立即提升轮询频率。"""
        if incubating_object_count <= 0:
            return
        if (
            not self._timer.isActive()
            or self._timer.interval() != self._active_interval
        ):
            self._timer.start(self._active_interval)

    def _on_tick(self) -> None:
        object_count_before = self.incubatingObjectCount()
        timer_interval_before = self._timer.interval()
        sequence = self._trace_tick_begin(
            object_count_before, timer_interval_before
        )
        object_count_after, elapsed_ms = self._advance_incubation(
            object_count_before, timer_interval_before, sequence
        )
        timer_interval_after = self._update_timer(object_count_after > 0)
        self._trace_tick_done(
            sequence,
            object_count_before,
            object_count_after,
            timer_interval_after,
            elapsed_ms,
        )

    def _trace_tick_begin(self, object_count, timer_interval):
        if object_count <= 0 or not self._diagnostics_enabled:
            return None
        self._diagnostic_sequence += 1
        sequence = self._diagnostic_sequence
        facade.debug(
            "tick begin "
            f"sequence={sequence} "
            f"object_count_before={object_count} "
            f"budget_ms={self._budget_ms} "
            f"timer_interval_ms={timer_interval}",
            tag=_DIAGNOSTIC_TAG,
        )
        return sequence

    def _advance_incubation(self, object_count, timer_interval, sequence):
        started_at = perf_counter()
        try:
            self.incubateFor(self._budget_ms)
            object_count_after = self.incubatingObjectCount()
        except (RuntimeError, TypeError) as exc:
            elapsed_ms = (perf_counter() - started_at) * 1000
            trace_sequence = sequence if sequence is not None else (
                "idle" if object_count <= 0 else "untraced"
            )
            facade.exception(
                "tick failed "
                f"sequence={trace_sequence} "
                f"object_count_before={object_count} "
                f"budget_ms={self._budget_ms} "
                f"timer_interval_ms={timer_interval} "
                f"elapsed_ms={elapsed_ms:.3f} "
                f"error={type(exc).__name__}: {exc}",
                tag=_DIAGNOSTIC_TAG,
            )
            raise
        return object_count_after, (perf_counter() - started_at) * 1000

    def _update_timer(self, active):
        want = self._active_interval if active else self._idle_interval
        if self._timer.interval() != want:
            self._timer.start(want)
        return self._timer.interval()

    def _trace_tick_done(
        self,
        sequence,
        object_count_before,
        object_count_after,
        timer_interval,
        elapsed_ms,
    ):
        if sequence is None:
            return
        facade.debug(
            "tick done "
            f"sequence={sequence} "
            f"object_count_before={object_count_before} "
            f"object_count_after={object_count_after} "
            f"budget_ms={self._budget_ms} "
            f"timer_interval_ms={timer_interval} "
            f"elapsed_ms={elapsed_ms:.3f}",
            tag=_DIAGNOSTIC_TAG,
        )


def install_incubation_controller(engine, budget_ms: int = 5):
    """Install or reuse the sliced incubation controller. 安装或复用分片孵化控制器。"""
    existing = engine.incubationController()
    if isinstance(existing, PrismIncubationController):
        _log_controller_reused(existing)
        return existing
    controller = PrismIncubationController(engine, budget_ms=budget_ms)
    engine.setIncubationController(controller)
    # setIncubationController does not retain the Python wrapper. 保留 Python 引用防止 GC。
    engine._fluent_incubation_ctrl = controller
    _log_controller_installed(engine, controller)
    return controller


def _log_controller_reused(controller):
    if not controller._diagnostics_enabled:
        return
    facade.info(
        "controller reused "
        f"controller_id={id(controller)} "
        f"budget_ms={controller._budget_ms} "
        f"timer_interval_ms={controller._timer.interval()}",
        tag=_DIAGNOSTIC_TAG,
    )


def _log_controller_installed(engine, controller):
    if not controller._diagnostics_enabled:
        return
    facade.info(
        "controller installed "
        f"controller_id={id(controller)} "
        f"engine_type={type(engine).__name__} "
        f"budget_ms={controller._budget_ms} "
        f"active_interval_ms={controller._active_interval} "
        f"idle_interval_ms={controller._idle_interval}",
        tag=_DIAGNOSTIC_TAG,
    )


__all__ = ["PrismIncubationController", "install_incubation_controller"]
