// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

import PrismQML
import PrismQML as Fluent
import "_internal" as GalleryInternal

// AutoUpdate Gallery page - real updater showcase 自动更新 Gallery 展示页
Item {
    id: root

    // ==================== Public Props 公开属性 ====================
    // Gallery may also load this page in a probe without its Python backend.
    // Gallery 在没有 Python 后端的探针中也可能加载此页面。
    readonly property var updaterBackend:
        (typeof appUpdater !== "undefined" && appUpdater) ? appUpdater : null
    property bool dryRunMode: true
    readonly property var activeUpdater: dryRunMode
        ? dryRunUpdater
        : updaterBackend
    property string statusText: "DRY 模式：等待开始演示"
    property string latestVersion: ""
    property bool useProgressDialog: false

    // ==================== Public Methods 公开方法 ====================
    function canCheck() {
        return activeUpdater && !autoUpdater._checking
                && !autoUpdater._downloading && !autoUpdater._awaitingDecision
    }

    function canChangeMode() {
        return !autoUpdater._checking && !autoUpdater._downloading
                && !autoUpdater._awaitingDecision
    }

    function resetStatusForMode() {
        latestVersion = ""
        statusText = dryRunMode
            ? "DRY 模式：等待开始演示"
            : (updaterBackend
                ? "真实模式：尚未检查"
                : "真实模式不可用：Gallery 未注入 appUpdater")
    }

    function statusForUpdate(version) {
        latestVersion = version
        statusText = (dryRunMode ? "DRY：发现模拟版本 " : "发现新版本 ")
            + version + "，等待确认"
    }

    onDryRunModeChanged: resetStatusForMode()

    // ==================== Content 内容 ====================
    ScrollArea {
        anchors.fill: parent

        Column {
            width: parent ? parent.width : 0
            spacing: Fluent.Enums.spacing.xxl

            Column {
                width: parent ? parent.width : 0
                spacing: Fluent.Enums.spacing.xs

                Text {
                    text: "自动更新"
                    font.family: Fluent.Enums.fontFamily
                    font.pixelSize: Fluent.Enums.typography.displayLarge
                    font.bold: true
                    color: Fluent.Enums.textColor.primary
                }
                Text {
                    text: "prismqml.controls.feedback.AutoUpdater"
                    font.family: Fluent.Enums.fontFamily
                    font.pixelSize: Fluent.Enums.typography.caption
                    color: Fluent.Enums.textColor.secondary
                }
            }

            ExampleCard {
                title: root.dryRunMode
                    ? "DRY 下载并安装演示"
                    : "真实 GitHub Releases 更新流程"
                description: root.dryRunMode
                    ? "完整展示检查、确认、下载进度和安装交接；全程不访问网络、不创建文件，也不启动安装器。"
                    : "使用 Gallery 注入的真实 Updater 检查 Release；此模式可能访问网络并打开发布页。"
                orientation: Qt.Vertical

                Column {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l

                    Column {
                        width: parent ? parent.width : 0
                        spacing: Fluent.Enums.spacing.xs

                        Toggle {
                            objectName: "galleryAutoUpdateDryRunToggle"
                            controlType: Fluent.Enums.toggle.control_switch
                            text: checked
                                ? "DRY 演示模式（安全模拟）"
                                : "真实 Release 模式"
                            checked: root.dryRunMode
                            enabled: root.canChangeMode()
                            onToggled: function(checked) {
                                root.dryRunMode = checked
                            }
                        }

                        Text {
                            width: parent ? parent.width : 0
                            text: root.dryRunMode
                                ? "用户会看到真实对话框和进度反馈，但不会产生任何安装副作用。"
                                : "真实模式取决于 Release 是否提供当前平台安装资产。"
                            font.family: Fluent.Enums.fontFamily
                            font.pixelSize: Fluent.Enums.typography.caption
                            color: Fluent.Enums.textColor.tertiary
                            wrapMode: Text.WordWrap
                        }
                    }

                    Toggle {
                        objectName: "galleryAutoUpdatePresenterToggle"
                        controlType: Fluent.Enums.toggle.control_switch
                        text: checked ? "ProgressDialog" : "右下角 Toast"
                        checked: root.useProgressDialog
                        onToggled: function(checked) {
                            root.useProgressDialog = checked
                        }
                    }

                    Row {
                        width: parent ? parent.width : 0
                        spacing: Fluent.Enums.spacing.xl

                        Column {
                            width: Math.max(
                                Fluent.Enums.controlSize.cardContentWidth,
                                parent.width - checkButton.width - Fluent.Enums.spacing.xl
                            )
                            spacing: Fluent.Enums.spacing.xs

                            Text {
                                text: (root.dryRunMode ? "演示源：" : "仓库：")
                                    + (autoUpdater.repository || "未配置")
                                font.family: Fluent.Enums.fontFamily
                                font.pixelSize: Fluent.Enums.typography.body
                                color: Fluent.Enums.textColor.primary
                                elide: Text.ElideRight
                            }
                            Text {
                                text: "当前版本：" + (autoUpdater.currentVersion || "未配置")
                                font.family: Fluent.Enums.fontFamily
                                font.pixelSize: Fluent.Enums.typography.bodySmall
                                color: Fluent.Enums.textColor.secondary
                            }
                        }

                        Button {
                            id: checkButton
                            objectName: "galleryAutoUpdateCheckButton"
                            text: autoUpdater._checking
                                ? (root.dryRunMode ? "模拟检查中…" : "检查中…")
                                : (root.dryRunMode ? "开始 DRY 演示" : "检查更新")
                            icon: root.dryRunMode ? "Beaker" : "ArrowSync"
                            style: Fluent.Enums.button.style_filled
                            enabled: root.canCheck()
                            onClicked: autoUpdater.check()
                        }
                    }

                    Rectangle {
                        width: parent ? parent.width : 0
                        height: statusLabel.implicitHeight + Fluent.Enums.spacing.m * 2
                        radius: Fluent.Enums.radius.large
                        color: Fluent.Enums.surfaceColor
                        border.width: Fluent.Enums.border.thin
                        border.color: Fluent.Enums.stateColor.cardBorder

                        Text {
                            id: statusLabel
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.leftMargin: Fluent.Enums.spacing.m
                            anchors.rightMargin: Fluent.Enums.spacing.m
                            text: root.statusText
                            font.family: Fluent.Enums.fontFamily
                            font.pixelSize: Fluent.Enums.typography.body
                            color: Fluent.Enums.textColor.primary
                            wrapMode: Text.WordWrap
                        }
                    }

                    Text {
                        width: parent ? parent.width : 0
                        text: root.latestVersion !== ""
                            ? "最近检测到：" + root.latestVersion
                            : "最近检测到：暂无"
                        font.family: Fluent.Enums.fontFamily
                        font.pixelSize: Fluent.Enums.typography.caption
                        color: Fluent.Enums.textColor.tertiary
                    }
                }
            }

            ExampleCard {
                title: "更新链路"
                description: "Gallery 中可以直接看到门面组件如何编排底层 Updater、UpdateDialog 和可替换反馈展示器。"
                orientation: Qt.Vertical

                Column {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.s

                    Repeater {
                        model: root.dryRunMode
                            ? [
                                "1. 模拟检查并返回一个演示版本",
                                "2. 使用真实 UpdateDialog 展示说明与“下载并安装”确认",
                                "3. 使用真实 Toast 或 ProgressDialog 将模拟进度推进到 100%",
                                "4. 模拟安装交接并明确告知未创建文件、未启动程序"
                            ]
                            : [
                                "1. 检查 GitHub Releases 并比较当前版本",
                                "2. 发现新版本后显示更新说明和确认对话框",
                                "3. 下载时由 Toast 或 ProgressDialog 显示不确定/确定进度",
                                "4. 下载完成后启动安装程序，或打开 Release 页面"
                            ]

                        delegate: Text {
                            required property string modelData
                            width: parent ? parent.width : 0
                            text: modelData
                            font.family: Fluent.Enums.fontFamily
                            font.pixelSize: Fluent.Enums.typography.body
                            color: Fluent.Enums.textColor.primary
                            wrapMode: Text.WordWrap
                        }
                    }
                }
            }
        }
    }

    GalleryInternal.GalleryDryRunUpdater {
        id: dryRunUpdater
        objectName: "galleryDryRunUpdater"
        currentVersion: root.updaterBackend
            ? root.updaterBackend.currentVersion
            : "Gallery"
    }

    // AutoUpdater facade is intentionally visible here, rather than hidden in
    // a startup hook, so the Gallery exposes the actual user-facing flow.
    // 门面直接放在页面中而不是藏在启动钩子里，确保 Gallery 展示真实用户流程。
    Component {
        id: toastFeedbackPresenter

        Fluent.AutoUpdaterToastPresenter {}
    }

    Component {
        id: progressDialogFeedbackPresenter

        Fluent.AutoUpdaterProgressDialogPresenter {}
    }

    Fluent.AutoUpdater {
        id: autoUpdater
        objectName: "galleryAutoUpdater"
        updater: root.activeUpdater
        autoDownload: true
        notifyWhenUpToDate: true
        feedbackPresenter: root.useProgressDialog
            ? progressDialogFeedbackPresenter
            : toastFeedbackPresenter

        onUpToDateNotified: function(version) {
            root.latestVersion = version
            root.statusText = "已是最新版本 " + version
        }
        onErrorOccurred: function(message) {
            root.statusText = "检查失败：" + message
        }
        onDownloadRequested: function(version) {
            root.statusText = "已确认下载 " + version
        }
    }

    Connections {
        target: root.activeUpdater
        ignoreUnknownSignals: true

        function onUpdateAvailable(version) {
            root.statusForUpdate(version)
        }
        function onUpToDate(version) {
            root.latestVersion = version
        }
        function onCheckFailed(error) {
            root.statusText = "检查失败：" + error
        }
    }

    Connections {
        target: dryRunUpdater

        function onStageChanged(message) {
            if (root.dryRunMode)
                root.statusText = message
        }
    }
}
