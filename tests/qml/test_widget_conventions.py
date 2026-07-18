# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Widget convention and tooltip metric regressions. Widget 规范与工具提示度量回归。"""

from pathlib import Path, PurePosixPath

import pytest
from PySide6.QtCore import QEventLoop, QMetaObject, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
METRICS_SOURCE = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"
WIDGET_SOURCE = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "containers" / "Widget.qml"
)
HINT_ICON_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "feedback"
    / "Tooltip"
    / "HintIcon.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "widget-conventions.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property real defaultWidgetWidth: defaultWidget.width
    readonly property real defaultWidgetHeight: defaultWidget.height
    readonly property real contentWidgetWidth: contentWidget.width
    readonly property real contentWidgetHeight: contentWidget.height
    readonly property real preferredWidgetWidth: preferredWidget.width
    readonly property real preferredWidgetHeight: preferredWidget.height
    readonly property real centeredChildX: centeredChild.x
    readonly property real centeredChildY: centeredChild.y
    readonly property int persistentDuration: Enums.duration.persistent
    readonly property int tooltipShowDelay: Enums.duration.tooltipShowDelay
    readonly property int noHideDelay: Enums.duration.none
    readonly property int widgetDuration: defaultWidget.toolTipDuration
    readonly property int widgetShowDelay: defaultWidget.toolTipShowDelay
    readonly property int widgetHideDelay: defaultWidget.toolTipHideDelay
    readonly property int buttonDuration: button.toolTipDuration
    readonly property int buttonShowDelay: button.toolTipShowDelay
    readonly property int buttonHideDelay: button.toolTipHideDelay
    readonly property int hintDuration: hintIcon.toolTipDuration
    readonly property int hintShowDelay: hintIcon.toolTipShowDelay
    readonly property int hintHideDelay: hintIcon.toolTipHideDelay
    readonly property int defaultTooltipPosition: defaultWidget.toolTipPosition
    readonly property int hintTooltipPosition: hintIcon.toolTipPosition
    readonly property int topPosition: Enums.position.top
    readonly property int rightPosition: Enums.position.right
    readonly property int tooltipHorizontalPadding: Enums.spacing.l
    readonly property int tooltipVerticalPadding: Enums.spacing.xs
    readonly property int tooltipGap: Enums.spacing.xs

    width: 320
    height: 240

    Widget {
        id: defaultWidget
        objectName: "defaultWidget"
    }

    Widget {
        id: contentWidget
        contentWidth: 80
        contentHeight: 30
    }

    Widget {
        id: preferredWidget
        contentWidth: 80
        contentHeight: 30
        preferredWidth: 120
        preferredHeight: 40
    }

    Widget {
        id: centeredWidget
        width: 120
        height: 60
        centerContent: true

        Rectangle {
            id: centeredChild
            objectName: "centeredChild"
            width: 20
            height: 30
        }
    }

    Button {
        id: button
    }

    HintIcon {
        id: hintIcon
        objectName: "hintIcon"
        x: 40
        y: 40
        toolTipText: "Hint tooltip"
    }
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlApplicationEngine()
    qml_warnings = []
    engine.warnings.connect(
        lambda errors: qml_warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _pump(50)
    assert qml_warnings == []
    return engine, component, root


def _new_visible_windows(windows_before):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
    ]


@pytest.fixture
def widget_scene(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, root = _create_scene()
    try:
        yield root, windows_before
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_widget_size_priority_remains_stable(widget_scene):
    root, _ = widget_scene
    assert root.property("defaultWidgetWidth") == pytest.approx(320)
    assert root.property("defaultWidgetHeight") == pytest.approx(0)
    assert root.property("contentWidgetWidth") == pytest.approx(80)
    assert root.property("contentWidgetHeight") == pytest.approx(30)
    assert root.property("preferredWidgetWidth") == pytest.approx(120)
    assert root.property("preferredWidgetHeight") == pytest.approx(40)


def test_widget_center_content_remains_stable(widget_scene):
    root, _ = widget_scene
    centered_child = root.findChild(QQuickItem, "centeredChild")
    assert centered_child is not None
    assert root.property("centeredChildX") == pytest.approx(50)
    assert root.property("centeredChildY") == pytest.approx(15)


def test_widget_tooltip_defaults_and_hidden_window_behavior(widget_scene):
    root, windows_before = widget_scene
    default_widget = root.findChild(QObject, "defaultWidget")
    hint_icon = root.findChild(QObject, "hintIcon")
    assert default_widget is not None
    assert hint_icon is not None
    assert default_widget.findChild(QObject, "_toolTip") is None
    assert hint_icon.findChild(QObject, "_toolTip") is not None
    assert (
        root.property("persistentDuration"),
        root.property("tooltipShowDelay"),
        root.property("noHideDelay"),
    ) == (-1, 500, 0)
    assert (
        root.property("widgetDuration"),
        root.property("widgetShowDelay"),
        root.property("widgetHideDelay"),
    ) == (-1, 500, 0)
    assert (
        root.property("buttonDuration"),
        root.property("buttonShowDelay"),
        root.property("buttonHideDelay"),
    ) == (-1, 500, 0)
    assert (
        root.property("hintDuration"),
        root.property("hintShowDelay"),
        root.property("hintHideDelay"),
    ) == (-1, 100, 0)
    assert root.property("defaultTooltipPosition") == root.property("topPosition")
    assert root.property("hintTooltipPosition") == root.property("rightPosition")
    assert _new_visible_windows(windows_before) == []


def test_hint_tooltip_uses_real_padding_and_right_position(widget_scene):
    root, _ = widget_scene
    window = QQuickWindow()
    window.setWidth(320)
    window.setHeight(240)
    root.setParentItem(window.contentItem())
    window.show()
    _pump(20)
    try:
        hint_icon = root.findChild(QQuickItem, "hintIcon")
        assert hint_icon is not None
        tooltip = hint_icon.findChild(QObject, "_toolTip")
        assert tooltip is not None

        assert QMetaObject.invokeMethod(hint_icon, "showToolTip")
        _pump(20)
        horizontal_padding = root.property("tooltipHorizontalPadding")
        vertical_padding = root.property("tooltipVerticalPadding")
        tooltip_gap = root.property("tooltipGap")
        assert tooltip.property("leftPadding") == pytest.approx(horizontal_padding)
        assert tooltip.property("rightPadding") == pytest.approx(horizontal_padding)
        assert tooltip.property("topPadding") == pytest.approx(vertical_padding)
        assert tooltip.property("bottomPadding") == pytest.approx(vertical_padding)
        assert tooltip.property("x") == pytest.approx(
            hint_icon.width() + tooltip_gap
        )
        assert tooltip.property("y") == pytest.approx(
            (hint_icon.height() - tooltip.property("height")) / 2
        )
        assert QMetaObject.invokeMethod(hint_icon, "hideToolTip")
    finally:
        root.setParentItem(None)
        window.close()
        window.deleteLater()
        _pump(1)


def test_widget_source_follows_conventions_and_uses_tooltip_tokens():
    metrics_source = METRICS_SOURCE.read_text(encoding="utf-8")
    widget_source = WIDGET_SOURCE.read_text(encoding="utf-8")
    hint_icon_source = HINT_ICON_SOURCE.read_text(encoding="utf-8")
    path = PurePosixPath(WIDGET_SOURCE.relative_to(ROOT).as_posix())
    violations = scan_source_text(widget_source, path)

    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009", "QML011"}
    ] == []
    assert "readonly property int tooltipShowDelay: 500" in metrics_source
    assert "property int toolTipDuration: Enums.duration.persistent" in widget_source
    assert (
        "property int toolTipShowDelay: Enums.duration.tooltipShowDelay"
        in widget_source
    )
    assert "property int toolTipHideDelay: Enums.duration.none" in widget_source
    assert "property int toolTipPosition: Enums.position.top" in widget_source
    assert "leftPadding: Enums.spacing.l" in widget_source
    assert "rightPadding: Enums.spacing.l" in widget_source
    assert "topPadding: Enums.spacing.xs" in widget_source
    assert "bottomPadding: Enums.spacing.xs" in widget_source
    assert "toolTipPosition: Enums.position.right" in hint_icon_source
    assert "property int toolTipDuration: -1" not in widget_source
    assert "property int toolTipShowDelay: 500" not in widget_source
    assert "property int toolTipHideDelay: 0" not in widget_source
