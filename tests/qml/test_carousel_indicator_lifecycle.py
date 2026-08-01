# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Carousel indicator lifecycle regressions. 轮播指示器生命周期回归。"""

from pathlib import Path

import pytest
import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QObject, Qt, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import configure_qml_environment, register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE = b"""
import QtQuick
import PrismQML

Carousel {
    objectName: "carousel"
    readonly property int testSpacingL: Enums.spacing.l
    width: 320
    height: 200
    model: [
        { text: "One" },
        { text: "Two" },
        { text: "Three" }
    ]
}
"""


def _release(qapp, *objects) -> None:
    for item in objects:
        if item is not None and shiboken6.isValid(item):
            item.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    qapp.processEvents()


def _indicator(carousel):
    matches = [
        child
        for child in carousel.findChildren(QObject)
        if "PipsPager" in child.metaObject().className()
        and child.metaObject().indexOfProperty("vertical") >= 0
    ]
    assert len(matches) == 1, [child.metaObject().className() for child in matches]
    return matches[0]


def test_carousel_reuses_one_indicator_across_orientation_changes(qapp):
    configure_qml_environment()
    engine = QQmlApplicationEngine()
    component = None
    carousel = None
    try:
        register_types(engine)
        component = QQmlComponent(engine)
        component.setData(
            SCENE,
            QUrl.fromLocalFile(
                str(ROOT / "tests/qml/carousel-indicator-lifecycle.qml")
            ),
        )
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        carousel = component.create(engine.rootContext())
        assert carousel is not None, [error.toString() for error in component.errors()]
        qapp.processEvents()

        indicator = _indicator(carousel)
        spacing = float(carousel.property("testSpacingL"))
        assert indicator.property("vertical") is False
        assert indicator.property("count") == 3
        assert indicator.property("currentIndex") == 0
        assert indicator.x() + indicator.width() / 2 == pytest.approx(
            carousel.width() / 2
        )
        assert indicator.y() + indicator.height() == pytest.approx(
            carousel.height() - spacing
        )

        carousel.setCurrentIndex(2)
        carousel.setProperty("orientation", Qt.Orientation.Vertical.value)
        qapp.processEvents()

        assert _indicator(carousel) == indicator
        assert indicator.property("vertical") is True
        assert indicator.property("currentIndex") == 2
        assert indicator.x() + indicator.width() == pytest.approx(
            carousel.width() - spacing
        )
        assert indicator.y() + indicator.height() / 2 == pytest.approx(
            carousel.height() / 2
        )
    finally:
        _release(qapp, carousel, component, engine)
