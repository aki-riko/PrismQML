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
    assert dialog.property("_dialogRadius") == 10
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
        _assert_dialog_surface(message_box, (244, 248, 247), (199, 212, 211), (248, 250, 249))
        assert message_box.property("minWidth") == 288
        assert _rgb(message_box.property("_titleColor")) == (21, 35, 38)
        assert _rgb(message_box.property("_contentColor")) == (86, 106, 109)

        keep.append(_build(engine, b"""
import PrismQML
DialogBoxCore {
    actionsVisible: false
}
"""))
        dialog_core = keep[-1][1]
        _assert_dialog_surface(dialog_core, (244, 248, 247), (199, 212, 211), None)

        keep.append(_build(engine, b"""
import PrismQML
ConfirmDialog {
    title: "Delete"
    message: "This cannot be undone."
    level: Enums.statusLevel.error
}
"""))
        confirm_dialog = keep[-1][1]
        _assert_dialog_surface(confirm_dialog, (244, 248, 247), (199, 212, 211), (248, 250, 249))
        assert abs(confirm_dialog.property("_iconBackgroundOpacity") - 0.12) < 0.001

        keep.append(_build(engine, b"""
import PrismQML
MaskedDialog {}
"""))
        masked_dialog = keep[-1][1]
        _assert_dialog_surface(masked_dialog, (244, 248, 247), (199, 212, 211))

        keep.append(_build(engine, b"""
import PrismQML
ProgressDialog {
    title: "Loading"
    content: "Please wait"
    progress: 45
}
"""))
        progress_dialog = keep[-1][1]
        _assert_dialog_surface(progress_dialog, (244, 248, 247), (199, 212, 211))

        keep.append(_build(engine, b"""
import PrismQML
UpdateDialog {
    version: "1.2.3"
    currentVersion: "1.2.2"
    notes: "Prism skin update"
}
"""))
        update_dialog = keep[-1][1]
        _assert_dialog_surface(update_dialog, (244, 248, 247), (199, 212, 211), (248, 250, 249))
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
        _assert_dialog_surface(message_box, (31, 42, 45), (42, 57, 59), (18, 25, 27), 69)
        assert _rgb(message_box.property("_titleColor")) == (238, 245, 243)
        assert _rgb(message_box.property("_contentColor")) == (164, 181, 182)

        keep.append(_build(engine, b"""
import PrismQML
DialogBoxCore {
    actionsVisible: false
}
"""))
        dark_dialog_core = keep[-1][1]
        _assert_dialog_surface(dark_dialog_core, (31, 42, 45), (42, 57, 59), None, 69)

        keep.append(_build(engine, b"""
import PrismQML
MaskedDialog {}
"""))
        masked_dialog = keep[-1][1]
        _assert_dialog_surface(masked_dialog, (31, 42, 45), (42, 57, 59), None, 69)

        keep.append(_build(engine, b"""
import PrismQML
ProgressDialog {
    title: "Loading"
    content: "Please wait"
    progress: 45
}
"""))
        progress_dialog = keep[-1][1]
        _assert_dialog_surface(progress_dialog, (31, 42, 45), (42, 57, 59), None, 69)
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
