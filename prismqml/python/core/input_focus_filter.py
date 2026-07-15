# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""
全局输入焦点过滤器 — 鼠标按下时,如果点击位置不在当前输入控件内, 就清除焦点.

QApplication.installEventFilter 是唯一可靠的全局事件拦截方式 (QML 端各种
PointerHandler/MouseArea 都因 grab 机制不可靠).

PrismQML App 会自动安装该过滤器。自建 QApplication 时可手动安装:
    from prismqml.python.core.input_focus_filter import install_input_focus_filter
    app = QApplication(...)
    install_input_focus_filter(app)
"""

from typing import Optional

from PySide6.QtCore import QObject, QEvent
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem, QQuickWindow

from .logger import debug


def _is_input_item(obj: QObject) -> bool:
    """判断 obj 是否是 QML 输入控件 (TextInput / TextEdit)"""
    if obj is None:
        return False
    try:
        return obj.inherits("QQuickTextInput") or obj.inherits("QQuickTextEdit")
    except (AttributeError, RuntimeError, TypeError) as exc:
        debug(f"[InputFocusFilter] 判断输入控件失败: {exc}")
        return False


def _is_inside(item: QQuickItem, global_pos) -> bool:
    """global 坐标是否落在 item 的局部边界内"""
    if item is None:
        return False
    try:
        local = item.mapFromGlobal(global_pos)
        return 0 <= local.x() <= item.width() and 0 <= local.y() <= item.height()
    except (AttributeError, RuntimeError, TypeError) as exc:
        debug(f"[InputFocusFilter] 坐标命中检测失败: {exc}")
        return False


def _mouse_global_position(event) -> tuple[bool, object]:
    """Resolve one mouse position with the legacy fallback. 解析鼠标位置并保留旧回退。"""
    try:
        return True, event.globalPosition().toPoint()
    except (AttributeError, RuntimeError) as exc:
        debug(f"[InputFocusFilter] globalPosition 不可用,尝试 globalPos: {exc}")
    try:
        return True, event.globalPos()
    except (AttributeError, RuntimeError) as fallback_exc:
        debug(f"[InputFocusFilter] 获取鼠标全局坐标失败: {fallback_exc}")
        return False, None


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

        resolved, gp = _mouse_global_position(event)
        if not resolved:
            return False

        # 点击位置在当前 focus 输入控件内 — 不清, 让 TextInput 自己处理 (光标移动等)
        if _is_inside(focus_obj, gp):
            return False

        # 点击位置在外部 — 清焦点
        try:
            focus_obj.setFocus(False)
        except (AttributeError, RuntimeError, TypeError) as exc:
            debug(f"[InputFocusFilter] 清除输入焦点失败: {exc}")

        return False  # 不消费事件, QML 继续处理


_filter: Optional[_InputFocusFilter] = None


def reset_input_focus_filter() -> None:
    """卸载全局输入焦点过滤器，供 App 测试生命周期安全重置。"""
    global _filter
    filter_object = _filter
    _filter = None
    if filter_object is None:
        return

    try:
        owner = filter_object.parent()
    except (RuntimeError, TypeError) as exc:
        debug(f"[InputFocusFilter] 获取过滤器所属应用失败: {exc}")
        return

    if owner is not None:
        try:
            owner.removeEventFilter(filter_object)
        except (AttributeError, RuntimeError, TypeError) as exc:
            debug(f"[InputFocusFilter] 卸载事件过滤器失败: {exc}")

    try:
        filter_object.setParent(None)
        filter_object.deleteLater()
    except (RuntimeError, TypeError) as exc:
        debug(f"[InputFocusFilter] 释放事件过滤器失败: {exc}")


def install_input_focus_filter(app: Optional[QObject] = None) -> _InputFocusFilter:
    """在 QApplication 上安装全局输入焦点过滤器. 多次调用幂等."""
    global _filter
    if app is None:
        app = QGuiApplication.instance()
    if app is None:
        raise RuntimeError("No QGuiApplication instance — call after QApplication() created.")

    if _filter is not None:
        try:
            if _filter.parent() == app:
                return _filter
        except (RuntimeError, TypeError) as exc:
            debug(f"[InputFocusFilter] 现有过滤器已失效，将重新安装: {exc}")
        reset_input_focus_filter()

    # 同时使用 QObject parent 和模块级强引用保证过滤器生命周期与应用一致。
    _filter = _InputFocusFilter(app)
    app.installEventFilter(_filter)
    return _filter
