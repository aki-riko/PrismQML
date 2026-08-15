// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick as QtQ
import QtQuick.Effects
import QtQuick.Layouts
import "../../.."
import "../../../effects"
import "../../containers/ScrollBar"
import QtQuick

// DataWidgetContent - Data widget visual and scrolling content 数据组件视觉与滚动内容
Item {
    id: contentLayer

    // ==================== Required Props 必需属性 ====================
    required property var dataControl

    // ==================== Public Props 公开属性 ====================
    property alias listView: listView
    property alias contentDelegate: listView.delegate
    property alias listModel: listView.model
    property alias spacing: listView.spacing
    property alias scrollViewportState: scrollViewportState
    property alias scrollHelper: scrollHelper
    property alias card: card
    property alias headerLoader: headerLoader
    property alias contentArea: contentArea
    readonly property alias needsVerticalScrollBar: scrollViewportState.needsVertical
    readonly property alias needsHorizontalScrollBar: scrollViewportState.needsHorizontal
    readonly property alias reserveVerticalScrollBarGutter:
        scrollViewportState.reserveVerticalGutter
    readonly property alias reserveHorizontalScrollBarGutter:
        scrollViewportState.reserveHorizontalGutter

    // ==================== Readonly State 只读状态 ====================
    readonly property var control: dataControl

    // ==================== Public Methods 公开方法 ====================
    function createHorizontalScrollMixin() {
        return horizontalScrollMixinComponent.createObject(contentArea)
    }

    anchors.fill: parent

    // Wheel handler 滚轮处理
    MouseArea {
        id: wheelArea

        anchors.fill: parent
        acceptedButtons: Qt.NoButton
        hoverEnabled: control.hoverElevation

        onWheel: (event) => {
            if (listView.contentHeight <= listView.height) {
                event.accepted = false
                return
            }
            scrollHelper.scrollBy(-event.angleDelta.y / 120 * scrollHelper.step)
            event.accepted = true
        }
    }

    // Shadow 阴影
    RectangularShadow {
        id: shadowEffect

        // Active shadow fallback lifecycle 主动阴影兜底生命周期
        // Enums._metrics may be destroyed before this shadow during engine teardown.
        // 引擎销毁期间，Enums._metrics 可能先于当前阴影对象销毁。
        // Cache the public token after construction so teardown no longer reads the singleton.
        // 构造完成后缓存公开 token，销毁期不再读取 singleton。
        property var _staticFallbackShadow: null
        property var _resolvedLevel: control.hoverElevation && wheelArea.containsMouse
                                   ? (Enums.shadow ? Enums.shadow.level4 : null)
                                   : control.shadowLevel
        property var _activeLevel: _resolvedLevel
                                 || (Enums.shadow ? Enums.shadow.level2 : null)
                                 || _staticFallbackShadow

        anchors.fill: card
        radius: card.radius
        visible: control.showShadow && Enums.usesSoftElevation && !Enums.isNeumorphism

        Component.onCompleted: _staticFallbackShadow = ({
            color: Enums.transparent,
            blur: 0,
            offset: 0
        })

        color: _activeLevel && _activeLevel.color !== undefined
               ? _activeLevel.color
               : (_staticFallbackShadow ? _staticFallbackShadow.color : Enums.transparent)
        blur: _activeLevel && _activeLevel.blur !== undefined
              ? _activeLevel.blur
              : (_staticFallbackShadow ? _staticFallbackShadow.blur : 0)
        offset.x: 0
        offset.y: _activeLevel && _activeLevel.offset !== undefined
                  ? _activeLevel.offset
                  : (_staticFallbackShadow ? _staticFallbackShadow.offset : 0)

        HoverBehavior on blur {
            active: wheelArea.containsMouse
            animationEnabled: control.animated && control.hoverElevation
            enterDuration: Enums.duration.elevation
            easingType: Easing.OutCubic
        }
        HoverBehavior on offset {
            active: wheelArea.containsMouse
            animationEnabled: control.animated && control.hoverElevation
            enterDuration: Enums.duration.elevation
            easingType: Easing.OutCubic
        }
    }

    NeumorphicShadow {
        target: card
        visible: control.showShadow && Enums.isNeumorphism
        z: card.z - 1
    }

    // Neo hard shadow Neo 硬阴影
    NeoShadow {
        target: card
        visible: control.showShadow && Enums.isNeobrutalism
        z: card.z - 1
    }

    // Card container 卡片容器
    Rectangle {
        id: card

        anchors.fill: parent
        anchors.margins: control.cardMargin
        color: control.cardColor
        radius: control._effectiveBorderRadius
        // Neo thick border Neo 粗黑边
        border.width: Enums.hasOutlinedSurfaces
                      ? Enums.surfaceBorderWidth(Enums.border.thin)
                      : (control.borderVisible ? Enums.border.thin : 0)
        border.color: Enums.hasOutlinedSurfaces
                      ? Enums.stateColor.border
                      : (control.borderVisible
                         ? Enums.stateColor.borderLight : Enums.transparent)

        Loader {
            anchors.fill: parent
            active: Enums.isVintageTicket && card.color.a > 0
            source: Qt.resolvedUrl("../../../effects/TicketPaper.qml")
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Enums.spacing.micro
            spacing: Enums.spacing.none

            // Header 表头
            Rectangle {
                Layout.fillWidth: true
                height: control.headerHeight
                color: control.headerColor
                radius: control._effectiveBorderRadius
                visible: control.showHeader

                // Bottom half fill 底部半圆填充
                Rectangle {
                    anchors.bottom: parent.bottom
                    width: parent.width
                    height: parent.height / 2
                    color: parent.color
                }

                // Header content loader 表头内容加载器
                // 横向滚动激活时，mixin 自动绑定 headerLoader.x = -listView.contentX。
                Item {
                    anchors.fill: parent
                    clip: true

                    Loader {
                        id: headerLoader

                        y: 0
                        width: control.contentTotalWidth > listView.width
                               ? control.contentTotalWidth : listView.width
                        height: parent.height
                        sourceComponent: control.headerContent
                    }
                }
            }

            // Header separator 表头分隔线
            Rectangle {
                Layout.fillWidth: true
                height: Enums.border.thin
                color: control.borderColor
                visible: control.showHeader
            }

            // Header floating shadow 表头浮起阴影
            Rectangle {
                Layout.fillWidth: true
                height: 4
                visible: !Enums.isVintageTicket && control.showHeader
                         && listView.contentY > 0
                opacity: Math.min(1, listView.contentY / 20)
                gradient: Gradient {
                    GradientStop {
                        position: 0
                        color: control._headerEdgeShadowColor
                    }
                    GradientStop { position: 1; color: Enums.transparent }
                }

                Behavior on opacity {
                    enabled: control.animated
                    NumberAnimation { duration: Enums.duration.fast }
                }
            }

            // Body (constant stretch container) 主体区（恒定伸缩容器）
            // contentArea / emptyArea / skeletonArea 三者互斥，原先各自用
            // Layout.fillHeight 绑定 itemCount/loading 时会在 ColumnLayout 里抢高度。
            // QtQuick.Layouts 不会在 fillHeight 绑定值异步变化时重新分配尺寸，
            // 因此使用恒定 fillHeight 容器，内部三区通过 anchors 和 visible 切换。
            Item {
                id: bodyContainer

                Layout.fillWidth: true
                Layout.fillHeight: true

                // Content area 内容区域
                Item {
                    id: contentArea

                    anchors.fill: parent
                    visible: control.itemCount > 0 || control.loading
                    opacity: control.loading ? 0 : 1

                    Behavior on opacity {
                        enabled: control.animated
                        NumberAnimation {
                            duration: Enums.duration.enter
                            easing.type: Easing.OutCubic
                        }
                    }

                    QtQ.ListView {
                        id: listView

                        anchors.fill: parent
                        anchors.rightMargin: control._reserveVerticalScrollBarGutter
                            ? Math.min(control._scrollBarGutter,
                                       Math.max(0, parent.width)) : 0
                        anchors.bottomMargin: control._reserveHorizontalScrollBarGutter
                            ? Math.min(control._scrollBarGutter,
                                       Math.max(0, parent.height)) : 0
                        clip: true
                        boundsBehavior: Flickable.DragAndOvershootBounds
                        interactive: false
                        cacheBuffer: 600
                        reuseItems: true
                        contentWidth: control.contentTotalWidth > width
                                      ? control.contentTotalWidth : width

                        // Transitions 过渡动画
                        add: Transition {
                            enabled: control.animated
                            ParallelAnimation {
                                NumberAnimation {
                                    property: "opacity"
                                    from: 0
                                    to: 1
                                    duration: Enums.duration.enter
                                    easing.type: Easing.OutCubic
                                }
                                NumberAnimation {
                                    property: "y"
                                    from: listView.contentY + 12
                                    duration: Enums.duration.enter
                                    easing.type: Easing.OutCubic
                                }
                            }
                        }

                        remove: Transition {
                            enabled: control.animated
                            ParallelAnimation {
                                NumberAnimation {
                                    property: "opacity"
                                    to: 0
                                    duration: Enums.duration.exit
                                    easing.type: Easing.InCubic
                                }
                                NumberAnimation {
                                    property: "x"
                                    to: 40
                                    duration: Enums.duration.exit
                                    easing.type: Easing.InCubic
                                }
                            }
                        }

                        displaced: Transition {
                            enabled: control.animated
                            NumberAnimation {
                                properties: "y"
                                duration: Enums.duration.medium
                                easing.type: Easing.OutQuart
                            }
                        }
                    }

                    ScrollViewportState {
                        id: scrollViewportState

                        target: listView
                        scrollBarsEnabled: control.showScrollBar
                        verticalEnabled: true
                        horizontalEnabled: true
                        itemCount: control.itemCount
                    }

                    // Smooth scroll helper 平滑滚动助手
                    SmoothScrollHelper {
                        id: scrollHelper

                        target: listView
                        orientation: Qt.Vertical
                        enabled: control.smoothScroll
                        duration: control.scrollDuration
                        step: control.scrollStep
                        easing: control.scrollEasing
                        bounceEnabled: true
                    }

                    // Custom scrollbar 自定义滚动条
                    ScrollBar {
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        anchors.rightMargin: Enums.spacing.xxs
                        anchors.bottomMargin: control._reserveHorizontalScrollBarGutter
                            ? Math.min(control._scrollBarGutter,
                                       Math.max(0, parent.height)) : 0

                        target: listView
                        scrollHelper: scrollHelper
                        orientation: Qt.Vertical
                        barWidth: Math.max(0, control.scrollBarWidth)
                        visible: control._needsVerticalScrollBar
                        z: Enums.zIndex.controlsAbove
                    }

                    // Horizontal scroll mixin 横向滚动
                    // mixin 内部封装横向滚动助手、滚动条与 Shift+wheel 路由。
                    Component {
                        id: horizontalScrollMixinComponent

                        HorizontalScrollMixin {
                            target: listView
                            headerContainer: headerLoader
                            smoothScroll: control.smoothScroll
                            scrollDuration: control.scrollDuration
                            scrollStep: control.scrollStep
                            scrollEasing: control.scrollEasing
                            barWidth: Math.max(0, control.scrollBarWidth)
                            showScrollBar: control.showScrollBar
                            rightInset: control._reserveVerticalScrollBarGutter
                                ? Math.min(control._scrollBarGutter,
                                           Math.max(0, contentArea.width)) : 0
                        }
                    }
                }

                // Empty state 空状态
                Item {
                    id: emptyArea

                    anchors.fill: parent
                    visible: control.itemCount === 0 && !control.loading
                    opacity: visible ? 1 : 0
                    scale: visible ? 1 : 0.95

                    Behavior on opacity {
                        enabled: control.animated
                        NumberAnimation {
                            duration: Enums.duration.enter
                            easing.type: Easing.OutCubic
                        }
                    }
                    Behavior on scale {
                        enabled: control.animated
                        NumberAnimation {
                            duration: Enums.duration.enter
                            easing.type: Easing.OutCubic
                        }
                    }

                    Label {
                        anchors.centerIn: parent
                        type: Enums.label.type_body
                        text: control.emptyText
                        color: control.secondaryColor
                    }
                }

                // Loading skeleton 骨架屏
                Item {
                    id: skeletonArea

                    anchors.fill: parent
                    visible: control.loading
                    opacity: control.loading ? 1 : 0

                    Behavior on opacity {
                        enabled: control.animated
                        NumberAnimation {
                            duration: Enums.duration.enter
                            easing.type: Easing.OutCubic
                        }
                    }

                    Column {
                        anchors.fill: parent
                        anchors.margins: Enums.spacing.m
                        spacing: Enums.spacing.s

                        Repeater {
                            model: control.loading ? Math.min(
                                5,
                                Math.max(3, Math.floor(
                                    (skeletonArea.height - Enums.spacing.m * 2)
                                    / (control.rowHeight + Enums.spacing.s)
                                ))
                            ) : 0

                            Skeleton {
                                width: parent ? parent.width : 0
                                height: control.rowHeight - Enums.spacing.s
                                loading: control.loading
                            }
                        }
                    }
                }
            }

            // Footer 底栏
            Rectangle {
                id: footerBar

                Layout.fillWidth: true
                height: Enums.controlSize.inputHeightCompact
                color: control.headerColor
                radius: control._effectiveBorderRadius
                visible: control.showFooter && control.itemCount > 0
                opacity: visible ? 1 : 0

                Behavior on opacity {
                    enabled: control.animated
                    NumberAnimation {
                        duration: Enums.duration.normal
                        easing.type: Easing.OutCubic
                    }
                }

                // Top half fill 顶部半圆填充
                Rectangle {
                    anchors.top: parent.top
                    width: parent.width
                    height: parent.height / 2
                    color: parent.color
                }

                Label {
                    anchors.centerIn: parent
                    type: Enums.label.type_caption
                    text: control.footerText
                          ? control.footerText.replace("{count}", control.itemCount)
                          : Enums.trCount("total_items", control.itemCount)
                    font.pixelSize: Enums.typography.captionCompact
                    color: control.secondaryColor
                }
            }
        }
    }
}
