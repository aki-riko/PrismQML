// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import ".."
import "../effects"

// WindowIcon - Reusable window icon component 可复用的窗口图标组件
Item {
    id: root

    property string source: ""
    property bool colored: false
    property bool deferLoad: false
    property var profileTarget: null

    property bool _deferredLoadReady: !deferLoad
    readonly property string _activeSource: _deferredLoadReady ? source : ""
    readonly property bool _hasActiveSource: _activeSource !== ""
    readonly property real _dpr: Screen.devicePixelRatio || 1.0
    readonly property int _physicalSize: Math.ceil(Enums.window.titleIconSize * _dpr)
    readonly property bool _isSvg: _activeSource.toLowerCase().endsWith(".svg")
    readonly property string _svgSource: {
        if (_activeSource === "") return ""
        let normalizedSource = _activeSource.replace(/\\/g, "/")
        if (!normalizedSource.toLowerCase().endsWith(".svg")) return ""
        let lowerSource = normalizedSource.toLowerCase()
        if (lowerSource.startsWith("file:") || lowerSource.startsWith("qrc:")) {
            return "image://svg/" + normalizedSource
        }
        return "image://svg/" + encodeURIComponent(normalizedSource)
    }
    readonly property string _directSource: {
        if (_activeSource === "") return ""
        let normalizedSource = _activeSource.replace(/\\/g, "/")
        if (normalizedSource.toLowerCase().endsWith(".svg")) return ""
        if (normalizedSource.startsWith("qrc:/") || normalizedSource.startsWith(":/")) {
            return normalizedSource.startsWith(":/") ? "qrc" + normalizedSource : normalizedSource
        }
        if (normalizedSource.startsWith("file:///")) {
            return normalizedSource
        }
        return "file:///" + normalizedSource
    }

    function _scheduleDeferredLoad() {
        if (!deferLoad) {
            _deferredLoadReady = true
            return
        }
        _deferredLoadReady = false
        if (source !== "") {
            deferredLoadTimer.restart()
        }
    }

    width: Enums.window.titleIconSize
    height: Enums.window.titleIconSize
    visible: source !== ""

    onSourceChanged: _scheduleDeferredLoad()
    onDeferLoadChanged: _scheduleDeferredLoad()

    Component.onCompleted: {
        _scheduleDeferredLoad()
        if (profileTarget && profileTarget.profileDetail) {
            profileTarget.profileDetail("WindowIcon root completed sourceSet=" + (source !== "") +
                                        " activeSourceSet=" + _hasActiveSource +
                                        " colored=" + colored +
                                        " deferLoad=" + deferLoad)
        }
    }

    Timer {
        id: deferredLoadTimer
        interval: Enums.window.iconDeferredLoadDelayMs
        repeat: false
        onTriggered: {
            root._deferredLoadReady = true
            if (root.profileTarget && root.profileTarget.profileDetail) {
                root.profileTarget.profileDetail("WindowIcon deferred source activated sourceSet=" + (root.source !== ""))
            }
        }
    }

    Image {
        id: svgImage
        anchors.fill: parent
        source: root._svgSource
        visible: root._hasActiveSource && root._isSvg
        fillMode: Image.PreserveAspectFit
        sourceSize: Qt.size(Enums.window.iconRenderSize, Enums.window.iconRenderSize)
        asynchronous: true
        cache: true
        smooth: true
        mipmap: true
        Component.onCompleted: {
            if (root.profileTarget && root.profileTarget.profileDetail) {
                root.profileTarget.profileDetail("WindowIcon svg Image completed status=" + status + " sourceSet=" + (source !== ""))
            }
        }
        onStatusChanged: {
            if (root.profileTarget && root.profileTarget.profileDetail) {
                root.profileTarget.profileDetail("WindowIcon svg Image status=" + status)
            }
        }

        layer.enabled: !root.colored
        layer.effect: ColorOverlay {
            color: Enums.textColor.primary
        }
    }

    Image {
        id: directImage
        anchors.fill: parent
        source: root._directSource
        visible: root._hasActiveSource && !root._isSvg
        fillMode: Image.PreserveAspectFit
        sourceSize: Qt.size(root._physicalSize, root._physicalSize)
        asynchronous: true
        cache: true
        smooth: true
        mipmap: true
        Component.onCompleted: {
            if (root.profileTarget && root.profileTarget.profileDetail) {
                root.profileTarget.profileDetail("WindowIcon direct Image completed status=" + status + " sourceSet=" + (source !== ""))
            }
        }
        onStatusChanged: {
            if (root.profileTarget && root.profileTarget.profileDetail) {
                root.profileTarget.profileDetail("WindowIcon direct Image status=" + status)
            }
        }
    }
}
