# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Popup surface window-activation contract. 弹层表面窗口激活契约。

An editable ComboBox keeps focus in its input while the candidate list is open, so its
popup surface must not take window activation either. If the platform activates that
native surface, the owner window goes inactive, the owner's input loses activeFocus, and
`ComboBoxCore`'s focus-loss guard dismisses the popup — the first click inside the list
closes it instead of selecting a row.
可编辑下拉框在候选列表展开期间把焦点留在输入框，因此它的弹层表面同样不能参与窗口激活。
平台一旦激活那个原生表面，宿主窗口就会转为非激活、宿主输入框失去 activeFocus，
`ComboBoxCore` 的失焦守卫随即驳回弹层 —— 列表里的第一次点击会关掉它而不是选中一行。

The surface that DOES own focus must keep ordinary activation, or its own focus-based
dismissal contract breaks.
真正持有焦点的表面必须保留常规激活能力，否则它自身的失焦驳回契约会失效。
"""

import shiboken6
from PySide6.QtCore import QEventLoop, QTimer, QUrl, Qt
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: scene
    width: 420
    height: 300
    visible: true

    ComboBox {
        objectName: "editableCombo"
        x: 20
        y: 20
        width: 200
        feature: Enums.comboBox.feature_editable
        model: ["alpha", "beta"]
    }

    ComboBox {
        objectName: "readonlyCombo"
        x: 20
        y: 90
        width: 200
        model: ["alpha", "beta"]
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _descendants(item):
    pending = list(item.childItems())
    while pending:
        child = pending.pop()
        yield child
        pending.extend(child.childItems())


def _core_of(combo):
    matches = [
        item
        for item in _descendants(combo)
        if item.metaObject().indexOfProperty("useDefaultContent") >= 0
        and item.metaObject().indexOfProperty("isOpen") >= 0
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _native_surface_of(core):
    """弹层核心里的原生 Window（懒创建，需要先打开）。"""
    for child in core.findChildren(QQuickWindow):
        return child
    return None


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath("prismqml")
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, QUrl("popup-native-focus-flags.qml"))
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    assert _wait_for(window.isExposed)
    _pump(120)
    return engine, component, window, warnings


def _dispose(engine, component, window):
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    _pump(60)


def _open_and_get_surface(combo):
    core = _core_of(combo)
    core.showPopup()
    assert _wait_for(lambda: core.property("isOpen")), "popup never opened"
    _pump(120)
    surface = _native_surface_of(core)
    assert surface is not None, "native popup surface was never created"
    assert surface.isVisible()
    return core, surface


def _assert_no_activation(surface, label):
    flags = surface.flags()
    assert flags & Qt.WindowType.WindowDoesNotAcceptFocus, (
        f"{label} 弹层表面必须声明 Qt.WindowDoesNotAcceptFocus，"
        f"否则点击它会抢走宿主窗口激活并让失焦守卫关掉弹层（实际 flags={int(flags)}）"
    )


def test_editable_popup_surface_never_takes_window_activation(qapp):
    """可编辑下拉的弹层表面不得参与窗口激活（点击列表不应关闭它）。"""
    engine, component, window, warnings = _create_scene()
    try:
        combo = window.findChild(QQuickItem, "editableCombo")
        assert combo is not None
        _core, surface = _open_and_get_surface(combo)
        _assert_no_activation(surface, "可编辑")
        assert warnings == []
    finally:
        _dispose(engine, component, window)


def test_focus_owning_popup_surface_keeps_normal_activation(qapp):
    """持有焦点的弹层表面必须保留常规激活，否则它自身的失焦契约失效。"""
    engine, component, window, warnings = _create_scene()
    try:
        combo = window.findChild(QQuickItem, "readonlyCombo")
        assert combo is not None
        _core, surface = _open_and_get_surface(combo)
        flags = surface.flags()
        assert not (flags & Qt.WindowType.WindowDoesNotAcceptFocus), (
            "非可编辑弹层表面必须可被激活（它靠自身失焦驳回）"
        )
        assert warnings == []
    finally:
        _dispose(engine, component, window)
