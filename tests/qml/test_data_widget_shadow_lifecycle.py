# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""DataWidget shadow fallback lifecycle regressions. 数据组件阴影兜底生命周期回归。"""

import re
import subprocess
import sys
from pathlib import Path

import shiboken6
from PySide6.QtCore import (
    QObject,
    QCoreApplication,
    QEvent,
    QEventLoop,
    QTimer,
    QtMsgType,
    QUrl,
    qInstallMessageHandler,
)
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


_ROOT = Path(__file__).resolve().parents[2]
_PROBE_QML = b"""
import QtQuick
import PrismQML

Item {
    property var enumsRef: Enums

    DataWidgetCore {
        width: 240
        height: 140
        shadowLevel: null
    }
}
"""
_QT_FAILURE_TYPES = {
    QtMsgType.QtWarningMsg,
    QtMsgType.QtCriticalMsg,
    QtMsgType.QtFatalMsg,
}
_PROCESS_EXIT_PROBE = r"""
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent

from prismqml import App


app = App([])
component = QQmlComponent(app._engine)
component.setData(
    b'''import QtQuick
import PrismQML

Item {
    DataWidgetCore {
        width: 240
        height: 140
    }
}
''',
    QUrl("data-widget-process-exit.qml"),
)
assert component.status() == QQmlComponent.Status.Ready, [
    error.toString() for error in component.errors()
]
root = component.create(app._engine.rootContext())
assert root is not None, [error.toString() for error in component.errors()]
"""


def _find_metrics(enums):
    """Find the verified Metrics child by its public property shape. 按已验证属性形状定位 Metrics 子对象。"""
    matches = []
    for child in enums.findChildren(QObject):
        meta = child.metaObject()
        names = {meta.property(index).name() for index in range(meta.propertyCount())}
        if {"duration", "spacing", "shadow"} <= names:
            matches.append(child)
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _find_shadow(widget):
    """Find the real RectangularShadow child. 定位真实 RectangularShadow 子对象。"""
    matches = [
        item
        for item in widget.findChildren(QObject)
        if "RectangularShadow" in item.metaObject().className()
    ]
    assert len(matches) == 1, [item.metaObject().className() for item in matches]
    return matches[0]


def _release(qapp, *objects):
    """Release QML objects and deferred deletes. 释放 QML 对象与延迟删除事件。"""
    for item in objects:
        if item is not None and shiboken6.isValid(item):
            item.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    qapp.processEvents()


def _settle_startup_events():
    """Let asynchronous singleton startup diagnostics finish. 等待 singleton 异步启动诊断落定。"""
    loop = QEventLoop()
    QTimer.singleShot(20, loop.quit)
    loop.exec()


def test_data_widget_shadow_survives_metrics_teardown_without_qml_warnings(qapp):
    """Metrics may die first while the live shadow still needs a safe fallback. Metrics 可先销毁，存活阴影仍须安全兜底。"""
    messages = []
    previous_handler = qInstallMessageHandler(
        lambda mode, _context, message: messages.append((mode, str(message)))
    )
    engine = QQmlApplicationEngine()
    component = None
    root = None
    try:
        register_types(engine)
        component = QQmlComponent(engine)
        component.setData(
            _PROBE_QML,
            QUrl.fromLocalFile(str(_ROOT / "tests/qml/data-widget-shadow-lifecycle.qml")),
        )
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        root = component.create(engine.rootContext())
        assert root is not None, [error.toString() for error in component.errors()]

        widget = root.children()[0]
        shadow = _find_shadow(widget)
        enums = root.property("enumsRef")
        metrics = _find_metrics(enums)

        assert QColor(shadow.property("color")).alpha() > 0
        _settle_startup_events()
        messages.clear()
        metrics.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        qapp.processEvents()

        assert not shiboken6.isValid(metrics)
        assert enums.property("shadow") is None
        assert QColor(shadow.property("color")).alpha() == 0
    finally:
        _release(qapp, root, component, engine)
        qInstallMessageHandler(previous_handler)

    failures = [
        message
        for mode, message in messages
        if mode in _QT_FAILURE_TYPES
    ]
    assert failures == []


def test_data_widget_default_shadow_process_exit_has_no_teardown_warning():
    """Natural process exit must not emit shadow teardown warnings. 自然退出不得产生阴影销毁警告。"""
    result = subprocess.run(
        [sys.executable, "-c", _PROCESS_EXIT_PROBE],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode == 0, output
    assert "Unable to assign [undefined] to QColor" not in output
    assert not re.search(
        r"DataWidgetCore\.qml:\d+:\d+:\s+\[QtContext\]",
        output,
    ), output
