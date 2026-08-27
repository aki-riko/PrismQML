# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""AutoUpdater orchestration regressions. AutoUpdater 编排回归。"""

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QMetaObject,
    QObject,
    QPointF,
    Qt,
    QtMsgType,
    QUrl,
    qInstallMessageHandler,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtTest import QSignalSpy, QTest

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
REAL_UPDATE_ERROR = (
    "Error transferring https://api.github.com/repos/aki-riko/MCNeteaseToolPE/"
    "releases/latest - server replied with status code 404"
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Window {
    id: scene

    property int errorCount: 0
    property string lastError: ""
    readonly property string facadeRepository: facade.repository
    readonly property string facadeVersion: facade.currentVersion
    readonly property bool facadeUsesDualSlot: facade.usesDualSlot
    readonly property bool facadePreparing: facade.feedbackModel.preparing
    readonly property bool facadeFeedbackActive: facade.feedbackModel.active
    readonly property string facadeFeedbackTitle: facade.feedbackModel.title
    readonly property string facadeFeedbackMessage: facade.feedbackModel.message
    readonly property string facadeFeedbackIcon: facade.feedbackModel.icon
    readonly property int indeterminateRingFeature: Enums.notification.feature_indeterminate_ring
    readonly property int progressRingFeature: Enums.notification.feature_progress_ring
    readonly property int toastWidth: Enums.controlSize.toastWidth
    readonly property int toastHeight: Enums.controlSize.toastHeight
    readonly property int toastHideDuration: Enums.notification.animation.hideDuration
    readonly property int progressCompleteDuration: Enums.duration.progressComplete
    readonly property int spacingM: Enums.spacing.m
    readonly property int spacingL: Enums.spacing.l
    readonly property int mebibyte: 1024 * 1024
    readonly property string installerSilentArgs:
        "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-"

    function triggerDoubleCheck() {
        facade.check();
        facade.check();
    }

    function finishCheck() {
        backend.checkFailed("check failed");
    }

    function triggerSilentCheck() {
        facade.checkSilently();
    }

    function finishSilentUpdate() {
        backend.updateAvailable(
            "v2.0.0", "silent check update", "download-token", ""
        );
    }

    function emitDownloadProgress() {
        facade._checking = false;
        facade._downloading = true;
        backend.downloadProgress(25 * scene.mebibyte, 100 * scene.mebibyte);
    }

    function emitSecondDownloadProgress() {
        backend.downloadProgress(50 * scene.mebibyte, 100 * scene.mebibyte);
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

    function disableFeedbackPresenter() {
        facade.feedbackPresenter = null;
    }

    function triggerInstallerFailure() {
        facade._downloading = true;
        backend.downloadFinished("missing-installer.exe");
    }

    function triggerDualSlotPreparation() {
        backend.installStrategy = "dual_slot";
        facade._pendingVersion = "v2.0.0";
        facade._downloading = true;
        backend.downloadFinished("dummy-installer.exe");
    }

    function finishDualSlotPreparation() {
        backend.installPreparationFinished();
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
    Component.onCompleted: Translator.setLanguage(Enums.lang.zh_CN)

    QtObject {
        id: backend

        property string repository: "owner/repo"
        property string currentVersion: "v1.0.0"
        property string installStrategy: "in_place"
        property int checkCalls: 0
        property int downloadCalls: 0
        property int installCalls: 0
        property int stageCalls: 0
        property int browserCalls: 0
        property string lastInstallerArgs: ""

        objectName: "backend"

        signal updateAvailable(string version, string notes, string downloadUrl, string htmlUrl)
        signal upToDate(string version)
        signal checkFailed(string error)
        signal downloadProgress(int received, int total)
        signal downloadFinished(string filePath)
        signal downloadFailed(string error)
        signal installPreparationFinished()
        signal installPreparationFailed(string error)

        function checkForUpdate() { checkCalls += 1; }
        function downloadUpdate(url) { downloadCalls += 1; }
        function runInstallerAndQuit(path, args) {
            installCalls += 1;
            lastInstallerArgs = args;
            return false;
        }
        function stageInstallerForNextLaunch(path, args) {
            stageCalls += 1;
            lastInstallerArgs = args;
            return true;
        }
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
        silentArgs: scene.installerSilentArgs

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


def _visible_text_item(toast, text):
    matches = [
        item
        for item in toast.findChildren(QObject)
        if isinstance(item, QQuickItem)
        and item.property("text") == text
        and item.property("visible")
    ]
    assert len(matches) == 1
    return matches[0]


def test_backend_metadata_is_bound_by_default(auto_updater_scene):
    root = auto_updater_scene

    assert root.property("facadeRepository") == "owner/repo"
    assert root.property("facadeVersion") == "v1.0.0"
    assert not any(
        "UpdateDialog" in obj.metaObject().className()
        for obj in root.findChildren(QObject)
    )


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
    sync_timer = root.findChild(QObject, "autoUpdaterToastSyncTimer")
    assert sync_timer is not None
    toast = root.findChild(QObject, "autoUpdaterToast")
    assert toast is not None
    assert toast.metaObject().className().startswith("Toast_QMLTYPE_")
    assert toast.property("feature") == root.property("indeterminateRingFeature")
    assert toast.property("width") == root.property("toastWidth")
    assert toast.property("height") == root.property("toastHeight")
    assert set(QGuiApplication.topLevelWindows()) == windows_before
    state_icon = toast.findChild(QObject, "toastProgressStateIcon")
    assert state_icon is not None
    assert state_icon.property("icon") == "ArrowSync"
    assert state_icon.property("visible") is True

    assert QMetaObject.invokeMethod(root, "emitDownloadProgress")
    qapp.processEvents()
    assert toast.property("feature") == root.property("progressRingFeature")
    assert toast.property("progress") == pytest.approx(0.25)
    assert toast.property("message") == "25%  (25.0 MB / 100.0 MB)"
    assert state_icon.property("icon") == "ArrowDownload"
    assert state_icon.property("visible") is True

    assert QMetaObject.invokeMethod(root, "emitSecondDownloadProgress")
    assert sync_timer.property("running") is True
    qapp.processEvents()
    assert sync_timer.property("running") is False
    assert root.findChild(QObject, "autoUpdaterToast") is toast
    assert toast.property("progress") == pytest.approx(0.5)
    assert toast.property("message") == "50%  (50.0 MB / 100.0 MB)"


def test_silent_check_has_no_toast_but_still_reports_failure(
    auto_updater_scene, qapp
):
    root = auto_updater_scene
    backend = _backend(root)

    assert QMetaObject.invokeMethod(root, "triggerSilentCheck")
    qapp.processEvents()
    assert backend.property("checkCalls") == 1
    assert root.findChild(QObject, "autoUpdaterToast") is None

    backend.checkFailed.emit("silent check failed")
    qapp.processEvents()
    assert root.property("errorCount") == 1
    assert root.property("lastError") == "silent check failed"
    assert root.findChild(QObject, "autoUpdaterToast") is None

    assert QMetaObject.invokeMethod(root, "triggerSilentCheck")
    backend.upToDate.emit("v1.0.0")
    qapp.processEvents()
    assert root.findChild(QObject, "autoUpdaterToast") is None


def test_silent_check_still_opens_update_confirmation(auto_updater_scene, qapp):
    root = auto_updater_scene

    assert QMetaObject.invokeMethod(root, "triggerSilentCheck")
    assert QMetaObject.invokeMethod(root, "finishSilentUpdate")
    qapp.processEvents()

    dialogs = [
        obj
        for obj in root.findChildren(QObject)
        if "UpdateDialog" in obj.metaObject().className()
    ]
    assert len(dialogs) == 1
    assert dialogs[0].property("isOpen") is True
    assert root.findChild(QObject, "autoUpdaterToast") is None


def test_reused_check_toast_reflows_for_real_multiline_error(auto_updater_scene, qapp):
    root = auto_updater_scene
    backend = _backend(root)

    assert QMetaObject.invokeMethod(root, "triggerDoubleCheck")
    toast = root.findChild(QQuickItem, "autoUpdaterToast")
    assert toast is not None
    assert toast.property("orient") == Qt.Orientation.Horizontal.value

    backend.checkFailed.emit(REAL_UPDATE_ERROR)
    qapp.processEvents()
    body = _visible_text_item(toast, REAL_UPDATE_ERROR)
    body_bottom = body.mapToItem(toast, QPointF(0, body.height())).y()

    assert toast.property("orient") == Qt.Orientation.Vertical.value
    assert body.property("lineCount") > 1
    assert toast.height() > root.property("toastHeight")
    assert toast.height() - body_bottom == pytest.approx(
        root.property("spacingM") + root.property("spacingL")
    )


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
    state_icon = root.findChild(QObject, "progressDialogCompletionIcon")
    assert state_icon is not None
    assert state_icon.property("icon") == "ArrowSync"
    assert state_icon.property("visible") is True

    assert QMetaObject.invokeMethod(root, "emitDownloadProgress")
    qapp.processEvents()
    assert dialog.property("progress") == pytest.approx(25)
    assert state_icon.property("icon") == "ArrowDownload"
    assert state_icon.property("visible") is True


def test_progress_dialog_timeout_timer_lifecycle(auto_updater_scene, qapp):
    root = auto_updater_scene
    assert QMetaObject.invokeMethod(root, "useProgressDialogAndCheck")
    qapp.processEvents()

    dialog = root.findChild(QObject, "autoUpdaterProgressDialog")
    assert dialog is not None
    timeout_timer = dialog.findChild(QObject, "progressDialogTimeoutTimer")
    assert timeout_timer is not None
    assert timeout_timer.parent() is dialog
    assert timeout_timer.property("host") == dialog
    assert timeout_timer.property("running") is False

    timeout_spy = QSignalSpy(dialog.timeout)
    assert dialog.setProperty("maxWaitingTime", 20)
    qapp.processEvents()
    assert timeout_timer.property("interval") == 20
    assert timeout_timer.property("running") is True

    assert timeout_spy.wait(2000)
    assert dialog.property("_isOpen") is False
    assert timeout_timer.property("running") is False


def test_progress_dialog_replaces_state_icon_with_ready_icon(auto_updater_scene, qapp):
    root = auto_updater_scene
    assert QMetaObject.invokeMethod(root, "useProgressDialogAndCheck")
    completion_icon = root.findChild(QObject, "progressDialogCompletionIcon")
    assert completion_icon is not None
    assert completion_icon.property("icon") == "ArrowSync"
    assert completion_icon.property("visible") is True
    assert QMetaObject.invokeMethod(root, "triggerDualSlotPreparation")
    assert QMetaObject.invokeMethod(root, "finishDualSlotPreparation")
    qapp.processEvents()
    dialog = root.findChild(QObject, "autoUpdaterProgressDialog")
    assert dialog.property("title") == "新版已准备完成"
    assert dialog.property("progress") == pytest.approx(100)
    assert completion_icon.property("icon") == "Checkmark"
    assert completion_icon.property("visible") is True


def test_progress_dialog_ready_state_uses_completion_timeout(auto_updater_scene):
    root = auto_updater_scene
    feedback_timer = root.findChild(QObject, "autoUpdaterFeedbackTimer")
    assert feedback_timer is not None
    assert feedback_timer.property("running") is False

    assert QMetaObject.invokeMethod(root, "useProgressDialogAndCheck")
    assert QMetaObject.invokeMethod(root, "triggerDualSlotPreparation")
    assert QMetaObject.invokeMethod(root, "finishDualSlotPreparation")

    dialog = root.findChild(QObject, "autoUpdaterProgressDialog")
    assert dialog is not None
    assert root.property("facadeFeedbackActive") is True
    assert dialog.property("_isOpen") is True
    assert feedback_timer.property("interval") == root.property(
        "progressCompleteDuration"
    )
    assert feedback_timer.property("running") is True

    QTest.qWait(int(root.property("progressCompleteDuration")) + 50)

    assert root.property("facadeFeedbackActive") is False
    assert dialog.property("_isOpen") is False
    assert feedback_timer.property("running") is False


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


def test_destroyed_toast_presenter_does_not_read_dead_root(auto_updater_scene):
    root = auto_updater_scene
    assert QMetaObject.invokeMethod(root, "triggerDoubleCheck")
    assert root.findChild(QObject, "autoUpdaterToast") is not None

    messages = []
    previous_handler = qInstallMessageHandler(
        lambda mode, _context, message: messages.append((mode, str(message)))
    )
    try:
        assert QMetaObject.invokeMethod(root, "disableFeedbackPresenter")
        QTest.qWait(int(root.property("toastHideDuration")) + 50)
    finally:
        qInstallMessageHandler(previous_handler)

    failures = [
        message
        for mode, message in messages
        if mode == QtMsgType.QtWarningMsg
        and "AutoUpdaterToastPresenter.qml" in message
        and "Cannot read property '_toast' of null" in message
    ]
    assert failures == []


def test_auto_updater_delegates_feedback_without_desktop_notification():
    facade_source = AUTO_UPDATER_SOURCE.read_text(encoding="utf-8")
    toast_source = TOAST_PRESENTER_SOURCE.read_text(encoding="utf-8")
    dialog_source = PROGRESS_DIALOG_PRESENTER_SOURCE.read_text(encoding="utf-8")
    qmldir_source = ROOT_QMLDIR.read_text(encoding="utf-8")

    assert "property Component feedbackPresenter" in facade_source
    assert "readonly property QtObject feedbackModel" in facade_source
    assert "NotificationManager.toast.info(" not in facade_source
    assert "NotificationManager.toast.info(" in toast_source
    assert "item.show();" not in toast_source
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
    assert backend.property("lastInstallerArgs") == root.property(
        "installerSilentArgs"
    )
    assert root.property("errorCount") == 1
    assert "安装程序" in root.property("lastError")


def test_dual_slot_preparation_keeps_feedback_until_next_launch_ready(
    auto_updater_scene, qapp
):
    root = auto_updater_scene
    backend = _backend(root)

    assert QMetaObject.invokeMethod(root, "triggerDualSlotPreparation")
    qapp.processEvents()
    assert backend.property("stageCalls") == 1
    assert root.property("facadeUsesDualSlot") is True
    assert root.property("facadePreparing") is True
    assert root.property("facadeFeedbackMessage") == (
        "当前版本可继续使用,完成后下次启动自动切换"
    )

    assert QMetaObject.invokeMethod(root, "finishDualSlotPreparation")
    qapp.processEvents()
    assert root.property("facadePreparing") is False
    assert root.property("facadeFeedbackTitle") == "新版已准备完成"
    assert root.property("facadeFeedbackMessage") == (
        "当前版本继续运行,下次启动将自动切换"
    )


def test_manual_no_asset_path_opens_release_page(auto_updater_scene):
    root = auto_updater_scene
    backend = _backend(root)

    assert QMetaObject.invokeMethod(root, "triggerReleaseFallback")

    assert backend.property("browserCalls") == 1
    assert backend.property("downloadCalls") == 0
