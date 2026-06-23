// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../.."
import "../../../effects"
import "../FlipView"
import "_internal"

// Carousel - Carousel component 轮播组件
// 两个正交维度：
//   effect      视觉效果 — effect_peek(Fluent slide+peek 露边,默认) / effect_slide(普通整图滑动)
//   orientation 方向     — Qt.Horizontal(默认) / Qt.Vertical
Item {
    id: control

    // Effect 视觉效果：effect_peek(默认) / effect_slide
    property int effect: Enums.carousel.effect_peek

    // Orientation 方向：Qt.Horizontal(水平) / Qt.Vertical(垂直)
    // 对齐项目惯例(ScrollBar / ChatMessageList / ExampleCard)。
    property int orientation: Qt.Horizontal
    
    // Data Props 数据属性
    property var model: []
    property int currentIndex: 0
    
    // Custom item delegate 自定义内容代理
    // When set, replaces the built-in image/color/text rendering with the
    // provided Component. The delegate root may read the per-page payload via
    // the contextual `itemData` property exposed by the host Loader.
    // 设置后将替换内置 image/color/text 渲染逻辑；delegate 根项可通过宿主 Loader 暴露的
    // 上下文属性 itemData 读取每页数据。
    property Component itemDelegate: null
    
    // Visual Props 视觉属性
    // Border radius for content clipping. 0 为不裁剪；非 0 时内部使用 MultiEffect mask 实现圆角裁剪。
    property real borderRadius: 0
    // Shadow level. 传入 Enums.shadow.levelN 启用阴影；null 为无阴影。
    property var shadowLevel: null
    
    // Feature Props 功能属性
    property bool autoPlay: false
    property int interval: Enums.duration.notification  // 5000ms
    property bool loop: true
    property bool showIndicator: true
    property bool showNavButtons: true
    property int navButtonPosition: Enums.carousel.nav_inside
    // Pause auto-play while the pointer hovers the carousel (or its nav buttons).
    // 鼠标悬停轮播（或导航按钮）时暂停自动播放，避免读图时被强行翻页。
    property bool pauseOnHover: true
    
    // Signals 信号
    signal indexChanged(int index)
    
    // Internal 内部属性
    readonly property bool isVertical: orientation === Qt.Vertical
    readonly property int _modelCount: model ? model.length : 0
    // 指针是否位于 Carousel 范围内（含 itemDelegate 的子元素、导航按钮）。
    // 用 HoverHandler 判定：传统 MouseArea 的 containsMouse 会被子元素自带的 hover MouseArea
    //   「偷走」（停在 delegate 里的按钮上时变 false），导致悬停子元素时自动播放又恢复。
    readonly property bool _isHovered: rootHover.hovered
    readonly property bool _navVisible: showNavButtons && _modelCount > 1 && _isHovered

    // ==================== Public Methods 公开方法 ====================
    function next() {
        if (_modelCount === 0) return
        if (loop) {
            currentIndex = (currentIndex + 1) % _modelCount
        } else if (currentIndex < _modelCount - 1) {
            currentIndex++
        }
        contentArea.setIndex(currentIndex)
    }

    function previous() {
        if (_modelCount === 0) return
        if (loop) {
            currentIndex = (currentIndex - 1 + _modelCount) % _modelCount
        } else if (currentIndex > 0) {
            currentIndex--
        }
        contentArea.setIndex(currentIndex)
    }

    function goTo(index) {
        if (index >= 0 && index < _modelCount) {
            currentIndex = index
            contentArea.setIndex(currentIndex)
        }
    }

    // Set current index 设置当前索引
    function setCurrentIndex(idx) { goTo(idx) }
    function getCurrentIndex() { return currentIndex }

    // Size 尺寸
    implicitWidth: Enums.controlSize.carouselDefaultWidth
    implicitHeight: Enums.controlSize.carouselDefaultHeight

    // ==================== Hover & Wheel Area 悬停和滚轮区域 ====================
    // HoverHandler：passive 检测指针是否在 Carousel 内（含子元素），不消费事件 →
    //   delegate 里的按钮、指示器、导航按钮仍可正常点击；悬停任意子元素都计入 _isHovered。
    HoverHandler {
        id: rootHover
    }

    MouseArea {
        id: hoverArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton

        onWheel: (wheel) => {
            // Use angleDelta.y for both horizontal and vertical carousel 统一使用angleDelta.y处理滚轮

            if (wheel.angleDelta.y > 0) {
                control.previous()
            } else if (wheel.angleDelta.y < 0) {
                control.next()
            }
        }
    }
    
    // ==================== Shadow Layer 阴影层（在内容后面，不影响布局） ====================
    // Fluent: 模糊阴影; neo: 硬阴影(同样 opt-in, 仅 shadowLevel 设置时显示)
    RectangularShadow {
        anchors.fill: contentArea
        visible: control.shadowLevel !== null && control.shadowLevel !== undefined && !Enums.isNeobrutalism
        radius: control.borderRadius
        color: control.shadowLevel ? control.shadowLevel.color : "transparent"
        blur: control.shadowLevel ? control.shadowLevel.blur : 0
        offset.x: 0
        offset.y: control.shadowLevel ? control.shadowLevel.offset : 0
    }

    NeoShadow {
        target: contentArea
        visible: Enums.isNeobrutalism && control.shadowLevel !== null && control.shadowLevel !== undefined
        radius: control.borderRadius
        z: contentArea.z - 1
    }

    // ==================== Content Area 内容区域 ====================
    CarouselContent {
        id: contentArea
        anchors.fill: parent
        model: control.model
        effect: control.effect
        orientation: control.orientation
        currentIndex: control.currentIndex
        itemDelegate: control.itemDelegate
        borderRadius: control.borderRadius
        
        onIndexChanged: (index) => {
            control.currentIndex = index
            control.indexChanged(index)
        }
    }
    
    // ==================== Indicator (PipsPager) 指示器 ====================
    HorizontalPipsPager {
        id: hIndicator
        visible: control.showIndicator && control._modelCount > 1 && !control.isVertical
        count: control._modelCount
        currentIndex: control.currentIndex
        
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: Enums.spacing.l
        
        onIndexClicked: (index) => control.goTo(index)
    }
    
    VerticalPipsPager {
        id: vIndicator
        visible: control.showIndicator && control._modelCount > 1 && control.isVertical
        count: control._modelCount
        currentIndex: control.currentIndex
        
        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right
        anchors.rightMargin: Enums.spacing.l
        
        onIndexClicked: (index) => control.goTo(index)
    }

    // ==================== Navigation Buttons 导航按钮 ====================
    // Prev button (horizontal left, vertical top) 上一个按钮（水平左侧，垂直顶部）

    CarouselNavButton {
        id: prevButton
        visible: control._navVisible
        opacity: control._navVisible ? 1.0 : 0.0
        isNext: false
        isVertical: control.isVertical
        
        // Position based on orientation 根据方向定位
        x: control.isVertical ? (parent.width - width) / 2 : Enums.spacing.m
        y: control.isVertical ? Enums.spacing.m : (parent.height - height) / 2
        
        Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
        
        onClicked: control.previous()
    }
    
    // Next button (horizontal right, vertical bottom) 下一个按钮（水平右侧，垂直底部）

    CarouselNavButton {
        id: nextButton
        visible: control._navVisible
        opacity: control._navVisible ? 1.0 : 0.0
        isNext: true
        isVertical: control.isVertical
        
        // Position based on orientation 根据方向定位
        x: control.isVertical ? (parent.width - width) / 2 : (parent.width - width - Enums.spacing.m)
        y: control.isVertical ? (parent.height - height - Enums.spacing.m) : (parent.height - height) / 2
        
        Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
        
        onClicked: control.next()
    }
    
    // ==================== Auto Play Timer 自动播放定时器 ====================
    // pauseOnHover=true 时，指针悬停轮播会暂停自动翻页（移开后自动恢复）。
    Timer {
        running: control.autoPlay && control._modelCount > 1 &&
                 !(control.pauseOnHover && control._isHovered)
        repeat: true
        interval: control.interval
        onTriggered: control.next()
    }
}
