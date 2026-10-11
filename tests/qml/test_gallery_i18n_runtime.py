# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Gallery page runtime i18n regressions. Gallery 页面运行时翻译回归。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from examples.resources import register_gallery_resources
from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
INPUT_PAGE = QUrl.fromLocalFile(str(ROOT / "examples" / "pages" / "InputPage.qml"))
# Copy owned by the SwipeControl example card 滑动操作示例卡片持有的文案
SWIPE_TITLE = "SwipeControl"
SWIPE_DESCRIPTION = {
    "zh_CN": "滑动或拖拽行以露出操作",
    "en": "Swipe / drag a row to reveal actions",
}
SWIPE_ROW_TEXT = {
    "zh_CN": "标记 / 归档 / 删除此行",
    "en": "Flag / Archive / Delete this row",
}
# Revealed action captions 露出的操作按钮文案
SWIPE_ACTION_TEXT = {
    "zh_CN": ("归档", "删除", "邮件"),
    "en": ("Archive", "Delete", "Mail"),
}


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _visible_texts(page: QQuickItem) -> list[str]:
    """Collect rendered text through the visual tree. 通过可视树收集已渲染文本。"""
    values: list[str] = []

    def walk(item: QQuickItem) -> None:
        value = item.property("text")
        if isinstance(value, str) and value:
            values.append(value)
        for child in item.childItems():
            walk(child)

    walk(page)
    return values


def _select_language(translator, code: str, page: QQuickItem, expected: tuple[str, ...]) -> list[str]:
    translator.setProperty("language", code)
    for _ in range(20):
        texts = _visible_texts(page)
        if all(value in texts for value in expected):
            return texts
        _pump()
    raise AssertionError(f"{code}: {expected!r} never rendered")


def test_gallery_pages_render_translated_copy(qapp):
    """The gallery must show localized copy and follow runtime language switches.

    Gallery 必须显示本地化文案，并跟随运行时语言切换。
    """
    assert register_gallery_resources()
    engine = QQmlApplicationEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine, INPUT_PAGE)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    page = component.create(engine.rootContext())
    assert isinstance(page, QQuickItem), [error.toString() for error in component.errors()]
    page.setWidth(1132)
    page.setHeight(800)
    try:
        _pump(200)
        translator = engine.singletonInstance("PrismQML", "Translator")
        assert translator is not None

        expected_zh = (
            SWIPE_DESCRIPTION["zh_CN"],
            SWIPE_ROW_TEXT["zh_CN"],
            *SWIPE_ACTION_TEXT["zh_CN"],
        )
        chinese = _select_language(translator, "zh_CN", page, expected_zh)
        assert SWIPE_DESCRIPTION["en"] not in chinese
        assert not set(SWIPE_ACTION_TEXT["en"]) & set(chinese)
        # Component names stay English in every catalog 组件名在所有语言目录中都保持英文
        assert SWIPE_TITLE in chinese

        expected_en = (
            SWIPE_DESCRIPTION["en"],
            SWIPE_ROW_TEXT["en"],
            *SWIPE_ACTION_TEXT["en"],
        )
        english = _select_language(translator, "en", page, expected_en)
        assert SWIPE_DESCRIPTION["zh_CN"] not in english
        assert not set(SWIPE_ACTION_TEXT["zh_CN"]) & set(english)

        _select_language(translator, "zh_CN", page, expected_zh)
        assert warnings == [], warnings
    finally:
        page.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        _pump()
