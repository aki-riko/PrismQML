# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design dialog and modal skin tests."""

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import Skin, Theme, register_types, setSkin, setTheme


def _build(engine, qml: bytes):
    component = QQmlComponent(engine)
    component.setData(qml, QUrl("inline"))
    assert not component.isError(), [error.toString() for error in component.errors()]

    item = component.create(engine.rootContext())
    assert item is not None, [error.toString() for error in component.errors()]
    return component, item


def _rgb(qcolor):
    return (
        round(qcolor.redF() * 255),
        round(qcolor.greenF() * 255),
        round(qcolor.blueF() * 255),
    )


def _alpha(qcolor):
    return round(qcolor.alphaF() * 255)


def _assert_dialog_surface(dialog, background, border, action_row=None, shadow_alpha=46):
    assert dialog.property("_dialogRadius") == 12
    assert dialog.property("_dialogBorderWidth") == 1
    assert _rgb(dialog.property("_dialogBackground")) == background
    assert _rgb(dialog.property("_dialogBorderColor")) == border
    assert dialog.property("_dialogShadowBlur") == 32
    assert dialog.property("_dialogShadowOffset") == 8
    assert _alpha(dialog.property("_dialogShadowColor")) == shadow_alpha
    if action_row is not None:
        assert _rgb(dialog.property("_actionsRowBackground")) == action_row


def test_prism_design_dialogs_light_and_dark(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build(engine, b"""
import PrismQML
MessageBox {
    title: "Prism"
    content: "Dialog surface"
}
"""))
        message_box = keep[-1][1]
        _assert_dialog_surface(message_box, (248, 251, 255), (217, 227, 236), (251, 252, 254))
        assert message_box.property("minWidth") == 288
        assert _rgb(message_box.property("_titleColor")) == (23, 32, 42)
        assert _rgb(message_box.property("_contentColor")) == (95, 111, 128)

        keep.append(_build(engine, b"""
import PrismQML
ConfirmDialog {
    title: "Delete"
    message: "This cannot be undone."
    level: Enums.statusLevel.error
}
"""))
        confirm_dialog = keep[-1][1]
        _assert_dialog_surface(confirm_dialog, (248, 251, 255), (217, 227, 236), (251, 252, 254))
        assert abs(confirm_dialog.property("_iconBackgroundOpacity") - 0.12) < 0.001

        keep.append(_build(engine, b"""
import PrismQML
MaskedDialog {}
"""))
        masked_dialog = keep[-1][1]
        _assert_dialog_surface(masked_dialog, (248, 251, 255), (217, 227, 236))

        keep.append(_build(engine, b"""
import PrismQML
ProgressDialog {
    title: "Loading"
    content: "Please wait"
    progress: 45
}
"""))
        progress_dialog = keep[-1][1]
        _assert_dialog_surface(progress_dialog, (248, 251, 255), (217, 227, 236))

        keep.append(_build(engine, b"""
import PrismQML
UpdateDialog {
    version: "1.2.3"
    currentVersion: "1.2.2"
    notes: "Prism skin update"
}
"""))
        update_dialog = keep[-1][1]
        _assert_dialog_surface(update_dialog, (248, 251, 255), (217, 227, 236), (251, 252, 254))
        assert abs(update_dialog.property("_iconBackgroundOpacity") - 0.12) < 0.001

        setTheme(Theme.DARK)
        keep.append(_build(engine, b"""
import PrismQML
MessageBox {
    title: "Prism"
    content: "Dialog surface"
}
"""))
        message_box = keep[-1][1]
        _assert_dialog_surface(message_box, (36, 43, 52), (48, 58, 70), (23, 28, 34), 69)
        assert _rgb(message_box.property("_titleColor")) == (238, 243, 248)
        assert _rgb(message_box.property("_contentColor")) == (166, 177, 191)

        keep.append(_build(engine, b"""
import PrismQML
MaskedDialog {}
"""))
        masked_dialog = keep[-1][1]
        _assert_dialog_surface(masked_dialog, (36, 43, 52), (48, 58, 70), None, 69)

        keep.append(_build(engine, b"""
import PrismQML
ProgressDialog {
    title: "Loading"
    content: "Please wait"
    progress: 45
}
"""))
        progress_dialog = keep[-1][1]
        _assert_dialog_surface(progress_dialog, (36, 43, 52), (48, 58, 70), None, 69)
    finally:
        for component, item in reversed(keep):
            item.deleteLater()
            component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        qapp.processEvents()
        setTheme(Theme.LIGHT)
        setSkin(Skin.FLUENT)
