# coding: utf-8
# Copyright 2026 aki-riko
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
from PySide6.QtCore import QTimer, Qt
from PySide6.QtQml import QQmlIncubationController


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

        # owner(QObject)作 parent: controller 非 QObject 不能当 parent。
        self._timer = QTimer(owner)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(self._idle_interval)

    def _on_tick(self) -> None:
        # incubatingObjectCount(): 当前仍在孵化中的对象数; >0 说明有异步实例化
        # 正在进行, 需要持续推进。incubateFor 在预算时间内尽可能多地推进孵化。
        self.incubateFor(self._budget_ms)

        active = self.incubatingObjectCount() > 0
        want = self._active_interval if active else self._idle_interval
        if self._timer.interval() != want:
            self._timer.start(want)


def install_incubation_controller(engine, budget_ms: int = 5):
    """给 ``engine`` 安装 PrismIncubationController 并返回它。

    幂等: 引擎已装则直接返回已有 controller, 不重复安装。
    controller 内部 QTimer 以 engine 为 parent; controller 自身挂到 engine 的
    属性上(``_fluent_incubation_ctrl``)防止被 Python GC 回收。
    """
    existing = engine.incubationController()
    if isinstance(existing, PrismIncubationController):
        return existing
    controller = PrismIncubationController(engine, budget_ms=budget_ms)
    engine.setIncubationController(controller)
    # 防 GC: setIncubationController 不取 Python 引用所有权, 必须自己留引用。
    engine._fluent_incubation_ctrl = controller
    return controller
