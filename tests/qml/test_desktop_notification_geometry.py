# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Desktop notification runtime geometry regressions. 桌面通知运行态几何回归。"""

from __future__ import annotations

import json
from pathlib import Path
import time

import pytest
from PySide6.QtCore import QObject, QPointF, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
REAL_EXPORT_PATH = (
    r"C:\Users\Kotori\AppData\Roaming\Kaleidos\recordings\clip_20260719_224354.mp4"
)
REAL_EXPORT_MESSAGE = f"00:14\n{REAL_EXPORT_PATH}"
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "desktop-notification-geometry.qml")
)
SCENE_SOURCE = f"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {{
    id: host

    property var firstToast: null
    property var secondToast: null
    property var standalone: null
    readonly property int screenMargin: Enums.notification.layout.screenMargin
    readonly property int stackGap: Enums.notification.layout.stackGapSmall
    readonly property int spacingXs: Enums.spacing.xs
    readonly property int spacingM: Enums.spacing.m
    readonly property int progressFeature: Enums.notification.feature_progress_bar
    readonly property color optionColor: Enums.accentColor
    readonly property real optionRadius: Enums.radius.large

    function createLateConfiguredExportToast() {{
        firstToast = NotificationManager.desktop.success(
            "导出成功",
            {json.dumps(REAL_EXPORT_MESSAGE, ensure_ascii=False)},
            0,
            Enums.notification.posBottomRight
        )
        firstToast.orient = Qt.Vertical
        firstToast.customContent = exportAction
    }}

    function createConfiguredExportToast() {{
        firstToast = NotificationManager.desktop.success(
            "导出成功",
            {json.dumps(REAL_EXPORT_MESSAGE, ensure_ascii=False)},
            0,
            Enums.notification.posBottomRight,
            {{
                "orient": Qt.Vertical,
                "customContent": wideExportAction,
                "closable": false,
                "feature": Enums.notification.feature_progress_bar,
                "progress": 0.25,
                "screen": host.screen
            }}
        )
    }}

    function createStackedToasts() {{
        firstToast = NotificationManager.desktop.success(
            "第一条", "底部通知", 0, Enums.notification.posBottomRight,
            {{ "screen": host.screen }}
        )
        secondToast = NotificationManager.desktop.info(
            "第二条", "上方通知", 0, Enums.notification.posBottomRight,
            {{ "screen": host.screen }}
        )
    }}

    function createConfiguredInfoBar() {{
        firstToast = NotificationManager.desktop.infoBar(
            "warning",
            "处理中",
            "正在准备导出文件",
            0,
            Enums.notification.posTopRight,
            {{
                "orient": Qt.Vertical,
                "customContent": exportAction,
                "closable": false,
                "feature": Enums.notification.feature_progress_bar,
                "progress": 0.5,
                "backgroundColorLight": host.optionColor,
                "backgroundColorDark": host.optionColor,
                "icon": "Warning",
                "radius": host.optionRadius,
                "screen": host.screen
            }}
        )
    }}

    function growFirstToast() {{
        firstToast.orient = Qt.Vertical
        firstToast.customContent = tallExportAction
    }}

    function createStandaloneNotification() {{
        standalone = standaloneComponent.createObject(null, {{ "screen": host.screen }})
        standalone.show()
    }}

    function closeNotifications() {{
        NotificationManager.closeAllDesktopNotifications()
        if (standalone) {{
            standalone.visible = false
            standalone.destroy()
            standalone = null
        }}
        firstToast = null
        secondToast = null
    }}

    width: 640
    height: 480
    visible: false

    Component {{
        id: exportAction
        Item {{
            objectName: "exportAction"
            implicitWidth: 320
            implicitHeight: 40
            width: implicitWidth
            height: implicitHeight
        }}
    }}

    Component {{
        id: wideExportAction
        Item {{
            objectName: "wideExportAction"
            implicitWidth: 520
            implicitHeight: 40
            width: implicitWidth
            height: implicitHeight
        }}
    }}

    Component {{
        id: tallExportAction
        Item {{
            objectName: "tallExportAction"
            implicitWidth: 320
            implicitHeight: 120
            width: implicitWidth
            height: implicitHeight
        }}
    }}

    Component {{
        id: standaloneAction
        Item {{
            objectName: "standaloneAction"
            implicitWidth: 320
            implicitHeight: 72
            width: implicitWidth
            height: implicitHeight
        }}
    }}

    Component {{
        id: standaloneComponent
        DesktopNotification {{
            objectName: "standaloneNotification"
            title: "导出成功"
            message: {json.dumps(REAL_EXPORT_MESSAGE, ensure_ascii=False)}
            duration: 0
            position: Enums.notification.posBottomRight
            customContent: standaloneAction
        }}
    }}
}}
""".encode("utf-8")


def _wait_until(predicate, timeout_ms: int = 1500) -> None:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        QGuiApplication.processEvents()
        if predicate():
            return
        QTest.qWait(10)
    assert predicate()


def _create_scene() -> tuple[QQmlApplicationEngine, QQmlComponent, QQuickWindow]:
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    _wait_until(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert isinstance(root, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    return engine, component, root


def _toast(root: QQuickWindow, property_name: str = "firstToast") -> QObject:
    toast = root.property(property_name)
    assert isinstance(toast, QObject)
    return toast


def _overlay(toast: QObject) -> QQuickWindow:
    window = toast.window()
    assert isinstance(window, QQuickWindow)
    return window


def _dispose(
    engine: QQmlApplicationEngine,
    component: QQmlComponent,
    root: QQuickWindow,
) -> None:
    root.closeNotifications()
    QTest.qWait(20)
    root.deleteLater()
    del component
    engine.deleteLater()
    QGuiApplication.processEvents()


def test_real_export_toast_reanchors_after_late_custom_content(qapp):
    """截图中的真实导出输入后注入按钮时仍贴合可用工作区底边。"""
    engine, component, root = _create_scene()
    try:
        root.createLateConfiguredExportToast()
        toast = _toast(root)
        overlay = _overlay(toast)
        _wait_until(
            lambda: toast.property("hasCustomContent") is True and overlay.isVisible()
        )
        QTest.qWait(400)

        geometry = overlay.screen().availableGeometry()
        expected_bottom = geometry.y() + geometry.height() - root.property("screenMargin")
        actual_bottom = overlay.y() + overlay.height()

        assert toast.property("message") == REAL_EXPORT_MESSAGE
        assert actual_bottom == pytest.approx(expected_bottom, abs=1)
        assert actual_bottom <= geometry.y() + geometry.height()
    finally:
        _dispose(engine, component, root)


def test_desktop_options_apply_before_show_and_overlay_tracks_width(qapp):
    """创建参数必须在首帧生效，原生浮层宽度跟随实际通知宽度。"""
    engine, component, root = _create_scene()
    try:
        root.createConfiguredExportToast()
        toast = _toast(root)
        overlay = _overlay(toast)
        _wait_until(
            lambda: toast.property("hasCustomContent") is True and overlay.isVisible()
        )
        QTest.qWait(400)

        assert toast.property("orient") == 2  # Qt.Vertical
        assert toast.property("closable") is False
        assert toast.property("feature") == root.property("progressFeature")
        assert toast.property("progress") == pytest.approx(0.25)
        assert toast.findChild(QObject, "wideExportAction") is not None
        assert overlay.width() == pytest.approx(
            toast.width() + root.property("spacingXs")
        )
        assert overlay.width() > 500
        assert overlay.screen() == root.screen()
    finally:
        _dispose(engine, component, root)


def test_desktop_stack_reflows_when_existing_toast_grows(qapp):
    """已有底部通知变高后，同屏后续通知必须按新高度重新排布。"""
    engine, component, root = _create_scene()
    try:
        root.createStackedToasts()
        first = _toast(root)
        second = _toast(root, "secondToast")
        first_overlay = _overlay(first)
        second_overlay = _overlay(second)
        _wait_until(lambda: first_overlay.isVisible() and second_overlay.isVisible())
        QTest.qWait(400)

        initial_offset = second_overlay.property("stackOffset")
        root.growFirstToast()
        _wait_until(lambda: first.property("hasCustomContent") is True)
        QTest.qWait(400)

        expected_offset = first_overlay.height() + root.property(
            "stackGap"
        )
        assert expected_offset > initial_offset
        assert second_overlay.property("stackOffset") == pytest.approx(expected_offset)
        assert second_overlay.y() + second_overlay.height() + root.property(
            "stackGap"
        ) <= first_overlay.y() + 1
    finally:
        _dispose(engine, component, root)


def test_desktop_infobar_receives_supported_options_before_show(qapp):
    """桌面 InfoBar 的布局、进度和样式选项须在首次定位前生效。"""
    engine, component, root = _create_scene()
    try:
        root.createConfiguredInfoBar()
        info_bar = _toast(root)
        overlay = _overlay(info_bar)
        _wait_until(
            lambda: info_bar.property("hasCustomContent") is True
            and overlay.isVisible()
        )
        QTest.qWait(400)

        assert info_bar.property("orient") == 2  # Qt.Vertical
        assert info_bar.property("closable") is False
        assert info_bar.property("feature") == root.property("progressFeature")
        assert info_bar.property("progress") == pytest.approx(0.5)
        assert info_bar.property("backgroundColorLight") == root.property("optionColor")
        assert info_bar.property("backgroundColorDark") == root.property("optionColor")
        assert info_bar.property("icon") == "Warning"
        assert info_bar.property("radius") == pytest.approx(
            root.property("optionRadius")
        )
        assert info_bar.findChild(QObject, "exportAction") is not None

        geometry = overlay.screen().availableGeometry()
        assert overlay.y() == pytest.approx(
            geometry.y() + root.property("screenMargin"), abs=1
        )
    finally:
        _dispose(engine, component, root)


def test_standalone_desktop_notification_counts_custom_content_once(qapp):
    """独立桌面通知的自定义内容只计高一次，并使用可用工作区定位。"""
    engine, component, root = _create_scene()
    try:
        root.createStandaloneNotification()
        standalone = root.property("standalone")
        assert isinstance(standalone, QQuickWindow)
        action = standalone.findChild(QQuickItem, "standaloneAction")
        assert action is not None

        _wait_until(lambda: standalone.isVisible())
        QTest.qWait(400)

        action_bottom = action.mapToItem(
            standalone.contentItem(), QPointF(0, action.height())
        ).y()
        assert standalone.height() - action_bottom == pytest.approx(
            root.property("spacingM"), abs=1
        )

        geometry = standalone.screen().availableGeometry()
        expected_bottom = geometry.y() + geometry.height() - root.property(
            "screenMargin"
        )
        assert standalone.y() + standalone.height() == pytest.approx(
            expected_bottom, abs=1
        )
    finally:
        _dispose(engine, component, root)
