# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Editable ComboBox focus regressions. 可编辑下拉框焦点回归。

The candidate surface takes no focus in editable mode, so the control must keep the
list and its own focus state in step: expanding focuses the input, and losing that
focus dismisses the list.
可编辑模式的候选表面不持有焦点, 因此控件必须让候选列表与自身聚焦态保持一致:
展开即聚焦输入框, 失去焦点即收起候选。
"""

from __future__ import annotations

import os
from pathlib import Path

import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlProperty
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import Skin, Theme, register_types, setSkin, setTheme


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "combo-box-editable-focus.qml")
)
SCENE_SOURCE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 380
    height: 260
    visible: true
    color: Enums.backgroundColor

    ComboBox {
        objectName: "combo"
        x: 20
        y: 20
        width: 200
        feature: Enums.comboBox.feature_editable
        model: ["北京", "上海", "广州", "深圳"]
        placeholderText: "select"
    }

    Item {
        objectName: "elsewhere"
        x: 20
        y: 200
        width: 100
        height: 30
        focus: true
    }
}
"""


def _pump(milliseconds: int = 40) -> None:
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


def _descendants(root):
    pending = list(root.childItems())
    while pending:
        item = pending.pop()
        yield item
        pending.extend(item.childItems())


def _only(items, label):
    matches = list(items)
    assert len(matches) == 1, (label, [item.metaObject().className() for item in matches])
    return matches[0]


def _read(obj, name):
    prop = QQmlProperty(obj, name)
    assert prop.isValid(), (obj.metaObject().className(), name)
    return prop.read()


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    register_types(engine)
    engine.addImportPath(str(ROOT / "prismqml"))
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE.encode("utf-8"), SCENE_URL)
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

    combo = window.findChild(QQuickItem, "combo")
    elsewhere = window.findChild(QQuickItem, "elsewhere")
    core = _only(
        (
            item
            for item in _descendants(combo)
            if item.metaObject().indexOfProperty("useDefaultContent") >= 0
            and item.metaObject().indexOfProperty("isOpen") >= 0
        ),
        "core",
    )
    focus_line = _only(
        (
            item
            for item in _descendants(core)
            if item.metaObject().className().startswith("FocusLine")
        ),
        "focusLine",
    )
    return engine, component, window, core, focus_line, elsewhere, warnings


def _dispose_scene(qapp, engine, component, window) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def test_combo_box_editable_expand_focuses_the_input(qapp):
    """展开可编辑下拉必须同时聚焦输入框并显示聚焦线。

    The chevron click used to open the list while the control stayed visually
    unfocused, which is the state this contract removes.
    点箭头展开时控件曾保持"未聚焦"外观, 本契约消除该状态。
    """
    setTheme(Theme.LIGHT)
    setSkin(Skin.FLUENT)
    engine, component, window, core, focus_line, _elsewhere, warnings = _create_scene()
    try:
        assert core.property("editable") is True
        assert _read(core, "editableInput").property("activeFocus") is False
        assert focus_line.property("showLine") is False

        core.showPopup()
        assert _wait_for(lambda: core.property("isOpen"))
        assert _read(core, "editableInput").property("activeFocus") is True
        assert core.property("focused") is True
        assert focus_line.property("showLine") is True
        assert core.property("popupVisible") is True
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)
        setSkin(Skin.FLUENT)
        setTheme(Theme.LIGHT)


def test_combo_box_editable_dismisses_when_input_loses_focus(qapp):
    """可编辑下拉失去输入框焦点时必须收起候选列表。"""
    setTheme(Theme.LIGHT)
    setSkin(Skin.FLUENT)
    engine, component, window, core, focus_line, elsewhere, warnings = _create_scene()
    try:
        core.showPopup()
        assert _wait_for(lambda: core.property("isOpen"))
        assert _read(core, "editableInput").property("activeFocus") is True

        elsewhere.forceActiveFocus()
        assert _wait_for(lambda: core.property("isOpen") is False)
        assert _wait_for(lambda: core.property("popupVisible") is False)
        assert core.property("focused") is False
        assert focus_line.property("showLine") is False
        assert elsewhere.property("activeFocus") is True
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)
        setSkin(Skin.FLUENT)
        setTheme(Theme.LIGHT)
