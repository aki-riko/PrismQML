# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""TooltipCore lazy-window and geometry contracts. TooltipCore 懒窗口与几何合同。"""

from pathlib import Path

import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QWindow
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import configure_qml_environment, register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "tooltip-core-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    property string sampleText: "Tooltip"
    readonly property int tooltipWidth: tooltip.tooltipWidth
    readonly property real measuredWidth: metrics.advanceWidth + Enums.spacing.xl

    function showTooltip() { tooltip.show() }
    function hideTooltip() { tooltip.hide() }
    function setLegacyVisible(value) { tooltip.visible = value }

    width: 320
    height: 120
    visible: true

    TooltipCore {
        id: tooltip

        objectName: "tooltip"
        text: root.sampleText
    }

    TextMetrics {
        id: metrics
        text: root.sampleText
        font.family: Enums.fontFamily
        font.pixelSize: Enums.typography.caption
        font.weight: Font.Normal
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


def _release(qapp, *objects) -> None:
    for item in objects:
        if item is not None and shiboken6.isValid(item):
            item.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def test_tooltip_text_metrics_match_existing_label_width(qapp):
    """TextMetrics must reproduce the current Label-based tooltip width.

    TextMetrics 必须复现当前基于 Label 的提示宽度。
    """
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    component = None
    root = None
    try:
        register_types(engine)
        component = QQmlComponent(engine)
        component.setData(SCENE_SOURCE, SCENE_URL)
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        root = component.create(engine.rootContext())
        assert root is not None, [error.toString() for error in component.errors()]
        _pump()

        for sample in ("", "Tooltip", "中文提示", "Mixed 提示 123"):
            root.setProperty("sampleText", sample)
            _pump()
            assert root.property("tooltipWidth") == int(root.property("measuredWidth"))

        assert warnings == []
    finally:
        _release(qapp, root, component, engine)
        assert not any(
            "Cannot read property 'visible' of null" in warning
            for warning in warnings
        ), warnings


def test_tooltip_window_is_created_on_first_show_and_reused(qapp):
    """The native window must be absent initially, then preserve all show paths.

    原生窗口初始须不存在，首次创建后须保持全部显示路径。
    """
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    component = None
    root = None
    try:
        register_types(engine)
        component = QQmlComponent(engine)
        component.setData(SCENE_SOURCE, SCENE_URL)
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        root = component.create(engine.rootContext())
        assert root is not None, [error.toString() for error in component.errors()]
        _pump()

        tooltip = root.findChild(QObject, "tooltip")
        assert tooltip is not None
        loader = tooltip.findChild(QQuickItem, "tooltipWindowLoader")
        assert loader is not None
        assert loader.property("item") is None
        assert tooltip.findChildren(QWindow) == []

        tooltip.setProperty("followAnchor", True)
        root.showTooltip()
        assert _wait_for(lambda: loader.property("item") is not None)

        host = loader.property("item")
        windows = tooltip.findChildren(QWindow)
        assert len(windows) == 1
        tip_window = windows[0]
        content = host.findChild(QQuickItem, "tooltipContent")
        assert content is not None
        assert _wait_for(tip_window.isVisible), (
            f"pending={tooltip.property('_pendingShow')} "
            f"requested={tooltip.property('_windowRequested')} "
            f"scheduled={tooltip.property('_openScheduled')} "
            f"hostVisible={host.property('windowVisible')} "
            f"hasParent={tooltip.parent() is not None} "
            f"warnings={warnings}"
        )
        assert _wait_for(
            lambda: content.property("opacity") == 1.0
            and content.property("scale") == 1.0
        )

        initial_position = (tip_window.x(), tip_window.y())
        tooltip.setProperty("x", tooltip.property("x") + 40)
        tooltip.setProperty("y", tooltip.property("y") + 20)
        assert _wait_for(
            lambda: (tip_window.x(), tip_window.y())
            == (initial_position[0] + 40, initial_position[1] + 20)
        )

        root.hideTooltip()
        assert _wait_for(lambda: not tip_window.isVisible())
        assert loader.property("item") is host

        root.setLegacyVisible(True)
        assert _wait_for(tip_window.isVisible)
        root.setLegacyVisible(False)
        assert _wait_for(lambda: not tip_window.isVisible())
        assert loader.property("item") is host
        assert warnings == []
    finally:
        _release(qapp, root, component, engine)


def test_tooltip_native_window_can_disappear_before_host_without_warning(qapp):
    """A detached native window must not make its QML host dereference null."""
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    component = None
    root = None
    try:
        register_types(engine)
        component = QQmlComponent(engine)
        component.setData(SCENE_SOURCE, SCENE_URL)
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        root = component.create(engine.rootContext())
        assert root is not None, [error.toString() for error in component.errors()]
        _pump()

        tooltip = root.findChild(QObject, "tooltip")
        loader = tooltip.findChild(QQuickItem, "tooltipWindowLoader")
        root.showTooltip()
        assert _wait_for(lambda: loader.property("item") is not None)
        tip_window = tooltip.findChildren(QWindow)[0]
        assert _wait_for(tip_window.isVisible)

        # NativeWindowHook can detach the native window before the QML host
        # is destroyed during application shutdown.
        tip_window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qapp.processEvents()

        assert not any(
            "Cannot read property 'visible' of null" in warning
            for warning in warnings
        ), warnings
    finally:
        _release(qapp, root, component, engine)
