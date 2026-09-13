# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""SkinScope surface and reparenting regression coverage. 局部皮肤表面与重挂载回归。"""

from pathlib import Path

import pytest

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import Skin, Theme, getSkin, getTheme, register_types, setSkin, setTheme


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "skin-scope-surfaces.qml")
)


def _pump(milliseconds: int = 0) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


@pytest.fixture(autouse=True)
def _preserve_global_appearance():
    previous_skin = getSkin()
    previous_theme = getTheme()
    try:
        yield
    finally:
        setSkin(previous_skin)
        setTheme(previous_theme)


def _create_scene(qapp):
    engine = QQmlApplicationEngine()
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    setSkin(Skin.FLUENT)
    setTheme(Theme.LIGHT)
    component = QQmlComponent(engine, SCENE_URL)
    if component.status() == QQmlComponent.Status.Loading:
        loop = QEventLoop()
        component.statusChanged.connect(lambda _status: loop.quit())
        QTimer.singleShot(5000, loop.quit)
        loop.exec()

    try:
        assert component.status() == QQmlComponent.Status.Ready, [
            error.toString() for error in component.errors()
        ]
        root = component.create(engine.rootContext())
        assert root is not None, [error.toString() for error in component.errors()]
        _pump(50)
        return engine, component, root, warnings
    except Exception:
        engine.deleteLater()
        raise


def test_ticket_scope_changes_real_surfaces_without_touching_global_skin(qapp):
    engine, component, root, warnings = _create_scene(qapp)
    try:
        for property_name in (
            "outsideUsesGlobal",
            "ticketCardUsesScope",
            "ticketButtonUsesScope",
            "ticketPaperUsesScope",
            "frameUsesScope",
            "frameChildUsesScope",
            "popupUsesScope",
            "popupMenuUsesScope",
            "dialogUsesScope",
            "dialogBodyButtonUsesScope",
            "dialogWasReparented",
            "ticketPaperVisible",
        ):
            assert root.property(property_name) is True, property_name

        assert root.property("globalCardRadius") > 0
        assert root.property("ticketCardRadius") == 0
        assert root.property("ticketButtonRadius") == 0
        assert root.property("ticketFrameRadius") == 0
        assert root.property("ticketPopupRadius") == 0
        assert root.property("ticketDialogRadius") == 0
        assert root.property("ticketCardColor") == root.property("expectedTicketCardColor")
        assert root.property("ticketPopupColor") == root.property("expectedTicketPopupColor")
        assert root.property("ticketDialogColor") == root.property("expectedTicketDialogColor")
        assert root.property("ticketCardColor") != root.property("globalCardColor")
        assert root.property("ticketCardColor") == QColor("#F8F3E8")
        popup_surface = root.findChild(QObject, "_popupSurface")
        assert popup_surface is not None
        scope = root.findChild(QObject, "ticketScope")
        assert scope is not None
        assert popup_surface.property("_skin") is scope.property("context")
        assert getSkin() == Skin.FLUENT
        assert warnings == []
    finally:
        root.close()
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        _pump()


def test_existing_scope_surfaces_follow_local_skin_and_global_theme_changes(qapp):
    engine, component, root, warnings = _create_scene(qapp)
    try:
        scope = root.findChild(QObject, "ticketScope")
        assert scope is not None

        assert scope.setProperty("skin", "fluent")
        _pump(300)
        assert root.property("ticketCardRadius") == root.property("globalCardRadius")
        assert root.property("ticketButtonRadius") > 0
        assert root.property("ticketFrameRadius") > 0
        assert root.property("ticketPopupRadius") > 0
        assert root.property("ticketDialogRadius") > 0
        assert root.property("ticketPaperVisible") is False
        assert root.property("ticketScopeSkin") == "fluent"
        assert root.property("ticketScopeDark") is False
        assert root.property("ticketScopeControlBackground") == root.property(
            "globalControlBackground"
        )
        assert root.property("ticketCardColor") == root.property("globalCardColor")

        assert scope.setProperty("skin", "vintage_ticket")
        setTheme(Theme.DARK)
        _pump(300)
        assert root.property("ticketCardRadius") == 0
        assert root.property("ticketButtonRadius") == 0
        assert root.property("ticketFrameRadius") == 0
        assert root.property("ticketPopupRadius") == 0
        assert root.property("ticketDialogRadius") == 0
        assert root.property("ticketPaperVisible") is True
        assert root.property("ticketCardColor") == QColor("#28231e")
        assert root.property("ticketDialogColor") == QColor("#28231e")
        assert warnings == []
    finally:
        root.close()
        root.deleteLater()
        component.deleteLater()
        engine.collectGarbage()
        engine.clearComponentCache()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        _pump()
