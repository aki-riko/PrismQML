// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

import PrismQML
import PrismQML as Fluent

// AutoUpdate Gallery page - real updater showcase 自动更新 Gallery 展示页
Item {
    id: root

    // ==================== Public Props 公开属性 ====================
    // Gallery may also load this page in a probe without its Python backend.
    // Gallery 在没有 Python 后端的探针中也可能加载此页面。
    readonly property var updaterBackend:
        (typeof appUpdater !== "undefined" && appUpdater) ? appUpdater : null
    property string statusText: updaterBackend
        ? "尚未检查"
        : "Gallery 未注入 appUpdater"
    property string latestVersion: ""

    // ==================== Public Methods 公开方法 ====================
    function canCheck() {
        return updaterBackend && !autoUpdater._checking
                && !autoUpdater._downloading && !autoUpdater._awaitingDecision
    }

    function statusForUpdate(version) {
        latestVersion = version
        statusText = "发现新版本 " + version + "，等待确认"
    }

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
                title: "真实 GitHub Releases 更新流程"
                description: "点击检查后，会使用 Gallery 注入的真实 Updater；发现版本时弹出 UpdateDialog，下载过程显示桌面通知。"
                orientation: Qt.Vertical

                Column {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.l

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
                                text: "仓库：" + (autoUpdater.repository || "未配置")
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
                            text: autoUpdater._checking ? "检查中…" : "检查更新"
                            icon: "ArrowSync"
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
                description: "Gallery 中可以直接看到门面组件如何编排底层 Updater、UpdateDialog 和下载进度。"
                orientation: Qt.Vertical

                Column {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.s

                    Repeater {
                        model: [
                            "1. 检查 GitHub Releases 并比较当前版本",
                            "2. 发现新版本后显示更新说明和确认对话框",
                            "3. 下载时显示不确定/确定进度环",
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

    // AutoUpdater facade is intentionally visible here, rather than hidden in
    // a startup hook, so the Gallery exposes the actual user-facing flow.
    // 门面直接放在页面中而不是藏在启动钩子里，确保 Gallery 展示真实用户流程。
    Fluent.AutoUpdater {
        id: autoUpdater
        updater: root.updaterBackend
        autoDownload: true
        notifyWhenUpToDate: true

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
        target: root.updaterBackend
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
}
