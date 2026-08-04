# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Confetti particle shape lifecycle regressions. 彩纸粒子形状生命周期回归。"""

from __future__ import annotations

from pathlib import Path
from time import perf_counter

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QEventLoop,
    QMetaObject,
    QObject,
    QPointF,
    QTimer,
    QUrl,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "confetti-particle-shape-lifecycle.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    property int sampleParticleCount: 1
    readonly property real expectedMicroRadius: Enums.radius.micro

    width: 420
    height: 320
    visible: true
    color: Enums.backgroundColor

    Confetti {
        id: confetti

        objectName: "confetti"
        particleCount: root.sampleParticleCount
        duration: 1000000
        colors: [Enums.accentColor]
    }
}
"""


def _pump(milliseconds: int = 20) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _wait_for(predicate, timeout_ms: int = 1_000) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if predicate():
            return True
        _pump()
        elapsed += 20
    return predicate()


def _new_visible_windows(windows_before, *allowed):
    return [
        window
        for window in QGuiApplication.topLevelWindows()
        if window.isVisible()
        and not any(window is existing for existing in windows_before)
        and not any(window is expected for expected in allowed)
    ]


def _create_scene(particle_count: int = 1):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.createWithInitialProperties(
        {"sampleParticleCount": particle_count}, engine.rootContext()
    )
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    QCoreApplication.processEvents()
    confetti = window.findChild(QQuickItem, "confetti")
    assert confetti is not None
    return engine, component, window, confetti, warnings


def _dispose_scene(engine, component, window) -> None:
    window.setVisible(False)
    window.deleteLater()
    component.deleteLater()
    engine.collectGarbage()
    engine.clearComponentCache()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def _particles(confetti: QQuickItem) -> list[QQuickItem]:
    return [
        item
        for item in confetti.findChildren(QQuickItem)
        if item.metaObject().indexOfProperty("shapeType") >= 0
        and item.metaObject().indexOfProperty("particleSize") >= 0
    ]


def _shape_rectangle(particle: QQuickItem) -> QQuickItem:
    rectangles = [
        item
        for item in particle.findChildren(QQuickItem)
        if item.metaObject().className().startswith("QQuickRectangle")
    ]
    assert len(rectangles) == 1
    return rectangles[0]


def _set_shape(particle: QQuickItem, shape_type: int) -> QQuickItem:
    intermediate_type = (shape_type + 1) % 3
    assert particle.setProperty("shapeType", intermediate_type)
    _pump()
    assert particle.setProperty("shapeType", shape_type)
    _pump()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()
    return _shape_rectangle(particle)


@pytest.mark.parametrize(
    ("shape_type", "width", "height", "radius_kind", "rotation"),
    [
        (0, 20.0, 12.0, "micro", 30.0),
        (1, 16.0, 16.0, "circle", 0.0),
        (2, 30.0, 6.0, "pill", 30.0),
    ],
)
def test_confetti_particle_shapes_preserve_geometry_and_color(
    shape_type, width, height, radius_kind, rotation, qapp
):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, confetti, warnings = _create_scene()
    try:
        assert QMetaObject.invokeMethod(confetti, "start")
        assert _wait_for(lambda: len(_particles(confetti)) == 1)
        particle = _particles(confetti)[0]
        assert particle.setProperty("particleSize", 20.0)
        assert particle.setProperty("initialRotation", 30.0)
        assert particle.setProperty("rotationSpeed", 0.0)
        rectangle = _set_shape(particle, shape_type)

        expected_radius = {
            "micro": window.property("expectedMicroRadius"),
            "circle": width / 2,
            "pill": height / 2,
        }[radius_kind]
        center = rectangle.mapToItem(
            particle, QPointF(width / 2, height / 2)
        )

        assert rectangle.width() == pytest.approx(width)
        assert rectangle.height() == pytest.approx(height)
        assert rectangle.property("radius") == pytest.approx(expected_radius)
        assert rectangle.rotation() == pytest.approx(rotation, abs=0.1)
        assert rectangle.property("color") == particle.property("particleColor")
        assert center.x() == pytest.approx(0.0, abs=0.1)
        assert center.y() == pytest.approx(0.0, abs=0.1)
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_confetti_particle_shape_object_baseline(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, confetti, warnings = _create_scene()
    try:
        assert QMetaObject.invokeMethod(confetti, "start")
        assert _wait_for(lambda: len(_particles(confetti)) == 1)
        particle = _particles(confetti)[0]
        rectangle = _set_shape(particle, 0)
        descendants = particle.findChildren(QObject)
        loaders = [
            obj
            for obj in descendants
            if obj.metaObject().className().startswith("QQuickLoader")
        ]
        components = [
            obj
            for obj in descendants
            if obj.metaObject().className().startswith("QQmlComponent")
        ]

        print(
            "CONFETTI_PARTICLE_OBJECTS",
            f"objects={len(descendants)}",
            f"loaders={len(loaders)}",
            f"components={len(components)}",
        )

        assert rectangle is not None
        assert len(descendants) == 16
        assert len(loaders) == 1
        assert len(components) == 3
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []


def test_confetti_initial_batch_object_baseline(qapp):
    windows_before = tuple(QGuiApplication.topLevelWindows())
    engine, component, window, confetti, warnings = _create_scene(20)
    try:
        started = perf_counter()
        assert QMetaObject.invokeMethod(confetti, "start")
        elapsed_ms = (perf_counter() - started) * 1_000
        particles = _particles(confetti)
        assert len(particles) == 20
        for particle in particles:
            assert particle.setProperty("shapeType", 0)
        _pump()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()
        object_count = len(confetti.findChildren(QObject))

        print(
            "CONFETTI_INITIAL_BATCH",
            f"objects={object_count}",
            f"start_ms={elapsed_ms:.3f}",
        )

        assert object_count == 343
        assert warnings == []
        assert _new_visible_windows(windows_before, window) == []
    finally:
        _dispose_scene(engine, component, window)
        assert _new_visible_windows(windows_before) == []
