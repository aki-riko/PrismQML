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
    readonly property string simulatedVersion: "DRY Next"
    readonly property string downloadToken: "gallery-dry-download"
    readonly property string installerPath: "PrismQML-Gallery-Setup-DryRun.exe"
    readonly property string releaseNotes:
        "## DRY 演示更新\n\n"
        + "- 展示真实更新确认对话框\n"
        + "- 模拟下载进度从 0% 到 100%\n"
        + "- 模拟安装交接，不创建文件或启动程序"
    readonly property int totalProgress: 100
    readonly property int minimumProgressStep: 1
    readonly property int progress: root._progress
    readonly property int checkSimulationCount: root._checkSimulationCount
    readonly property int downloadSimulationCount: root._downloadSimulationCount
    readonly property int installSimulationCount: root._installSimulationCount

    // ==================== Internal Props 内部属性 ====================
    property int _progress: 0
    property int _checkSimulationCount: 0
    property int _downloadSimulationCount: 0
    property int _installSimulationCount: 0
    property Timer _checkTimer: Timer {
        interval: Math.max(Enums.duration.tick, root.checkDelay)
        repeat: false

        onTriggered: {
            root.stageChanged("DRY：发现模拟版本，等待用户确认")
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
            root.downloadProgress(root._progress, root.totalProgress)
            root.stageChanged("DRY：模拟下载中 " + root._progress + "%")
            if (root._progress >= root.totalProgress) {
                stop()
                root.stageChanged("DRY：模拟下载完成，正在交接安装")
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
    signal stageChanged(string message)
    signal installSimulated(string installerPath)

    // ==================== Public Methods 公开方法 ====================
    function checkForUpdate() {
        if (root._checkTimer.running || root._downloadTimer.running) {
            root.checkFailed("DRY 演示正在进行")
            return
        }
        root._checkSimulationCount += 1
        root._progress = 0
        root.stageChanged("DRY：正在模拟检查更新…")
        root._checkTimer.restart()
    }

    function downloadUpdate(token) {
        if (token !== root.downloadToken) {
            root.downloadFailed("DRY 下载令牌无效")
            return
        }
        if (root._downloadTimer.running) {
            root.downloadFailed("DRY 模拟下载正在进行")
            return
        }
        root._downloadSimulationCount += 1
        root._progress = 0
        root.stageChanged("DRY：准备模拟下载")
        root._downloadTimer.restart()
    }

    function runInstallerAndQuit(path, args) {
        if (path !== root.installerPath) {
            root.stageChanged("DRY：安装交接失败")
            return false
        }
        root._installSimulationCount += 1
        root.stageChanged("DRY 演示完成：未下载文件，也未启动安装器")
        root.installSimulated(path)
        return true
    }

    function openInBrowser(url) {
        root.stageChanged("DRY 模式不会打开外部页面")
        return true
    }
}
