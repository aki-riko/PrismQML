# coding: utf-8
# Copyright 2026 aki-riko
# SPDX-License-Identifier: MIT
"""
全局输入焦点过滤器 — 鼠标按下时,如果点击位置不在当前输入控件内, 就清除焦点.

QApplication.installEventFilter 是唯一可靠的全局事件拦截方式 (QML 端各种
PointerHandler/MouseArea 都因 grab 机制不可靠).

使用:
    from prismqml.python.core.input_focus_filter import install_input_focus_filter
    app = QApplication(...)
    install_input_focus_filter(app)
"""

from typing import Optional

from PySide6.QtCore import QObject, QEvent
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem, QQuickWindow


def _is_input_item(obj: QObject) -> bool:
    """判断 obj 是否是 QML 输入控件 (TextInput / TextEdit)"""
    if obj is None:
        return False
    try:
        return obj.inherits("QQuickTextInput") or obj.inherits("QQuickTextEdit")
    except Exception:
        return False


def _is_inside(item: QQuickItem, global_pos) -> bool:
    """global 坐标是否落在 item 的局部边界内"""
    if item is None:
        return False
    try:
        local = item.mapFromGlobal(global_pos)
        return 0 <= local.x() <= item.width() and 0 <= local.y() <= item.height()
    except Exception:
        return False


class _InputFocusFilter(QObject):
    """全局事件过滤器 — 鼠标按下时若点击不在输入控件内, 主动清焦点."""

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() != QEvent.Type.MouseButtonPress:
            return False

        app = QGuiApplication.instance()
        if app is None:
            return False

        focus_obj = app.focusObject()
        if not _is_input_item(focus_obj):
            return False

        # 拿全局坐标. PySide6 中 QMouseEvent.globalPosition 返回 QPointF
        try:
            gp = event.globalPosition().toPoint()
        except Exception:
            try:
                gp = event.globalPos()
            except Exception:
                return False

        # 点击位置在当前 focus 输入控件内 — 不清, 让 TextInput 自己处理 (光标移动等)
        if _is_inside(focus_obj, gp):
            return False

        # 点击位置在外部 — 清焦点
        try:
            focus_obj.setFocus(False)
        except Exception:
            pass

        return False  # 不消费事件, QML 继续处理


_filter: Optional[_InputFocusFilter] = None


def install_input_focus_filter(app: Optional[QObject] = None) -> _InputFocusFilter:
    """在 QApplication 上安装全局输入焦点过滤器. 多次调用幂等."""
    global _filter
    if _filter is not None:
        return _filter
    if app is None:
        app = QGuiApplication.instance()
    if app is None:
        raise RuntimeError("No QGuiApplication instance — call after QApplication() created.")
    _filter = _InputFocusFilter()
    # 必须保留模块级强引用 (PySide6 的 installEventFilter 不持有引用,
    # 否则 _filter 被 GC 后事件过滤静默失效)
    app.installEventFilter(_filter)
    return _filter
