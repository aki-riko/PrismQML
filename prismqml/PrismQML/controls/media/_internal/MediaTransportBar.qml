// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// MediaTransportBar - Compact transport bar 紧凑播放控制条
// Reads playback state from the host control and forwards user intent back.
// 从宿主控件读取播放状态，并把用户意图回传。
Item {
    id: control

    // ==================== Required Props 必需属性 ====================
    required property Item host

    // ==================== Readonly State 只读状态 ====================
    readonly property bool playing: host.playbackState === Enums.media.playback_playing
    readonly property string positionText: _formatTime(host.position)
    readonly property string durationText: _formatTime(host.duration)

    // ==================== Internal Methods 内部方法 ====================
    // Format milliseconds as m:ss 把毫秒格式化为 m:ss
    function _formatTime(milliseconds) {
        var totalSeconds = Math.max(0, Math.floor(milliseconds / 1000))
        var minutes = Math.floor(totalSeconds / 60)
        var seconds = totalSeconds % 60
        return minutes + ":" + (seconds < 10 ? "0" : "") + seconds
    }

    // ==================== Size 尺寸 ====================
    height: Enums.controlSize.inputHeight
    anchors.left: parent.left
    anchors.right: parent.right
    anchors.bottom: parent.bottom

    // ==================== Content 内容 ====================
    Rectangle {
        anchors.fill: parent
        color: Enums.withAlpha(Enums.dialogColor, Enums.opacityLevel.strong)
    }

    // Seekable progress track 可拖动进度轨道
    Rectangle {
        id: progressTrack
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: Enums.border.normal
        color: Enums.dividerColor

        Rectangle {
            width: progressTrack.width * control.host.progress
            height: parent.height
            color: Enums.accentColor
        }

        MouseArea {
            anchors.fill: parent
            anchors.topMargin: -Enums.spacing.xs
            anchors.bottomMargin: -Enums.spacing.xs
            cursorShape: Qt.PointingHandCursor
            onClicked: function(mouse) {
                var ratio = Math.max(0, Math.min(1, mouse.x / Math.max(1, progressTrack.width)))
                control.host.seek(ratio * control.host.duration)
            }
        }
    }

    Row {
        anchors.left: parent.left
        anchors.leftMargin: Enums.spacing.s
        anchors.verticalCenter: parent.verticalCenter
        spacing: Enums.spacing.xxs

        MediaTransportButton {
            iconName: control.playing ? Enums.icon.pause : Enums.icon.play
            onClicked: control.host.togglePlayPause()
        }

        MediaTransportButton {
            iconName: Enums.icon.stop
            onClicked: control.host.stop()
        }
    }

    Text {
        anchors.right: parent.right
        anchors.rightMargin: Enums.spacing.s
        anchors.verticalCenter: parent.verticalCenter
        text: control.positionText + " / " + control.durationText
        color: Enums.secondaryForeground
        font.family: Enums.fontFamily
        font.pixelSize: Enums.typography.caption
    }
}
