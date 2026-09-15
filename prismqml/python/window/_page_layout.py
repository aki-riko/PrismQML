# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Page layout binding helpers. 页面布局绑定辅助函数。"""

from typing import Any

from PySide6.QtCore import QTimer

from ..core.logger import exception


_PAGE_SIZE_BIND_DELAY_MS = 50
_PAGE_SIZE_RETRY_DELAY_MS = 200


def _emit_page_size_signals(page_item: Any) -> None:
    try:
        page_item.widthChanged.emit()
        page_item.heightChanged.emit()
    except Exception as exc:
        exception(f"页面尺寸信号触发失败: {type(exc).__name__}: {exc}")


def _resolve_page_layout_item(page_instance: Any):
    layout_item = getattr(page_instance, "_prismqml_layout_item", None)
    return layout_item if layout_item is not None else page_instance._qml_item


def _make_page_size_binder(
    page_instance: Any, page_container: Any, emit_signals: bool
):
    from shiboken6 import isValid

    def bind_size():
        page_item = _resolve_page_layout_item(page_instance)
        if not isValid(page_item) or not isValid(page_container):
            return
        width = page_container.width()
        height = page_container.height()
        if width > 0 and height > 0:
            page_item.setWidth(width)
            page_item.setHeight(height)
            if emit_signals:
                _emit_page_size_signals(page_item)

    return bind_size


def _connect_page_size_binding(
    page_container: Any, bind_size, delays, schedule_callback=QTimer.singleShot
) -> None:
    page_container.widthChanged.connect(bind_size)
    page_container.heightChanged.connect(bind_size)
    for delay in delays:
        schedule_callback(delay, bind_size)
