# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""TeachingTour spotlight and step-flow regressions. 新手指引聚光灯与步骤流程回归。"""

from pathlib import Path, PurePosixPath
import time

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QPoint,
    QPointF,
    QUrl,
    Qt,
    QMetaObject,
)
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtTest import QTest

from prismqml import register_types
from scripts.qml_conventions import scan_source_text


ROOT = Path(__file__).resolve().parents[2]
OPACITY_MASK_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "effects"
    / "OpacityMask.qml"
)
TEACHING_TOUR_SOURCE = (
    ROOT
    / "prismqml"
    / "PrismQML"
    / "controls"
    / "feedback"
    / "Overlay"
    / "TeachingTour.qml"
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
GALLERY_EXAMPLE_SOURCE = (
    ROOT / "examples" / "pages" / "FeedbackTeachingTourExample.qml"
)
QMLDIR_SOURCE = ROOT / "prismqml" / "PrismQML" / "qmldir"
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "teaching-tour.qml"))
SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root

    property int targetClickCount: 0
    property int backgroundClickCount: 0
    property int completedCount: 0
    property int skippedCount: 0
    property int stepChangeCount: 0

    function startTour() { return tour.start() }
    function moveFirstTarget() { firstTarget.x += 48 }

    width: 640
    height: 480
    color: "white"
    visible: true

    MouseArea {
        anchors.fill: parent
        onClicked: root.backgroundClickCount++
    }

    Item {
        id: sourceHost

        objectName: "sourceHost"
        width: 320
        height: 240

        Rectangle {
            id: firstTarget

            objectName: "firstTarget"
            x: 100
            y: 120
            width: 80
            height: 40
            color: "steelblue"

            MouseArea {
                anchors.fill: parent
                onClicked: root.targetClickCount++
            }
        }

        Rectangle {
            id: secondTarget

            objectName: "secondTarget"
            x: 360
            y: 260
            width: 96
            height: 48
            color: "seagreen"
        }

        TeachingTour {
            id: tour

            objectName: "tour"
            nextButtonText: "Continue"
            finishButtonText: "Done"
            skipButtonText: "Skip"
            steps: [
                {
                    "target": firstTarget,
                    "title": "First",
                    "content": "First target",
                    "anchorPosition": Enums.teachingTip.anchor_top
                },
                {
                    "target": secondTarget,
                    "title": "Second",
                    "content": "Second target",
                    "anchorPosition": Enums.teachingTip.anchor_left
                }
            ]
            onCompleted: root.completedCount++
            onSkipped: root.skippedCount++
            onStepChanged: root.stepChangeCount++
        }
    }
}
"""


def _pump(milliseconds: int = 10) -> None:
    QTest.qWait(milliseconds)


def _wait_for(predicate, timeout_ms: int = 2_000) -> bool:
    deadline = time.monotonic() + timeout_ms / 1_000
    while time.monotonic() < deadline:
        QCoreApplication.processEvents()
        if predicate():
            return True
        _pump(10)
    return predicate()


def _dispose_scene(engine, component, window, tour) -> None:
    QMetaObject.invokeMethod(tour, "stop")
    _pump(200)
    window.close()
    window.deleteLater()
    del component
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.mark.parametrize(
    ("invert", "expected_threshold"),
    ((False, 0.0), (True, 0.5)),
)
def test_opacity_mask_preserves_regular_and_inverted_thresholds(
    qapp, invert, expected_threshold
):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(
        (
            "import PrismQML\n"
            f"OpacityMask {{ invert: {str(invert).lower()} }}"
        ).encode("utf-8"),
        QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "opacity-mask.qml")),
    )
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    item = component.create(engine.rootContext())
    assert isinstance(item, QQuickItem)
    try:
        assert item.property("invert") is invert
        assert item.property("maskInverted") is invert
        assert item.property("maskThresholdMin") == pytest.approx(expected_threshold)
        assert item.property("maskSpreadAtMin") == pytest.approx(1.0)
    finally:
        item.deleteLater()
        del component
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QCoreApplication.processEvents()


def test_gallery_example_creates(qapp):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(GALLERY_EXAMPLE_SOURCE)))
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    item = component.create(engine.rootContext())
    assert isinstance(item, QQuickItem), [
        error.toString() for error in component.errors()
    ]
    item.deleteLater()
    del component
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


@pytest.fixture
def tour_scene(qapp):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    window = component.create(engine.rootContext())
    assert isinstance(window, QQuickWindow), [
        error.toString() for error in component.errors()
    ]
    tour = window.findChild(QQuickItem, "tour")
    assert tour is not None
    _pump(50)
    try:
        yield window, tour
    finally:
        _dispose_scene(engine, component, window, tour)


def test_tour_spotlight_tracks_target_and_keeps_hole_clickable(tour_scene):
    window, tour = tour_scene
    first_target = window.findChild(QQuickItem, "firstTarget")
    source_host = window.findChild(QQuickItem, "sourceHost")
    assert first_target is not None and source_host is not None
    assert tour.parentItem() is source_host

    assert QMetaObject.invokeMethod(window, "startTour")
    assert _wait_for(lambda: tour.property("active"))
    overlay = window.findChild(QQuickItem, "teachingTourOverlay")
    scrim_area = window.findChild(QQuickItem, "teachingTourScrimArea")
    assert overlay is not None and scrim_area is not None
    assert overlay.parentItem() is window.contentItem()
    assert tour.parentItem() is source_host
    assert tour.property("highlightBorderColor").alpha() == 0
    assert tour.property("currentIndex") == 0
    assert window.property("stepChangeCount") == 1

    rect = tour.property("spotlightRect")
    assert rect.x() == pytest.approx(first_target.x() - 8)
    assert rect.y() == pytest.approx(first_target.y() - 8)
    assert rect.width() == pytest.approx(first_target.width() + 16)
    assert rect.height() == pytest.approx(first_target.height() + 16)
    assert scrim_area.contains(QPointF(140, 140)) is False
    assert scrim_area.contains(QPointF(20, 20)) is True

    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=QPoint(140, 140))
    assert _wait_for(lambda: window.property("targetClickCount") == 1)
    assert window.property("backgroundClickCount") == 0

    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=QPoint(20, 20))
    _pump(20)
    assert window.property("backgroundClickCount") == 0

    old_x = rect.x()
    assert QMetaObject.invokeMethod(window, "moveFirstTarget")
    assert _wait_for(lambda: tour.property("spotlightRect").x() == old_x + 48)


def test_tip_actions_advance_finish_and_skip(tour_scene):
    window, tour = tour_scene
    primary = tour.findChild(QQuickItem, "tipPrimaryActionButton")
    secondary = tour.findChild(QQuickItem, "tipSecondaryActionButton")
    assert primary is not None and secondary is not None

    assert QMetaObject.invokeMethod(window, "startTour")
    assert _wait_for(lambda: tour.property("active"))
    assert primary.property("text") == "Continue"

    assert QMetaObject.invokeMethod(primary, "click")
    assert _wait_for(lambda: tour.property("currentIndex") == 1)
    assert primary.property("text") == "Done"
    assert window.property("stepChangeCount") == 2

    assert QMetaObject.invokeMethod(primary, "click")
    assert _wait_for(lambda: not tour.property("active"))
    assert window.property("completedCount") == 1

    assert QMetaObject.invokeMethod(window, "startTour")
    assert _wait_for(lambda: tour.property("active"))
    assert QMetaObject.invokeMethod(secondary, "click")
    assert _wait_for(lambda: not tour.property("active"))
    assert window.property("skippedCount") == 1


def test_tour_components_are_public_and_follow_qml_conventions():
    qmldir = QMLDIR_SOURCE.read_text(encoding="utf-8")
    assert "TeachingTour controls/feedback/Overlay/TeachingTour.qml" in qmldir

    opacity_mask_source = OPACITY_MASK_SOURCE.read_text(encoding="utf-8")
    assert "property bool invert: false" in opacity_mask_source
    assert "maskInverted: root.invert" in opacity_mask_source
    assert "maskThresholdMin: root.invert ? 0.5 : 0.0" in opacity_mask_source
    assert "maskSpreadAtMin: 1.0" in opacity_mask_source

    tour_source = TEACHING_TOUR_SOURCE.read_text(encoding="utf-8")
    assert "mask: ShaderEffectSource" in tour_source
    assert "hideSource: true" in tour_source
    assert "smooth: true" in tour_source
    assert "antialiasing: true" in tour_source
    assert "overlayComponent.createObject(resolvedTarget)" in tour_source
    assert "property color highlightBorderColor: Enums.transparent" in tour_source
    assert "border.width: Enums.border.thin" in tour_source
    assert "property color highlightBorderColor: Enums.accentColor" not in tour_source

    gallery_source = GALLERY_EXAMPLE_SOURCE.read_text(encoding="utf-8")
    assert 'objectName: "galleryTeachingTourStartButton"' in gallery_source
    assert 'objectName: "galleryTeachingTour"' in gallery_source

    for source_path in (OPACITY_MASK_SOURCE, TEACHING_TOUR_SOURCE, TIP_POPUP_SOURCE):
        source = source_path.read_text(encoding="utf-8")
        relative_path = PurePosixPath(source_path.relative_to(ROOT).as_posix())
        violations = scan_source_text(source, relative_path)
        assert [
            violation
            for violation in violations
            if violation.rule in {"QML003", "QML008", "QML009", "QML011"}
        ] == []
