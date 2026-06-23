// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import "../.."
import "../buttons/Button"
import "../data/Label"
import "../icons"

// ConfirmDialog - 通用二次确认对话框 (设计感版)
//
// 用法:
//     Fluent.ConfirmDialog {
//         id: deleteConfirm
//         level: Fluent.Enums.statusLevel.error
//         title: "删除记录"
//         message: "确定删除这条记录? 删除后无法恢复。"
//         confirmText: "删除"
//         onConfirmed: viewModel.deleteRecord(currentId)
//     }
//     deleteConfirm.open()
//
// API:
// - level (int): info / success / warning / error / attention / processing
//                决定图标 + 主按钮颜色, 默认 warning
// - title (string): 标题, 默认 "确认操作"
// - message (string): 消息正文
// - messageAlignment (int): 消息正文水平对齐, 默认 Text.AlignHCenter; 长文本可设 Text.AlignLeft
// - confirmText (string): 主按钮文案, 不设则按 level 自动 ("删除"/"确认"/"知道了")
// - cancelText (string): 取消按钮文案, 默认 "取消"
// - confirmIcon (string): 主按钮图标, 不设则按 level 自动
// - countdown (int): 秒数, > 0 时主按钮在倒计时结束前禁用 (防误点危险操作)。
//                   倒计时显示 "删除 (3s)" → "删除 (2s)" → "删除"。默认 0 = 不倒计时。
// - confirmed (signal): 用户点确认时触发
// - cancelled (signal): 用户点取消时触发
DialogBoxCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    property int level: Enums.statusLevel.warning
    property string title: qsTr("确认操作")
    property string message: ""
    property int messageAlignment: Text.AlignHCenter  // 消息正文水平对齐, 默认居中; 长文本(如更新说明)可设 Text.AlignLeft
    property string confirmText: ""
    property string cancelText: qsTr("取消")
    property string confirmIcon: ""
    property bool destructive: level === Enums.statusLevel.error  // error 自动 destructive 视觉
    property int countdown: 0  // 倒计时秒数, 0 = 关闭

    // 暴露公开 isOpen 标志: _isOpen 是基类内部下划线属性, QML Connections 对下划线属性
    // 的 handler 名 (on_IsOpenChanged) 在 Qt 6 行为不稳定, 用 readonly 中转更可靠。
    readonly property bool isOpen: _isOpen

    // ==================== Internal 内部 ====================
    // level → icon name 映射 (Fluent UI 系统图标)
    readonly property string _autoIcon: {
        switch (level) {
            case Enums.statusLevel.error:      return "ErrorCircle"
            case Enums.statusLevel.warning:    return "Warning"
            case Enums.statusLevel.success:    return "CheckmarkCircle"
            case Enums.statusLevel.processing: return "ArrowSync"
            case Enums.statusLevel.attention:  return "Info"
            default:                                  return "Info"  // info
        }
    }

    // level → 主按钮默认文案 (用户没显式设 confirmText 时回退)
    readonly property string _autoConfirmText: {
        switch (level) {
            case Enums.statusLevel.error:   return qsTr("删除")
            case Enums.statusLevel.warning: return qsTr("确认")
            case Enums.statusLevel.success: return qsTr("好的")
            default:                               return qsTr("确认")
        }
    }

    readonly property string _baseConfirmText: confirmText !== "" ? confirmText : _autoConfirmText
    // 倒计时未结束时拼后缀 "删除 (3s)", 结束后回到 "删除"
    readonly property string _effectiveConfirmText: _countdownRemaining > 0
        ? _baseConfirmText + " (" + _countdownRemaining + "s)"
        : _baseConfirmText
    readonly property string _effectiveConfirmIcon: confirmIcon !== "" ? confirmIcon : _autoIcon
    readonly property color _accentColor: Enums.statusLevel.getColorByLevel(level)
    // 倒计时进行中主按钮禁用 (防误点危险操作)
    readonly property bool _confirmEnabled: _countdownRemaining === 0

    // ==================== Signals 信号 ====================
    signal confirmed()
    signal cancelled()

    // ==================== Internal 倒计时 ====================
    property int _countdownRemaining: 0
    Timer {
        id: countdownTimer
        interval: 1000
        repeat: true
        onTriggered: {
            if (control._countdownRemaining > 0) {
                control._countdownRemaining--
                if (control._countdownRemaining === 0) running = false
            }
        }
    }

    // 暴露公开 isOpen 标志: _isOpen 是基类内部下划线属性, QML Connections 对下划线属性
    // 的 handler 名 (on_IsOpenChanged) 在 Qt 6 行为不稳定, 用 readonly 中转更可靠。

    // 打开时启动倒计时, 关闭时复位
    onIsOpenChanged: {
        if (isOpen && countdown > 0) {
            _countdownRemaining = countdown
            countdownTimer.restart()
        } else {
            countdownTimer.stop()
            _countdownRemaining = 0
        }
    }

    // ==================== Footer 按钮组 ====================
    footer: Component {
        Row {
            property var dialog
            spacing: Enums.spacing.l

            // 主按钮: filled + level 色, 视觉强调
            // 倒计时进行中走 enabled=false: filled 禁用态保留 level 色相淡化版 (引擎层
             // 已修, 不再灰化), 视觉仍是"红色褪色"的危险按钮在冷却。
            ButtonCore {
                text: control._effectiveConfirmText
                icon: control._effectiveConfirmIcon
                style: Enums.button.style_filled
                level: control.level
                enabled: control._confirmEnabled
                width: Enums.dialog.buttonWidth
                height: Enums.dialog.buttonHeight
                onClicked: {
                    control.confirmed()
                    control.accept()
                }
            }

            // 次按钮: default 中性
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

    // ==================== Content 内容区域 ====================
    ColumnLayout {
        width: 360
        spacing: Enums.spacing.l

        // 顶部图标圈 — 圆形背景 (level 色 12% 透明) + 实色图标, 给确认操作仪式感
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
                width: 28
                height: 28
                icon: control._effectiveConfirmIcon
                color: control._accentColor
            }
        }

        // 标题 — 居中, subtitle 字号
        Label {
            Layout.fillWidth: true
            text: control.title
            type: Enums.label.type_subtitle
            color: Enums.stateColor.textStrong
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
        }

        // 消息正文 — 对齐方式由 messageAlignment 控制(默认居中), body 字号, 次要色
        Label {
            Layout.fillWidth: true
            text: control.message
            type: Enums.label.type_body
            color: Enums.stateColor.textMedium
            horizontalAlignment: control.messageAlignment
            wrapMode: Text.WordWrap
            visible: text !== ""
        }
    }
}
