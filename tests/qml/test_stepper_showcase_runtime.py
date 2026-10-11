# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Showcase stepper runtime regressions. 炫技步骤条运行时回归。"""

from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import register_types, set_reduce_motion


ROOT = Path(__file__).resolve().parents[2]
STEP_ROOT = ROOT / "prismqml" / "PrismQML" / "controls" / "data" / "Step"
STEPPER_SOURCE = STEP_ROOT / "Stepper.qml"
INTERNAL_SOURCES = (
    STEP_ROOT / "_internal" / "StepperMotion.qml",
    STEP_ROOT / "_internal" / "StepperTrack.qml",
    STEP_ROOT / "_internal" / "StepperHalo.qml",
    STEP_ROOT / "_internal" / "StepperBurst.qml",
)
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "stepper-showcase.qml"))

# A five-step stepper keeps exactly three looping animations alive: the highlight
# sweep, the pending dot trail and the active halo breath. The step count must not
# raise that number, and the burst peak must stay bounded.
# 五步步骤条恰好保持三个循环动画：流光、流动点阵与当前光晕呼吸。
# 步骤数不得抬高该数量，迸发峰值也必须有界。
IDLE_LOOP_BUDGET = 3
BURST_PEAK_BUDGET = 20
FRAME_DRIVEN_TOKENS = (
    "Canvas {",
    "Timer {",
    "ShaderEffect",
    "layer.enabled",
    "Qt.rgba",
    "Qt.hsla",
)

SCENE_TEMPLATE = """
import QtQuick
import PrismQML

Item {
    id: scene

    property alias stepper: stepper
    property int clicks: 0
    property int changes: 0

    width: 900
    height: 300

    Stepper {
        id: stepper
        objectName: "stepper"
        width: 800
        steps: %s
        currentStep: %d
        onStepClicked: function(index) { scene.clicks = index + 1 }
        onStepChanged: scene.changes = scene.changes + 1
    }
}
"""


def _steps_literal(count: int) -> str:
    entries = ", ".join('{ text: "Step %d" }' % (index + 1) for index in range(count))
    return "[" + entries + "]"


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _create_scene(step_count: int = 5, current_step: int = 2):
    warnings: list[str] = []
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    engine.warnings.connect(lambda items: warnings.extend(i.toString() for i in items))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        (SCENE_TEMPLATE % (_steps_literal(step_count), current_step)).encode("utf-8"),
        SCENE_URL,
    )
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    _pump(40)
    return engine, component, root, warnings


def _destroy(engine, component, root) -> None:
    root.deleteLater()
    del component
    engine.deleteLater()
    _pump(1)


def _walk(root):
    stack = [root]
    while stack:
        item = stack.pop()
        yield item
        stack.extend(item.childItems())


def _snapshot(root) -> dict:
    """Count live animations and showcase layer states. 统计活动动画与炫技层状态。"""
    state = {
        "running": 0,
        "looping": 0,
        "halos": 0,
        "active_halos": 0,
        "bursts": 0,
        "bursting": 0,
    }
    for item in _walk(root):
        class_name = item.metaObject().className()
        if class_name.startswith("StepperHalo"):
            state["halos"] += 1
            if item.property("active"):
                state["active_halos"] += 1
        elif class_name.startswith("StepperBurst"):
            state["bursts"] += 1
            if item.property("_bursting"):
                state["bursting"] += 1
        for child in item.children():
            meta = child.metaObject()
            if "Animation" not in meta.className():
                continue
            if meta.indexOfProperty("running") < 0:
                continue
            if not child.property("running"):
                continue
            state["running"] += 1
            if child.property("loops") == -1:
                state["looping"] += 1
    return state


def test_showcase_stepper_preserves_public_api(qapp):
    engine, component, root, warnings = _create_scene()
    try:
        stepper = root.findChild(QQuickItem, "stepper")
        assert stepper is not None
        assert stepper.property("implicitWidth") == 500.0
        assert stepper.property("implicitHeight") == 62.0
        assert root.property("changes") == 0

        stepper.setProperty("currentStep", 3)
        _pump(10)
        assert root.property("changes") == 1

        stepper.metaObject().invokeMethod(stepper, "stepNext")
        _pump(10)
        assert stepper.property("currentStep") == 4
        stepper.metaObject().invokeMethod(stepper, "stepBack")
        _pump(10)
        assert stepper.property("currentStep") == 3

        assert warnings == []
    finally:
        _destroy(engine, component, root)


def test_showcase_scene_loads_without_qml_warnings(qapp):
    engine, component, root, warnings = _create_scene()
    try:
        assert warnings == []
        stepper = root.findChild(QQuickItem, "stepper")
        stepper.setProperty("steps", None)
        _pump(20)
        assert warnings == []
        assert stepper.property("implicitWidth") >= 0
        assert stepper.property("implicitHeight") > 0
    finally:
        _destroy(engine, component, root)


def test_showcase_layers_follow_steps_without_growing_loops(qapp):
    loops: list[int] = []
    for step_count in (3, 8):
        engine, component, root, warnings = _create_scene(step_count, 1)
        try:
            state = _snapshot(root)
            assert state["halos"] == step_count
            assert state["bursts"] == step_count
            assert state["active_halos"] == 1
            assert state["bursting"] == 0
            assert state["looping"] <= IDLE_LOOP_BUDGET
            assert warnings == []
            loops.append(state["looping"])
        finally:
            _destroy(engine, component, root)
    assert loops[0] == loops[1], loops


def test_showcase_burst_fires_once_per_advance(qapp):
    engine, component, root, warnings = _create_scene()
    try:
        stepper = root.findChild(QQuickItem, "stepper")
        assert _snapshot(root)["bursting"] == 0

        stepper.setProperty("currentStep", 3)
        _pump(30)
        advancing = _snapshot(root)
        assert advancing["bursting"] == 1
        assert advancing["running"] <= BURST_PEAK_BUDGET

        _pump(400)
        settled = _snapshot(root)
        assert settled["bursting"] == 0
        assert settled["looping"] <= IDLE_LOOP_BUDGET
        assert warnings == []
    finally:
        _destroy(engine, component, root)


def test_showcase_loops_stop_under_reduced_motion(qapp):
    set_reduce_motion(True)
    engine = component = root = None
    try:
        engine, component, root, warnings = _create_scene()
        assert _snapshot(root)["looping"] == 0

        stepper = root.findChild(QQuickItem, "stepper")
        stepper.setProperty("currentStep", 3)
        _pump(30)
        assert _snapshot(root)["bursting"] == 0
        assert warnings == []
    finally:
        set_reduce_motion(False)
        if root is not None:
            _destroy(engine, component, root)


def test_showcase_sources_avoid_frame_driven_work():
    for path in (STEPPER_SOURCE,) + INTERNAL_SOURCES:
        source = path.read_text(encoding="utf-8")
        assert len(source.splitlines()) < 500, path.name
        for token in FRAME_DRIVEN_TOKENS:
            assert token not in source, (path.name, token)


def test_showcase_entry_keeps_shared_token_anchors():
    source = STEPPER_SOURCE.read_text(encoding="utf-8")
    assert source.count("HoverBehavior on ") == 1
    assert "id: checkIcon" in source
    assert "id: numberText" in source
    assert (
        "readonly property color _stepActiveContentColor: Enums.accentForeground"
        in source
    )
    assert (
        "readonly property color _stepInactiveContentColor: Enums.textColor.secondary"
        in source
    )
