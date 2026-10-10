// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtLocation
import QtPositioning
import "../../.."
import "../../icons"

// MapSurface - QtLocation map surface QtLocation 地图表面
// Loaded lazily by MapControl so the geoservices plugin never starts during
// component construction. 由 MapControl 懒加载，避免构造期启动地理服务插件。
// Tile provider, parameters and map type are always injected by the caller.
// 瓦片提供方、参数与地图类型一律由调用方注入。
Item {
    id: surface

    // ==================== Required Props 必需属性 ====================
    required property Item host

    // ==================== Readonly State 只读状态 ====================
    readonly property var mapItem: mapView

    // ==================== Public Methods 公开方法 ====================
    function requestCenter(latitude, longitude) {
        mapView.center = QtPositioning.coordinate(latitude, longitude)
    }

    // ==================== Internal Methods 内部方法 ====================
    // Injected plugin parameter name 注入的插件参数名
    function _parameterNameAt(index) {
        var parameters = surface.host.pluginParameters
        return parameters && index < parameters.length ? parameters[index].name : ""
    }

    // Injected plugin parameter value 注入的插件参数值
    function _parameterValueAt(index) {
        var parameters = surface.host.pluginParameters
        return parameters && index < parameters.length ? parameters[index].value : undefined
    }

    // ==================== Size 尺寸 ====================
    anchors.fill: parent

    Component.onCompleted: {
        if (surface.host.activeMapType !== null) {
            mapView.activeMapType = surface.host.activeMapType
        }
    }

    // ==================== Content 内容 ====================
    Map {
        id: mapView
        anchors.fill: parent
        center: surface.host.center !== null
            ? surface.host.center
            : QtPositioning.coordinate(surface.host.latitude, surface.host.longitude)
        zoomLevel: surface.host.zoomLevel
        copyrightsVisible: surface.host.copyrightsVisible

        onMapReadyChanged: surface.host._onMapReady(mapReady)

        plugin: Plugin {
            id: mapPlugin
            name: surface.host.pluginName
            PluginParameter { name: surface._parameterNameAt(0); value: surface._parameterValueAt(0) }
            PluginParameter { name: surface._parameterNameAt(1); value: surface._parameterValueAt(1) }
            PluginParameter { name: surface._parameterNameAt(2); value: surface._parameterValueAt(2) }
            PluginParameter { name: surface._parameterNameAt(3); value: surface._parameterValueAt(3) }
        }

        MapItemView {
            id: markerView
            model: surface.host.markers

            delegate: MapQuickItem {
                required property var modelData

                coordinate: QtPositioning.coordinate(modelData.latitude, modelData.longitude)
                anchorPoint.x: Enums.iconSize.xl / 2
                anchorPoint.y: Enums.iconSize.xl

                sourceItem: Item {
                    width: Enums.iconSize.xl
                    height: Enums.iconSize.xl

                    Icon {
                        anchors.fill: parent
                        icon: Enums.icon.location
                        iconSize: Enums.iconSize.xl
                        color: Enums.accentColor
                    }
                }
            }
        }

        MapItemView {
            id: polylineView
            model: surface.host.polylines

            delegate: MapPolyline {
                required property var modelData

                line.width: Enums.border.normal
                line.color: modelData.color !== undefined ? modelData.color : Enums.accentColor
                path: {
                    var points = modelData.path
                    var coordinates = []
                    for (var index = 0; index < points.length; ++index) {
                        coordinates.push(QtPositioning.coordinate(
                            points[index].latitude, points[index].longitude))
                    }
                    return coordinates
                }
            }
        }

        MapItemView {
            id: circleView
            model: surface.host.circles

            delegate: MapCircle {
                required property var modelData

                center: QtPositioning.coordinate(modelData.latitude, modelData.longitude)
                radius: modelData.radius
                color: Enums.withAlpha(Enums.accentColor, Enums.opacityLevel.light)
                border.width: Enums.border.normal
                border.color: Enums.accentColor
            }
        }
    }
}
