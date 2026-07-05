# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design auxiliary navigation skin tests."""

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import Skin, Theme, register_types, setSkin, setTheme


ROOT = Path(__file__).resolve().parents[2]
NAVIGATION_DIR = ROOT / "prismqml" / "PrismQML" / "navigation"


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


def _bottom_tab_qml() -> bytes:
    navigation_url = NAVIGATION_DIR.as_posix()
    return f"""
import PrismQML
import "file:///{navigation_url}" as Nav

Nav.BottomTabBar {{
    width: 360
    model: [
        {{ "text": "Files", "icon": "Home" }},
        {{ "text": "Settings", "icon": "Settings" }}
    ]
    currentIndex: 1
}}
""".encode()


def test_prism_design_auxiliary_navigation_light_and_dark(qapp):
    setTheme(Theme.LIGHT)
    setSkin(Skin.PRISM_DESIGN)

    engine = QQmlApplicationEngine()
    register_types(engine)
    keep = []

    try:
        keep.append(_build(engine, b"""
import PrismQML
Paginator {
    currentPage: 2
    totalPages: 6
    visiblePages: 5
}
"""))
        paginator = keep[-1][1]
        assert paginator.property("_pageRadius") == 4
        assert _rgb(paginator.property("_pageIndicatorColor")) == (22, 124, 128)
        assert _rgb(paginator.property("_pageHoverColor")) == (230, 238, 237)
        assert _rgb(paginator.property("_pageTextColor")) == (21, 35, 38)
        assert _rgb(paginator.property("_pageSelectedTextColor")) == (255, 255, 255)

        keep.append(_build(engine, b"""
import PrismQML
PipsPager {
    pageCount: 4
    currentIndex: 1
}
"""))
        pips = keep[-1][1]
        assert pips.property("_pipRadius") == 4
        assert pips.property("_navButtonRadius") == 4
        assert _rgb(pips.property("_pipActiveColor")) == (22, 124, 128)
        assert _rgb(pips.property("_pipInactiveColor")) == (142, 164, 163)
        assert _rgb(pips.property("_navButtonHoverColor")) == (230, 238, 237)
        assert _rgb(pips.property("_navIconColor")) == (122, 141, 144)

        keep.append(_build(engine, _bottom_tab_qml()))
        bottom_tab = keep[-1][1]
        assert _rgb(bottom_tab.property("_bottomTabBackground")) == (238, 243, 242)
        assert _rgb(bottom_tab.property("_bottomTabDividerColor")) == (213, 223, 221)
        assert bottom_tab.property("_bottomTabDividerHeight") == 1

        setTheme(Theme.DARK)

        keep.append(_build(engine, b"""
import PrismQML
Paginator {
    currentPage: 2
    totalPages: 6
    visiblePages: 5
}
"""))
        dark_paginator = keep[-1][1]
        assert dark_paginator.property("_pageRadius") == 4
        assert _rgb(dark_paginator.property("_pageIndicatorColor")) == (85, 214, 210)
        assert _rgb(dark_paginator.property("_pageHoverColor")) == (29, 41, 43)
        assert _rgb(dark_paginator.property("_pageTextColor")) == (238, 245, 243)
        assert _rgb(dark_paginator.property("_pageSelectedTextColor")) == (6, 23, 24)

        keep.append(_build(engine, b"""
import PrismQML
PipsPager {
    pageCount: 4
    currentIndex: 1
}
"""))
        dark_pips = keep[-1][1]
        assert dark_pips.property("_pipRadius") == 4
        assert dark_pips.property("_navButtonRadius") == 4
        assert _rgb(dark_pips.property("_pipActiveColor")) == (85, 214, 210)
        assert _rgb(dark_pips.property("_pipInactiveColor")) == (73, 96, 99)
        assert _rgb(dark_pips.property("_navButtonHoverColor")) == (29, 41, 43)
        assert _rgb(dark_pips.property("_navIconColor")) == (113, 134, 135)

        keep.append(_build(engine, _bottom_tab_qml()))
        dark_bottom_tab = keep[-1][1]
        assert _rgb(dark_bottom_tab.property("_bottomTabBackground")) == (13, 18, 19)
        assert _rgb(dark_bottom_tab.property("_bottomTabDividerColor")) == (37, 52, 55)
        assert dark_bottom_tab.property("_bottomTabDividerHeight") == 1
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
