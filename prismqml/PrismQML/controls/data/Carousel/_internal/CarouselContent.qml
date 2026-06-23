// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick.Effects
import "../../../.."
import "../../../data"
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// CarouselContent - Carousel content area module 轮播内容区域模块
// Peek 模式采用 Fluent 商店式 "slide + 两侧 peek" 范式：中心项满显，
// 左右(垂直则上下)露出相邻项缩放半透明的边缘，翻页时整条带子平滑滑动归位，
// 图片全程不变形(保持纵横比)。
Item {
    id: control

    // ==================== Required Props 必需属性 ====================
    required property var model
    required property int effect
    required property int orientation
    required property int currentIndex

    // ==================== Optional Props 可选属性 ====================
    // Custom item delegate. When non-null, used instead of the built-in
    // image/color/text content component. The delegate root receives the
    // per-page payload through the host Loader's contextual `itemData`.
    // 自定义页内容代理；非空时替代内置 image/color/text 渲染。
    property Component itemDelegate: null

    // Border radius for content area; 0 disables the rounded mask.
    // 内容区域圆角半径；0 表示不启用圆角 mask。
    property real borderRadius: 0

    // ==================== Signals 信号 ====================
    signal indexChanged(int index)

    // ==================== Internal 内部属性 ====================
    readonly property bool isVertical: orientation === Qt.Vertical

    clip: true

    // Rounded corner mask via MultiEffect (project convention) 项目统一范式的圆角 mask
    layer.enabled: control.borderRadius > 0
    layer.smooth: true
    layer.effect: MultiEffect {
        maskEnabled: true
        maskThresholdMin: 0.5
        maskSpreadAtMin: 1.0
        maskSource: ShaderEffectSource {
            sourceItem: Rectangle {
                width: control.width
                height: control.height
                radius: control.borderRadius
                color: "white"
            }
        }
    }

    // ==================== Content Loader 内容加载器 ====================
    readonly property bool isPeek: effect === Enums.carousel.effect_peek

    // ==================== Public Methods 公开方法 ====================
    function setIndex(index) {
        // 两种 effect 的内容视图(PathView / ListView)都通过 currentIndex 绑定驱动，
        // 无需手动设置。保留此方法仅为兼容 Carousel.qml 既有调用契约。
    }

    Loader {
        id: contentLoader
        anchors.fill: parent
        sourceComponent: control.isPeek ? peekComponent : defaultComponent
    }

    // ==================== Default ListView (plain slide) 普通滑动 ====================
    Component {
        id: defaultComponent

        ListView {
            id: defaultListView
            anchors.fill: parent
            model: control.model
            orientation: control.isVertical ? ListView.Vertical : ListView.Horizontal
            snapMode: ListView.SnapOneItem
            highlightRangeMode: ListView.StrictlyEnforceRange
            highlightMoveDuration: Enums.duration.slower
            currentIndex: control.currentIndex
            interactive: false

            onCurrentIndexChanged: {
                if (control.currentIndex !== currentIndex) {
                    control.indexChanged(currentIndex)
                }
            }

            delegate: Item {
                width: defaultListView.width
                height: defaultListView.height

                Loader {
                    anchors.fill: parent
                    sourceComponent: control.itemDelegate ? control.itemDelegate : _contentComponent
                    property var itemData: modelData
                }
            }
        }
    }

    // ==================== Peek (Fluent Store slide + peek) 露边：滑动+两侧窥视 ====================
    // 中心项满显(scale 1.0/opacity 1.0)，相邻项缩放(peekScale)+半透明(peekOpacity)
    // 在两侧露出边缘(peek)；翻页时整条带子沿 Path 平滑滑动归位，图片不变形。
    Component {
        id: peekComponent

        PathView {
            id: pv
            anchors.fill: parent
            clip: true
            model: control.model
            interactive: false  // 翻页由 Carousel 的导航按钮/滚轮/自动播放驱动

            // ----- 几何参数(可微调) 中心卡占视图比例 + 相邻槽位偏移 -----
            readonly property bool isVertical: control.isVertical
            readonly property real axisLen: isVertical ? height : width
            // 中心卡沿主轴占视图的比例(<1 才能让两侧相邻项 peek 出来)
            readonly property real centerRatio: 0.82
            // 相邻槽位中心相对视图中心的偏移量(决定 peek 露出多少)
            readonly property real slotOffset: axisLen * (centerRatio + Enums.carousel.peekScale * centerRatio) / 2
                                               + axisLen * Enums.carousel.peekSpacing
            readonly property real cardLen: axisLen * centerRatio

            pathItemCount: 3            // 同时实例化 prev/current/next
            preferredHighlightBegin: 0.5
            preferredHighlightEnd: 0.5
            highlightRangeMode: PathView.StrictlyEnforceRange
            snapMode: PathView.SnapToItem
            highlightMoveDuration: Enums.duration.slower
            movementDirection: PathView.Shortest

            // currentIndex 双向桥接(与 default 模式一致的契约)
            currentIndex: control.currentIndex
            onCurrentIndexChanged: {
                if (control.currentIndex !== currentIndex) {
                    control.indexChanged(currentIndex)
                }
            }

            // 主轴方向的直线路径：start(相邻) → mid(中心高亮) → end(相邻)
            // PathAttribute 在控制点间插值，delegate 通过 PathView.<name> 读取。
            path: Path {
                startX: pv.isVertical ? pv.width / 2 : pv.width / 2 - pv.slotOffset
                startY: pv.isVertical ? pv.height / 2 - pv.slotOffset : pv.height / 2

                PathAttribute { name: "iScale"; value: Enums.carousel.peekScale }
                PathAttribute { name: "iOpacity"; value: Enums.carousel.peekOpacity }
                PathAttribute { name: "iZ"; value: 0 }

                PathLine {
                    x: pv.width / 2
                    y: pv.height / 2
                }
                PathAttribute { name: "iScale"; value: 1.0 }
                PathAttribute { name: "iOpacity"; value: 1.0 }
                PathAttribute { name: "iZ"; value: 1 }

                PathLine {
                    x: pv.isVertical ? pv.width / 2 : pv.width / 2 + pv.slotOffset
                    y: pv.isVertical ? pv.height / 2 + pv.slotOffset : pv.height / 2
                }
                PathAttribute { name: "iScale"; value: Enums.carousel.peekScale }
                PathAttribute { name: "iOpacity"; value: Enums.carousel.peekOpacity }
                PathAttribute { name: "iZ"; value: 0 }
            }

            delegate: Item {
                id: peekDelegate
                width: pv.isVertical ? pv.width : pv.cardLen
                height: pv.isVertical ? pv.cardLen : pv.height

                // PathView 注入的插值属性(路径端点外可能为 undefined，回退到相邻项取值)
                scale: PathView.iScale === undefined ? Enums.carousel.peekScale : PathView.iScale
                opacity: PathView.iOpacity === undefined ? Enums.carousel.peekOpacity : PathView.iOpacity
                z: PathView.iZ === undefined ? 0 : PathView.iZ

                Loader {
                    anchors.fill: parent
                    sourceComponent: control.itemDelegate ? control.itemDelegate : _contentComponent
                    property var itemData: modelData
                }
            }
        }
    }

    // ==================== Content Component 内容组件 ====================
    Component {
        id: _contentComponent

        Item {
            anchors.fill: parent

            // Check if image source 检查是否为图片源图片识别逻辑
            readonly property bool isImage: {
                var src = itemData.source || itemData
                return typeof src === "string" && (src.indexOf("/") >= 0 || src.indexOf(".") >= 0 || src.indexOf(":") >= 0)
            }

            // Image content 图片内容渲染图片内容
            Image {
                id: contentImage
                anchors.fill: parent
                source: parent.isImage ? (itemData.source || itemData) : ""
                fillMode: Image.PreserveAspectCrop
                visible: parent.isImage
                // 异步解码 + sourceSize 上限 1920(全屏轮播覆盖大多数显示器宽度),
                // 避免 Qt 把 4K/8K 原图按原始分辨率解到 GPU 纹理 (可能数 MB),
                // 滚动 ScrollArea 平移多张大图时纹理带宽吃紧, 是 CarouselPage 滚动卡的主因.
                // 不绑 sourceSize 到 width: width 抖动会触发整图重新解码, 引入新卡顿.
                asynchronous: true
                cache: true
                sourceSize.width: 1920
                sourceSize.height: 1080
            }

            // Color/Text content 颜色/文本内容渲染颜色或文本内容
            Rectangle {
                anchors.fill: parent
                color: itemData.color || Enums.surfaceColor
                visible: !parent.isImage

                Label {
                    anchors.centerIn: parent
                    type: Enums.label.type_body_strong
                    text: typeof itemData === 'string' ? itemData : (itemData.text || "")
                    visible: text.length > 0
                }
            }
        }
    }
}
