// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import PrismQML

// GalleryDryRunUpdater - Gallery-only updater simulator Gallery 专用更新模拟器
// Implements the public Updater contract without network, files, processes, or quit.
// 实现公开 Updater 契约，但不访问网络、不创建文件、不启动进程，也不退出应用。
QtObject {
    id: root

    // ==================== Public Props 公开属性 ====================
    property string currentVersion: "Gallery"
    property int checkDelay: Enums.duration.slower
    property int progressInterval: Enums.duration.medium
    property int progressStep: 10

    // ==================== Readonly State 只读状态 ====================
    readonly property string repository: "Gallery DRY"
    readonly property string installStrategy: "dual_slot"
    readonly property string simulatedVersion: "DRY Next"
    readonly property string downloadToken: "gallery-dry-download"
    readonly property string installerPath: "PrismQML-Gallery-Setup-DryRun.exe"
    readonly property string installerSilentArgs:
        "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-"
    readonly property string releaseNotes:
        Fluent.Translator.tr("gallery_fdd95a07de7bba4c", Fluent.Translator._v)
        + Fluent.Translator.tr("gallery_5274664fbfa7dd5b", Fluent.Translator._v)
        + Fluent.Translator.tr("gallery_13321e8fb49bf67f", Fluent.Translator._v)
        + Fluent.Translator.tr("gallery_138d19b516ca852a", Fluent.Translator._v)
    readonly property int totalProgress: 100
    readonly property int bytesPerMebibyte: 1024 * 1024
    readonly property int totalDownloadBytes: totalProgress * bytesPerMebibyte
    readonly property int minimumProgressStep: 1
    readonly property int progress: root._progress
    readonly property int checkSimulationCount: root._checkSimulationCount
    readonly property int downloadSimulationCount: root._downloadSimulationCount
    readonly property int installSimulationCount: root._installSimulationCount
    readonly property string lastInstallerArgs: root._lastInstallerArgs

    // ==================== Internal Props 内部属性 ====================
    property int _progress: 0
    property int _checkSimulationCount: 0
    property int _downloadSimulationCount: 0
    property int _installSimulationCount: 0
    property string _lastInstallerArgs: ""
    property Timer _prepareTimer: Timer {
        interval: Enums.duration.slower
        repeat: false

        onTriggered: {
            root.stageChanged(Fluent.Translator.tr("gallery_a9e0091fbab4d524", Fluent.Translator._v))
            root.installPreparationFinished()
        }
    }
    property Timer _checkTimer: Timer {
        interval: Math.max(Enums.duration.tick, root.checkDelay)
        repeat: false

        onTriggered: {
            root.stageChanged(Fluent.Translator.tr("gallery_b5e0ef52a7a37b1d", Fluent.Translator._v))
            root.updateAvailable(
                root.simulatedVersion,
                root.releaseNotes,
                root.downloadToken,
                ""
            )
        }
    }
    property Timer _downloadTimer: Timer {
        interval: Math.max(Enums.duration.tick, root.progressInterval)
        repeat: true

        onTriggered: {
            root._progress = Math.min(
                root.totalProgress,
                root._progress + Math.max(root.minimumProgressStep, root.progressStep)
            )
            var receivedBytes = Math.round(
                root.totalDownloadBytes * root._progress / root.totalProgress
            )
            root.downloadProgress(receivedBytes, root.totalDownloadBytes)
            root.stageChanged(Fluent.Translator.tr("gallery_127f9ed8b1424cd5") + root._progress + "%")
            if (root._progress >= root.totalProgress) {
                stop()
                root.stageChanged(Fluent.Translator.tr("gallery_2f5728cf56fedde6", Fluent.Translator._v))
                root.downloadFinished(root.installerPath)
            }
        }
    }

    // ==================== Signals 信号 ====================
    signal updateAvailable(
        string version,
        string notes,
        string downloadUrl,
        string htmlUrl
    )
    signal upToDate(string version)
    signal checkFailed(string error)
    signal downloadProgress(int received, int total)
    signal downloadFinished(string filePath)
    signal downloadFailed(string error)
    signal installPreparationFinished()
    signal installPreparationFailed(string error)
    signal stageChanged(string message)
    signal installSimulated(string installerPath)

    // ==================== Public Methods 公开方法 ====================
    function checkForUpdate() {
        if (root._checkTimer.running || root._downloadTimer.running) {
            root.checkFailed(Fluent.Translator.tr("gallery_df9f58a00cbd3fba", Fluent.Translator._v))
            return
        }
        root._checkSimulationCount += 1
        root._progress = 0
        root.stageChanged(Fluent.Translator.tr("gallery_099a3aa23c93d0a0", Fluent.Translator._v))
        root._checkTimer.restart()
    }

    function downloadUpdate(token) {
        if (token !== root.downloadToken) {
            root.downloadFailed(Fluent.Translator.tr("gallery_95e7b76fc84f3c1b", Fluent.Translator._v))
            return
        }
        if (root._downloadTimer.running) {
            root.downloadFailed(Fluent.Translator.tr("gallery_55f00b29001662c4", Fluent.Translator._v))
            return
        }
        root._downloadSimulationCount += 1
        root._progress = 0
        root.stageChanged(Fluent.Translator.tr("gallery_92632cc23944f0d8", Fluent.Translator._v))
        root._downloadTimer.restart()
    }

    function runInstallerAndQuit(path, args) {
        root._lastInstallerArgs = args
        if (path !== root.installerPath) {
            root.stageChanged(Fluent.Translator.tr("gallery_a611629f3acb875b", Fluent.Translator._v))
            return false
        }
        root._installSimulationCount += 1
        root.stageChanged(Fluent.Translator.tr("gallery_05707114351490dc", Fluent.Translator._v))
        root.installSimulated(path)
        return true
    }

    function stageInstallerForNextLaunch(path, args) {
        root._lastInstallerArgs = args
        if (path !== root.installerPath) {
            root.stageChanged(Fluent.Translator.tr("gallery_a6d25e4657be00d5", Fluent.Translator._v))
            root.installPreparationFailed(Fluent.Translator.tr("gallery_010faedd6f1eae59", Fluent.Translator._v))
            return false
        }
        root._installSimulationCount += 1
        root.stageChanged(Fluent.Translator.tr("gallery_b53ff9606b8b1f8c", Fluent.Translator._v))
        root._prepareTimer.restart()
        return true
    }

    function openInBrowser(url) {
        root.stageChanged(Fluent.Translator.tr("gallery_26448145cd75932b", Fluent.Translator._v))
        return true
    }
}
