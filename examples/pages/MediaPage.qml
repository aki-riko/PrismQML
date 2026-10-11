// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// Import components 导入组件
import PrismQML
import PrismQML as Fluent

// Media components page 媒体组件页面
Item {
    id: root

    ScrollArea {
        anchors.fill: parent

        Column {
            width: parent ? parent.width : 0
            spacing: Fluent.Enums.spacing.xxl

            // Page title 页面标题
            Column {
                width: parent ? parent.width : 0
                spacing: Fluent.Enums.spacing.xs
                Text { text: "Media"; font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
            }

            // WebView2 内嵌浏览器
            ExampleCard {
                title: "WebView2"
                description: "url / autoActivate / available / degraded"
                ComponentCard {
                    label: "embedded browser"
                    Column {
                        spacing: Fluent.Enums.spacing.s
                        WebView2 {
                            id: webViewDemo
                            width: 420
                            height: 220
                        }
                        Text {
                            text: "available: " + webViewDemo.available + " / degraded: " + webViewDemo.degraded
                            color: Fluent.Enums.textColor.secondary
                            font.family: Fluent.Enums.fontFamily
                            font.pixelSize: Fluent.Enums.typography.caption
                        }
                    }
                }
            }

            // MediaPlayerElement 媒体播放面
            ExampleCard {
                title: "MediaPlayerElement"
                description: "source / showControls / volume"
                ComponentCard {
                    label: "media surface"
                    Column {
                        spacing: Fluent.Enums.spacing.s
                        MediaPlayerElement {
                            id: mediaPlayerDemo
                            width: 420
                            height: 220
                            showControls: true
                            volume: 0.5
                        }
                        Text {
                            text: "available: " + mediaPlayerDemo.available + " / loading: " + mediaPlayerDemo.loading
                            color: Fluent.Enums.textColor.secondary
                            font.family: Fluent.Enums.fontFamily
                            font.pixelSize: Fluent.Enums.typography.caption
                        }
                    }
                }
            }

            // MapControl 地图面
            ExampleCard {
                title: "MapControl"
                description: "pluginName / latitude / longitude / zoomLevel"
                ComponentCard {
                    label: "map surface"
                    Column {
                        spacing: Fluent.Enums.spacing.s
                        MapControl {
                            id: mapDemo
                            width: 420
                            height: 260
                            pluginName: "osm"
                            latitude: 31.2304
                            longitude: 121.4737
                            zoomLevel: 10
                        }
                        Text {
                            text: "available: " + mapDemo.available + " / degraded: " + mapDemo.degraded
                            color: Fluent.Enums.textColor.secondary
                            font.family: Fluent.Enums.fontFamily
                            font.pixelSize: Fluent.Enums.typography.caption
                        }
                    }
                }
            }
        }
    }
}
