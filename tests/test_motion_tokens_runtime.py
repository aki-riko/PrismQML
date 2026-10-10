# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Motion token runtime contracts. 动效令牌运行时合同。

覆盖 W5 阶段一新增的 PrismEnums/Motion.qml：三条 Fluent 2 标准曲线、时长语义
别名、reduceMotion 归零，以及既有 Enums.motion / Enums.duration 语义零回归。
真实运行时证据：令牌驱动的 NumberAnimation 必须真的跑完。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types, set_reduce_motion
from prismqml.python.core.theme import ThemeManager

ROOT = Path(__file__).resolve().parents[1]

STANDARD = [0.8, 0.0, 0.2, 1.0, 1.0, 1.0]
DECELERATE = [0.1, 0.9, 0.2, 1.0, 1.0, 1.0]
ACCELERATE = [0.7, 0.0, 1.0, 0.5, 1.0, 1.0]

SCENE = """
import QtQuick
import PrismQML

Item {
    id: root
    property var standard: Enums.motionCurve.standard
    property var decelerate: Enums.motionCurve.decelerate
    property var accelerate: Enums.motionCurve.accelerate
    property int easingType: Enums.motionTokens.easingType
    property int bezierEasing: Easing.BezierSpline
    property bool reduceFlag: Enums.reduceMotion
    property int tokenFast: Enums.motionDuration.fast
    property int tokenNormal: Enums.motionDuration.normal
    property int tokenGentle: Enums.motionDuration.gentle
    property int tokenSlow: Enums.motionDuration.slow
    property int tokenFaster: Enums.motionDuration.faster
    property int tokenUltraFast: Enums.motionDuration.ultraFast
    // Legacy metrics must stay untouched 既有度量必须保持原样
    property int legacyNormal: Enums.duration.normal
    property int legacyMedium: Enums.duration.medium
    property int legacySlow: Enums.duration.slow
    property int legacySlower: Enums.duration.slower
    property int legacyFast: Enums.duration.fast
    property int legacyUltraFast: Enums.duration.ultraFast
    property int legacyHoverExit: Enums.motion.hoverExitDuration
    property int legacyMarquee: Enums.motion.navigationTitleMarqueeSpeed

    property real probe: 0
    property bool animDone: false

    NumberAnimation {
        id: tokenAnimation
        target: root
        property: "probe"
        from: 0
        to: 100
        duration: Enums.motionDuration.normal
        easing.type: Enums.motionTokens.easingType
        easing.bezierCurve: Enums.motionCurve.standard
        onFinished: root.animDone = true
    }

    function runTokenAnimation() { tokenAnimation.start() }
}
"""


def _pump(milliseconds: int = 10) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 2_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 10
    return predicate()


def _create(engine: QQmlApplicationEngine, source: str, name: str):
    component = QQmlComponent(engine)
    component.setData(source.encode("utf-8"), QUrl(f"inline:{name}.qml"))
    for _ in range(50):
        if component.status() != QQmlComponent.Status.Loading:
            break
        _pump(20)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    instance = component.create(engine.rootContext())
    assert instance is not None, [error.toString() for error in component.errors()]
    return component, instance


def _dispose(engine, component, instance) -> None:
    if instance is not None:
        instance.deleteLater()
    if component is not None:
        component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def _as_list(value) -> list[float]:
    if hasattr(value, "toVariant"):
        value = value.toVariant()
    return [float(item) for item in value]


@pytest.fixture()
def motion_scene(qapp):
    del qapp
    engine = QQmlApplicationEngine()
    register_types(engine)
    component = instance = None
    set_reduce_motion(False)
    try:
        component, instance = _create(engine, SCENE, "w5-motion-tokens")
        yield instance
    finally:
        set_reduce_motion(False)
        _dispose(engine, component, instance)


def test_fluent_curve_tokens_are_exact(motion_scene):
    assert _as_list(motion_scene.property("standard")) == STANDARD
    assert _as_list(motion_scene.property("decelerate")) == DECELERATE
    assert _as_list(motion_scene.property("accelerate")) == ACCELERATE
    assert motion_scene.property("easingType") == motion_scene.property("bezierEasing")


def test_duration_aliases_track_existing_metrics(motion_scene):
    assert motion_scene.property("tokenUltraFast") == motion_scene.property("legacyUltraFast")
    assert motion_scene.property("tokenFaster") == motion_scene.property("legacyFast")
    assert motion_scene.property("tokenFast") == motion_scene.property("legacyNormal")
    assert motion_scene.property("tokenNormal") == motion_scene.property("legacyMedium")
    assert motion_scene.property("tokenGentle") == motion_scene.property("legacySlow")
    assert motion_scene.property("tokenSlow") == motion_scene.property("legacySlower")


def test_existing_motion_and_duration_aliases_are_unchanged(motion_scene):
    assert motion_scene.property("legacyHoverExit") == 0
    assert motion_scene.property("legacyMarquee") == 25
    assert motion_scene.property("legacyNormal") == 150
    assert motion_scene.property("legacyMedium") == 200
    assert motion_scene.property("legacySlow") == 250
    assert motion_scene.property("legacySlower") == 300


def test_reduce_motion_zeroes_new_tokens_only(motion_scene):
    assert motion_scene.property("reduceFlag") is False
    assert motion_scene.property("tokenNormal") == 200

    set_reduce_motion(True)
    _pump()

    assert motion_scene.property("reduceFlag") is True
    for token in (
        "tokenUltraFast",
        "tokenFaster",
        "tokenFast",
        "tokenNormal",
        "tokenGentle",
        "tokenSlow",
    ):
        assert motion_scene.property(token) == 0, token
    # Existing metrics stay untouched; only the new token layer collapses.
    # 既有度量保持不变，仅新增令牌层归零。
    assert motion_scene.property("legacyMedium") == 200
    assert motion_scene.property("legacyNormal") == 150

    set_reduce_motion(False)
    _pump()
    assert motion_scene.property("tokenNormal") == 200


def test_token_curve_drives_a_real_animation(motion_scene):
    assert motion_scene.property("animDone") is False
    motion_scene.setProperty("probe", 0.0)
    assert motion_scene.metaObject().indexOfMethod("runTokenAnimation()") >= 0
    assert motion_scene.metaObject().invokeMethod(motion_scene, "runTokenAnimation")
    assert _wait_for(lambda: motion_scene.property("animDone") is True)
    assert motion_scene.property("probe") == 100.0


def test_reduce_motion_token_animation_finishes_immediately(motion_scene):
    set_reduce_motion(True)
    _pump()
    motion_scene.setProperty("probe", 0.0)
    assert motion_scene.metaObject().invokeMethod(motion_scene, "runTokenAnimation")
    assert _wait_for(lambda: motion_scene.property("animDone") is True, 500)
    assert motion_scene.property("probe") == 100.0


def test_theme_manager_exposes_reduce_motion_property(qapp):
    del qapp
    manager = ThemeManager()
    assert manager.property("reduceMotion") in (True, False)
    set_reduce_motion(True)
    try:
        assert manager.property("reduceMotion") is True
    finally:
        set_reduce_motion(False)
    assert manager.property("reduceMotion") is False
