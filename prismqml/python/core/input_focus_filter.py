# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""
全局输入焦点过滤器 — 鼠标按下时,如果点击位置不在当前输入控件内, 就清除焦点.

QApplication.installEventFilter 是唯一可靠的全局事件拦截方式 (QML 端各种
PointerHandler/MouseArea 都因 grab 机制不可靠).

清除范围只限输入框**所属窗口**: 本应用的弹层(候选列表 / 菜单)是独立原生窗口,
点它属于该输入控件自己的交互; 若这里也清掉焦点, 控件自己的失焦守卫会把刚被点击
的弹层收掉(可编辑下拉"点分类行展开就消失"即此).

PrismQML App 会自动安装该过滤器。自建 QApplication 时可手动安装:
    from prismqml.python.core.input_focus_filter import install_input_focus_filter
    app = QApplication(...)
    install_input_focus_filter(app)
"""

from typing import Optional

from PySide6.QtCore import QObject, QEvent, Qt
from PySide6.QtGui import QGuiApplication, QWindow
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


_MAX_OWNER_HOPS = 64


def _scene_root_of(obj) -> Optional[QQuickItem]:
    """item 所在的场景根项(`parentItem()` 一路到顶); 非 QQuickItem 返回 None.

    🔴 解析「对象属于哪个窗口」**绝不要**调 `QQuickItem.window()`: 在应用级事件过滤器
    里对焦点 TextInput 调它, 实测会让 PySide 把整个场景的 wrapper 判成失效(此后
    `shiboken6.isValid()` 全 False, 2026-10-28 定位)。场景根项不依赖窗口对象即可区分
    「主窗口」与「弹层原生窗口」: 两边根项不同即不同场景。
    """
    if not isinstance(obj, QQuickItem):
        return None
    current = obj
    for _ in range(_MAX_OWNER_HOPS):
        try:
            parent = current.parentItem()
        except (AttributeError, RuntimeError, TypeError):
            return None
        if parent is None:
            return current
        current = parent
    return None


# Qt 的窗口「类型」是枚举值(Window=1/Popup=9/ToolTip=13…), 低位掩码里只能整体比对,
# 不能用 `flags & Qt.ToolTip` —— ToolTip(13) 的二进制含 Window(1) 的位, 会把普通窗口误判。
_WINDOW_KIND_MASK = int(Qt.WindowType.WindowType_Mask)
_POPUP_WINDOW_KINDS = (
    int(Qt.WindowType.ToolTip),
    int(Qt.WindowType.Popup),
    int(Qt.WindowType.Tool),
)


def _is_popup_surface(window: QWindow) -> bool:
    """按窗口类型判断是否是本应用的弹层原生表面(候选列表 / 菜单 / 工具提示)."""
    try:
        kind = int(window.flags()) & _WINDOW_KIND_MASK
    except (AttributeError, RuntimeError, TypeError):
        return False
    if kind in _POPUP_WINDOW_KINDS:
        return True
    try:
        return window.transientParent() is not None
    except (AttributeError, RuntimeError, TypeError):
        return False


def _press_in_other_window(watched, focus_obj) -> bool:
    """按下事件是否属于「焦点输入框之外的另一个窗口」的交互.

    弹层(候选列表/菜单)是独立原生窗口: 点它时坐标天然在输入框矩形之外, 但它属于
    这个输入控件自己的交互, 不得清焦点 —— 否则控件的失焦守卫会收掉正在点的弹层。

    一次真实点击会投递两次按下事件(先 `QQuickWindow`, 再命中的 item), 两种都要认:
    - 窗口级按下: 看窗口是不是弹层表面(`Qt.ToolTip`/`Qt.Popup`/`Qt.Tool`/transient)。
    - item 级按下: 弹层里的项父链被截断, 改用「场景根项」比较, 不在同一场景即弹层。
    解析不出来(单测桩/非 QML 对象)时按「不是其它窗口」处理, 保持旧行为。
    """
    if isinstance(watched, QWindow):
        return _is_popup_surface(watched)

    press_root = _scene_root_of(watched)
    focus_root = _scene_root_of(focus_obj)
    if press_root is None or focus_root is None:
        return False
    return press_root is not focus_root


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
        # 本应用其它窗口(弹层)里的点击 — 同样不清, 那是该输入控件自己的交互
        if _is_inside(focus_obj, gp) or _press_in_other_window(watched, focus_obj):
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
