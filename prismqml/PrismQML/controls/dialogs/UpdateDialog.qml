// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import "../.."
import "../buttons/Button"
import "../data/Label"
import "../containers"
import "../icons"

// UpdateDialog - 应用更新提示对话框(配合 python.core.Updater 使用)
//
// 展示"发现新版本"信息:版本对比 + Markdown 渲染的更新说明(带边框,可滚动) + 下载/稍后按钮。
// 有更新说明时对话框取窗口 75% 尺寸;无说明时按内容自适应高度。
// 与 Updater 组件解耦:本组件只负责展示与发信号,下载/安装由调用方接 confirmed()。
//
// 用法:
//     Fluent.UpdateDialog {
//         id: updateDialog
//         version: "v1.0.4"
//         currentVersion: "v1.0.3"
//         notes: releaseNotesMarkdown   // GitHub release 的 body(markdown)
//         onConfirmed: updater.downloadUpdate(downloadUrl)
//     }
//     updateDialog.open()
//
// API:
// - version (string): 新版本号
// - currentVersion (string): 当前版本号
// - notes (string): 更新说明(Markdown 文本),为空时隐藏说明区并按内容自适应高度
// - confirmText (string): 主按钮文案, 默认 "下载并安装"
// - cancelText (string): 次按钮文案, 默认 "稍后"
// - confirmed (signal): 点"下载并安装"触发
// - cancelled (signal): 点"稍后"触发
DialogBoxCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string version: ""
    property string currentVersion: ""
    property string notes: ""
    property string confirmText: qsTr("下载并安装")
    property string cancelText: qsTr("稍后")

    readonly property bool isOpen: _isOpen
    readonly property color _accentColor: Enums.statusLevel.getColorByLevel(Enums.statusLevel.attention)

    // ==================== Signals 信号 ====================
    signal confirmed()
    signal cancelled()

    // ==================== Footer 按钮组 ====================
    footer: Component {
        Row {
            property var dialog
            spacing: Enums.spacing.l

            ButtonCore {
                text: control.confirmText
                icon: "ArrowDownload"
                style: Enums.button.style_filled
                level: Enums.statusLevel.attention
                width: Enums.dialog.buttonWidth
                height: Enums.dialog.buttonHeight
                onClicked: {
                    control.confirmed()
                    control.accept()
                }
            }
            ButtonCore {
                text: control.cancelText
                style: Enums.button.style_default
                width: Enums.dialog.buttonWidth
                height: Enums.dialog.buttonHeight
                onClicked: {
                    control.cancelled()
                    control.reject()
                }
            }
        }
    }

    // ==================== Content 内容区 ====================
    // 有更新说明时对话框取窗口 75%(control 为 overlay 根,anchors.fill 窗口 contentItem,
    // 故 control.width/height ≈ 窗口宽高),说明区 fillHeight 占剩余空间;
    // 无说明时不设固定高,按内容(图标+标题+版本)自适应,避免大片空白。
    ColumnLayout {
        id: contentLayout
        readonly property bool _hasNotes: control.notes !== ""
        width: Math.max(360, control.width * 0.75)
        height: _hasNotes ? Math.max(320, control.height * 0.75) : implicitHeight
        spacing: Enums.spacing.l

        // 顶部图标圈
        Item {
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: Enums.spacing.s
            implicitWidth: 56
            implicitHeight: 56
            Rectangle {
                anchors.fill: parent
                radius: width / 2
                color: control._accentColor
                opacity: 0.12
            }
            Icon {
                anchors.centerIn: parent
                width: 28; height: 28
                icon: "ArrowSync"
                color: control._accentColor
            }
        }

        // 标题
        Label {
            Layout.fillWidth: true
            text: qsTr("发现新版本")
            type: Enums.label.type_subtitle
            color: Enums.stateColor.textStrong
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
        }

        // 版本对比副文本
        Label {
            Layout.fillWidth: true
            text: control.version + (control.currentVersion !== "" ? ("  (" + qsTr("当前") + " " + control.currentVersion + ")") : "")
            type: Enums.label.type_body
            color: Enums.stateColor.textMedium
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            visible: control.version !== ""
        }

        // 更新说明区:外层 Rectangle 提供边框+圆角,内部 ScrollArea 滚动 Markdown 文本。
        // 用 Qt 原生 Text.MarkdownText 渲染(标题/列表/加粗/链接),避免跨目录引 MarkdownView
        // 导致其相对 import 的 Enums 解析失败。
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: control.notes !== ""
            radius: Enums.radius.medium
            color: "transparent"
            border.width: Enums.border.thin
            border.color: Enums.stateColor.cardBorder

            ScrollArea {
                anchors.fill: parent
                anchors.margins: Enums.border.thin
                padding: Enums.spacing.m

                Text {
                    id: mdText
                    // contentHolder 宽度已扣除 ScrollArea padding,直接用 parent.width
                    width: parent ? parent.width : 0
                    text: control.notes
                    textFormat: Text.MarkdownText
                    wrapMode: Text.WordWrap
                    color: Enums.textColor.primary
                    linkColor: Enums.accentColor
                    font.family: Enums.fontFamily
                    font.pixelSize: 14
                    onLinkActivated: (url) => Qt.openUrlExternally(url)
                }
            }
        }
    }
}
