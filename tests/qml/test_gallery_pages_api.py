# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Gallery page API smoke coverage. Gallery 页面 API 全量冒烟覆盖。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow

from examples.resources import register_gallery_resources
from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
GALLERY_PAGES = tuple(sorted((ROOT / "examples" / "pages").glob("*.qml")))


def _pump(milliseconds: int = 50) -> None:
    loop = QEventLoop()
    QTimer.singleShot(milliseconds, loop.quit)
    loop.exec()


def _dispose_object(obj) -> None:
    if obj is None:
        return
    obj.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QCoreApplication.processEvents()


def _create_page(engine, host, page_path):
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(page_path)))
    if component.isLoading():
        _pump()
    errors = [error.toString() for error in component.errors()]
    page = (
        component.create(engine.rootContext())
        if component.status() == QQmlComponent.Status.Ready
        else None
    )
    if isinstance(page, QQuickItem):
        page.setParentItem(host.contentItem())
        page.setWidth(1000)
        page.setHeight(760)
    _pump(150)
    return component, page, errors


def _failure_message(page_path, page, errors, warnings):
    if not errors and page is not None and not warnings:
        return None
    return f"{page_path.name}: errors={errors}, warnings={warnings}"


def _create_engine():
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    warnings: list[str] = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    return engine, warnings


def _collect_page_failures(engine, host, warnings):
    failures: list[str] = []
    for page_path in GALLERY_PAGES:
        warning_start = len(warnings)
        component, page, errors = _create_page(engine, host, page_path)
        failure = _failure_message(
            page_path, page, errors, warnings[warning_start:]
        )
        if failure:
            failures.append(failure)
        _dispose_object(page)
        _dispose_object(component)
    return failures


def test_all_gallery_pages_create_with_current_runtime_api(qapp):
    """Every Gallery page must create without QML API warnings.

    每个 Gallery 页面都必须在当前运行时 API 下无警告创建。
    """
    assert GALLERY_PAGES
    register_gallery_resources()
    engine, warnings = _create_engine()
    windows_before = tuple(QGuiApplication.topLevelWindows())
    host = QQuickWindow()

    try:
        failures = _collect_page_failures(engine, host, warnings)
        assert not failures, "\n".join(failures)
        assert warnings == []
    finally:
        _dispose_object(host)
        engine.collectGarbage()
        engine.clearComponentCache()
        _dispose_object(engine)
        assert tuple(QGuiApplication.topLevelWindows()) == windows_before
