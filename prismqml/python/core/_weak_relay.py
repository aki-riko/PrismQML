# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Signal slots that keep only a weak reference to their host. 只弱引用宿主的信号槽。"""

import weakref
from typing import Any

__all__ = ["WeakMethodRelay"]


class WeakMethodRelay:
    """Forward a Qt signal to a host method without pinning the host.
    把 Qt 信号转发到宿主方法，但不把宿主钉住。

    Qt keeps a strong reference to every connected Python callable, so connecting a
    bound method such as ``self._relay_settled`` keeps the host alive. Under Nuitka
    that reference survives ``disconnect()``: shiboken retains the compiled method
    wrapper whose ``__self__`` keeps pointing at the host, so the object is never
    collected. For ``TaskHandle`` this leaked the handle together with the
    ``_TaskControl`` it owned -- four kernel semaphores per task (``Lock``/``RLock``
    on the handle, ``Lock``/``Event`` on the control).
    Holding only a weak reference breaks that cycle while keeping the signal
    contract unchanged: the relay is still a queued slot executed on the receiver's
    thread, and once the host is gone later emissions simply become no-ops.
    Qt 会强引用每一个已连接的 Python 可调用对象，因此连接 ``self._relay_settled``
    这类 bound method 等于把宿主钉住。Nuitka 产物中该引用在 ``disconnect()``
    之后依然存在：shiboken 保留着编译后的方法包装，其 ``__self__`` 始终指向
    宿主，对象永远无法回收。对 ``TaskHandle`` 而言，这会让句柄连同它持有的
    ``_TaskControl`` 一起泄漏，每个任务四个内核信号量（句柄上的
    ``Lock``/``RLock``，控制块上的 ``Lock``/``Event``）。只保存弱引用即可打断
    该引用环，同时保持信号契约不变：中继仍然是在接收者线程上执行的队列槽，
    宿主被回收后后续发射自然成为空操作。
    """

    __slots__ = ("_host_ref", "_method_name")

    def __init__(self, host: Any, method_name: str) -> None:
        # Fail at connection time rather than silently dropping every emission later.
        # 连接时即校验契约，避免此后每一次发射都被静默丢弃。
        if not callable(getattr(host, method_name, None)):
            raise AttributeError(
                f"{type(host).__name__} has no relay target {method_name!r}"
            )
        self._host_ref = weakref.ref(host)
        self._method_name = method_name

    def __call__(self, *args: Any) -> None:
        """Invoke the host method if the host is still alive. 宿主仍存活时调用其方法。"""
        host = self._host_ref()
        if host is None:
            return
        target = getattr(host, self._method_name, None)
        if target is not None:
            target(*args)