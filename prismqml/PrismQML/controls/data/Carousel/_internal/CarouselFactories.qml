// CarouselFactories - Carousel dynamic component factories 轮播动态组件工厂
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../FlipView" as FlipViewControls

// CarouselFactories - Keeps creation definitions separate from lifecycle orchestration
// 将创建定义与生命周期编排分离。
Item {
    id: factories

    // ==================== Required Props 必需属性 ====================
    required property var carouselControl

    // ==================== Public Props 公开属性 ====================
    property alias contentAreaComponent: contentAreaComponent
    property alias indicatorComponent: indicatorComponent
    property alias navButtonComponent: navButtonComponent

    // ==================== Size 尺寸 ====================
    width: 0
    height: 0
    visible: false

    // ==================== Content 内容 ====================
    // Content area factory 内容区域工厂
    Component {
        id: contentAreaComponent

        CarouselContent {
            anchors.fill: parent
            model: factories.carouselControl._safeModel
            effect: factories.carouselControl.effect
            orientation: factories.carouselControl.orientation
            currentIndex: factories.carouselControl.currentIndex
            itemDelegate: factories.carouselControl.itemDelegate
            borderRadius: factories.carouselControl._effectiveBorderRadius

            onIndexChanged: (index) => {
                factories.carouselControl.currentIndex = index
                factories.carouselControl.indexChanged(index)
            }
        }
    }

    // Indicator factory 指示器工厂
    Component {
        id: indicatorComponent

        FlipViewControls.PipsPager {
            visible: factories.carouselControl._hasIndicator
            count: factories.carouselControl._modelCount
            currentIndex: factories.carouselControl.currentIndex
            orientation: factories.carouselControl.orientation

            anchors.horizontalCenter: factories.carouselControl.isVertical
                                      ? undefined : parent.horizontalCenter
            anchors.bottom: factories.carouselControl.isVertical
                            ? undefined : parent.bottom
            anchors.bottomMargin: factories.carouselControl.isVertical
                                 ? Enums.spacing.none : Enums.spacing.l
            anchors.verticalCenter: factories.carouselControl.isVertical
                                   ? parent.verticalCenter : undefined
            anchors.right: factories.carouselControl.isVertical
                           ? parent.right : undefined
            anchors.rightMargin: factories.carouselControl.isVertical
                                ? Enums.spacing.l : Enums.spacing.none

            onIndexClicked: (index) => factories.carouselControl.goTo(index)
        }
    }

    // Navigation button factory 导航按钮工厂
    Component {
        id: navButtonComponent

        CarouselNavButton {
            property bool _revealEnabled: false

            visible: factories.carouselControl._navVisible
            opacity: _revealEnabled && factories.carouselControl._navVisible ? 1 : 0
            isVertical: factories.carouselControl.isVertical

            x: factories.carouselControl.isVertical
                ? (parent.width - width) / 2
                : (isNext ? parent.width - width - Enums.spacing.m : Enums.spacing.m)
            y: factories.carouselControl.isVertical
                ? (isNext ? parent.height - height - Enums.spacing.m : Enums.spacing.m)
                : (parent.height - height) / 2

            onClicked: {
                if (isNext) factories.carouselControl.next()
                else factories.carouselControl.previous()
            }

            HoverBehavior on opacity {
                active: _revealEnabled && factories.carouselControl._navVisible
                enterDuration: Enums.duration.fast
            }
        }
    }
}
