# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Engine-managed asynchronous QML page. 引擎管理的异步 QML 页面。"""

from pathlib import Path
from typing import Optional, Union

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem
import shiboken6

from ..core.logger import error, warning
from ..core.utils import qml_path


_ASYNC_PAGE_HOST = "_internal/AsyncQmlPageHost.qml"

# Milliseconds a Python-backed page may hold the navigation loading overlay
# before the engine releases it anyway. / Python 页面最多可占用导航 loading
# 遮罩的时长，超时后引擎强制放行。
#
# 🔴 为什么必须有（2026-11-02，下游实测事故）：遮罩只有两条放行路径——
#    ① 目标页把 `prismqmlAsyncReady` 置 true；② 宿主 `pageLoadFailed`。
#    对"页面建出来了、既不报错也永不就绪"这一种状态，此前**没有任何超时**，
#    于是 `_pythonLoading` 永远为 true、遮罩永久停留。下游 Kaleidos 2.0.2.284
#    （prismqml 0.5.0.31）用户报告「游戏库一直转圈显示加载中、永远进不去」即此形态。
#
# 🔴 标定依据：
#   - 远大于正常首屏就绪（引擎侧 Gallery 与下游实测均为百毫秒量级），正常路径
#     绝不会走到兜底，因此不会改变既有揭幕时序；
#   - 必须有限：任何"永不就绪"的组合（判据写错、依赖的 Loader 卡在 Loading、
#     backend 属性没注入）都必须在可接受等待内收敛到可交互状态；
#   - 取 8000ms 而非更短，是因为重页面在慢机器上的真实首屏可能到秒级，
#     过早放行会把"等页面画完"的既有语义破坏成"固定延时"。
DEFAULT_PAGE_READY_DEADLINE_MS = 8000


def _as_qml_url(source: Union[str, Path, QUrl]) -> QUrl:
    if isinstance(source, QUrl):
        return QUrl(source)
    return QUrl.fromLocalFile(str(Path(source).resolve()))


def _component_errors(component: QQmlComponent) -> str:
    return "\n".join(item.toString() for item in component.errors())


def _cached_host_component(engine, host_url: QUrl) -> QQmlComponent:
    """Reuse the compiled host component for one engine lifetime.

    同一个 QML engine 内所有 AsyncQmlPage 共用已编译宿主，页面实例仍然各自
    create；engine 被 reset 后 C++ 对象失效，下一页会重新编译。
    """
    cached = getattr(engine, "_prismqml_async_page_host_component", None)
    if cached is not None and shiboken6.isValid(cached):
        return cached
    component = QQmlComponent(engine, host_url)
    engine._prismqml_async_page_host_component = component
    return component


class AsyncQmlPage(QObject):
    """Load a Python-backed QML page through the engine incubation pipeline.

    通过引擎孵化管线加载带 Python backend 的 QML 页面。目标 QML 根对象必须
    声明 ``property var backend``；导航窗口会一直保留标准 loading 遮罩，直到
    ``page_ready`` 发出。目标根对象可额外声明 ``property bool prismqmlAsyncReady``，
    让引擎等待页面内部的首屏容器完成后再发出就绪信号。
    """

    page_ready = Signal()
    page_failed = Signal(str)
    _prismqml_async_page = True

    def __init__(
        self,
        qml_source: Union[str, Path, QUrl],
        parent: Optional[QObject] = None,
        backend: Optional[QObject] = None,
        page_ready_deadline_ms: Optional[int] = None,
    ):
        super().__init__(parent)
        self._source_url = _as_qml_url(qml_source)
        self._backend = backend if backend is not None else self
        self._qml_component = None
        self._qml_host = None
        self._prismqml_layout_item = None
        self._qml_item = None
        self._load_started = False
        self._load_ready = False
        self._load_error = ""
        self._ready_deadline_ms = (
            DEFAULT_PAGE_READY_DEADLINE_MS
            if page_ready_deadline_ms is None
            else max(0, int(page_ready_deadline_ms))
        )
        self._ready_deadline_timer = None
        self._ready_deadline_expired = False
        self._create_host()

    @property
    def is_ready(self) -> bool:
        """Return whether the target QML tree is ready. 返回目标 QML 是否就绪。"""
        return self._load_ready

    @property
    def load_error(self) -> str:
        """Return the last target load error. 返回最近一次目标加载错误。"""
        return self._load_error

    def start_loading(self) -> None:
        """Start loading once after the page host is attached. 挂载后开始一次加载。"""
        if self._load_started:
            return
        self._load_started = True
        self._arm_ready_deadline()
        if not self._qml_item.setProperty("loadRequested", True):
            raise RuntimeError("AsyncQmlPage host rejected loadRequested")

    # ==================== Ready deadline 就绪兜底 ====================
    #
    # 遮罩（`_pythonLoading`）只由 page_ready / page_failed 释放。对"创建成功但
    # 永不就绪"的页面此前无任何兜底，遮罩会永久停留（见 DEFAULT_PAGE_READY_DEADLINE_MS
    # 的注释）。这里在开始加载时布一颗一次性定时器：到点仍未就绪就按就绪放行，
    # 并留可见日志，便于定位是哪个页面、哪条判据没翻 true。

    def _arm_ready_deadline(self) -> None:
        """Arm the one-shot ready deadline. 布下一次性的就绪兜底计时。"""
        if self._ready_deadline_ms <= 0 or self._load_ready:
            return
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(self._ready_deadline_ms)
        timer.timeout.connect(self._on_ready_deadline_expired)
        self._ready_deadline_timer = timer
        timer.start()

    def _disarm_ready_deadline(self) -> None:
        """Stop and drop the deadline timer. 停止并释放就绪兜底计时。"""
        timer = self._ready_deadline_timer
        self._ready_deadline_timer = None
        if timer is None:
            return
        try:
            timer.stop()
            timer.deleteLater()
        except RuntimeError:
            # QObject already destroyed / 对象已析构
            pass

    def _on_ready_deadline_expired(self) -> None:
        """Release the overlay when the page never reports ready. 页面永不就绪时放行。"""
        self._ready_deadline_timer = None
        if self._load_ready or self._load_error:
            # Normal path or a real failure already settled this page.
            # 正常路径或真实失败已经结算过，兜底不得覆盖。
            return
        self._ready_deadline_expired = True
        self._load_ready = True
        message = (
            f"页面 {self._source_url.fileName() or self._source_url.toString()} "
            f"超过 {self._ready_deadline_ms}ms 未就绪，已按就绪放行以免遮罩永久停留"
            f"（请检查该页面 prismqmlAsyncReady 的判据与其依赖的 Loader 状态）"
        )
        warning(message)
        # 只发 page_ready 不够：宿主 pageReady 由 QML 侧 _targetReady 驱动，
        # 必须同时把兜底标志写进宿主，遮罩才会真正揭幕。
        host = self._qml_host
        if host is not None and shiboken6.isValid(host):
            try:
                host.setProperty("readyDeadlineExpired", True)
            except RuntimeError:
                pass
        self.page_ready.emit()

    def _create_host(self) -> None:
        from ..runtime import get_published_qml_engine

        engine = get_published_qml_engine()
        host_url = QUrl.fromLocalFile(str(qml_path(_ASYNC_PAGE_HOST)))
        component = _cached_host_component(engine, host_url)
        self._qml_component = component
        if component.isError():
            details = _component_errors(component)
            raise RuntimeError(f"AsyncQmlPage host load failed:\n{details}")
        host = component.create()
        if not isinstance(host, QQuickItem):
            raise RuntimeError("AsyncQmlPage host did not create a QQuickItem")
        self._qml_item = host
        self._qml_host = host
        self._prismqml_layout_item = host
        host.pageLoaded.connect(self._on_page_loaded)
        host.pageLoadFailed.connect(self._on_page_failed)
        host.setProperty("backend", self._backend)
        host.setProperty("pageSource", self._source_url)

    def _on_page_loaded(self) -> None:
        self._disarm_ready_deadline()
        content_item = self._qml_host.property("contentItem")
        if not isinstance(content_item, QQuickItem):
            self._on_page_failed(self._source_url.toString())
            return
        self._qml_item = content_item
        self._load_ready = True
        self.page_ready.emit()

    def _on_page_failed(self, source: str) -> None:
        self._disarm_ready_deadline()
        self._load_error = f"Failed to load asynchronous QML page: {source}"
        error(self._load_error)
        self.page_failed.emit(self._load_error)
