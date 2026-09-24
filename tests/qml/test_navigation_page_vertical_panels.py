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
    QTimer,
    QUrl,
    QtMsgType,
    qInstallMessageHandler,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import configure_qml_environment, register_types


_ROOT = Path(__file__).resolve().parents[2]
_PAGE = _ROOT / "examples" / "pages" / "NavigationPage.qml"

# Window-level vertical navigation panels the Gallery page must demonstrate.
# 画廊页面必须展示的窗口级垂直导航面板。
_EXPECTED_PANELS = {
    "NavigationView": 2,
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
    ):
        assert marker in source


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
