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


def _visual_child_with_object_name(root, object_name: str):
    pending = list(root.childItems())
    while pending:
        candidate = pending.pop()
        if candidate.objectName() == object_name:
            return candidate
        pending.extend(candidate.childItems())
    return None


def _bottom_tab_qml() -> bytes:
    navigation_url = NAVIGATION_DIR.as_posix()
    return f"""
import PrismQML
import "file:///{navigation_url}" as Nav

Nav.BottomTabBar {{
    width: 360
    model: [
        {{ "text": "Files", "icon": "Home" }},
        {{ "text": "Settings", "icon": "Settings", "badgeCount": 12 }}
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
        assert paginator.property("_pageRadius") == 10
        assert _rgb(paginator.property("_pageIndicatorColor")) == (11, 127, 137)
        assert _rgb(paginator.property("_pageHoverColor")) == (234, 244, 247)
        assert _rgb(paginator.property("_pageTextColor")) == (18, 34, 38)
        assert _rgb(paginator.property("_pageSelectedTextColor")) == (255, 255, 255)

        keep.append(_build(engine, b"""
import PrismQML
PipsPager {
    pageCount: 4
    currentIndex: 1
}
"""))
        pips = keep[-1][1]
        assert pips.property("_pipRadius") == 10
        assert pips.property("_navButtonRadius") == 10
        assert _rgb(pips.property("_pipActiveColor")) == (11, 127, 137)
        assert _rgb(pips.property("_pipInactiveColor")) == (120, 173, 184)
        assert _rgb(pips.property("_navButtonHoverColor")) == (234, 244, 247)
        assert _rgb(pips.property("_navIconColor")) == (118, 138, 145)

        keep.append(_build(engine, _bottom_tab_qml()))
        bottom_tab = keep[-1][1]
        assert _rgb(bottom_tab.property("_bottomTabBackground")) == (238, 245, 247)
        assert _rgb(bottom_tab.property("_bottomTabDividerColor")) == (214, 227, 230)
        assert bottom_tab.property("_bottomTabDividerHeight") == 1
        files_badge = _visual_child_with_object_name(bottom_tab, "navigationBadge_Files")
        settings_badge = _visual_child_with_object_name(bottom_tab, "navigationBadge_Settings")
        assert files_badge is not None
        assert settings_badge is not None
        assert files_badge.property("count") == 0
        assert not files_badge.property("visible")
        assert settings_badge.property("count") == 12
        assert settings_badge.property("visible")

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
        assert dark_paginator.property("_pageRadius") == 10
        assert _rgb(dark_paginator.property("_pageIndicatorColor")) == (109, 235, 242)
        assert _rgb(dark_paginator.property("_pageHoverColor")) == (33, 49, 54)
        assert _rgb(dark_paginator.property("_pageTextColor")) == (238, 247, 248)
        assert _rgb(dark_paginator.property("_pageSelectedTextColor")) == (4, 23, 25)

        keep.append(_build(engine, b"""
import PrismQML
PipsPager {
    pageCount: 4
    currentIndex: 1
}
"""))
        dark_pips = keep[-1][1]
        assert dark_pips.property("_pipRadius") == 10
        assert dark_pips.property("_navButtonRadius") == 10
        assert _rgb(dark_pips.property("_pipActiveColor")) == (109, 235, 242)
        assert _rgb(dark_pips.property("_pipInactiveColor")) == (106, 169, 181)
        assert _rgb(dark_pips.property("_navButtonHoverColor")) == (33, 49, 54)
        assert _rgb(dark_pips.property("_navIconColor")) == (115, 138, 145)

        keep.append(_build(engine, _bottom_tab_qml()))
        dark_bottom_tab = keep[-1][1]
        assert _rgb(dark_bottom_tab.property("_bottomTabBackground")) == (9, 14, 16)
        assert _rgb(dark_bottom_tab.property("_bottomTabDividerColor")) == (34, 52, 58)
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
