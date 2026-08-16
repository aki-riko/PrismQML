// AutoUpdaterSignalConnections - Updater signal orchestration 更新器信号编排
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import PrismQML

Connections {
    id: connections

    required property var host

    function onUpdateAvailable(version, notes, downloadUrl, htmlUrl) {
        if (!host._checking)
            return;
        // Finish checking and wait for the decision dialog. 结束检查并等待确认弹窗。
        host._checking = false;
        host._checkSilent = false;
        host._awaitingDecision = true;
        host._dismissFeedback();
        host._pendingVersion = version;
        host._pendingUrl = downloadUrl;
        host._pendingHtmlUrl = htmlUrl;
        var dialog = host._ensureUpdateDialog();
        if (!dialog) {
            host._awaitingDecision = false;
            console.error("AutoUpdater: Failed to create UpdateDialog.");
            return;
        }
        dialog.version = version;
        dialog.currentVersion = host.currentVersion;
        dialog.notes = notes;
        dialog.open();
    }

    function onUpToDate(version) {
        if (!host._checking)
            return;
        host._checking = false;
        var silent = host._checkSilent;
        host._checkSilent = false;
        if (silent || !host.notifyWhenUpToDate)
            host._dismissFeedback();
        if (!silent && host.notifyWhenUpToDate) {
            host._presentFeedback(
                Translator.tr("already_latest_version"), version, "success",
                Enums.notification.feature_normal,
                Enums.duration.notification, 0
            );
        }
        host.upToDateNotified(version);
    }

    function onCheckFailed(error) {
        if (!host._checking)
            return;
        host._checking = false;
        if (host._checkSilent) {
            host._checkSilent = false;
            host._dismissFeedback();
            host.errorOccurred(error);
            return;
        }
        host._showError(Translator.tr("check_updates_failed"), error);
    }

    function onDownloadProgress(received, total) {
        if (!host._downloading)
            return;
        if (total > 0 && !host._rangeKnown) {
            host._rangeKnown = true;
            host._feedbackFeature = Enums.notification.feature_progress_ring;
        }
        if (host._rangeKnown) {
            var progress = Math.max(0, Math.min(1, received / total));
            host._feedbackProgress = progress;
            host._feedbackMessage = Math.round(progress * 100) + "%  ("
                + host._formatSize(received) + " / " + host._formatSize(total) + ")";
        } else {
            host._feedbackMessage = host._formatSize(received)
                + Translator.tr("downloaded_suffix");
        }
    }

    function onDownloadFinished(filePath) {
        if (!host._downloading)
            return;
        host._downloading = false;
        if (host.usesDualSlot) {
            if (!host.updater.stageInstallerForNextLaunch(filePath, host.silentArgs)) {
                host._showError(Translator.tr("background_install_start_failed"),
                                Translator.tr("cannot_prepare_next_version"));
                return;
            }
            host._installPreparing = true;
            host._presentFeedback(
                Translator.tr("preparing_update_in_background"),
                Translator.tr("current_version_remains_available"),
                "info", Enums.notification.feature_indeterminate_ring,
                Enums.duration.none, 0
            );
            return;
        }
        if (!host.updater.runInstallerAndQuit(filePath, host.silentArgs)) {
            host._showError(Translator.tr("install_start_failed"),
                            Translator.tr("cannot_start_installer"));
            return;
        }
        host._presentFeedback(
            Translator.tr("installer_started"),
            Translator.tr("install_completes_in_background"),
            "success", Enums.notification.feature_normal,
            Enums.duration.notification, 0
        );
    }

    function onDownloadFailed(error) {
        if (!host._downloading)
            return;
        host._downloading = false;
        host._showError(Translator.tr("download_failed"), error);
    }

    function onInstallPreparationFinished() {
        if (!host._installPreparing)
            return;
        host._installPreparing = false;
        host._presentFeedback(
            Translator.tr("new_version_ready"),
            Translator.tr("switch_on_next_start"),
            "success", Enums.notification.feature_normal,
            Enums.duration.progressComplete, 0
        );
        var version = host._pendingVersion;
        host._clearPending();
        host.updatePreparedForNextLaunch(version);
    }

    function onInstallPreparationFailed(error) {
        if (!host._installPreparing)
            return;
        host._installPreparing = false;
        host._showError(Translator.tr("background_install_failed"), error);
    }

    target: host.updater
    ignoreUnknownSignals: true
}
