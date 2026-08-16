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
from PySide6.QtCore import QObject, QPointF, QUrl, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtTest import QTest

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
REAL_EXPORT_PATH = (
    r"C:\Users\Kotori\AppData\Roaming\Kaleidos\recordings\clip_20260720_005908.mp4"
)
REAL_EXPORT_MESSAGE = f"00:05\n{REAL_EXPORT_PATH}"
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
    readonly property int stackGap: Enums.spacing.m
    readonly property int spacingXs: Enums.spacing.xs
    readonly property int spacingM: Enums.spacing.m
    readonly property int progressFeature: Enums.notification.feature_progress_bar
    readonly property color optionColor: Enums.accentColor
    readonly property real optionRadius: Enums.radius.large
    readonly property var notificationPositions: ({{
        "topLeft": NotificationManager.posTopLeft,
        "top": NotificationManager.posTop,
        "topRight": NotificationManager.posTopRight,
        "left": NotificationManager.posLeft,
        "center": NotificationManager.posCenter,
        "right": NotificationManager.posRight,
        "bottomLeft": NotificationManager.posBottomLeft,
        "bottom": NotificationManager.posBottom,
        "bottomRight": NotificationManager.posBottomRight
    }})

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

    function createToastAt(requestedPosition) {{
        firstToast = NotificationManager.desktop.success(
            "九宫格定位",
            "工作区边缘间距",
            0,
            requestedPosition,
            {{
                "closable": false,
                "screen": host.screen
            }}
        )
    }}

    function createExportToastAt(requestedPosition) {{
        firstToast = NotificationManager.desktop.success(
            "导出成功",
            {json.dumps(REAL_EXPORT_MESSAGE, ensure_ascii=False)},
            0,
            requestedPosition,
            {{
                "orient": Qt.Vertical,
                "customContent": exportAction,
                "screen": host.screen
            }}
        )
    }}

    function createInfoBarAt(requestedPosition) {{
        firstToast = NotificationManager.desktop.infoBar(
            "warning",
            "导出处理中",
            "正在准备导出文件",
            0,
            requestedPosition,
            {{ "screen": host.screen }}
        )
    }}

    function hideFirstToast() {{
        if (firstToast) firstToast.hide()
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

    function createScreenshotStackedToasts(requestedPosition) {{
        firstToast = NotificationManager.desktop.info(
            "提示", "左上位置", 0, requestedPosition,
            {{ "screen": host.screen }}
        )
        secondToast = NotificationManager.desktop.info(
            "提示", "左上位置", 0, requestedPosition,
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


class _FakeWindowHelper(QObject):
    """Expose a deterministic work area to QML without relying on the host taskbar."""

    def __init__(self, geometry: dict[str, int], parent: QObject) -> None:
        super().__init__(parent)
        self._geometry = geometry

    @Slot(int, int, result="QVariantMap")
    def availableScreenGeometryAt(self, _x: int, _y: int) -> dict[str, int]:
        return dict(self._geometry)


def _create_scene(
    available_geometry: dict[str, int] | None = None,
) -> tuple[QQmlApplicationEngine, QQmlComponent, QQuickWindow]:
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    if available_geometry is not None:
        helper = _FakeWindowHelper(available_geometry, engine)
        engine.rootContext().setContextProperty("WindowHelper", helper)
        engine._test_window_helper = helper
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


def test_notification_manager_exposes_row_major_nine_grid(qapp):
    """NotificationManager must expose all nine public positions. 管理器须公开完整九宫格。"""
    engine, component, root = _create_scene()
    try:
        positions = root.property("notificationPositions")
        if hasattr(positions, "toVariant"):
            positions = positions.toVariant()
        assert positions == {
            "topLeft": 0,
            "top": 1,
            "topRight": 2,
            "left": 3,
            "center": 4,
            "right": 5,
            "bottomLeft": 6,
            "bottom": 7,
            "bottomRight": 8,
        }
    finally:
        _dispose(engine, component, root)


@pytest.mark.parametrize("notification_kind", ["toast", "infoBar"])
@pytest.mark.parametrize("position", range(9))
def test_desktop_notifications_remain_visible_during_nine_grid_exit_animation(
    qapp, notification_kind, position
):
    """Desktop content must stay rendered while its overlay exits at all nine positions."""
    engine, component, root = _create_scene()
    try:
        if notification_kind == "toast":
            root.createExportToastAt(position)
        else:
            root.createInfoBarAt(position)

        notification = _toast(root)
        overlay = _overlay(notification)
        _wait_until(lambda: notification.property("visible") and overlay.isVisible())
        QTest.qWait(400)

        start_x = overlay.x()
        start_y = overlay.y()
        root.hideFirstToast()
        QTest.qWait(150)

        assert notification.property("visible") is True
        assert overlay.isVisible()

        if position in (0, 3, 6):
            assert overlay.x() < start_x
        elif position in (2, 5, 8):
            assert overlay.x() > start_x
        elif position == 1:
            assert overlay.y() < start_y
        elif position == 7:
            assert overlay.y() > start_y
        else:
            assert overlay.property("opacity") < 1
    finally:
        _dispose(engine, component, root)


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


def test_desktop_toast_uses_native_available_geometry_provider(qapp):
    """QML Screen lacks availableGeometry, so the host helper must define the work area."""
    screen_geometry = QGuiApplication.primaryScreen().geometry()
    work_area = {
        "x": screen_geometry.x() + 17,
        "y": screen_geometry.y() + 23,
        "width": screen_geometry.width() - 41,
        "height": screen_geometry.height() - 95,
    }
    engine, component, root = _create_scene(work_area)
    try:
        root.createConfiguredExportToast()
        toast = _toast(root)
        overlay = _overlay(toast)
        _wait_until(
            lambda: toast.property("hasCustomContent") is True and overlay.isVisible()
        )
        QTest.qWait(400)

        margin = root.property("screenMargin")
        expected_right = work_area["x"] + work_area["width"] - margin
        expected_bottom = work_area["y"] + work_area["height"] - margin
        assert overlay.x() + overlay.width() == pytest.approx(expected_right, abs=1)
        assert overlay.y() + overlay.height() == pytest.approx(expected_bottom, abs=1)
    finally:
        _dispose(engine, component, root)


@pytest.mark.parametrize(
    ("position", "horizontal", "vertical"),
    [
        (0, "left", "top"),
        (1, "center", "top"),
        (2, "right", "top"),
        (3, "left", "center"),
        (4, "center", "center"),
        (5, "right", "center"),
        (6, "left", "bottom"),
        (7, "center", "bottom"),
        (8, "right", "bottom"),
    ],
)
def test_desktop_toast_anchors_all_nine_work_area_positions(
    qapp, position: int, horizontal: str, vertical: str
):
    """All nine positions share the compact work-area edge margin. 九宫格位置共享紧凑工作区边距。"""
    work_area = {"x": 113, "y": 71, "width": 997, "height": 701}
    engine, component, root = _create_scene(work_area)
    try:
        root.createToastAt(position)
        toast = _toast(root)
        overlay = _overlay(toast)
        _wait_until(overlay.isVisible)
        QTest.qWait(400)

        margin = 8
        expected_x = {
            "left": work_area["x"] + margin,
            "center": work_area["x"] + (work_area["width"] - overlay.width()) / 2,
            "right": work_area["x"] + work_area["width"] - overlay.width() - margin,
        }[horizontal]
        expected_y = {
            "top": work_area["y"] + margin,
            "center": work_area["y"] + (work_area["height"] - overlay.height()) / 2,
            "bottom": work_area["y"] + work_area["height"] - overlay.height() - margin,
        }[vertical]

        assert overlay.x() == pytest.approx(expected_x, abs=1)
        assert overlay.y() == pytest.approx(expected_y, abs=1)
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

        expected_offset = (
            first_overlay.height()
            + root.property("stackGap")
            - first_overlay.property("_stackTopInset")
            - second_overlay.property("_stackBottomInset")
        )
        assert expected_offset > initial_offset
        assert second_overlay.property("stackOffset") == pytest.approx(expected_offset)
        first_visual_top = first_overlay.y() + first.y() + root.property("spacingM")
        second_visual_bottom = (
            second_overlay.y()
            + second.y()
            + second.height()
            - root.property("spacingM")
        )
        assert first_visual_top - second_visual_bottom == pytest.approx(
            root.property("stackGap")
        )
    finally:
        _dispose(engine, component, root)


@pytest.mark.parametrize("position, stacks_upward", [(0, False), (6, True)])
def test_desktop_toasts_use_visual_edge_stack_gap(qapp, position, stacks_upward):
    """Desktop Toasts share the compact visual gap used by in-window Toasts."""
    engine, component, root = _create_scene()
    try:
        root.createScreenshotStackedToasts(position)
        first = _toast(root)
        second = _toast(root, "secondToast")
        first_overlay = _overlay(first)
        second_overlay = _overlay(second)
        _wait_until(lambda: first_overlay.isVisible() and second_overlay.isVisible())
        QTest.qWait(400)

        inset = root.property("spacingM")
        first_visual_top = first_overlay.y() + first.y() + inset
        first_visual_bottom = first_overlay.y() + first.y() + first.height() - inset
        second_visual_top = second_overlay.y() + second.y() + inset
        second_visual_bottom = (
            second_overlay.y() + second.y() + second.height() - inset
        )
        actual_gap = (
            first_visual_top - second_visual_bottom
            if stacks_upward
            else second_visual_top - first_visual_bottom
        )
        assert actual_gap == pytest.approx(root.property("stackGap"))
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
        auto_close_timer = standalone.findChild(
            QObject, "desktopNotificationAutoCloseTimer"
        )
        assert auto_close_timer is not None
        assert auto_close_timer.parent() is standalone.contentItem()
        assert auto_close_timer.property("running") is False
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
