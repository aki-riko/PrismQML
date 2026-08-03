// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../.."
import "../../../effects"
import "../FlipView" as FlipViewControls
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

    readonly property var _safeModel:
        model === null || model === undefined ? []
        : (typeof model.length === "number" ? model : [])
    
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
    
    // Internal 内部属性
    readonly property bool isVertical: orientation === Qt.Vertical
    readonly property int _modelCount: (_safeModel || []).length
    readonly property bool _needsContentArea:
        _modelCount > 0 || (shadowLevel !== null && shadowLevel !== undefined)
    readonly property bool _hasIndicator: showIndicator && _modelCount > 1
    readonly property bool _hasNavButtons: showNavButtons && _modelCount > 1
    // 指针是否位于 Carousel 范围内（含 itemDelegate 的子元素、导航按钮）。
    // 用 HoverHandler 判定：传统 MouseArea 的 containsMouse 会被子元素自带的 hover MouseArea
    //   「偷走」（停在 delegate 里的按钮上时变 false），导致悬停子元素时自动播放又恢复。
    readonly property bool _isHovered: rootHover.hovered
    readonly property bool _navVisible: _hasNavButtons && _isHovered
    property Item _contentArea: null
    property Item _indicator: null
    property Item _prevNavButton: null
    property Item _nextNavButton: null

    // Signals 信号
    signal indexChanged(int index)

    // ==================== Public Methods 公开方法 ====================
    function next() {
        if (_modelCount === 0) return
        if (loop) {
            currentIndex = (currentIndex + 1) % _modelCount
        } else if (currentIndex < _modelCount - 1) {
            currentIndex++
        }
        if (_contentArea) _contentArea.setIndex(currentIndex)
    }

    function previous() {
        if (_modelCount === 0) return
        if (loop) {
            currentIndex = (currentIndex - 1 + _modelCount) % _modelCount
        } else if (currentIndex > 0) {
            currentIndex--
        }
        if (_contentArea) _contentArea.setIndex(currentIndex)
    }

    function goTo(index) {
        if (index >= 0 && index < _modelCount) {
            currentIndex = index
            if (_contentArea) _contentArea.setIndex(currentIndex)
        }
    }

    // Set current index 设置当前索引
    function setCurrentIndex(idx) { goTo(idx) }
    function getCurrentIndex() { return currentIndex }

    // ==================== Internal Methods 内部方法 ====================
    function _createNavButtons() {
        if (_prevNavButton && _nextNavButton) return
        _destroyNavButtons()

        const previous = navButtonComponent.createObject(control, { "isNext": false })
        const following = navButtonComponent.createObject(control, { "isNext": true })
        if (!previous || !following) {
            if (previous) previous.destroy()
            if (following) following.destroy()
            console.error("Carousel: failed to create navigation buttons")
            return
        }

        _prevNavButton = previous
        _nextNavButton = following
        previous._revealEnabled = true
        following._revealEnabled = true
    }

    function _destroyNavButtons() {
        const previous = _prevNavButton
        const following = _nextNavButton
        _prevNavButton = null
        _nextNavButton = null
        _retireNavButton(previous)
        _retireNavButton(following)
    }

    function _retireNavButton(button) {
        if (!button) return
        button.visible = false
        button.x = Enums.spacing.none
        button.y = Enums.spacing.none
        button.parent = null
        button.destroy()
    }

    function _syncNavButtons() {
        if (_hasNavButtons) _createNavButtons()
        else _destroyNavButtons()
    }

    function _createIndicator() {
        if (_indicator) return
        const indicator = indicatorComponent.createObject(control)
        if (!indicator) {
            console.error("Carousel: failed to create indicator")
            return
        }
        _indicator = indicator
    }

    function _destroyIndicator() {
        const indicator = _indicator
        _indicator = null
        if (!indicator) return
        indicator.visible = false
        indicator.destroy()
    }

    function _syncIndicator() {
        if (_hasIndicator) _createIndicator()
        else _destroyIndicator()
    }

    function _createContentArea() {
        if (_contentArea) return
        const area = contentAreaComponent.createObject(control)
        if (!area) {
            console.error("Carousel: failed to create content area")
            return
        }
        _contentArea = area
    }

    function _syncContentArea() {
        if (_needsContentArea) _createContentArea()
    }

    // Size 尺寸
    implicitWidth: Enums.controlSize.carouselDefaultWidth
    implicitHeight: Enums.controlSize.carouselDefaultHeight

    on_NeedsContentAreaChanged: _syncContentArea()
    on_HasIndicatorChanged: _syncIndicator()
    on_HasNavButtonsChanged: _syncNavButtons()

    // ==================== Content 内容 ====================
    // Hover and wheel area 悬停和滚轮区域
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
    
    // Shadow layer 阴影层（在内容后面，不影响布局）
    // Fluent: 模糊阴影; neo: 硬阴影(同样 opt-in, 仅 shadowLevel 设置时显示)
    RectangularShadow {
        // Active shadow fallback lifecycle 主动阴影兜底生命周期
        // Enums._metrics may be destroyed before this shadow during engine teardown.
        // 引擎销毁期间，Enums._metrics 可能先于当前阴影对象销毁。
        // Cache the public token after construction so teardown no longer reads the singleton.
        // 构造完成后缓存公开 token，销毁期不再读取 singleton。
        property var _staticFallbackShadow: null
        property var _activeLevel: control.shadowLevel || _staticFallbackShadow

        anchors.fill: control._contentArea
        visible: control._contentArea !== null &&
                 control.shadowLevel !== null &&
                 control.shadowLevel !== undefined &&
                 !Enums.isNeobrutalism
        radius: control.borderRadius

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
    }

    NeoShadow {
        target: control._contentArea
        visible: control._contentArea !== null &&
                 Enums.isNeobrutalism &&
                 control.shadowLevel !== null &&
                 control.shadowLevel !== undefined
        radius: control.borderRadius
        z: control._contentArea ? control._contentArea.z - 1 : 0
    }

    // Content area factory 内容区域工厂
    Component {
        id: contentAreaComponent

        CarouselContent {
            anchors.fill: parent
            model: control._safeModel
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
    }
    
    // Indicator factory 指示器工厂
    Component {
        id: indicatorComponent

        FlipViewControls.PipsPager {
            visible: control._hasIndicator
            count: control._modelCount
            currentIndex: control.currentIndex
            orientation: control.orientation

            anchors.horizontalCenter: control.isVertical ? undefined : parent.horizontalCenter
            anchors.bottom: control.isVertical ? undefined : parent.bottom
            anchors.bottomMargin: control.isVertical ? Enums.spacing.none : Enums.spacing.l
            anchors.verticalCenter: control.isVertical ? parent.verticalCenter : undefined
            anchors.right: control.isVertical ? parent.right : undefined
            anchors.rightMargin: control.isVertical ? Enums.spacing.l : Enums.spacing.none

            onIndexClicked: (index) => control.goTo(index)
        }
    }

    // Navigation button factory 导航按钮工厂
    Component {
        id: navButtonComponent

        CarouselNavButton {
            property bool _revealEnabled: false

            visible: control._navVisible
            opacity: _revealEnabled && control._navVisible ? 1 : 0
            isVertical: control.isVertical

            x: control.isVertical
                ? (parent.width - width) / 2
                : (isNext ? parent.width - width - Enums.spacing.m : Enums.spacing.m)
            y: control.isVertical
                ? (isNext ? parent.height - height - Enums.spacing.m : Enums.spacing.m)
                : (parent.height - height) / 2

            Behavior on opacity {
                NumberAnimation { duration: Enums.duration.fast }
            }

            onClicked: {
                if (isNext) control.next()
                else control.previous()
            }
        }
    }
    
    // Auto play timer 自动播放定时器
    // pauseOnHover=true 时，指针悬停轮播会暂停自动翻页（移开后自动恢复）。
    Timer {
        running: control.autoPlay && control._modelCount > 1 &&
                 !(control.pauseOnHover && control._isHovered)
        repeat: true
        interval: control.interval
        onTriggered: control.next()
    }
}
