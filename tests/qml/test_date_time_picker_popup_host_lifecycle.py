# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""DateTimePicker popup-host lifecycle regressions. 日期时间选择器弹层宿主生命周期回归。"""

from __future__ import annotations

import os
from pathlib import Path

import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QMetaObject, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(
    os.environ.get("PRISMQML_TEST_ROOT", Path(__file__).resolve().parents[2])
).resolve()
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "date-time-picker-popup-host-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    width: 480
    height: 280
    visible: true

    DateTimePicker {
        objectName: "picker"
        x: 40
        y: 40
        width: 320
        type: Enums.picker.type_datetime
        timePrecision: Enums.picker.time_second
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
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


def _popup_hosts(picker: QQuickItem) -> list[QObject]:
    return [
        child
        for child in picker.findChildren(QObject)
        if child.metaObject().className().startswith("PopupWindowCore_QMLTYPE_")
    ]


def _object_count(picker: QQuickItem) -> int:
    return 1 + len(picker.findChildren(QObject))


def _init_timer(picker: QQuickItem) -> QObject:
    timer = picker.findChild(QObject, "dateTimePickerInitTimer")
    assert timer is not None
    return timer


def _dispose(qapp, engine, component, window) -> None:
    if window is not None and shiboken6.isValid(window):
        window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def test_date_time_picker_creates_popup_host_on_first_intent(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
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
    picker = window.findChild(QQuickItem, "picker")
    assert picker is not None
    assert _wait_for(window.isExposed)

    try:
        lazy_host = picker.metaObject().indexOfProperty("_popupHostRequested") >= 0
        cold_objects = _object_count(picker)
        cold_hosts = _popup_hosts(picker)
        init_timer = _init_timer(picker)
        assert len(cold_hosts) == (0 if lazy_host else 1)
        assert not picker.property("_popupContentRequested")
        assert init_timer.parent() is picker
        assert init_timer.property("host") == picker
        assert init_timer.property("interval") == 50
        assert init_timer.property("repeat") is False
        assert init_timer.property("running") is False

        assert QMetaObject.invokeMethod(picker, "_prewarmPopupContent")
        assert _wait_for(lambda: len(_popup_hosts(picker)) == 1)
        popup = _popup_hosts(picker)[0]
        assert _wait_for(lambda: bool(popup.property("_prewarmed")))
        assert not picker.property("isOpen")
        assert not popup.property("isOpen")
        warm_objects = _object_count(picker)

        assert QMetaObject.invokeMethod(picker, "openPopup")
        assert picker.property("_initializing") is True
        assert init_timer.property("running") is True
        assert _wait_for(lambda: picker.property("isOpen") and popup.property("isOpen"))
        assert _wait_for(lambda: not picker.property("_initializing"))
        assert init_timer.property("running") is False
        assert QMetaObject.invokeMethod(picker, "closePopup")
        assert _wait_for(
            lambda: not picker.property("isOpen")
            and not popup.property("isOpen")
            and not popup.property("isClosing")
        )

        assert QMetaObject.invokeMethod(picker, "openPopup")
        assert picker.property("_initializing") is True
        assert init_timer.property("running") is True
        assert QMetaObject.invokeMethod(picker, "closePopup")
        assert picker.property("_initializing") is False
        assert init_timer.property("running") is False
        assert _wait_for(
            lambda: not picker.property("isOpen")
            and not popup.property("isOpen")
            and not popup.property("isClosing")
        )

        print(
            "DATE_TIME_POPUP_HOST",
            f"objects={cold_objects}/{warm_objects}",
            f"lazy_host={lazy_host}",
        )
        if lazy_host:
            assert cold_objects + 40 < warm_objects
        assert warnings == []
        assert [
            item
            for item in QGuiApplication.topLevelWindows()
            if item.isVisible()
            and item is not window
            and not any(item is existing for existing in windows_before)
        ] == []
    finally:
        _dispose(qapp, engine, component, window)
        assert [
            item
            for item in QGuiApplication.topLevelWindows()
            if item.isVisible()
            and not any(item is existing for existing in windows_before)
        ] == []
