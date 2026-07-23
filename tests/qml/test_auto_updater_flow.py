# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""AutoUpdater orchestration regressions. AutoUpdater 编排回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from prismqml import register_types


ROOT = Path(__file__).resolve().parents[2]
SCENE_URL = QUrl.fromLocalFile(str(ROOT / "tests" / "qml" / "auto-updater-flow.qml"))
AUTO_UPDATER_SOURCE = (
    ROOT / "prismqml" / "PrismQML" / "controls" / "feedback" / "AutoUpdater.qml"
)
TOAST_PRESENTER_SOURCE = AUTO_UPDATER_SOURCE.with_name("AutoUpdaterToastPresenter.qml")
PROGRESS_DIALOG_PRESENTER_SOURCE = AUTO_UPDATER_SOURCE.with_name(
    "AutoUpdaterProgressDialogPresenter.qml"
)
ROOT_QMLDIR = ROOT / "prismqml" / "PrismQML" / "qmldir"
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Window {
    id: scene

    property int errorCount: 0
    property string lastError: ""
    readonly property string facadeRepository: facade.repository
    readonly property string facadeVersion: facade.currentVersion
    readonly property int indeterminateRingFeature: Enums.notification.feature_indeterminate_ring
    readonly property int progressRingFeature: Enums.notification.feature_progress_ring
    readonly property int toastWidth: Enums.controlSize.toastWidth
    readonly property int toastHeight: Enums.controlSize.toastHeight

    function triggerDoubleCheck() {
        facade.check();
        facade.check();
    }

    function finishCheck() {
        backend.checkFailed("check failed");
    }

    function emitDownloadProgress() {
        facade._checking = false;
        facade._downloading = true;
        backend.downloadProgress(25, 100);
    }

    function useProgressDialogAndCheck() {
        facade.feedbackModel.dismiss();
        facade.feedbackPresenter = progressDialogPresenter;
        facade.check();
    }

    function useCustomPresenterAndCheck() {
        facade.feedbackModel.dismiss();
        facade.feedbackPresenter = customPresenter;
        facade.check();
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

    Component {
        id: progressDialogPresenter

        AutoUpdaterProgressDialogPresenter {}
    }

    Component {
        id: customPresenter

        QtObject {
            property var feedbackModel: null
            property Item presenterHost: null
            readonly property bool active: feedbackModel ? feedbackModel.active : false
            readonly property bool checking: feedbackModel ? feedbackModel.checking : false
            readonly property string title: feedbackModel ? feedbackModel.title : ""
            readonly property real progress: feedbackModel ? feedbackModel.progress : 0

            objectName: "customAutoUpdaterPresenter"
        }
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


def test_check_uses_managed_toast_and_builtin_progress(auto_updater_scene, qapp):
    root = auto_updater_scene
    windows_before = set(QGuiApplication.topLevelWindows())

    assert QMetaObject.invokeMethod(root, "triggerDoubleCheck")
    toast = root.findChild(QObject, "autoUpdaterToast")
    assert toast is not None
    assert toast.metaObject().className().startswith("Toast_QMLTYPE_")
    assert toast.property("feature") == root.property("indeterminateRingFeature")
    assert toast.property("width") == root.property("toastWidth")
    assert toast.property("height") == root.property("toastHeight")
    assert set(QGuiApplication.topLevelWindows()) == windows_before

    assert QMetaObject.invokeMethod(root, "emitDownloadProgress")
    qapp.processEvents()
    assert toast.property("feature") == root.property("progressRingFeature")
    assert toast.property("progress") == pytest.approx(0.25)


def test_progress_dialog_presenter_can_replace_default(auto_updater_scene, qapp):
    root = auto_updater_scene

    assert QMetaObject.invokeMethod(root, "useProgressDialogAndCheck")
    qapp.processEvents()
    dialog = root.findChild(QObject, "autoUpdaterProgressDialog")
    assert dialog is not None
    assert dialog.metaObject().className().startswith("ProgressDialog_QMLTYPE_")
    assert dialog.property("_isOpen") is True
    assert dialog.property("title") == "正在检查更新"
    assert dialog.property("progress") == pytest.approx(-1)
    assert root.findChild(QObject, "autoUpdaterToast") is None

    assert QMetaObject.invokeMethod(root, "emitDownloadProgress")
    qapp.processEvents()
    assert dialog.property("progress") == pytest.approx(25)


def test_developer_component_receives_shared_feedback_model(auto_updater_scene, qapp):
    root = auto_updater_scene

    assert QMetaObject.invokeMethod(root, "useCustomPresenterAndCheck")
    presenter = root.findChild(QObject, "customAutoUpdaterPresenter")
    assert presenter is not None
    assert presenter.property("active") is True
    assert presenter.property("checking") is True
    assert presenter.property("title") == "正在检查更新"

    assert QMetaObject.invokeMethod(root, "emitDownloadProgress")
    qapp.processEvents()
    assert presenter.property("progress") == pytest.approx(0.25)


def test_auto_updater_delegates_feedback_without_desktop_notification():
    facade_source = AUTO_UPDATER_SOURCE.read_text(encoding="utf-8")
    toast_source = TOAST_PRESENTER_SOURCE.read_text(encoding="utf-8")
    dialog_source = PROGRESS_DIALOG_PRESENTER_SOURCE.read_text(encoding="utf-8")
    qmldir_source = ROOT_QMLDIR.read_text(encoding="utf-8")

    assert "property Component feedbackPresenter" in facade_source
    assert "readonly property QtObject feedbackModel" in facade_source
    assert "NotificationManager.toast.info(" not in facade_source
    assert "NotificationManager.toast.info(" in toast_source
    assert "ProgressDialog {" in dialog_source
    assert "AutoUpdaterToastPresenter controls/feedback/AutoUpdaterToastPresenter.qml" in qmldir_source
    assert (
        "AutoUpdaterProgressDialogPresenter "
        "controls/feedback/AutoUpdaterProgressDialogPresenter.qml"
    ) in qmldir_source
    for source in (facade_source, toast_source, dialog_source):
        assert "DesktopNotification {" not in source
        assert "customContent: Component" not in source


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
