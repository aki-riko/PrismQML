# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""BottomSheet runtime contracts. BottomSheet 运行时合同。"""

from pathlib import Path

import pytest
import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import Skin, getSkin, register_types, setSkin

ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "bottom-sheet.qml"))
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property int detentMedium: Enums.sheet.detent_medium
    readonly property int detentLarge: Enums.sheet.detent_large
    readonly property real mediumRatio: Enums.sheet.mediumRatio
    readonly property int topInset: Enums.sheet.topInset
    readonly property int maxWidth: Enums.sheet.maxWidth
    readonly property int modalZ: Enums.zIndex.modal

    width: 800
    height: 600
    visible: true

    BottomSheet {
        id: sheet
        objectName: "sheet"

        Rectangle {
            objectName: "sheetContent"
            width: 80
            height: 40
        }
    }
}
"""


def _pump(milliseconds: int = 30) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 30
    return predicate()


def _create_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    _pump()
    return engine, component, window, warnings


def _dispose_scene(engine, component, window) -> None:
    if shiboken6.isValid(window):
        window.close()
        window.deleteLater()
    component.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.fixture
def sheet_scene(qapp):
    engine, component, window, warnings = _create_scene()
    try:
        sheet = window.findChild(QQuickItem, "sheet")
        panel = sheet.findChild(QQuickItem, "bottomSheetPanel")
        assert sheet is not None and panel is not None
        yield window, sheet, panel, warnings
    finally:
        _dispose_scene(engine, component, window)


def _open(sheet) -> None:
    sheet.metaObject().invokeMethod(sheet, "open")
    assert _wait_for(lambda: sheet.property("revealProgress") == 1)


def _close(sheet) -> None:
    # Record progress at the instant the sheet hides: the slide-out must already be
    # complete, otherwise the base restore timer cut it short.
    # 记录弹层隐藏瞬间的进度：此时滑出必须已完成，否则说明基类恢复计时器截断了它。
    progress_at_hide = []

    def _on_visible_changed():
        if not sheet.isVisible():
            progress_at_hide.append(sheet.property("revealProgress"))

    sheet.visibleChanged.connect(_on_visible_changed)
    try:
        sheet.metaObject().invokeMethod(sheet, "close")
        assert _wait_for(lambda: not sheet.isVisible())
    finally:
        sheet.visibleChanged.disconnect(_on_visible_changed)
    assert progress_at_hide == [0]


def test_bottom_sheet_is_hidden_until_opened(sheet_scene):
    _window, sheet, _panel, warnings = sheet_scene

    assert not sheet.isVisible()
    assert sheet.property("revealProgress") == 0
    assert warnings == []


def test_bottom_sheet_rests_at_medium_detent_on_window_overlay(sheet_scene):
    window, sheet, panel, warnings = sheet_scene

    _open(sheet)

    assert sheet.isVisible()
    assert sheet.parentItem() is window.contentItem()
    assert sheet.z() == window.property("modalZ")
    expected_height = window.height() * window.property("mediumRatio")
    assert panel.height() == pytest.approx(expected_height)
    assert panel.y() == pytest.approx(window.height() - expected_height)
    assert panel.width() == min(window.width(), window.property("maxWidth"))
    assert panel.x() == pytest.approx((window.width() - panel.width()) / 2)
    content = sheet.findChild(QQuickItem, "sheetContent")
    assert content is not None and content.isVisible()
    assert warnings == []


def test_bottom_sheet_large_detent_leaves_top_inset(sheet_scene):
    window, sheet, panel, _warnings = sheet_scene

    sheet.setProperty("detent", window.property("detentLarge"))
    _open(sheet)

    assert panel.y() == pytest.approx(window.property("topInset"))
    assert panel.height() == pytest.approx(
        window.height() - window.property("topInset")
    )


def test_bottom_sheet_close_slides_out_and_hides(sheet_scene):
    window, sheet, panel, warnings = sheet_scene

    _open(sheet)
    _close(sheet)

    assert sheet.property("revealProgress") == 0
    assert panel.y() == pytest.approx(window.height())
    assert sheet.property("opened") is False
    assert warnings == []


def test_bottom_sheet_reopen_after_close(sheet_scene):
    _window, sheet, _panel, warnings = sheet_scene

    _open(sheet)
    _close(sheet)
    _open(sheet)

    assert sheet.isVisible()
    assert warnings == []


@pytest.mark.parametrize("skin", list(Skin))
def test_bottom_sheet_opens_without_warnings_in_every_skin(qapp, skin):
    previous_skin = getSkin()
    setSkin(skin)
    _pump()
    engine, component, window, warnings = _create_scene()
    try:
        sheet = window.findChild(QQuickItem, "sheet")
        _open(sheet)
        assert warnings == [], (skin, warnings)
    finally:
        _dispose_scene(engine, component, window)
        setSkin(previous_skin)
        _pump()
