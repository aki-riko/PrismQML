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


def _live_qt_object(value: Any):
    """返回仍持有 C++ 对象的 Qt 对象，空值或已析构时返回 None。

    Shiboken 包装器在 C++ 对象被删除后**依然是真值**，``if not window`` 挡不住；
    退出清理在 ``aboutToQuit`` 销毁 QML 窗口后，仍排在定时器队列里的页面任务会
    继续持有窗口、页面容器与页项，此时对它们调用 Qt API 会抛
    ``libshiboken: Internal C++ object already deleted``。
    注意 ``shiboken6.isValid(None)`` 返回 True，空值必须显式判断。
    """
    from shiboken6 import isValid

    if value is None or not isValid(value):
        return None
    return value


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
    def bind_size():
        page_item = _live_qt_object(_resolve_page_layout_item(page_instance))
        container = _live_qt_object(page_container)
        if page_item is None or container is None:
            return
        width = container.width()
        height = container.height()
        if width > 0 and height > 0:
            page_item.setWidth(width)
            page_item.setHeight(height)
            if emit_signals:
                _emit_page_size_signals(page_item)

    return bind_size


def _connect_page_size_binding(
    page_container: Any, bind_size, delays, schedule_callback=QTimer.singleShot
) -> None:
    # 容器可能随窗口在退出清理里析构；此时连接信号会抛
    # ``RuntimeError: Signal source has been deleted``，直接跳过绑定。
    container = _live_qt_object(page_container)
    if container is None:
        return
    container.widthChanged.connect(bind_size)
    container.heightChanged.connect(bind_size)
    for delay in delays:
        schedule_callback(delay, bind_size)
