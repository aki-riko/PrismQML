# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Duration sentinel token regressions. 动画时长哨兵令牌回归。"""

from pathlib import Path, PurePosixPath

from PySide6.QtCore import QEventLoop, QMetaObject, QTimer, QUrl
from PySide6.QtGui import QWindow
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
METRICS_SOURCE = ROOT / "prismqml" / "PrismQML" / "PrismEnums" / "Metrics.qml"
BREADCRUMB_DELEGATE_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "navigation"
    / "_internal"
    / "BreadcrumbDelegate.qml"
)
TIP_POPUP_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "feedback"
    / "Tooltip"
    / "TipPopup.qml"
)
TIP_POPUP_TIMER_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "feedback"
    / "Tooltip"
    / "_internal"
    / "TipPopupAutoCloseTimer.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "duration-sentinel-tokens.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    readonly property int durationNone: Enums.duration.none
    readonly property int durationPersistent: Enums.duration.persistent
    readonly property int durationInstant: Enums.duration.instant
    readonly property int flyoutType: Enums.tip.type_flyout
    readonly property int teachingTipType: Enums.tip.type_teaching_tip

    width: 640
    height: 120

    Breadcrumb {
        id: breadcrumb
        objectName: "breadcrumb"
        width: 600
        animated: true

        Component.onCompleted: {
            addItem("root", "Root", "")
            addItem("section", "Section", "")
            addItem("leaf", "Leaf", "")
        }
    }

    TipPopup {
        objectName: "tipPopup"
    }

    TeachingTip {
        objectName: "teachingTip"
    }
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene():
    engine = QQmlApplicationEngine()
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
    _pump(20)
    return engine, component, root


def test_duration_sentinels_preserve_runtime_behavior(qapp):
    engine, component, root = _create_scene()
    try:
        breadcrumb = root.findChild(QQuickItem, "breadcrumb")
        tip_popup = root.findChild(QQuickItem, "tipPopup")
        teaching_tip = root.findChild(QQuickItem, "teachingTip")
        assert breadcrumb is not None and tip_popup is not None
        assert teaching_tip is not None

        assert root.property("durationNone") == 0
        assert root.property("durationPersistent") == -1
        assert root.property("durationInstant") == 50
        assert breadcrumb.property("count") == 3
        assert breadcrumb.property("currentIndex") == 2
        assert breadcrumb.property("currentKey") == "leaf"
        assert tip_popup.property("duration") == root.property("durationPersistent")
        flyout_windows = tip_popup.findChildren(QWindow)
        teaching_windows = teaching_tip.findChildren(QWindow)
        assert flyout_windows == []
        assert teaching_windows == []
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_tip_popup_creates_action_buttons_only_when_needed(qapp):
    engine, component, root = _create_scene()
    try:
        tip_popup = root.findChild(QQuickItem, "tipPopup")
        assert tip_popup is not None
        assert tip_popup.findChild(QQuickItem, "tipPrimaryActionButton") is None
        assert tip_popup.findChild(QQuickItem, "tipSecondaryActionButton") is None

        tip_popup.setProperty("target", root)
        tip_popup.setProperty("primaryButtonText", "Apply")
        tip_popup.setProperty("secondaryButtonText", "Back")
        assert QMetaObject.invokeMethod(tip_popup, "prewarm")
        _pump()

        primary = tip_popup.findChild(QQuickItem, "tipPrimaryActionButton")
        secondary = tip_popup.findChild(QQuickItem, "tipSecondaryActionButton")
        assert primary is not None and secondary is not None
        assert primary.property("text") == "Apply"
        assert secondary.property("text") == "Back"
        assert primary.property("visible") is True
        assert secondary.property("visible") is True

        tip_popup.setProperty("primaryButtonText", "")
        tip_popup.setProperty("secondaryButtonText", "")
        _pump()
        assert tip_popup.findChild(QQuickItem, "tipPrimaryActionButton") is None
        assert tip_popup.findChild(QQuickItem, "tipSecondaryActionButton") is None
        assert not any(window.isVisible() for window in tip_popup.findChildren(QWindow))
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_tip_popup_creates_and_reuses_arrow_window_after_teaching_tip_use(qapp):
    engine, component, root = _create_scene()
    try:
        tip_popup = root.findChild(QQuickItem, "tipPopup")
        teaching_tip = root.findChild(QQuickItem, "teachingTip")
        assert tip_popup is not None and teaching_tip is not None
        assert tip_popup.findChildren(QWindow) == []
        assert teaching_tip.findChildren(QWindow) == []

        tip_popup.setProperty("target", root)
        tip_popup.setProperty("tipType", root.property("teachingTipType"))
        assert QMetaObject.invokeMethod(tip_popup, "prewarm")
        _pump()
        arrow_window = tip_popup.findChild(QWindow, "tipArrowWindow")
        assert arrow_window is not None
        assert len(tip_popup.findChildren(QWindow)) == 2
        assert arrow_window.isVisible() is False

        tip_popup.setProperty("tipType", root.property("flyoutType"))
        _pump()
        assert tip_popup.findChild(QWindow, "tipArrowWindow") is arrow_window
        assert len(tip_popup.findChildren(QWindow)) == 2
        assert arrow_window.isVisible() is False
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()
        _pump(1)


def test_duration_sentinels_use_semantic_tokens():
    metrics_source = METRICS_SOURCE.read_text(encoding="utf-8")
    breadcrumb_source = BREADCRUMB_DELEGATE_SOURCE.read_text(encoding="utf-8")
    tip_popup_source = TIP_POPUP_SOURCE.read_text(encoding="utf-8")

    duration_block = metrics_source.split(
        "readonly property QtObject duration: QtObject {", 1
    )[1].split("// ==================== Z-Index", 1)[0]
    breadcrumb_enter_block = breadcrumb_source.split(
        "Component.onCompleted:", 1
    )[1].split("ParallelAnimation {", 1)[0]

    assert "readonly property int none: 0" in duration_block
    assert "readonly property int persistent: -1" in duration_block
    assert "readonly property int instant: 50" in duration_block
    assert "var delay = index * Enums.duration.instant" in breadcrumb_enter_block
    assert "duration: Enums.duration.none" in breadcrumb_enter_block
    assert "var delay = index * 50" not in breadcrumb_enter_block
    assert "duration: 0" not in breadcrumb_enter_block
    assert "property int duration: Enums.duration.persistent" in tip_popup_source
    assert "property int duration: -1" not in tip_popup_source


def test_tip_popup_source_follows_member_and_section_conventions():
    source = TIP_POPUP_SOURCE.read_text(encoding="utf-8")
    path = PurePosixPath(TIP_POPUP_SOURCE.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)

    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009", "QML011"}
    ] == []


def test_tip_popup_shadow_is_attached_after_the_window_is_revealed():
    source = TIP_POPUP_SOURCE.read_text(encoding="utf-8")
    show_block = source.split("function show()", 1)[1].split(
        "function prewarm()", 1
    )[0]
    animation_block = source.split("id: showAnim", 1)[1].split(
        "ParallelAnimation {", 1
    )[0]

    assert show_block.index("_setNativeShadow(false)") < show_block.index(
        "popupWindow.show()"
    )
    assert "ShadowManager.enableShadowForWindow" not in show_block
    assert "_setNativeShadow(true)" in animation_block
    assert "_setNativeShadow(false)" in source.split(
        "function _doClose()", 1
    )[1].split("function _applyTrackedPosition", 1)[0]


def test_tip_popup_auto_close_timer_source_follows_conventions():
    source = TIP_POPUP_TIMER_SOURCE.read_text(encoding="utf-8")
    path = PurePosixPath(TIP_POPUP_TIMER_SOURCE.relative_to(ROOT).as_posix())
    violations = scan_source_text(source, path)

    assert [
        violation
        for violation in violations
        if violation.rule in {"QML008", "QML009", "QML011"}
    ] == []
