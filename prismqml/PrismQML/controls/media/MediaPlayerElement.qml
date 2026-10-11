// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "_internal" as MediaInternal

// MediaPlayerElement - Inline media playback surface 内嵌媒体播放元素
// Fluent parity for MediaPlayerElement: the transport surface is incubated on
// demand, so constructing the element never starts the audio backend.
// 对齐 Fluent MediaPlayerElement：传输表面按需孵化，构造元素不会启动音频后端。
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property url surfaceUrl: Qt.resolvedUrl("_internal/MediaSurface.qml")   // Injected surface component 注入的表面组件
    property url source: ""                     // Media source, injected by the caller 调用方注入的媒体源
    property bool autoActivate: false           // Activate during construction 构造期是否激活
    property bool autoPlay: false               // Play as soon as the surface is ready 表面就绪后立即播放
    property bool showControls: true            // Show the transport bar 是否显示播放控制条
    property bool stretch: false                // Stretch video instead of fitting it 视频拉伸而非等比适配
    property bool muted: false                  // Mute the audio output 静音
    property real volume: Enums.media.media_default_volume
    property real playbackRate: Enums.media.media_default_playback_rate
    property int loops: Enums.media.media_default_loops
    property string unavailableMessage: ""      // Localized fallback text 本地化回退文案

    // ==================== Readonly State 只读状态 ====================
    readonly property bool active: surfaceLoader.status !== Loader.Null
    readonly property bool loading: surfaceLoader.status === Loader.Loading
    readonly property bool surfaceCreated: surfaceLoader.item !== null
    readonly property bool available: _availability === Enums.media.availability_available
    readonly property bool degraded: _availability === Enums.media.availability_unavailable
    readonly property int availabilityState: _availability
    readonly property string errorString: _errorString
    readonly property int playbackState: _playbackState
    readonly property int position: _position
    readonly property int duration: _duration
    readonly property bool hasVideo: _hasVideo
    readonly property real progress: _duration > 0 ? _position / _duration : 0

    // ==================== Internal Props 内部属性 ====================
    property int _availability: Enums.media.availability_unknown
    property string _errorString: ""
    property int _playbackState: Enums.media.playback_stopped
    property int _position: 0
    property int _duration: 0
    property bool _hasVideo: false
    property bool _pendingPlay: false
    property int _pendingSeek: -1
    property var _probeComponent: null

    // ==================== Signals 信号 ====================
    signal activated()
    signal availabilityFailed(string message)
    signal mediaFinished()
    signal mediaError(string message)

    // ==================== Public Methods 公开方法 ====================
    // Incubate the playback surface 孵化播放表面
    function activate() {
        if (surfaceLoader.status !== Loader.Null) {
            return available
        }
        surfaceLoader.asynchronous = true
        surfaceLoader.setSource(surfaceUrl, { "host": control })
        return true
    }

    // Compile the surface without creating it 只编译表面而不创建实例
    // Returns true once the surface is known to be loadable; module resolution may
    // still be in flight, in which case the public availability state settles later.
    // 表面可加载时返回 true；模块解析可能仍在进行，此时公开可用性状态稍后落定。
    function probeAvailability() {
        if (_probeComponent === null) {
            _probeComponent = Qt.createComponent(surfaceUrl)
            _probeComponent.statusChanged.connect(control._applyProbeStatus)
        }
        return control._applyProbeStatus()
    }

    // Start playback 开始播放
    function play() {
        _pendingPlay = true
        activate()
        _flushPendingCommands()
    }

    // Pause playback 暂停播放
    function pause() {
        _pendingPlay = false
        if (surfaceLoader.item !== null) {
            surfaceLoader.item.requestPause()
        }
    }

    // Stop playback and rewind 停止播放并回到起点
    function stop() {
        _pendingPlay = false
        _pendingSeek = -1
        if (surfaceLoader.item !== null) {
            surfaceLoader.item.requestStop()
        }
        _position = 0
        _playbackState = Enums.media.playback_stopped
    }

    // Toggle between play and pause 在播放与暂停之间切换
    function togglePlayPause() {
        if (_playbackState === Enums.media.playback_playing) {
            pause()
        } else {
            play()
        }
    }

    // Seek to an absolute position 跳转到绝对位置
    function seek(milliseconds) {
        if (surfaceLoader.item !== null) {
            surfaceLoader.item.requestSeek(milliseconds)
        } else {
            _pendingSeek = milliseconds
        }
    }

    // Replace the media source 替换媒体源
    function setSource(value) {
        source = value
        _position = 0
        _duration = 0
    }

    // Clamp and set the volume 限幅设置音量
    function setVolume(value) {
        volume = Math.max(0, Math.min(1, value))
    }

    // Set the mute flag 设置静音
    function setMuted(flag) {
        muted = flag
    }

    // ==================== Internal Methods 内部方法 ====================
    // Apply commands queued before the surface was ready 应用表面就绪前排队的命令
    function _flushPendingCommands() {
        var surface = surfaceLoader.item
        if (surface === null) {
            return
        }
        if (_pendingPlay) {
            surface.requestPlay()
            _pendingPlay = false
        }
        if (_pendingSeek >= 0) {
            surface.requestSeek(_pendingSeek)
            _pendingSeek = -1
        }
    }

    // Extract the incubation error text 提取孵化错误文本
    function _surfaceErrorText() {
        if (_probeComponent === null) {
            _probeComponent = Qt.createComponent(surfaceUrl)
            _probeComponent.statusChanged.connect(control._applyProbeStatus)
        }
        return _probeComponent.status === Component.Error
            ? _probeComponent.errorString()
            : "media surface component failed to load"
    }

    // Apply the probe result to the public availability state 把探测结果写入公开可用性状态
    function _applyProbeStatus() {
        if (_probeComponent === null) {
            return false
        }
        if (_probeComponent.status === Component.Error) {
            _availability = Enums.media.availability_unavailable
            _errorString = _probeComponent.errorString()
            return false
        }
        if (_probeComponent.status === Component.Ready) {
            _availability = Enums.media.availability_available
            _errorString = ""
            return true
        }
        return false
    }

    // Surface ready callback 表面就绪回调
    function _onSurfaceReady() {
        _availability = Enums.media.availability_available
        _errorString = ""
        if (autoPlay) {
            _pendingPlay = true
        }
        _flushPendingCommands()
        activated()
    }

    function _onPlaybackState(value) { _playbackState = value }
    function _onPosition(value) { _position = value }
    function _onDuration(value) { _duration = value }
    function _onHasVideo(value) { _hasVideo = value }
    function _onMediaFinished() { mediaFinished() }

    function _onMediaError(message) {
        _playbackState = Enums.media.playback_error
        _errorString = message
        mediaError(message)
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.media.media_default_width
    implicitHeight: Enums.media.media_default_height

    Component.onCompleted: {
        if (autoActivate) {
            activate()
        }
    }

    // ==================== Content 内容 ====================
    // Incubated playback surface 按需孵化的播放表面
    Loader {
        id: surfaceLoader
        anchors.fill: parent

        // Ready is reported here: an incubated surface runs its own
        // Component.onCompleted before the Loader exposes it to the host.
        // 就绪在这里上报：被孵化的表面自身的 Component.onCompleted 先于宿主可见。
        onLoaded: control._onSurfaceReady()

        onStatusChanged: {
            if (surfaceLoader.status === Loader.Error) {
                control._availability = Enums.media.availability_unavailable
                control._errorString = control._surfaceErrorText()
                control.availabilityFailed(control._errorString)
            }
        }
    }

    // Graceful fallback when the playback surface cannot load 播放表面无法加载时的优雅回退
    Loader {
        id: unavailableLoader
        anchors.fill: parent
        active: control.degraded
        sourceComponent: MediaInternal.SurfaceUnavailable {
            host: control
        }
    }
}
