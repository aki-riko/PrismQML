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
    property string statusText: Fluent.Translator.tr("gallery_d815f8ae15604066", Fluent.Translator._v)
    property string latestVersion: ""
    property bool useProgressDialog: false

    // ==================== Public Methods 公开方法 ====================
    function canCheck() {
        return activeUpdater && !autoUpdater._checking
                && !autoUpdater._downloading && !autoUpdater._awaitingDecision
                && !autoUpdater._installPreparing
    }

    function canChangeMode() {
        return !autoUpdater._checking && !autoUpdater._downloading
                && !autoUpdater._awaitingDecision && !autoUpdater._installPreparing
    }

    function resetStatusForMode() {
        latestVersion = ""
        statusText = dryRunMode
            ? Fluent.Translator.tr("gallery_d815f8ae15604066", Fluent.Translator._v)
            : (updaterBackend
                ? Fluent.Translator.tr("gallery_c3a7f22f02dbf5be", Fluent.Translator._v)
                : Fluent.Translator.tr("gallery_bb2f5a1bc47e85f4", Fluent.Translator._v))
    }

    function statusForUpdate(version) {
        latestVersion = version
        statusText = (dryRunMode ? Fluent.Translator.tr("gallery_ea965553d7b1859b", Fluent.Translator._v) : Fluent.Translator.tr("gallery_596dd46cfde5249d", Fluent.Translator._v))
            + version + Fluent.Translator.tr("gallery_01724aca88b28fcd")
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
                    text: Fluent.Translator.tr("gallery_736cff237d7d9255", Fluent.Translator._v)
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
                    ? Fluent.Translator.tr("gallery_42af2e26ff25e6dd", Fluent.Translator._v)
                    : Fluent.Translator.tr("gallery_e7a7cc8a258f77dc", Fluent.Translator._v)
                description: root.dryRunMode
                    ? Fluent.Translator.tr("gallery_03c05ebdc6e9216f", Fluent.Translator._v)
                    : Fluent.Translator.tr("gallery_168f3c5f6ee51608", Fluent.Translator._v)
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
                                ? Fluent.Translator.tr("gallery_43638d9715e217ac", Fluent.Translator._v)
                                : Fluent.Translator.tr("gallery_3aa15fd389abde55", Fluent.Translator._v)
                            checked: root.dryRunMode
                            enabled: root.canChangeMode()
                            onToggled: function(checked) {
                                root.dryRunMode = checked
                            }
                        }

                        Text {
                            width: parent ? parent.width : 0
                            text: root.dryRunMode
                                ? Fluent.Translator.tr("gallery_35a4f3eef6a0e6cf", Fluent.Translator._v)
                                : Fluent.Translator.tr("gallery_fadb1e1080535c78", Fluent.Translator._v)
                            font.family: Fluent.Enums.fontFamily
                            font.pixelSize: Fluent.Enums.typography.caption
                            color: Fluent.Enums.textColor.tertiary
                            wrapMode: Text.WordWrap
                        }
                    }

                    Toggle {
                        objectName: "galleryAutoUpdatePresenterToggle"
                        controlType: Fluent.Enums.toggle.control_switch
                        text: checked ? "ProgressDialog" : Fluent.Translator.tr("gallery_0acfb46690c50b2a", Fluent.Translator._v)
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
                                text: (root.dryRunMode ? Fluent.Translator.tr("gallery_7dac0a434f2c4ced", Fluent.Translator._v) : Fluent.Translator.tr("gallery_aca80488058c3db1", Fluent.Translator._v))
                                    + (autoUpdater.repository || Fluent.Translator.tr("gallery_80a57e03f0717f91", Fluent.Translator._v))
                                font.family: Fluent.Enums.fontFamily
                                font.pixelSize: Fluent.Enums.typography.body
                                color: Fluent.Enums.textColor.primary
                                elide: Text.ElideRight
                            }
                            Text {
                                text: Fluent.Translator.tr("gallery_435bd0f89db53b12", Fluent.Translator._v) + (autoUpdater.currentVersion || Fluent.Translator.tr("gallery_80a57e03f0717f91", Fluent.Translator._v))
                                font.family: Fluent.Enums.fontFamily
                                font.pixelSize: Fluent.Enums.typography.bodySmall
                                color: Fluent.Enums.textColor.secondary
                            }
                        }

                        Button {
                            id: checkButton
                            objectName: "galleryAutoUpdateCheckButton"
                            text: autoUpdater._installPreparing
                                ? Fluent.Translator.tr("gallery_6dd602065dbc624a", Fluent.Translator._v)
                                : (autoUpdater._checking
                                    ? (root.dryRunMode ? Fluent.Translator.tr("gallery_563bc55f19cf95dc", Fluent.Translator._v) : Fluent.Translator.tr("gallery_fb11aa6f29827095", Fluent.Translator._v))
                                    : (root.dryRunMode ? Fluent.Translator.tr("gallery_688bfdcebbc5683d", Fluent.Translator._v) : Fluent.Translator.tr("gallery_7f68ebad19ba6bcd", Fluent.Translator._v)))
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
                            ? Fluent.Translator.tr("gallery_28a283caa1210bfe") + root.latestVersion
                            : Fluent.Translator.tr("gallery_48c34effb083ee53", Fluent.Translator._v)
                        font.family: Fluent.Enums.fontFamily
                        font.pixelSize: Fluent.Enums.typography.caption
                        color: Fluent.Enums.textColor.tertiary
                    }
                }
            }

            ExampleCard {
                title: Fluent.Translator.tr("gallery_50989d57fa728663", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_56df4f714ccb84b5", Fluent.Translator._v)
                orientation: Qt.Vertical

                Column {
                    width: parent ? parent.width : 0
                    spacing: Fluent.Enums.spacing.s

                    Repeater {
                        model: root.dryRunMode
                            ? [
                                Fluent.Translator.tr("gallery_c690f3d0291abc07", Fluent.Translator._v),
                                Fluent.Translator.tr("gallery_10c0380b93f668a7", Fluent.Translator._v),
                                Fluent.Translator.tr("gallery_ca2ad481307e7199", Fluent.Translator._v),
                                Fluent.Translator.tr("gallery_db0d7260525e8cc2", Fluent.Translator._v)
                            ]
                            : [
                                Fluent.Translator.tr("gallery_762fc61305fbb999", Fluent.Translator._v),
                                Fluent.Translator.tr("gallery_7e2cc0c8ed7296d6", Fluent.Translator._v),
                                Fluent.Translator.tr("gallery_34c08a5b0b855bdc", Fluent.Translator._v),
                                Fluent.Translator.tr("gallery_8f6e4a4cb2a5c74f", Fluent.Translator._v)
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
        silentArgs: root.dryRunMode || Qt.platform.os === "windows"
            ? dryRunUpdater.installerSilentArgs
            : ""
        notifyWhenUpToDate: true
        feedbackPresenter: root.useProgressDialog
            ? progressDialogFeedbackPresenter
            : toastFeedbackPresenter

        onUpToDateNotified: function(version) {
            root.latestVersion = version
            root.statusText = Fluent.Translator.tr("gallery_94c0372cbcf556d1") + version
        }
        onErrorOccurred: function(message) {
            root.statusText = Fluent.Translator.tr("gallery_d2bd1fcb3b15dbdf") + message
        }
        onDownloadRequested: function(version) {
            root.statusText = Fluent.Translator.tr("gallery_68b849d1a0436c51") + version
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
            root.statusText = Fluent.Translator.tr("gallery_d2bd1fcb3b15dbdf") + error
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
