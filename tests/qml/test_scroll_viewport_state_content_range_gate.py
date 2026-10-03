# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Content-range conclusion gate regressions. 内容范围结论门回归。"""

from __future__ import annotations

from pathlib import Path

import shiboken6
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QTimer,
    QUrl,
)
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import configure_qml_environment, register_types


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
GATE_CALL = "ScrollViewportConclusion.keepsConclusion(control)"
CONCLUSION_PATH = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "containers"
    / "ScrollBar"
    / "_internal"
    / "ScrollViewportConclusion.js"
)
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "scroll-viewport-state-content-range-gate.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick as QtQ
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/controls/containers/ScrollBar"

Window {
    id: root

    readonly property real overflowingHeight: 960
    readonly property real shortHeight: 40
    readonly property real virtualRowHeight: 40

    property real contentTotalHeight: overflowingHeight
    property real contentTotalWidth: 0
    property int rowCount: 24
    property int virtualRowCount: 0

    function requestInvalidate() {
        viewportState.invalidate()
    }
    function requestScheduleUpdate() {
        viewportState.scheduleUpdate()
    }
    function swapTarget() {
        viewportState.target = viewportState.target === viewport
            ? alternateViewport : viewport
    }
    function wakeVirtualContentChange() {
        virtualState._handleContentChange()
    }
    function rebuildVirtualRows() {
        virtualRows.clear()
        for (var index = 0; index < virtualRowCount; ++index)
            virtualRows.append({ "text": "Row " + index })
    }

    onVirtualRowCountChanged: rebuildVirtualRows()

    width: 360
    height: 240
    visible: true
    color: Enums.backgroundColor

    QtQ.ListModel { id: virtualRows }

    Item {
        id: viewportHost

        width: root.width
        height: root.height

        Flickable {
            id: viewport
            objectName: "viewport"
            anchors.fill: parent
            anchors.rightMargin: viewportState.reserveVerticalGutter
                ? Enums.controlSize.scrollBarWidth : 0
            anchors.bottomMargin: viewportState.reserveHorizontalGutter
                ? Enums.controlSize.scrollBarWidth : 0
            contentWidth: root.contentTotalWidth > width
                ? root.contentTotalWidth : width
            contentHeight: root.contentTotalHeight
        }

        Flickable {
            id: alternateViewport
            objectName: "alternateViewport"
            width: viewportHost.width
            height: viewportHost.height
            contentWidth: width
            contentHeight: root.shortHeight
            visible: false
        }

        // Virtual view whose content extent is committed by a layout pass only.
        QtQ.ListView {
            id: virtualViewport
            objectName: "virtualViewport"
            anchors.fill: parent
            anchors.rightMargin: virtualState.reserveVerticalGutter
                ? Enums.controlSize.scrollBarWidth : 0
            clip: true
            cacheBuffer: 600
            reuseItems: true
            model: virtualRows

            delegate: Item {
                required property string text

                width: QtQ.ListView.view ? QtQ.ListView.view.width : 0
                height: root.virtualRowHeight
            }
        }
    }

    ScrollViewportState {
        id: viewportState
        objectName: "viewportState"
        target: viewport
        scrollBarsEnabled: true
        verticalEnabled: true
        horizontalEnabled: true
        itemCount: root.rowCount
    }

    ScrollViewportState {
        id: virtualState
        objectName: "virtualState"
        target: virtualViewport
        scrollBarsEnabled: true
        verticalEnabled: true
        horizontalEnabled: false
        itemCount: virtualViewport.count
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 3_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _settle_transaction(state: QQuickItem) -> None:
    """Wait for the running re-measure transaction to close. 等待当前重测事务结束。"""
    assert _wait_for(lambda: state.property("_updatePending") is False)


class _ViewportRecorder:
    """Count re-measure rounds and gutter/conclusion changes. 记录重测轮次与避让槽/结论变化。"""

    def __init__(self, state: QQuickItem, viewport: QQuickItem) -> None:
        self._state = state
        self._viewport = viewport
        self._phase_begin = state.property("_phaseBegin")
        self.rounds = 0
        self.gutter_changes: list[bool] = []
        self.vertical_changes: list[bool] = []
        self.horizontal_changes: list[bool] = []
        self.width_changes: list[float] = []
        self.tracking = False
        state._phaseChanged.connect(self._on_phase)
        state.reserveVerticalGutterChanged.connect(self._on_gutter)
        state.needsVerticalChanged.connect(self._on_vertical)
        state.needsHorizontalChanged.connect(self._on_horizontal)
        viewport.widthChanged.connect(self._on_width)

    def start(self) -> None:
        self.rounds = 0
        self.gutter_changes = []
        self.vertical_changes = []
        self.horizontal_changes = []
        self.width_changes = []
        self.tracking = True

    def stop(self) -> None:
        self.tracking = False

    def _on_phase(self) -> None:
        # A gutter round is the re-measure itself, so counting _phaseBegin
        # entries counts how often a content range forced a re-measure.
        # 避让槽轮次就是重测本身，因此统计 _phaseBegin 进入次数即统计内容范围
        # 触发的重测次数。
        if self.tracking and self._state.property("_phase") == self._phase_begin:
            self.rounds += 1

    def _on_gutter(self) -> None:
        if self.tracking:
            self.gutter_changes.append(
                bool(self._state.property("reserveVerticalGutter"))
            )

    def _on_vertical(self) -> None:
        if self.tracking:
            self.vertical_changes.append(bool(self._state.property("needsVertical")))

    def _on_horizontal(self) -> None:
        if self.tracking:
            self.horizontal_changes.append(
                bool(self._state.property("needsHorizontal"))
            )

    def _on_width(self) -> None:
        if self.tracking:
            self.width_changes.append(float(self._viewport.property("width")))


def _function_body(source: str, name: str) -> str:
    start = source.index(f"function {name}(")
    depth = 0
    for index in range(source.index("{", start), len(source)):
        character = source[index]
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"unterminated function {name}")


def _create_scene():
    configure_qml_environment()
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
    # The initial overflow must settle with a committed vertical gutter.
    # 初始溢出必须停稳并提交垂直避让槽。
    assert _wait_for(
        lambda: state.property("_updatePending") is False
        and state.property("needsVertical") is True
        and state.property("reserveVerticalGutter") is True
    ), (
        state.property("_updatePending"),
        state.property("needsVertical"),
        state.property("reserveVerticalGutter"),
    )
    return engine, component, window, state, viewport, warnings


def _dispose_scene(qapp, engine, component, window) -> None:
    window.close()
    for obj in (window, component, engine):
        if obj is not None and shiboken6.isValid(obj):
            obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def test_refined_content_range_keeps_conclusion_without_remeasure(qapp):
    """Scrolling content estimates must not re-run the gutter round.

    滚动中的内容范围估算不得重跑避让槽重测轮次。
    """
    engine, component, window, state, viewport, warnings = _create_scene()
    try:
        recorder = _ViewportRecorder(state, viewport)
        settled_width = float(viewport.property("width"))
        viewport_height = float(viewport.property("height"))
        # A long virtual list keeps refining contentHeight while scrolling, and
        # every estimate still overflows the viewport.
        # 长虚拟列表滚动时持续修正 contentHeight，每一版估算都仍然溢出视口。
        estimates = [
            viewport_height * 32,
            viewport_height * 30,
            viewport_height * 28.5,
            viewport_height * 27.2,
            viewport_height * 25.9,
            viewport_height * 24.4,
        ]
        recorder.start()
        for estimate in estimates:
            window.setProperty("contentTotalHeight", estimate)
            _pump(30)
        _pump(400)
        recorder.stop()

        assert float(viewport.property("contentHeight")) == estimates[-1]
        assert recorder.rounds == 0, recorder.rounds
        assert recorder.gutter_changes == [], recorder.gutter_changes
        assert recorder.vertical_changes == [], recorder.vertical_changes
        assert recorder.horizontal_changes == [], recorder.horizontal_changes
        assert recorder.width_changes == [], recorder.width_changes
        assert float(viewport.property("width")) == settled_width
        assert state.property("needsVertical") is True
        assert state.property("reserveVerticalGutter") is True
        assert state.property("_updatePending") is False
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_conclusion_flip_still_runs_the_full_round(qapp):
    """A flipped overflow answer must still re-measure both axes.

    溢出结论翻转时必须仍然完整重测两轴。
    """
    engine, component, window, state, viewport, warnings = _create_scene()
    try:
        recorder = _ViewportRecorder(state, viewport)
        guttered_width = float(viewport.property("width"))
        viewport_height = float(viewport.property("height"))

        # Overflow -> fits: the vertical conclusion flips and must re-measure.
        # 溢出 -> 不溢出: 垂直结论翻转，必须重新测量。
        recorder.start()
        window.setProperty("contentTotalHeight", viewport_height - 40)
        assert _wait_for(lambda: state.property("needsVertical") is False)
        _settle_transaction(state)
        recorder.stop()
        assert recorder.rounds >= 1, recorder.rounds
        assert recorder.gutter_changes[-1] is False, recorder.gutter_changes
        assert recorder.vertical_changes[-1] is False, recorder.vertical_changes
        assert state.property("reserveVerticalGutter") is False
        assert float(viewport.property("width")) > guttered_width

        # Fits -> overflow: the reverse flip must re-measure as well.
        # 不溢出 -> 溢出: 反向翻转同样必须重新测量。
        recorder.start()
        window.setProperty("contentTotalHeight", viewport_height * 4)
        assert _wait_for(lambda: state.property("needsVertical") is True)
        _settle_transaction(state)
        recorder.stop()
        assert recorder.rounds >= 1, recorder.rounds
        assert recorder.gutter_changes[-1] is True, recorder.gutter_changes
        assert recorder.vertical_changes[-1] is True, recorder.vertical_changes
        assert float(viewport.property("width")) == guttered_width

        # Cross axis: a horizontal flip must re-measure even though the
        # vertical conclusion stays committed.
        # 交叉轴: 即使垂直结论保持不变，水平翻转也必须重新测量。
        recorder.start()
        window.setProperty("contentTotalWidth", guttered_width + 120)
        assert _wait_for(lambda: state.property("needsHorizontal") is True)
        _settle_transaction(state)
        recorder.stop()
        assert recorder.rounds >= 1, recorder.rounds
        assert recorder.horizontal_changes[-1] is True, recorder.horizontal_changes

        # Both axes stable again: further range corrections stay gated.
        # 两轴再次稳定: 后续内容范围修正继续被结论门拦下。
        recorder.start()
        window.setProperty("contentTotalWidth", guttered_width + 360)
        _pump(400)
        recorder.stop()
        assert recorder.rounds == 0, recorder.rounds
        assert recorder.horizontal_changes == [], recorder.horizontal_changes
        assert state.property("needsHorizontal") is True

        # Horizontal overflow -> fits with a stable vertical conclusion.
        # 水平溢出 -> 不溢出，且垂直结论保持稳定。
        recorder.start()
        window.setProperty("contentTotalWidth", 0)
        assert _wait_for(lambda: state.property("needsHorizontal") is False)
        _settle_transaction(state)
        recorder.stop()
        assert recorder.rounds >= 1, recorder.rounds
        assert recorder.horizontal_changes[-1] is False, recorder.horizontal_changes

        # itemCount === 0 must still collapse both conclusions.
        # itemCount === 0 必须仍然把两轴结论都收敛为 false。
        recorder.start()
        window.setProperty("rowCount", 0)
        assert _wait_for(
            lambda: state.property("needsVertical") is False
            and state.property("needsHorizontal") is False
        )
        _settle_transaction(state)
        recorder.stop()
        assert recorder.rounds >= 1, recorder.rounds
        assert state.property("reserveVerticalGutter") is False
        assert state.property("reserveHorizontalGutter") is False

        recorder.start()
        window.setProperty("rowCount", 24)
        assert _wait_for(lambda: state.property("needsVertical") is True)
        _settle_transaction(state)
        recorder.stop()
        assert recorder.rounds >= 1, recorder.rounds
        assert state.property("reserveVerticalGutter") is True
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_explicit_requests_and_viewport_changes_keep_the_full_round(qapp):
    """Explicit requests, resizes and target rebuilds are never gated.

    显式请求、视口变尺与目标重建永不被结论门拦下。
    """
    engine, component, window, state, viewport, warnings = _create_scene()
    try:
        recorder = _ViewportRecorder(state, viewport)
        viewport_height = float(viewport.property("height"))

        recorder.start()
        assert QMetaObject.invokeMethod(window, "requestInvalidate")
        _settle_transaction(state)
        recorder.stop()
        assert recorder.rounds >= 1, recorder.rounds

        recorder.start()
        assert QMetaObject.invokeMethod(window, "requestScheduleUpdate")
        _settle_transaction(state)
        recorder.stop()
        assert recorder.rounds >= 1, recorder.rounds

        # A viewport resize that also refines the content range must keep the
        # full round instead of being gated away.
        # 视口变尺与内容范围修正同时发生时，必须保留完整流程，不得被结论门跳过。
        recorder.start()
        window.resize(360, int(viewport_height - 60))
        _pump(80)
        window.setProperty("contentTotalHeight", viewport_height * 3)
        _pump(400)
        _settle_transaction(state)
        recorder.stop()
        assert recorder.rounds >= 1, recorder.rounds
        assert state.property("needsVertical") is True

        # A rebuilt target always re-measures, even with a stable range.
        # 目标重建即使内容范围不变也必须重新测量。
        recorder.start()
        assert QMetaObject.invokeMethod(window, "swapTarget")
        assert _wait_for(lambda: state.property("needsVertical") is False)
        _settle_transaction(state)
        recorder.stop()
        assert recorder.rounds >= 1, recorder.rounds
        assert state.property("reserveVerticalGutter") is False

        recorder.start()
        assert QMetaObject.invokeMethod(window, "swapTarget")
        assert _wait_for(lambda: state.property("needsVertical") is True)
        _settle_transaction(state)
        recorder.stop()
        assert recorder.rounds >= 1, recorder.rounds
        assert state.property("reserveVerticalGutter") is True
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_virtual_view_model_clear_still_removes_the_gutter(qapp):
    """Clearing a virtual view's model must still remove the gutter.

    清空虚拟视图的模型必须仍然撤销避让槽。
    """
    engine, component, window, state, viewport, warnings = _create_scene()
    try:
        virtual_state = window.findChild(QQuickItem, "virtualState")
        virtual_view = window.findChild(QQuickItem, "virtualViewport")
        assert virtual_state is not None
        assert virtual_view is not None
        window.setProperty("virtualRowCount", 20)
        assert _wait_for(
            lambda: virtual_view.property("count") == 20
            and virtual_state.property("_updatePending") is False
            and virtual_state.property("needsVertical") is True
            and virtual_state.property("reserveVerticalGutter") is True
        ), (
            virtual_view.property("count"),
            virtual_view.property("contentHeight"),
            virtual_state.property("needsVertical"),
        )
        guttered_width = float(virtual_view.property("width"))
        assert float(virtual_view.property("contentHeight")) > float(
            virtual_view.property("height")
        )

        # A virtual view may commit its cleared extent without emitting a
        # content signal, so wake the content-range path explicitly and require
        # the round to still conclude "no overflow".
        # 虚拟视图清空后可能不发内容信号，因此显式唤醒内容范围路径，并要求该轮
        # 仍然得出「不溢出」结论。
        window.setProperty("virtualRowCount", 0)
        assert _wait_for(lambda: virtual_view.property("count") == 0)
        assert QMetaObject.invokeMethod(window, "wakeVirtualContentChange")
        assert _wait_for(
            lambda: virtual_state.property("needsVertical") is False
        ), (
            virtual_view.property("contentHeight"),
            virtual_state.property("needsVertical"),
            virtual_state.property("reserveVerticalGutter"),
        )
        _settle_transaction(virtual_state)
        assert virtual_state.property("reserveVerticalGutter") is False
        assert float(virtual_view.property("width")) > guttered_width
        assert warnings == []
    finally:
        _dispose_scene(qapp, engine, component, window)


def test_content_range_gate_stays_on_the_content_update_path():
    """The gate may only guard the content-range path. 结论门只允许作用于内容范围路径。"""
    source = SOURCE_PATH.read_text(encoding="utf-8")
    helper = CONCLUSION_PATH.read_text(encoding="utf-8")
    # Each gutter round measures once, and the gate commits the pending layout
    # once instead of running a round, so counting rounds is the observable form
    # of counting gutter re-measures.
    # 每轮避让槽重测测量一次；结论门则以一次布局提交取代一整轮，因此统计轮次即
    # 统计避让槽重测次数。
    assert source.count("target.forceLayout()") == 1
    assert source.count("typeof target.forceLayout") == 1
    assert helper.count("target.forceLayout()") == 1
    assert helper.count("typeof target.forceLayout") == 1
    # Exactly one call site: the deferred content-range phase. Explicit
    # scheduleUpdate()/invalidate() requests must stay ungated.
    # 全文件只有一个调用点: 延迟的内容范围阶段；显式 scheduleUpdate()/invalidate()
    # 请求必须保持不被结论门拦截。
    assert source.count(GATE_CALL) == 1
    phase_body = source.split("case _phaseContentUpdate:", 1)[1].split("break", 1)[0]
    assert GATE_CALL in phase_body
    assert "scheduleUpdate()" in phase_body
    # Both axes decide whether a range change may skip the round.
    # 两轴分别决定内容范围变化能否跳过本轮重测。
    gate_body = _function_body(helper, "keepsConclusion")
    assert "target.contentHeight > target.height" in gate_body
    assert "target.contentWidth > target.width" in gate_body
    assert "alwaysShowVertical" in gate_body
    assert "alwaysShowHorizontal" in gate_body
    assert "scrollBarsEnabled" in gate_body
    assert "verticalEnabled" in gate_body
    assert "horizontalEnabled" in gate_body
    assert "itemCount === 0" in gate_body
    assert "vertical === host._needsVertical" in gate_body
    assert "horizontal === host._needsHorizontal" in gate_body
    # The range must be read after committing the pending layout, otherwise a
    # virtual view is judged by its previous extent.
    # 必须先提交待处理布局再读取内容范围，否则虚拟视图会被旧范围判定。
    assert gate_body.index("target.forceLayout()") < gate_body.index(
        "target.contentHeight > target.height"
    )
