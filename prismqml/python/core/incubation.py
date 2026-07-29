# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""QML 异步孵化(incubation)控制器。

# 为什么需要它
QML 的 `Loader { asynchronous: true }`(StackedWidget 懒加载就用它)只有在引擎
**安装了 QQmlIncubationController** 时才会真正"分帧切片"实例化对象树;否则 Qt
默认行为是在事件循环空闲时**一次性同步**建完整棵页面树 —— 切到未加载页的那一帧
里 GUI 线程被这棵树的实例化占满, 与同时进行的导航指示器动画(NumberAnimation,
同样跑在 GUI 线程)抢同一帧 → 掉帧。

# 做什么
周期性调用 `incubateFor(budget_ms)`, 把孵化工作限制在每次很小的时间预算内,
分散到多帧完成, 不再单帧爆建。真机实测(Windows 平台真实窗口 frameSwapped 计时,
切到未加载页 + 指示器动画并发, 各 3 次取稳定值):
  默认无 controller: >20ms 卡帧 ~28-30 / 次
  装本 controller:   >20ms 卡帧 ~6-7  / 次  (减少约 78%)

# 自适应频率
有待孵化对象时用 `_active_interval`(贴近一帧, 16ms)持续推进; 空闲时切到
`_idle_interval`(250ms)低频轮询, 几乎不占 CPU, 一旦有新异步对象立即升频。
"""
import sys
from time import perf_counter

from PySide6.QtCore import QTimer, Qt, qVersion
from PySide6.QtQml import QQmlIncubationController

from prismqml.python.core.diagnostics import startup_profile_verbose_enabled
from prismqml.python.core.logger import debug, exception, info


_DIAGNOSTIC_TAG = "Incubation"
_CONNECTIONS_VME_CRASH_PLATFORM = "win32"
_CONNECTIONS_VME_CRASH_QT_VERSIONS = frozenset(("6.11.1",))


def asynchronous_page_loader_enabled(qt_version=None, platform_name=None):
    """Return whether framework page Loaders may use asynchronous incubation.

    返回框架页面 Loader 是否可安全使用异步孵化。自定义 controller 与 QML Loader
    必须使用同一安全判定；否则跳过 controller 后，Loader 仍可能永久停在 Loading。
    """
    resolved_qt_version = qVersion() if qt_version is None else qt_version
    resolved_platform = sys.platform if platform_name is None else platform_name
    return not _requires_synchronous_incubation_fallback(
        resolved_qt_version, resolved_platform
    )


class PrismIncubationController(QQmlIncubationController):
    """驱动 QML 异步孵化的时间分片控制器。

    安装后, 异步 Loader 的实例化按每帧 ``budget_ms`` 毫秒切片推进, 避免单帧
    同步建整棵对象树造成的掉帧。

    注意: QQmlIncubationController **不是** QObject 子类, 不能作为 QTimer 的
    parent, 也没有 Qt parent 生命周期管理。故内部 QTimer 以传入的 ``owner``
    (QObject, 通常是 engine)为 parent, 随 owner 销毁自动回收; controller 自身
    由 install_incubation_controller 挂到 engine 上防止被 GC。
    """

    def __init__(self, owner, budget_ms: int = 5,
                 active_interval: int = 16, idle_interval: int = 250):
        super().__init__()
        self._budget_ms = max(1, int(budget_ms))
        self._active_interval = max(1, int(active_interval))
        self._idle_interval = max(self._active_interval, int(idle_interval))
        self._diagnostics_enabled = startup_profile_verbose_enabled()
        self._diagnostic_sequence = 0

        # owner(QObject)作 parent: controller 非 QObject 不能当 parent。
        self._timer = QTimer(owner)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(self._idle_interval)

    def incubatingObjectCountChanged(self, incubating_object_count: int) -> None:
        """Promote polling as soon as Qt queues work. Qt 入队任务后立即升频。"""
        if incubating_object_count <= 0:
            return
        if (not self._timer.isActive()
                or self._timer.interval() != self._active_interval):
            self._timer.start(self._active_interval)

    def _on_tick(self) -> None:
        # incubatingObjectCount(): 当前仍在孵化中的对象数; >0 说明有异步实例化
        # 正在进行, 需要持续推进。incubateFor 在预算时间内尽可能多地推进孵化。
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
        debug(
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
            exception(
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
        self, sequence, object_count_before, object_count_after,
        timer_interval, elapsed_ms,
    ):
        if sequence is None:
            return
        debug(
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
    """给 ``engine`` 安装 PrismIncubationController 并返回它。

    幂等: 引擎已装则直接返回已有 controller, 不重复安装。
    controller 内部 QTimer 以 engine 为 parent; controller 自身挂到 engine 的
    属性上(``_fluent_incubation_ctrl``)防止被 Python GC 回收。
    """
    existing = engine.incubationController()
    if isinstance(existing, PrismIncubationController):
        _log_controller_reused(existing)
        return existing
    controller = PrismIncubationController(engine, budget_ms=budget_ms)
    engine.setIncubationController(controller)
    # 防 GC: setIncubationController 不取 Python 引用所有权, 必须自己留引用。
    engine._fluent_incubation_ctrl = controller
    _log_controller_installed(engine, controller)
    return controller


def _requires_synchronous_incubation_fallback(qt_version, platform_name):
    """Return whether automatic sliced incubation is unsafe. 判断自动分片孵化是否不安全。"""
    return (
        platform_name == _CONNECTIONS_VME_CRASH_PLATFORM
        and qt_version in _CONNECTIONS_VME_CRASH_QT_VERSIONS
    )


def install_default_incubation_controller(engine, budget_ms: int = 5):
    """Install the default controller unless this Qt build is unsafe. 安全时安装默认控制器。

    Qt 6.11.1 on Windows can return a null VME method while finalizing a
    function-style ``Connections`` handler from ``incubateFor()``. Two real
    crash dumps reached different handlers through that same native path, so
    automatic engine setup falls back to Qt's synchronous incubation there.
    Explicit callers can still opt into the controller through
    ``install_incubation_controller()`` for diagnostics and controlled tests.
    """
    qt_version = qVersion()
    if not asynchronous_page_loader_enabled(qt_version, sys.platform):
        _log_synchronous_incubation_fallback(qt_version)
        return None
    return install_incubation_controller(engine, budget_ms=budget_ms)


def _log_synchronous_incubation_fallback(qt_version):
    """Log an expected fallback only in verbose diagnostics. 仅在详细诊断中记录预期回退。"""
    if not startup_profile_verbose_enabled():
        return
    debug(
        "controller skipped "
        f"qt_version={qt_version} "
        f"platform={sys.platform} "
        "reason=QQmlConnections null VME method during sliced incubation",
        tag=_DIAGNOSTIC_TAG,
    )


def _log_controller_reused(controller):
    if not controller._diagnostics_enabled:
        return
    info(
        "controller reused "
        f"controller_id={id(controller)} "
        f"budget_ms={controller._budget_ms} "
        f"timer_interval_ms={controller._timer.interval()}",
        tag=_DIAGNOSTIC_TAG,
    )


def _log_controller_installed(engine, controller):
    if not controller._diagnostics_enabled:
        return
    info(
        "controller installed "
        f"controller_id={id(controller)} "
        f"engine_type={type(engine).__name__} "
        f"budget_ms={controller._budget_ms} "
        f"active_interval_ms={controller._active_interval} "
        f"idle_interval_ms={controller._idle_interval}",
        tag=_DIAGNOSTIC_TAG,
    )
