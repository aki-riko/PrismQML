# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Loading-overlay teardown diagnostics for async page tests. 异步页面用例的加载遮罩销毁诊断。"""

import time

from PySide6.QtCore import QObject


def loading_exit_state(host, stack, page_transition, circle_transition, overlay):
    """Describe every gate the overlay teardown waits on. 描述遮罩销毁所等待的各个闸门。"""
    # The loader sits in the window's page-stack shell, not inside the stack
    # 加载器位于窗口的页面栈外壳中, 不在 stack 之内
    loader = host.findChild(QObject, "loadingOverlayLoader")
    guard = overlay.findChild(QObject, "qmlPageFinishGuard")
    loader_state = (
        f"active:{loader.property('active')}/transition:{loader.property('transitionActive')}"
        if loader is not None else "missing"
    )
    return (
        f"overlay=visible:{overlay.property('visible')}/"
        f"finishing:{overlay.property('finishing')}/"
        f"loading:{overlay.property('loading')} "
        f"guard={guard.property('running') if guard is not None else None} "
        f"loader={loader_state} "
        f"host=loading:{host.property('_pythonLoading')}/"
        f"pending:{host.property('_pythonPendingIndex')}/"
        f"collapsed:{host.property('_pythonLazyCollapseComplete')}/"
        f"finishRequested:{host.property('_pythonLoadingFinishRequested')}/"
        f"revealScheduled:{host.property('_pythonRevealScheduled')} "
        f"stack=pending:{stack.property('_pendingLazySwitchIndex')}/"
        f"display:{stack.property('_displayIndex')} "
        f"transition=active:{page_transition.property('active')}/"
        f"collapsed:{page_transition.property('collapsed')}/"
        f"circle:{circle_transition.property('running')}"
    )


def pump_until_overlay_gone(pump_until, host, stack, page_transition, circle_transition):
    """Wait for the overlay to be destroyed, keeping the last state seen. 等待遮罩销毁并保留最后观测状态。

    The state is captured on every poll, so a timeout still reports what held the
    overlay even if it is destroyed right after the wait.
    每次轮询都记录状态, 因此即使遮罩在等待结束后立刻被销毁, 超时仍能报告是什么拖住了它。
    """
    started = time.perf_counter()
    last = {"state": "overlay never observed"}

    def overlay_gone():
        overlay = host.findChild(QObject, "loadingOverlay")
        if overlay is None:
            return True
        last["state"] = loading_exit_state(
            host, stack, page_transition, circle_transition, overlay
        )
        return False

    gone = pump_until(overlay_gone)
    return gone, f"waited={time.perf_counter() - started:.3f}s {last['state']}"
