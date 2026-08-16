# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Scroll viewport timer lifecycle regressions. 滚动视口计时器生命周期回归。"""

from __future__ import annotations

import hashlib
from pathlib import Path

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "containers"
    / "ScrollBar"
    / "ScrollViewportState.qml"
)
TIMER_SOURCE_PATH = (
    SOURCE_PATH.parent / "_internal" / "ScrollViewportPhaseTimer.qml"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "scroll-viewport-state-timer-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/containers/ScrollBar"

Window {
    id: root

    readonly property int contentDelay: Enums.duration.fast
    readonly property int suppressionDelay: Enums.duration.instant

    function growContent() {
        viewport.contentHeight += Enums.spacing.xl
    }
    function startSuppressedUpdate() {
        viewportState.scheduleUpdate()
        viewport.width -= Enums.border.thin
        viewportState._handleContentChange()
    }
    function restoreViewportWidth() {
        viewport.width = root.width
    }

    width: 320
    height: 180
    visible: true
    color: Enums.backgroundColor

    Rectangle {
        anchors.fill: parent
        color: Enums.cardColor
    }

    Flickable {
        id: viewport
        objectName: "viewport"
        width: root.width
        height: root.height
        contentWidth: width
        contentHeight: height + Enums.controlSize.navBarHeight
        visible: false
    }

    ScrollViewportState {
        id: viewportState
        objectName: "viewportState"
        target: viewport
        scrollBarsEnabled: true
        verticalEnabled: true
        horizontalEnabled: false
        itemCount: 1
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


def _direct_timers(state: QObject) -> list[QObject]:
    return [
        child
        for child in state.children()
        if child.objectName() == "scrollViewportPhaseTimer"
    ]


def _running_timers(state: QObject) -> list[QObject]:
    return [timer for timer in _direct_timers(state) if timer.property("running")]


def _image_hash(image: QImage) -> str:
    normalized = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return hashlib.sha256(bytes(normalized.bits())).hexdigest()


def _stable_hash(window: QQuickWindow) -> str:
    previous = ""
    stable_count = 0
    for _ in range(30):
        _pump(40)
        image = window.grabWindow()
        assert not image.isNull()
        current = _image_hash(image)
        stable_count = stable_count + 1 if current == previous else 1
        if stable_count >= 3:
            return current
        previous = current
    raise AssertionError("Scroll viewport pixels did not stabilize")


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
    assert _wait_for(lambda: component.status() != QQmlComponent.Status.Loading)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    state = window.findChild(QQuickItem, "viewportState")
    viewport = window.findChild(QQuickItem, "viewport")
    assert state is not None
    assert viewport is not None
    assert _wait_for(window.isExposed)
    assert _wait_for(
        lambda: state.property("_updatePending") is False
        and state.property("needsVertical") is True
    )
    return engine, component, window, state, viewport, warnings


def _dispose_scene(qapp, engine, component, window) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def test_scroll_viewport_state_timer_phase_baseline(qapp):
    """One timer remains exclusive across debounce and clear phases.

    一个计时器在内容防抖与抑制清理阶段保持互斥。
    """
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, state, viewport, warnings = _create_scene()
    try:
        initial_hash = _stable_hash(window)
        initial_object_count = len(state.findChildren(QObject))
        assert len(_direct_timers(state)) == 1
        phase_timer = _direct_timers(state)[0]
        assert phase_timer.parent() is state
        assert phase_timer.property("host") == state
        assert phase_timer.property("repeat") is False
        assert _running_timers(state) == []

        assert QMetaObject.invokeMethod(window, "growContent")
        assert _wait_for(lambda: len(_running_timers(state)) == 1)
        content_timer = _running_timers(state)[0]
        content_timer_count = len(_direct_timers(state))
        assert content_timer.property("interval") == window.property("contentDelay")
        assert content_timer.property("repeat") is False
        assert _wait_for(
            lambda: state.property("_updatePending") is False
            and _running_timers(state) == []
        )
        assert state.property("needsVertical") is True

        assert QMetaObject.invokeMethod(window, "startSuppressedUpdate")
        assert _wait_for(
            lambda: len(_running_timers(state)) == 1
            and _running_timers(state)[0].property("interval")
            == window.property("suppressionDelay")
        )
        suppression_timer_count = len(_direct_timers(state))
        assert state.property("_suppressViewportContentChanges") is True
        assert state.property("_clearDeferrals") == 1
        assert _wait_for(
            lambda: state.property("_updatePending") is False
            and _running_timers(state) == []
        )
        assert QMetaObject.invokeMethod(window, "restoreViewportWidth")
        restored_hash = _stable_hash(window)
        settled_timer_count = len(_direct_timers(state))
        settled_object_count = len(state.findChildren(QObject))

        print(
            "SCROLL_VIEWPORT_TIMER",
            f"timers=1/{content_timer_count}/{suppression_timer_count}/"
            f"{settled_timer_count}",
            f"objects={initial_object_count}/{settled_object_count}",
            f"hashes={initial_hash}/{restored_hash}",
        )

        assert (
            content_timer_count,
            suppression_timer_count,
            settled_timer_count,
        ) == (1, 1, 1)
        assert (initial_object_count, settled_object_count) == (3, 3)
        assert (initial_hash, restored_hash) == (
            "1516b21572cdecd2baad775e49c4a2d235b7ce37c9692d90df6b9e0df92f820c",
            "1516b21572cdecd2baad775e49c4a2d235b7ce37c9692d90df6b9e0df92f820c",
        )
        assert warnings == []
        assert state.property("needsVertical") is True
        assert state.property("needsHorizontal") is False
        assert viewport.property("width") == window.property("width")
    finally:
        _dispose_scene(qapp, engine, component, window)
        assert [
            candidate
            for candidate in QGuiApplication.topLevelWindows()
            if candidate.isVisible()
            and not any(candidate is existing for existing in windows_before)
        ] == []


def test_scroll_viewport_state_source_reuses_one_phase_timer():
    """Exclusive roles reuse one timer. 互斥角色复用一个计时器。"""
    source = SOURCE_PATH.read_text(encoding="utf-8")
    timer_source = TIMER_SOURCE_PATH.read_text(encoding="utf-8")
    assert "\n    Timer {" not in source
    assert timer_source.count("Timer {") == 1
    assert "ScrollBarInternal.ScrollViewportPhaseTimer {" in source
    assert "id: phaseTimer" in source
    assert "host: control" in source
    assert "id: contentUpdateTimer" not in source
    assert "id: suppressionClearTimer" not in source
    assert "_phaseContentUpdate" in source
    assert "_phaseSuppressionClear" in source
    assert "onTriggered: host._runPhase()" in timer_source
