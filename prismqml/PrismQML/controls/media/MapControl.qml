// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "_internal" as MediaInternal

// MapControl - Map, geo coordinates and layers 地图、地理坐标与图层
// Fluent parity for the map control family. The geoservices plugin, tile
// provider parameters and map type are always injected by the caller.
// 对齐 Fluent 地图控件族：地理服务插件、瓦片提供方参数与地图类型一律由调用方注入。
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property url surfaceUrl: Qt.resolvedUrl("_internal/MapSurface.qml")   // Injected surface component 注入的表面组件
    property string pluginName: ""              // Injected geoservices plugin name 注入的地理服务插件名
    property var pluginParameters: []           // Injected plugin parameters, at most 4 entries 注入的插件参数（最多 4 项）
    property real latitude: Enums.media.map_default_latitude
    property real longitude: Enums.media.map_default_longitude
    property var center: null                   // Optional explicit coordinate override 可选的显式坐标覆盖
    property real zoomLevel: Enums.media.map_default_zoom
    property var activeMapType: null            // Optional injected map type 可选注入的地图类型
    property bool copyrightsVisible: true       // Show the provider copyright notice 显示提供方版权信息
    property var markers: []                    // Marker layer: { latitude, longitude, title } 标记图层
    property var polylines: []                  // Polyline layer: { path: [{ latitude, longitude }] } 折线图层
    property var circles: []                    // Circle layer: { latitude, longitude, radius } 圆图层
    property bool autoActivate: false           // Activate during construction 构造期是否激活
    property bool schedulerActive: true         // Runtime activation gate 运行时激活门控
    property string activationGroup: "map"
    property string unavailableMessage: ""      // Localized fallback text 本地化回退文案

    // ==================== Readonly State 只读状态 ====================
    readonly property bool active: surfaceLoader.status !== Loader.Null
    readonly property bool loading: surfaceLoader.status === Loader.Loading
    readonly property bool surfaceCreated: surfaceLoader.item !== null
    readonly property bool available: _availability === Enums.media.availability_available
    readonly property bool degraded: _availability === Enums.media.availability_unavailable
    readonly property int availabilityState: _availability
    readonly property string errorString: _errorString
    readonly property bool mapReady: _mapReady
    readonly property bool activationQueued: _surfaceActivationQueued
    readonly property bool activationInProgress: _surfaceActivationActive
    readonly property int layerCount: markers.length + polylines.length + circles.length

    // ==================== Internal Props 内部属性 ====================
    property int _availability: Enums.media.availability_unknown
    property string _errorString: ""
    property bool _mapReady: false
    property var _probeComponent: null
    property bool _activationRequested: false
    property bool _surfaceActivationQueued: false
    property bool _surfaceActivationActive: false

    // ==================== Signals 信号 ====================
    signal activated()
    signal availabilityFailed(string message)

    // ==================== Public Methods 公开方法 ====================
    // Incubate the map surface 孵化地图表面
    function activate() {
        _activationRequested = true
        if (!schedulerActive) return false
        if (surfaceLoader.status !== Loader.Null) {
            return available
        }
        if (_availability === Enums.media.availability_unavailable) {
            return _surfaceActivate()
        }
        return SurfaceActivationScheduler.request(control, activationGroup)
    }

    function _surfaceCanActivate() {
        return schedulerActive && _activationRequested
                && surfaceLoader.status === Loader.Null
    }

    function _surfaceActivate() {
        if (!_surfaceCanActivate()) return false
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

    // Move the map centre 移动地图中心
    function setCenter(latitude, longitude) {
        control.center = null
        control.latitude = latitude
        control.longitude = longitude
    }

    // Zoom one step in 放大一档
    function zoomIn() {
        zoomLevel = Math.min(Enums.media.map_max_zoom, zoomLevel + Enums.media.map_zoom_step)
    }

    // Zoom one step out 缩小一档
    function zoomOut() {
        zoomLevel = Math.max(Enums.media.map_min_zoom, zoomLevel - Enums.media.map_zoom_step)
    }

    // Append one marker 追加一个标记
    function addMarker(latitude, longitude, title) {
        markers = markers.concat([{
            "latitude": latitude,
            "longitude": longitude,
            "title": title === undefined ? "" : title
        }])
    }

    // Append one polyline 追加一条折线
    function addPolyline(points, color) {
        polylines = polylines.concat([{
            "path": points,
            "color": color
        }])
    }

    // Append one circle 追加一个圆
    function addCircle(latitude, longitude, radius) {
        circles = circles.concat([{
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius
        }])
    }

    // Remove one marker by index 按下标移除标记
    function removeMarkerAt(index) {
        if (index < 0 || index >= markers.length) {
            return
        }
        markers = markers.slice(0, index).concat(markers.slice(index + 1))
    }

    function clearMarkers() { markers = [] }
    function clearPolylines() { polylines = [] }
    function clearCircles() { circles = [] }

    // Remove every layer 清空全部图层
    function clearLayers() {
        markers = []
        polylines = []
        circles = []
    }

    // ==================== Internal Methods 内部方法 ====================
    // Extract the incubation error text 提取孵化错误文本
    function _surfaceErrorText() {
        if (_probeComponent === null) {
            _probeComponent = Qt.createComponent(surfaceUrl)
            _probeComponent.statusChanged.connect(control._applyProbeStatus)
        }
        return _probeComponent.status === Component.Error
            ? _probeComponent.errorString()
            : "map surface component failed to load"
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
        activated()
    }

    function _onMapReady(value) { _mapReady = value }

    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.controlSize.inputDefaultWidth
    implicitHeight: Enums.controlSize.inputDefaultWidth

    Component.onCompleted: {
        if (autoActivate) {
            activate()
        }
    }

    onSchedulerActiveChanged: {
        if (!schedulerActive) SurfaceActivationScheduler.cancel(control)
        else if (_activationRequested && surfaceLoader.status === Loader.Null) {
            activate()
        }
    }
    Component.onDestruction: SurfaceActivationScheduler.release(control)

    // ==================== Content 内容 ====================
    // Incubated map surface 按需孵化的地图表面
    Loader {
        id: surfaceLoader
        anchors.fill: parent

        // Ready is reported here: an incubated surface runs its own
        // Component.onCompleted before the Loader exposes it to the host.
        // 就绪在这里上报：被孵化的表面自身的 Component.onCompleted 先于宿主可见。
        onLoaded: {
            SurfaceActivationScheduler.release(control)
            control._activationRequested = false
            control._onSurfaceReady()
        }

        onStatusChanged: {
            if (surfaceLoader.status === Loader.Error) {
                SurfaceActivationScheduler.release(control)
                control._activationRequested = false
                control._availability = Enums.media.availability_unavailable
                control._errorString = control._surfaceErrorText()
                control.availabilityFailed(control._errorString)
            }
        }
    }

    // Graceful fallback when the map surface cannot load 地图表面无法加载时的优雅回退
    Loader {
        id: unavailableLoader
        anchors.fill: parent
        active: control.degraded
        sourceComponent: MediaInternal.SurfaceUnavailable {
            host: control
        }
    }
}
