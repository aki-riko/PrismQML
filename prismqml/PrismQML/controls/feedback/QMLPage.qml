// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../.."
import QtQuick  // Keep native types unprefixed after library import 库导入后保留原生类型无前缀

// QMLPage - Reusable QML loading page matching SplashScreen 可复用的 SplashScreen 同款 QML 加载页
Rectangle {
    id: control

    // ==================== Public Props 公开属性 ====================
    property string text: Translator.tr("loading")  // Loading message 加载提示
    property bool running: visible                  // Run animation while loading 加载时运行动画
    property color backgroundColor: Enums.backgroundColor  // Page background 页面背景

    // ==================== Internal Props 内部属性 ====================
    readonly property int _progressRingSize: Enums.splashScreenMetrics.progressRingSize
    readonly property int _progressRingBorderWidth: Enums.splashScreenMetrics.progressRingBorderWidth
    readonly property real _progressTrackOpacity: Enums.splashScreenMetrics.progressTrackOpacity
    readonly property int _progressDotSize: Enums.splashScreenMetrics.progressDotSize
    readonly property int _progressDotRadius: Enums.splashScreenMetrics.progressDotRadius
    readonly property int _progressDotTopMargin: Enums.splashScreenMetrics.progressDotTopMargin

    color: control.backgroundColor

    // ==================== Content 内容 ====================
    Row {
        anchors.centerIn: parent
        spacing: Enums.spacing.m

        ProgressRing {
            id: progressRing

            objectName: "qmlPageProgressRing"
            anchors.verticalCenter: parent.verticalCenter
            width: control._progressRingSize
            height: control._progressRingSize
            indeterminate: control.running
            indeterminateStyle: Enums.progress.indeterminate_style_orbit_dot
            paused: !control.running
            strokeWidth: control._progressRingBorderWidth
            spinDuration: Enums.duration.splashProgressSpin
            trackColorLight: Qt.rgba(
                Enums.accentColor.r,
                Enums.accentColor.g,
                Enums.accentColor.b,
                control._progressTrackOpacity
            )
            trackColorDark: Qt.rgba(
                Enums.accentColor.r,
                Enums.accentColor.g,
                Enums.accentColor.b,
                control._progressTrackOpacity
            )
            indeterminateDotSize: control._progressDotSize
            indeterminateDotRadius: control._progressDotRadius
            indeterminateDotTopMargin: control._progressDotTopMargin
        }

        Label {
            anchors.verticalCenter: parent.verticalCenter
            text: control.text
            type: Enums.label.type_body
            visible: control.text !== ""
        }
    }
}
