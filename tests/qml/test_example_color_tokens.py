# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Example page color-token runtime regressions. 示例页面颜色令牌运行时回归。"""

import re
from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickView

from prismqml import Skin, Theme, register_types, setSkin, setTheme


ROOT = Path(__file__).resolve().parents[2]
CHART_PAGE_PATH = ROOT / "examples" / "pages" / "ChartPage.qml"
PAGE_NAMES = (
    "CarouselPage.qml",
    "ChartPage.qml",
    "EffectsPage.qml",
    "IconPage.qml",
    "InputPage.qml",
    "MenuPage.qml",
)
SOURCE_REFERENCES = {
    "CarouselPage.qml": {"examplePageColors.carouselRed"},
    "ChartPage.qml": {"chartColors.palette[5]"},
    "EffectsPage.qml": {"Enums.transparent", "stateColor.dialogBorder"},
    "IconPage.qml": {"Enums.transparent"},
    "InputPage.qml": {"chartColors.palette[3]"},
    "MenuPage.qml": {
        "stateColor.treeItemHover",
        "examplePageColors.tableDivider",
        "examplePageColors.statusEnabledBg",
        "examplePageColors.statusDisabledText",
    },
    "SettingsPage.qml": {"examplePageColors.settingsCustomAccent"},
}
EXPECTED_FIXED_COLORS = {
    "carouselRed": "#e74c3c",
    "carouselBlue": "#3498db",
    "carouselGreen": "#2ecc71",
    "carouselPurple": "#9b59b6",
    "statusEnabledText": "#1fa84d",
    "statusDisabledText": "#c93c3c",
    "settingsCustomAccent": "#ff6b6b",
    "chartBlue": "#0078d4",
    "chartGreen": "#107c10",
    "chartGold": "#ffb900",
    "chartRed": "#d13438",
    "chartCyan": "#00b7c3",
}
TOKEN_SOURCE = b"""import QtQuick
import PrismQML
QtObject {
    property color carouselRed: Enums.examplePageColors.carouselRed
    property color carouselBlue: Enums.examplePageColors.carouselBlue
    property color carouselGreen: Enums.examplePageColors.carouselGreen
    property color carouselPurple: Enums.examplePageColors.carouselPurple
    property color tableDivider: Enums.examplePageColors.tableDivider
    property color statusEnabledBg: Enums.examplePageColors.statusEnabledBg
    property color statusDisabledBg: Enums.examplePageColors.statusDisabledBg
    property color statusEnabledText: Enums.examplePageColors.statusEnabledText
    property color statusDisabledText: Enums.examplePageColors.statusDisabledText
    property color settingsCustomAccent: Enums.examplePageColors.settingsCustomAccent
    property color chartBlue: Enums.chartColors.palette[0]
    property color chartGreen: Enums.chartColors.palette[1]
    property color chartGold: Enums.chartColors.palette[2]
    property color chartRed: Enums.chartColors.palette[3]
    property color chartCyan: Enums.chartColors.palette[5]
    property color transparentColor: Enums.transparent
    property color dialogBorder: Enums.stateColor.dialogBorder
    property color treeHover: Enums.stateColor.treeItemHover
    property color selected: Enums.stateColor.selected
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_until_ready(component: QQmlComponent) -> None:
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            return
        _pump(20)


def _create_inline(engine: QQmlApplicationEngine):
    component = QQmlComponent(engine)
    component.setData(TOKEN_SOURCE, QUrl("inline:p9-example-color-tokens.qml"))
    _wait_until_ready(component)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    instance = component.create(engine.rootContext())
    assert instance is not None, [error.toString() for error in component.errors()]
    return component, instance


def _rgba(color: QColor) -> tuple[float, float, float, float]:
    return color.redF(), color.greenF(), color.blueF(), color.alphaF()


def _find_visual_item(root, object_name: str):
    if root.objectName() == object_name:
        return root
    for child in root.childItems():
        match = _find_visual_item(child, object_name)
        if match is not None:
            return match
    return None


def _assert_color(instance, name: str, expected: str) -> None:
    assert _rgba(instance.property(name)) == pytest.approx(
        _rgba(QColor(expected)), abs=1 / 65535
    )


def _assert_alpha(instance, name: str, expected: float) -> None:
    assert instance.property(name).alphaF() == pytest.approx(
        expected, abs=1 / 65535
    )


def _load_page(engine: QQmlApplicationEngine, page_name: str):
    page_path = ROOT / "examples" / "pages" / page_name
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(page_path)))
    _wait_until_ready(component)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    page = component.create(engine.rootContext())
    assert page is not None, [error.toString() for error in component.errors()]
    return component, page


def test_migrated_example_sources_reference_global_color_tokens():
    page_root = ROOT / "examples" / "pages"
    for page_name, references in SOURCE_REFERENCES.items():
        source = (page_root / page_name).read_text(encoding="utf-8")
        assert all(reference in source for reference in references), page_name


def test_horizontal_bar_gallery_uses_the_skin_chart_palette():
    source = CHART_PAGE_PATH.read_text(encoding="utf-8")
    match = re.search(
        r"Horizontal Bar Chart.*?(?P<section>ExampleCard \{.*?)"
        r"// ==================== Line Chart",
        source,
        re.DOTALL,
    )
    assert match is not None
    section = match.group("section")
    assert "demoPalette." not in section
    label_keys = (
        "gallery_bc89675cb97d885b",
        "gallery_37a41cac23af4aca",
        "gallery_14ae1ed5ea1092e3",
        "gallery_2fc2cfbe651c8f7a",
        "gallery_d00568f458f0dfd1",
    )
    for index, label_key in enumerate(label_keys):
        assert (
            f'{{label: Fluent.Translator.tr("{label_key}", '
            "Fluent.Translator._v), value: "
            in section
        )
        assert f"chartColors.palette[{index}]" in section


def _assert_light_values(instance) -> None:
    for name, color in EXPECTED_FIXED_COLORS.items():
        _assert_color(instance, name, color)
    assert _rgba(instance.property("statusEnabledBg")) == pytest.approx(
        (0.18, 0.75, 0.45, 0.12), abs=1 / 65535
    )
    assert _rgba(instance.property("statusDisabledBg")) == pytest.approx(
        (0.85, 0.25, 0.25, 0.10), abs=1 / 65535
    )
    _assert_alpha(instance, "transparentColor", 0)
    _assert_alpha(instance, "dialogBorder", 0.1)
    _assert_alpha(instance, "treeHover", 0.035)
    _assert_alpha(instance, "tableDivider", 0.05)


def test_example_color_tokens_preserve_fluent_values_and_dark_divider(qapp):
    setSkin(Skin.FLUENT)
    setTheme(Theme.LIGHT)
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = instance = None
    try:
        component, instance = _create_inline(engine)
        _assert_light_values(instance)
        setTheme(Theme.DARK)
        _pump()
        _assert_alpha(instance, "tableDivider", 0.06)
    finally:
        setTheme(Theme.LIGHT)
        setSkin(Skin.FLUENT)
        if instance is not None:
            instance.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_migrated_example_pages_load_with_global_color_tokens(qapp):
    setSkin(Skin.FLUENT)
    setTheme(Theme.LIGHT)
    engine = QQmlApplicationEngine()
    register_types(engine)
    retained = []
    try:
        for page_name in PAGE_NAMES:
            retained.append(_load_page(engine, page_name))
        _pump(20)
    finally:
        setTheme(Theme.LIGHT)
        setSkin(Skin.FLUENT)
        for component, page in reversed(retained):
            page.deleteLater()
            component.deleteLater()
        engine.deleteLater()
        _pump(1)


def test_gallery_list_view_current_item_keeps_selected_visual(qapp):
    setSkin(Skin.FLUENT)
    setTheme(Theme.LIGHT)
    view = QQuickView()
    engine = view.engine()
    register_types(engine)
    token_component = token_instance = page = None
    try:
        token_component, token_instance = _create_inline(engine)
        page_path = ROOT / "examples" / "pages" / "MenuPage.qml"
        view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
        view.resize(1200, 900)
        view.setSource(QUrl.fromLocalFile(str(page_path)))
        assert view.status() == QQuickView.Status.Ready, [
            error.toString() for error in view.errors()
        ]
        page = view.rootObject()
        assert page is not None
        view.show()
        _pump(150)

        list_view = _find_visual_item(page, "galleryListViewDemo")
        assert list_view is not None
        list_view.setProperty("currentIndex", 2)
        _pump(150)

        selected_delegate = _find_visual_item(page, "galleryListViewDelegate-2")
        other_delegate = _find_visual_item(page, "galleryListViewDelegate-1")
        assert selected_delegate is not None
        assert other_delegate is not None
        assert selected_delegate.property("_selected") is True
        assert other_delegate.property("_selected") is False
        assert _rgba(selected_delegate.property("color")) == pytest.approx(
            _rgba(token_instance.property("selected")), abs=1 / 65535
        )
    finally:
        setTheme(Theme.LIGHT)
        setSkin(Skin.FLUENT)
        if page is not None:
            page.deleteLater()
        if token_instance is not None:
            token_instance.deleteLater()
        if token_component is not None:
            token_component.deleteLater()
        view.close()
        view.deleteLater()
        _pump(1)
