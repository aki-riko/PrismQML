// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../../effects"

// AudioWaveformContent - Waveform visual tree 波形视觉树
// Keeps AudioWaveform focused on public state, normalization and methods.
// 将 AudioWaveform 入口限制为公开状态、归一化逻辑与方法。
ShadowedRectangle {
    id: content

    // ==================== Required Props 必需属性 ====================
    required property var waveformControl

    // ==================== Public Props 公开属性 ====================
    property alias waveformContainer: waveformContainer
    property alias mouseArea: mouseArea

    // ==================== Readonly State 只读状态 ====================
    readonly property bool hovered: mouseArea.containsMouse
    readonly property bool pressed: mouseArea.pressed

    anchors.fill: parent
    color: waveformControl.backgroundColor
    radius: waveformControl._waveformRadius
    border.width: Enums.surfaceBorderWidth(Enums.border.thin)
    border.color: waveformControl._waveformBorderColor
    shadowLevel: waveformControl._hovered ? Enums.shadow.level4 : Enums.shadow.level2

    HoverBehavior on border.color {
        active: waveformControl._hovered && !waveformControl._pressed
        animationEnabled: waveformControl.animated
        enterDuration: Enums.duration.fast
    }

    // ==================== Content 内容 ====================
    // Waveform container 波形容器
    Item {
        id: waveformContainer
        parent: waveformControl
        anchors.fill: parent
        anchors.margins: Enums.spacing.m
        clip: true

        // Progress background overlay 进度背景遮罩
        Rectangle {
            id: progressOverlay
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            width: parent.width * waveformControl._safeProgress
            color: waveformControl._progressOverlayColor
            radius: waveformControl._waveformInnerRadius

            Behavior on width {
                enabled: waveformControl.animated && !mouseArea.pressed
                NumberAnimation { duration: Enums.duration.fast }
            }
        }

        // Waveform bars 波形条
        Item {
            id: waveformBars

            readonly property int _sampleCount: waveformControl._safeWaveformData.length
            readonly property real _pitch: waveformControl._safeBarWidth + waveformControl._safeBarSpacing
            readonly property real _contentWidth:
                _sampleCount > 0
                    ? _sampleCount * waveformControl._safeBarWidth
                      + (_sampleCount - 1) * waveformControl._safeBarSpacing
                    : 0
            readonly property real _viewportLeft:
                Math.max(0, (width - waveformContainer.width) / 2)
            readonly property real _viewportRight:
                Math.min(width, _viewportLeft + waveformContainer.width)
            readonly property int _firstVisibleIndex:
                _sampleCount > 0
                    ? Math.max(0, Math.min(
                        _sampleCount - 1, Math.floor(_viewportLeft / _pitch)
                    )) : 0
            readonly property int _visibleCount:
                _sampleCount > 0
                    ? Math.min(
                        _sampleCount - _firstVisibleIndex,
                        Math.max(0, Math.ceil(
                            (_viewportRight - _firstVisibleIndex * _pitch) / _pitch
                        ) + 1)
                    ) : 0

            objectName: "waveformBars"
            anchors.centerIn: parent
            width: _contentWidth
            height: parent.height

            Repeater {
                model: waveformBars._visibleCount

                Rectangle {
                    id: bar

                    readonly property int _dataIndex:
                        waveformBars._firstVisibleIndex + index
                    readonly property real _positionRatio:
                        waveformControl._safeWaveformData.length > 0
                            ? _dataIndex / waveformControl._safeWaveformData.length : 0
                    readonly property bool _played: bar._positionRatio < waveformControl._safeProgress

                    x: _dataIndex * waveformBars._pitch
                    width: waveformControl._safeBarWidth
                    height: Math.max(
                        Enums.spacing.xs,
                        waveformControl._safeWaveformData[_dataIndex] * waveformBars.height * 0.9
                    )
                    radius: width / 2
                    anchors.verticalCenter: parent.verticalCenter

                    // Gradient based on position and progress 基于位置和进度的渐变
                    gradient: Enums.isVintageTicket ? null
                        : (bar._played ? waveformControl._playedGradient : waveformControl._unplayedGradient)
                    color: _played ? waveformControl.progressColor : waveformControl.waveColor

                    // Subtle glow effect for active bars 活跃条的微妙发光效果
                    opacity: bar._played ? 1.0 : (waveformControl._hovered ? 0.85 : 0.7)

                    // Scale animation on hover 悬停时的缩放动画
                    transform: Scale {
                        origin.x: bar.width / 2
                        origin.y: bar.height / 2
                        xScale: waveformControl._barBaseScale
                            + (waveformControl._barHoverXScale - waveformControl._barBaseScale)
                              * waveformControl._hoverScaleProgress
                        yScale: waveformControl._barBaseScale
                            + (waveformControl._barHoverYScale - waveformControl._barBaseScale)
                              * waveformControl._hoverScaleProgress
                    }

                    HoverBehavior on opacity {
                        active: waveformControl._hovered && !waveformControl._pressed
                        animationEnabled: waveformControl.animated
                        enterDuration: Enums.duration.fast
                    }
                }
            }
        }

        // Progress indicator line 进度指示线
        Rectangle {
            id: progressLine
            visible: waveformControl.showProgressIndicator && waveformControl._safeProgress > 0
            x: parent.width * waveformControl._safeProgress - 1
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.topMargin: Enums.spacing.xs
            anchors.bottomMargin: Enums.spacing.xs
            width: Enums.spacing.xxs
            radius: width / 2
            color: Enums.accentForeground

            // Glow effect 发光效果
            Rectangle {
                anchors.centerIn: parent
                width: Enums.spacing.s
                height: parent.height
                radius: width / 2
                color: Enums.accentColor
                opacity: 0.4
            }

            Behavior on x {
                enabled: waveformControl.animated && !mouseArea.pressed
                NumberAnimation { duration: Enums.duration.fast }
            }
        }

        // Hover position indicator 悬停位置指示器
        Rectangle {
            id: hoverIndicator
            visible: waveformControl._hovered && !waveformControl._pressed
            x: Math.max(0, Math.min(mouseArea.mouseX - parent.anchors.margins - 1, parent.width - 2))
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: Enums.spacing.xxs
            radius: width / 2
            color: Enums.accentColor
            opacity: 0.5
        }
    }

    // Interaction 交互
    MouseArea {
        id: mouseArea
        parent: waveformControl
        anchors.fill: parent
        enabled: waveformControl.enabled
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor

        onClicked: function(mouse) {
            var pos = waveformControl._positionAt(mouse.x)
            waveformControl.progress = pos
            waveformControl.clicked(pos)
            waveformControl.progressUpdated(pos)
        }

        onPositionChanged: function(mouse) {
            if (pressed) {
                var pos = waveformControl._positionAt(mouse.x)
                waveformControl.progress = pos
                waveformControl.progressUpdated(pos)
            }
        }
    }
}
