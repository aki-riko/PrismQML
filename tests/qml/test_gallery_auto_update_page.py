# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Gallery AutoUpdater page runtime contracts. Gallery 自动更新页运行时合同。"""

from pathlib import Path

from PySide6.QtCore import Property, QMetaObject, QObject, Signal, Slot, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

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


def test_gallery_auto_update_page_is_safe_without_python_backend(qapp):
    engine, component, root = _load_page(qapp)
    try:
        assert root.property("updaterBackend") is None
        assert root.property("statusText") == "Gallery 未注入 appUpdater"
        button = root.findChild(QObject, "galleryAutoUpdateCheckButton")
        assert button is not None
        assert button.property("enabled") is False
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        qapp.processEvents()


def test_gallery_auto_update_page_binds_backend_metadata(qapp):
    backend = _GalleryUpdater()
    engine, component, root = _load_page(qapp, backend)
    try:
        assert root.property("updaterBackend") is backend
        assert root.property("statusText") == "尚未检查"
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
