# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Engine-managed asynchronous QML page. 引擎管理的异步 QML 页面。"""

from pathlib import Path
from typing import Optional, Union

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem

from ..core.logger import error
from ..core.utils import qml_path


_ASYNC_PAGE_HOST = "_internal/AsyncQmlPageHost.qml"


def _as_qml_url(source: Union[str, Path, QUrl]) -> QUrl:
    if isinstance(source, QUrl):
        return QUrl(source)
    return QUrl.fromLocalFile(str(Path(source).resolve()))


def _component_errors(component: QQmlComponent) -> str:
    return "\n".join(item.toString() for item in component.errors())


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
        if not self._qml_item.setProperty("loadRequested", True):
            raise RuntimeError("AsyncQmlPage host rejected loadRequested")

    def _create_host(self) -> None:
        from ..runtime import get_published_qml_engine

        engine = get_published_qml_engine()
        host_url = QUrl.fromLocalFile(str(qml_path(_ASYNC_PAGE_HOST)))
        component = QQmlComponent(engine, host_url)
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
        content_item = self._qml_host.property("contentItem")
        if not isinstance(content_item, QQuickItem):
            self._on_page_failed(self._source_url.toString())
            return
        self._qml_item = content_item
        self._load_ready = True
        self.page_ready.emit()

    def _on_page_failed(self, source: str) -> None:
        self._load_error = f"Failed to load asynchronous QML page: {source}"
        error(self._load_error)
        self.page_failed.emit(self._load_error)
