// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// Media - Media / map / web / animated icon enums 媒体、地图、网页与动效图标枚举
// Usage 使用方式: Enums.media.playback_playing, Enums.media.animated_state_pressed
// One category file keeps every media surface token in a single reviewed owner.
// 单一分类文件让所有媒体表面 token 拥有同一个已评审归属。
QtObject {
    // ==================== Playback 播放状态 ====================
    readonly property int playback_none: 0
    readonly property int playback_stopped: 1
    readonly property int playback_playing: 2
    readonly property int playback_paused: 3
    readonly property int playback_error: 4

    // ==================== Availability 可用性 ====================
    readonly property int availability_unknown: 0
    readonly property int availability_available: 1
    readonly property int availability_unavailable: 2

    // ==================== Load State 加载状态 ====================
    readonly property int load_idle: 0
    readonly property int load_loading: 1
    readonly property int load_ready: 2
    readonly property int load_error: 3

    // ==================== Layer 图层类型 ====================
    readonly property int layer_marker: 0
    readonly property int layer_polyline: 1
    readonly property int layer_circle: 2

    // ==================== Animated Icon State 动效图标状态 ====================
    readonly property int animated_state_normal: 0
    readonly property int animated_state_pointer_over: 1
    readonly property int animated_state_pressed: 2
    readonly property int animated_state_disabled: 3

    // ==================== Animated Icon Motion 动效图标运动参数 ====================
    readonly property real animated_scale_normal: 1.0
    readonly property real animated_scale_pointer_over: 1.12
    readonly property real animated_scale_pressed: 0.92
    readonly property real animated_scale_disabled: 1.0

    // ==================== Media Defaults 媒体默认值 ====================
    readonly property real media_default_volume: 1.0
    readonly property real media_default_playback_rate: 1.0
    readonly property int media_default_loops: 1
    readonly property int media_default_width: 320
    readonly property int media_default_height: 180

    // ==================== Map Defaults 地图默认值 ====================
    readonly property real map_default_zoom: 8.0
    readonly property int map_activation_timeout: 5000
    readonly property real map_min_zoom: 0.0
    readonly property real map_max_zoom: 30.0
    readonly property real map_zoom_step: 1.0
    readonly property real map_default_latitude: 0.0
    readonly property real map_default_longitude: 0.0

    // ==================== Web Defaults 网页默认值 ====================
    readonly property real webview_default_zoom: 1.0
}
