# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""DateTimePicker visual stacking regressions. 日期时间选择器视觉层级回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import (
    Q_ARG,
    QEventLoop,
    QLocale,
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "date-time-picker-visual-regression.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property int expectedBaseZ: Enums.zIndex.base
    readonly property int expectedContentZ: Enums.zIndex.content
    readonly property int expectedPopupPanelOffset: Enums.popupMetrics.panelOffset
    readonly property string selectedLanguage: Translator.language
    readonly property string resolvedLanguage: Translator._resolvedLanguage
    readonly property var pickerDateOrder: picker._dateFieldOrder
    readonly property var pickerDisplayTexts: picker._buildDisplayModel().map(function(entry) { return entry.text })

    function useLanguage(code) { Translator.setLanguage(code) }
    function useAutoResolvedChinese() {
        Translator.setLanguage("zh_CN")
        Translator.language = "auto"
    }

    width: 700
    height: 400

    DateTimePicker {
        id: picker
        objectName: "picker"
        width: 520
        type: Enums.picker.type_datetime
        year: 2026
        month: 7
        day: 3
        hour: 10
        minute: 30
        second: 10
        timePrecision: Enums.picker.time_second
    }
}
"""

HOVER_SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 700
    height: 400
    visible: true

    DateTimePicker {
        id: picker
        objectName: "picker"
        x: 40
        y: 40
        width: 520
        type: Enums.picker.type_datetime
        timePrecision: Enums.picker.time_second
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1600) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _descendants(root: QObject) -> list[QObject]:
    result = []
    pending = list(root.children())
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(child.children())
    return result


def _new_visible_windows(windows_before):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
    ]


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _use_language(root, language, auto_resolved=False):
    previous_locale = QLocale() if auto_resolved else None
    if auto_resolved:
        # Keep auto-resolution deterministic across developer and CI locales.
        QLocale.setDefault(QLocale(language))
    try:
        if auto_resolved:
            assert QMetaObject.invokeMethod(root, "useAutoResolvedChinese")
            assert root.property("selectedLanguage") == "auto"
        else:
            assert QMetaObject.invokeMethod(
                root, "useLanguage", Q_ARG("QVariant", language)
            )
        assert _wait_for(lambda: root.property("resolvedLanguage") == language)
    finally:
        if previous_locale is not None:
            QLocale.setDefault(previous_locale)


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
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    picker = root.findChild(QObject, "picker")
    assert picker is not None
    return engine, component, root, picker, warnings


def _popup_parts(picker):
    popup_content = next(
        child
        for child in _descendants(picker)
        if all(
            child.metaObject().indexOfProperty(name) >= 0
            for name in ("col2Loader", "col3Loader", "hourWheelLoader")
        )
    )
    wheel_area = next(
        child
        for child in _descendants(popup_content)
        if child.metaObject().indexOfProperty("_wheelWidth") >= 0
    )
    row = next(
        child
        for child in wheel_area.childItems()
        if child.metaObject().className().startswith("QQuickRow")
    )
    highlight = next(
        child
        for child in wheel_area.childItems()
        if child.metaObject().className().startswith("QQuickRectangle")
    )
    loaders = [
        child
        for child in row.childItems()
        if child.metaObject().className().startswith("QQuickLoader")
        and child.property("active")
    ]
    return row, highlight, loaders


def _has_popup_content(picker):
    return any(
        child.metaObject().indexOfProperty("hourWheelLoader") >= 0
        and child.metaObject().indexOfProperty("minuteWheelLoader") >= 0
        for child in _descendants(picker)
    )


def _popup_core(picker):
    return next(
        child
        for child in _descendants(picker)
        if all(
            child.metaObject().indexOfProperty(name) >= 0
            for name in ("verticalCenterExpand", "isClosing", "popupWidth")
        )
    )


def _has_popup_core(picker):
    return any(
        all(
            child.metaObject().indexOfProperty(name) >= 0
            for name in ("verticalCenterExpand", "isClosing", "popupWidth")
        )
        for child in _descendants(picker)
    )


def _assert_vertically_centered(item, expected_center):
    center = item.property("y") + item.property("height") / 2
    assert center == pytest.approx(expected_center)


def _assert_reveal_geometry(root, popup, panel_scale, shadow):
    popup_height = popup.property("popupHeight")
    expected_y = root.property("expectedPopupPanelOffset")
    clip_height = popup.property("_clipHeight")
    assert 0 < clip_height < popup_height
    assert panel_scale is None
    assert shadow.property("width") == pytest.approx(popup.property("popupWidth"))
    assert shadow.property("height") == pytest.approx(popup_height)
    assert shadow.property("y") == pytest.approx(expected_y)


def _destroy_scene(engine, component, root):
    root.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    _pump()


def _create_hover_scene():
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(HOVER_SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    picker = window.findChild(QQuickItem, "picker")
    assert picker is not None
    assert _wait_for(window.isExposed)
    return engine, component, window, picker, warnings


def test_selected_row_text_stays_above_opaque_highlight(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, picker, warnings = _create_scene()
    try:
        _use_language(root, "fr")
        assert not picker.property("_popupContentRequested")
        assert not _has_popup_content(picker)
        picker.openPopup()
        assert picker.property("_popupContentRequested")
        assert _wait_for(lambda: picker.property("isOpen"))
        assert _wait_for(lambda: picker.property("_tempYear") == 2026)
        row, highlight, loaders = _popup_parts(picker)

        assert highlight.property("z") == root.property("expectedBaseZ")
        assert row.property("z") == root.property("expectedContentZ")
        assert row.property("z") > highlight.property("z")

        assert len(loaders) == 6
        date_indices = {"year": 100, "month": 6, "day": 2}
        date_order = _variant(picker.property("_dateFieldOrder"))
        expected_date_indices = [date_indices[field] for field in date_order]
        expected_indices = [*expected_date_indices, 10, 30, 10]
        assert _wait_for(
            lambda: [
                loader.property("item").property("currentIndex")
                for loader in loaders
            ]
            == expected_indices
        ), (
            [
                loader.property("item").property("currentIndex")
                for loader in loaders
            ],
            expected_indices,
            date_order,
        )
        assert warnings == []
    finally:
        picker.closePopup()
        _destroy_scene(engine, component, root)
        assert _new_visible_windows(windows_before) == []


def test_hover_prewarms_hidden_popup_without_opening(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, picker, warnings = _create_hover_scene()
    try:
        assert not _has_popup_core(picker)
        assert not picker.property("_popupContentRequested")
        assert not _has_popup_content(picker)

        QTest.mouseMove(window, QPoint(window.width() - 12, window.height() - 12))
        _pump()
        point = picker.mapToItem(
            window.contentItem(), QPointF(picker.width() / 2, picker.height() / 2)
        )
        QTest.mouseMove(window, point.toPoint())

        assert _wait_for(lambda: picker.property("_popupContentRequested"))
        assert _wait_for(lambda: _has_popup_content(picker))
        assert _wait_for(lambda: _has_popup_core(picker))
        popup = _popup_core(picker)
        assert _wait_for(lambda: popup.property("_prewarmed"))
        assert not picker.property("isOpen")
        assert not popup.property("isOpen")
        assert [
            item
            for item in _new_visible_windows(windows_before)
            if item is not window
        ] == []
        assert warnings == []
    finally:
        picker.closePopup()
        window.close()
        _destroy_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


@pytest.mark.parametrize(
    ("language", "auto_resolved", "expected_order", "expected_texts"),
    [
        (
            "zh_CN",
            True,
            ["year", "month", "day"],
            ["2026年", "7月", "3日", "10时", "30分", "10秒"],
        ),
        (
            "en",
            False,
            ["month", "day", "year"],
            ["July", "3", "2026", "10", "30", "10"],
        ),
        (
            "fr",
            False,
            ["day", "month", "year"],
            ["3", "Juillet", "2026", "10", "30", "10"],
        ),
    ],
)
def test_display_order_and_units_follow_i18n_locale(
    qapp, language, auto_resolved, expected_order, expected_texts
):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, picker, warnings = _create_scene()
    try:
        _use_language(root, language, auto_resolved)
        assert _variant(root.property("pickerDateOrder")) == expected_order
        assert _variant(root.property("pickerDisplayTexts")) == expected_texts
        assert warnings == []
    finally:
        picker.closePopup()
        _destroy_scene(engine, component, root)
        assert _new_visible_windows(windows_before) == []


def test_popup_reveals_from_plane_without_scaling_or_movement(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root, picker, warnings = _create_scene()
    try:
        assert not _has_popup_core(picker)
        picker.openPopup()
        assert _wait_for(lambda: _has_popup_core(picker))
        popup = _popup_core(picker)
        panel_scale = popup.findChild(QObject, "_popupPanelScale")
        shadow = popup.findChild(QObject, "_popupShadow")
        assert popup.property("verticalCenterExpand")
        assert panel_scale is None
        assert shadow is not None

        assert _wait_for(lambda: popup.property("isOpen"))
        _pump()
        _assert_reveal_geometry(root, popup, panel_scale, shadow)
        assert _wait_for(
            lambda: popup.property("_clipHeight")
            == pytest.approx(popup.property("popupHeight"))
        )
        assert warnings == []
    finally:
        picker.closePopup()
        _destroy_scene(engine, component, root)
        assert _new_visible_windows(windows_before) == []
