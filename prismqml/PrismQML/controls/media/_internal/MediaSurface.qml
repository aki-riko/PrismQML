// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtMultimedia
import "../../.."

// MediaSurface - QtMultimedia playback surface QtMultimedia 播放表面
// Loaded lazily by MediaPlayerElement so the audio backend never starts during
// component construction. 由 MediaPlayerElement 懒加载，避免构造期启动音频后端。
Item {
    id: surface

    // ==================== Required Props 必需属性 ====================
    required property Item host

    // ==================== Internal Props 内部属性 ====================
    // Latched play intent: play() before the media finished loading must survive.
    // 锁存播放意图：媒体尚未加载完成时发出的 play() 必须保留。
    property bool _playRequested: false

    // ==================== Public Methods 公开方法 ====================
    function requestPlay() {
        _playRequested = true
        player.play()
    }

    function requestPause() {
        _playRequested = false
        player.pause()
    }

    function requestStop() {
        _playRequested = false
        player.stop()
    }

    function requestSeek(milliseconds) { player.position = Math.max(0, milliseconds) }

    // ==================== Internal Methods 内部方法 ====================
    // Map Qt playback states onto Enums.media tokens 把 Qt 播放状态映射到 Enums.media
    function _playbackStateToken(state) {
        switch (state) {
        case MediaPlayer.PlayingState:
            return Enums.media.playback_playing
        case MediaPlayer.PausedState:
            return Enums.media.playback_paused
        case MediaPlayer.StoppedState:
            return Enums.media.playback_stopped
        default:
            return Enums.media.playback_none
        }
    }

    // ==================== Size 尺寸 ====================
    anchors.fill: parent

    // ==================== Content 内容 ====================
    MediaPlayer {
        id: player
        source: surface.host.source
        playbackRate: surface.host.playbackRate
        loops: surface.host.loops
        videoOutput: videoOutput
        audioOutput: audioOutput

        onPlaybackStateChanged: surface.host._onPlaybackState(
            surface._playbackStateToken(playbackState))
        onPositionChanged: surface.host._onPosition(position)
        onDurationChanged: surface.host._onDuration(duration)
        onHasVideoChanged: surface.host._onHasVideo(hasVideo)
        onMediaStatusChanged: {
            if (mediaStatus === MediaPlayer.EndOfMedia) {
                surface.host._onMediaFinished()
            } else if (surface._playRequested
                    && mediaStatus === MediaPlayer.LoadedMedia
                    && playbackState !== MediaPlayer.PlayingState) {
                // The latch re-applies play() once the media is actually loadable.
                // 媒体真正可加载后，锁存意图重新执行 play()。
                player.play()
            }
        }
        onErrorOccurred: function(errorCode, message) {
            surface.host._onMediaError(message)
        }
    }

    AudioOutput {
        id: audioOutput
        volume: surface.host.volume
        muted: surface.host.muted
    }

    VideoOutput {
        id: videoOutput
        anchors.fill: parent
        visible: surface.host.hasVideo
        fillMode: surface.host.stretch ? VideoOutput.Stretch : VideoOutput.PreserveAspectFit
    }

    MediaTransportBar {
        id: transportBar
        visible: surface.host.showControls
        host: surface.host
    }
}
