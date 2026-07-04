# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design picker input skin tests."""

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import Skin, Theme, register_types, setSkin, setTheme


def _build_file(engine, path: Path):
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(path)))
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


def test_prism_design_datetime_picker_popup_selection_highlight(qapp):
    popup_path = (
        Path(__file__).resolve().parents[2]
        / "prismqml"
        / "PrismQML"
        / "controls"
        / "inputs"
        / "Picker"
        / "_internal"
        / "DateTimePickerPopup.qml"
    )

    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build_file(engine, popup_path))
        popup = keep[-1][1]
        assert _rgb(popup.property("_selectionHighlightColor")) == (219, 234, 255)

        setTheme(Theme.DARK)
        keep.append(_build_file(engine, popup_path))
        dark_popup = keep[-1][1]
        assert _rgb(dark_popup.property("_selectionHighlightColor")) == (29, 58, 99)
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
