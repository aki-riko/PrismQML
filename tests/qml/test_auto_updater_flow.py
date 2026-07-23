# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""AutoUpdater orchestration regressions. AutoUpdater 编排回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "auto-updater-flow.qml"))
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Window {
    id: scene

    property int errorCount: 0
    property string lastError: ""
    readonly property string facadeRepository: facade.repository
    readonly property string facadeVersion: facade.currentVersion

    function triggerDoubleCheck() {
        facade.check();
        facade.check();
    }

    function finishCheck() {
        backend.checkFailed("check failed");
    }

    function triggerInstallerFailure() {
        facade._downloading = true;
        backend.downloadFinished("missing-installer.exe");
    }

    function triggerReleaseFallback() {
        facade._pendingVersion = "v2.0.0";
        facade._pendingUrl = "";
        facade._pendingHtmlUrl = "https://example.test/releases/v2.0.0";
        facade.startDownload();
    }

    width: 320
    height: 240
    visible: false

    QtObject {
        id: backend

        property string repository: "owner/repo"
        property string currentVersion: "v1.0.0"
        property int checkCalls: 0
        property int downloadCalls: 0
        property int installCalls: 0
        property int browserCalls: 0

        objectName: "backend"

        signal updateAvailable(string version, string notes, string downloadUrl, string htmlUrl)
        signal upToDate(string version)
        signal checkFailed(string error)
        signal downloadProgress(int received, int total)
        signal downloadFinished(string filePath)
        signal downloadFailed(string error)

        function checkForUpdate() { checkCalls += 1; }
        function downloadUpdate(url) { downloadCalls += 1; }
        function runInstallerAndQuit(path, args) { installCalls += 1; return false; }
        function openInBrowser(url) { browserCalls += 1; return true; }
    }

    AutoUpdater {
        id: facade
        updater: backend

        onErrorOccurred: function(message) {
            scene.errorCount += 1;
            scene.lastError = message;
        }
    }
}
"""


@pytest.fixture
def auto_updater_scene(qapp):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    try:
        yield root
    finally:
        root.deleteLater()
        del component
        engine.deleteLater()


def _backend(root):
    backend = root.findChild(QObject, "backend")
    assert backend is not None
    return backend


def test_backend_metadata_is_bound_by_default(auto_updater_scene):
    root = auto_updater_scene

    assert root.property("facadeRepository") == "owner/repo"
    assert root.property("facadeVersion") == "v1.0.0"


def test_check_is_single_flight_until_terminal_signal(auto_updater_scene):
    root = auto_updater_scene
    backend = _backend(root)

    assert QMetaObject.invokeMethod(root, "triggerDoubleCheck")
    assert backend.property("checkCalls") == 1
    assert QMetaObject.invokeMethod(root, "finishCheck")
    assert QMetaObject.invokeMethod(root, "triggerDoubleCheck")
    assert backend.property("checkCalls") == 2


def test_installer_launch_failure_is_reported_and_retryable(auto_updater_scene):
    root = auto_updater_scene
    backend = _backend(root)

    assert QMetaObject.invokeMethod(root, "triggerInstallerFailure")

    assert backend.property("installCalls") == 1
    assert root.property("errorCount") == 1
    assert "安装程序" in root.property("lastError")


def test_manual_no_asset_path_opens_release_page(auto_updater_scene):
    root = auto_updater_scene
    backend = _backend(root)

    assert QMetaObject.invokeMethod(root, "triggerReleaseFallback")

    assert backend.property("browserCalls") == 1
    assert backend.property("downloadCalls") == 0
