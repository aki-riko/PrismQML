# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Gallery AutoUpdater page runtime contracts. Gallery 自动更新页运行时合同。"""

import time
from pathlib import Path

from PySide6.QtCore import Property, QMetaObject, QObject, Signal, Slot, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
PAGE_URL = QUrl.fromLocalFile(str(ROOT / "examples" / "pages" / "AutoUpdatePage.qml"))


class _GalleryUpdater(QObject):
    updateAvailable = Signal(str, str, str, str)
    upToDate = Signal(str)
    checkFailed = Signal(str)
    downloadProgress = Signal(int, int)
    downloadFinished = Signal(str)
    downloadFailed = Signal(str)

    def __init__(self):
        super().__init__()
        self.check_calls = 0

    @Property(str, constant=True)
    def repository(self):
        return "owner/repo"

    @Property(str, constant=True)
    def currentVersion(self):
        return "v1.0.0"

    @Slot()
    def checkForUpdate(self):
        self.check_calls += 1

    @Slot(str)
    def downloadUpdate(self, _url):
        pass

    @Slot(str, str, result=bool)
    def runInstallerAndQuit(self, _path, _args):
        return False

    @Slot(str, result=bool)
    def openInBrowser(self, _url):
        return True


def _load_page(qapp, backend=None):
    engine = QQmlEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    if backend is not None:
        engine.rootContext().setContextProperty("appUpdater", backend)

    component = QQmlComponent(engine)
    component.loadUrl(PAGE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create()
    assert root is not None, [error.toString() for error in component.errors()]
    return engine, component, root


def _wait_until(qapp, predicate, timeout_ms=2_000):
    deadline = time.monotonic() + timeout_ms / 1_000
    while time.monotonic() < deadline:
        qapp.processEvents()
        if predicate():
            return
        time.sleep(0.005)
    raise AssertionError("等待 Gallery DRY 状态超时")


def _attach_page_to_window(root):
    assert isinstance(root, QQuickItem)
    window = QQuickWindow()
    window.setWidth(1_200)
    window.setHeight(800)
    root.setParentItem(window.contentItem())
    root.setWidth(window.width())
    root.setHeight(window.height())
    return window


def test_gallery_auto_update_page_is_safe_without_python_backend(qapp):
    engine, component, root = _load_page(qapp)
    try:
        assert root.property("updaterBackend") is None
        assert root.property("dryRunMode") is True
        assert root.property("statusText") == "DRY 模式：等待开始演示"
        button = root.findChild(QObject, "galleryAutoUpdateCheckButton")
        dry_run_backend = root.findChild(QObject, "galleryDryRunUpdater")
        assert button is not None
        assert dry_run_backend is not None
        assert button.property("enabled") is True
        assert button.property("text") == "开始 DRY 演示"
        assert dry_run_backend.property("repository") == "Gallery DRY"
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        qapp.processEvents()


def test_gallery_dry_run_shows_download_progress_and_simulates_install(qapp):
    engine, component, root = _load_page(qapp)
    window = _attach_page_to_window(root)
    try:
        facade = root.findChild(QObject, "galleryAutoUpdater")
        dry_run_backend = root.findChild(QObject, "galleryDryRunUpdater")
        assert facade is not None
        assert dry_run_backend is not None

        dry_run_backend.setProperty("checkDelay", 1)
        dry_run_backend.setProperty("progressInterval", 40)
        dry_run_backend.setProperty("progressStep", 25)

        assert QMetaObject.invokeMethod(facade, "check")
        _wait_until(qapp, lambda: facade.property("_awaitingDecision"))

        dialogs = [
            obj
            for obj in root.findChildren(QObject)
            if "UpdateDialog" in obj.metaObject().className()
        ]
        assert len(dialogs) == 1
        assert dialogs[0].property("isOpen") is True
        confirm_button = dialogs[0].findChild(QObject, "updateDialogConfirmButton")
        assert confirm_button is not None
        assert QMetaObject.invokeMethod(confirm_button, "clicked")

        _wait_until(qapp, lambda: dry_run_backend.property("progress") >= 25)
        feedback = facade.property("feedbackModel")
        assert feedback.property("message") == "25%  (25.0 MB / 100.0 MB)"

        _wait_until(
            qapp,
            lambda: dry_run_backend.property("installSimulationCount") == 1,
        )
        _wait_until(
            qapp,
            lambda: root.property("statusText")
            == "DRY：双槽已准备完成，下次启动自动切换",
        )
        assert dry_run_backend.property("checkSimulationCount") == 1
        assert dry_run_backend.property("downloadSimulationCount") == 1
        assert dry_run_backend.property("progress") == 100
        assert dry_run_backend.property("lastInstallerArgs") == (
            "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-"
        )
        assert dialogs[0].property("isOpen") is False
        assert feedback.property("title") == "新版已准备完成"
        assert root.property("statusText") == (
            "DRY：双槽已准备完成，下次启动自动切换"
        )
    finally:
        root.setParentItem(None)
        root.deleteLater()
        window.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        qapp.processEvents()


def test_gallery_auto_update_page_binds_backend_metadata(qapp):
    backend = _GalleryUpdater()
    engine, component, root = _load_page(qapp, backend)
    try:
        assert root.property("updaterBackend") is backend
        assert root.property("statusText") == "DRY 模式：等待开始演示"
        root.setProperty("dryRunMode", False)
        qapp.processEvents()
        assert root.property("statusText") == "真实模式：尚未检查"
        backend.upToDate.emit("v1.0.0")
        qapp.processEvents()
        assert root.property("latestVersion") == "v1.0.0"

        toggle = root.findChild(QObject, "galleryAutoUpdatePresenterToggle")
        facade = root.findChild(QObject, "galleryAutoUpdater")
        assert toggle is not None
        assert facade is not None
        assert toggle.property("checked") is False

        root.setProperty("useProgressDialog", True)
        qapp.processEvents()
        assert toggle.property("checked") is True
        assert QMetaObject.invokeMethod(facade, "check")
        qapp.processEvents()
        dialog = root.findChild(QObject, "autoUpdaterProgressDialog")
        assert dialog is not None
        assert dialog.property("_isOpen") is True
        assert backend.check_calls == 1
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        qapp.processEvents()
