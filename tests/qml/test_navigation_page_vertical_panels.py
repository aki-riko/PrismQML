# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Gallery vertical-navigation coverage. 画廊垂直导航覆盖回归。"""

import re
import time
from pathlib import Path

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QObject,
    QPoint,
    QPointF,
    QTimer,
    QUrl,
    Qt,
    QtMsgType,
    qInstallMessageHandler,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from prismqml import configure_qml_environment, register_types


_ROOT = Path(__file__).resolve().parents[2]
_PAGE = _ROOT / "examples" / "pages" / "NavigationPage.qml"

# A host window is needed to deliver real mouse events to the Gallery page.
# 需要宿主窗口才能向画廊页面投递真实鼠标事件。
_GALLERY_HOST_SCENE = """
import QtQuick
import QtQuick.Window
import PrismQML

Window {{
    id: host
    objectName: "galleryHost"

    // Identifying a pane by its display mode keeps the click test unambiguous now
    // that the page also demonstrates pane_left_minimal (also 48px wide).
    // 页面同时展示了同为 48px 宽的 pane_left_minimal, 用显示模式定位才唯一。
    readonly property int compactPaneMode: Enums.navigation.pane_left_compact

    width: 900
    height: 900
    visible: true

    Loader {{
        objectName: "pageLoader"
        anchors.fill: parent
        source: "{page_url}"
    }}
}}
"""

# Window-level vertical navigation panels the Gallery page must demonstrate.
# 画廊页面必须展示的窗口级垂直导航面板。
_EXPECTED_PANELS = {
    "NavigationView": 3,
    "NavigationBar": 1,
    "ToggleNavigationBar": 1,
}

# Substrings that indicate a real QML binding/loading failure rather than a
# benign runtime note. 这些子串代表真实的 QML 绑定/加载失败, 而不是无害提示。
_ERROR_MARKERS = (
    "ReferenceError",
    "TypeError",
    "is not defined",
    "Unable to assign",
    "Cannot assign",
    "Cannot read property",
)


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_until(predicate, timeout_ms: int = 3000) -> bool:
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if predicate():
            return True
        _pump()
    return predicate()


def _release(qapp, *objects) -> None:
    for item in objects:
        if item is not None and shiboken6.isValid(item):
            item.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    qapp.processEvents()


def _type_name(obj: QObject) -> str:
    """Strip Qt's per-registration suffix from a QML type name.

    去掉 Qt 为每次注册附加的后缀，还原 QML 类型名。
    """
    return re.sub(r"_QMLTYPE_\d+$", "", obj.metaObject().className())


def _panel_counts(root: QObject) -> dict:
    counts = {}
    for child in root.findChildren(QObject):
        name = _type_name(child)
        counts[name] = counts.get(name, 0) + 1
    return counts


def _panels_of(root: QObject, name: str) -> list:
    return [
        child
        for child in root.findChildren(QQuickItem)
        if _type_name(child) == name
    ]


def _vertical_panels_of(root: QObject, name: str) -> list:
    return [
        panel for panel in _panels_of(root, name)
        if panel.property("vertical") is True
    ]


def test_gallery_navigation_page_documents_vertical_panels():
    """The navigation page must keep showing the window-level vertical panels.

    导航页必须持续展示窗口级垂直导航面板（防止覆盖缺口回流）。
    """
    source = _PAGE.read_text(encoding="utf-8")
    for marker in (
        "NavigationView {",
        "NavigationBar {",
        "ToggleNavigationBar {",
        "Vertical navigation",
        "SegmentedControl (orientation: Qt.Vertical)",
        "Pivot (orientation: Qt.Vertical)",
    ):
        assert marker in source
    assert source.count("orientation: Qt.Vertical") >= 2


def test_gallery_navigation_page_builds_vertical_panels_without_qml_errors(qapp):
    """The real Gallery page must instantiate every vertical panel with geometry.

    真实画廊页面必须无 QML 错误地实例化每个垂直面板, 并拿到非零几何。
    """
    configure_qml_environment()
    messages = []
    previous = qInstallMessageHandler(
        lambda mode, context, message: messages.append((mode, message))
    )
    engine = QQmlApplicationEngine()
    component = None
    page = None
    try:
        register_types(engine)
        component = QQmlComponent(engine, QUrl.fromLocalFile(str(_PAGE)))
        assert _wait_until(
            lambda: component.status() != QQmlComponent.Status.Loading
        )
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        page = component.create(engine.rootContext())
        assert page is not None, [error.toString() for error in component.errors()]
        assert _wait_until(
            lambda: all(
                len(_panels_of(page, name)) == expected
                for name, expected in _EXPECTED_PANELS.items()
            )
        ), f"panel counts: {_panel_counts(page)}"

        for name, expected in _EXPECTED_PANELS.items():
            panels = _panels_of(page, name)
            assert len(panels) == expected, f"{name}: {len(panels)} != {expected}"
            for panel in panels:
                assert panel.width() > 0, f"{name} width collapsed"
                assert panel.height() > 0, f"{name} height collapsed"
                assert panel.property("model") is not None, f"{name} lost its model"

        # Page-level vertical strips must be demonstrated too
        # 页内竖版条带同样必须被展示
        for name in ("SegmentedControl", "Pivot"):
            vertical = _vertical_panels_of(page, name)
            assert len(vertical) == 1, f"{name} vertical instances: {len(vertical)}"
            assert vertical[0].width() > 0, f"{name} vertical width collapsed"
            assert vertical[0].height() > 0, f"{name} vertical height collapsed"
    finally:
        qInstallMessageHandler(previous)
        _release(qapp, page, component, engine)

    failures = [
        message
        for mode, message in messages
        if mode in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg,
                    QtMsgType.QtFatalMsg)
        and any(marker in message for marker in _ERROR_MARKERS)
    ]
    assert failures == []


def _create_host_scene(qapp):
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        _GALLERY_HOST_SCENE.format(
            page_url=QUrl.fromLocalFile(str(_PAGE)).toString()
        ).encode("utf-8"),
        QUrl.fromLocalFile(str(_ROOT / "tests" / "qml" / "gallery-nav-host.qml")),
    )
    assert _wait_until(
        lambda: component.status() != QQmlComponent.Status.Loading
    )
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    loader = window.findChild(QObject, "pageLoader")
    # Read the loaded item instead of Loader.status: the status enum has no Python
    # converter. 读取已加载项而不是 Loader.status: 该状态枚举在 Python 侧无转换器。
    assert _wait_until(lambda: loader.property("item") is not None)
    _pump(120)
    return engine, component, window, loader.property("item")


def _class_histogram(root) -> list:
    counts = {}
    for child in root.findChildren(QObject):
        name = _type_name(child)
        counts[name] = counts.get(name, 0) + 1
    return sorted(counts.items(), key=lambda entry: -entry[1])[:12]


def _nav_items(panel):
    """Panel rows through the sanctioned accessor.

    通过正式访问器读取面板条目: 条目由 JS 创建, QObject 树 (findChildren) 看不到它们,
    因此面板根提供 itemCount / itemAt()。
    """
    return [
        panel.itemAt(index) for index in range(panel.property("itemCount"))
    ]


def test_gallery_vertical_panels_switch_selection_on_real_click(qapp):
    """Clicking a Gallery panel item must really move its selection.

    点击画廊面板条目必须真的改变选中项。

    回归点：NavigationPanelCore 刻意不自改 currentIndex（只发 itemClicked，交由宿主
    外壳回灌），演示里漏了这段接线时面板点不动。
    """
    engine = component = window = page = None
    try:
        engine, component, window, page = _create_host_scene(qapp)
        compact_mode = window.property("compactPaneMode")
        views = [
            panel for panel in _panels_of(page, "NavigationView")
            if panel.property("paneDisplayMode") == compact_mode
        ]
        assert len(views) == 1
        compact = views[0]
        assert compact.property("isExpanded") is False
        assert compact.property("currentIndex") == 0

        assert _wait_until(lambda: len(_nav_items(compact)) == 5), (
            f"compact rail items: {len(_nav_items(compact))} "
            f"size={compact.width()}x{compact.height()} "
            f"qobjects={len(compact.findChildren(QObject))} "
            f"classes={_class_histogram(compact)}"
        )
        items = _nav_items(compact)

        target = items[2]
        centre = target.mapToItem(
            window.contentItem(),
            QPointF(target.width() / 2, target.height() / 2),
        )
        point = QPoint(round(centre.x()), round(centre.y()))
        QTest.mouseMove(window, point)
        QTest.mouseClick(
            window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier, point,
        )
        assert _wait_until(lambda: compact.property("currentIndex") == 2), (
            f"click did not move the selection: {compact.property('currentIndex')}"
        )

        # A second click on another row must move it again
        # 再点另一行必须继续移动
        other = items[4]
        centre = other.mapToItem(
            window.contentItem(),
            QPointF(other.width() / 2, other.height() / 2),
        )
        point = QPoint(round(centre.x()), round(centre.y()))
        QTest.mouseClick(
            window, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier, point,
        )
        assert _wait_until(lambda: compact.property("currentIndex") == 4), (
            f"second click did not move: {compact.property('currentIndex')}"
        )
    finally:
        if window is not None:
            window.close()
        _release(qapp, page, component, engine)
