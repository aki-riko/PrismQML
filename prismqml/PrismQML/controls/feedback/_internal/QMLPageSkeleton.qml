// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "QMLPageSkeletonLayout.js" as SkeletonLayout

// QMLPageSkeleton - Self-sizing skeleton layout for the lazy-loading page
// QMLPageSkeleton - 懒加载页面自适应骨架布局
//
// Two rendering paths share this entry point:
// 1. A page may declare its structure through `blocks` (the engine reads it from
//    `pageProperties`, before the page itself is instantiated). Each declared block
//    is rendered by QMLPageSkeletonBlock.
// 2. Without a usable declaration the generic document skeleton below is used.
// Either way every size and count is derived from this item's own available
// width/height plus Enums tokens, so the host passes no geometry at all.
// 两条渲染路径共用本入口:
// 1. 页面可通过 `blocks` 声明结构(引擎在页面实例化前从 `pageProperties` 读取),
//    每个声明块由 QMLPageSkeletonBlock 渲染。
// 2. 没有可用声明时使用下面的通用文档骨架。
// 两种情况下每个尺寸与数量都由本项自身可用宽高加 Enums 令牌推导, 宿主完全不传几何。
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property bool loading: true
    // Declared structure, structure-only and geometry-free. 声明的结构, 仅结构不含几何。
    property var blocks: []

    // ==================== Readonly State 只读状态 ====================
    // Normalized declaration; null means "no usable declaration, use the generic
    // skeleton". Unknown types, non-arrays and empty declarations all land here.
    // 归一化声明; null 表示"无可用声明, 用通用骨架"。未知类型、非数组、空声明都会落到这里。
    readonly property var _declared: SkeletonLayout.normalize(
        blocks, Enums.skeleton.block_table)
    readonly property bool _hasDeclaration: _declared !== null
    // Outer margin and the single structural gap between the three sections.
    // 外边距，以及三个区段之间的统一结构间距。
    readonly property real _margin: Enums.spacing.xl
    readonly property real _gap: Enums.spacing.xl
    readonly property real _headerHeight: Enums.skeletonMetrics.pageHeaderHeight
    readonly property real _rowHeight: Enums.skeletonMetrics.pageRowHeight
    readonly property real _cardHeight: Enums.skeletonMetrics.pageCardHeight
    // One row plus its gap: the height a single additional row costs.
    // 单行高度加行间距，即多一行所消耗的高度。
    readonly property real _rowPitch: _rowHeight + _gap
    // Vertical budget left for the rows once the margins, the header, the card
    // and the two structural gaps are taken out. The trailing gap of the last
    // row is added back because it is not spent below the rows region.
    // 扣掉外边距、标题条、卡片与两处结构间距后留给内容行的垂直预算。末行的尾随行间距
    // 不计入行区高度，因此在这里补回。
    readonly property real _rowsBudget: Math.max(
        height - _margin * 2 - _headerHeight - _cardHeight - _gap * 2, 0)
    // The engine picks the row count from the available height, clamped so a
    // tiny overlay stays readable and a tall one never turns into noise.
    // 引擎按可用高度决定行数并夹紧区间，使过小的遮罩仍可读、过高的遮罩不至于变成噪声。
    readonly property int _rowCount: Math.max(
        Enums.skeletonMetrics.pageRowMinCount,
        Math.min(Enums.skeletonMetrics.pageRowMaxCount,
                 Math.floor((_rowsBudget + _gap) / Math.max(_rowPitch, 1))))
    readonly property real _rowsHeight: _rowCount > 0
        ? _rowCount * _rowHeight + (_rowCount - 1) * _gap : 0

    // ==================== Content 内容 ====================
    // Declared structure path 声明结构路径
    Column {
        id: declaredLayout

        objectName: "qmlPageSkeletonDeclaredLayout"
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: control._margin
        spacing: Enums.skeletonMetrics.blockGap
        visible: control._hasDeclaration

        Repeater {
            objectName: "qmlPageSkeletonDeclaredRepeater"
            model: control._hasDeclaration ? control._declared.length : 0

            delegate: QMLPageSkeletonBlock {
                // Type-suffixed name so every declared block type is addressable.
                // 带类型后缀的名称, 使每种声明块都可被定位。
                objectName: "qmlPageSkeletonBlock-" + SkeletonLayout.typeName(
                    control._declared[index].type, Enums.skeleton)
                width: declaredLayout.width
                entry: control._declared[index]
                availableHeight: control.height - control._margin * 2
                loading: control.loading
            }
        }
    }

    // Generic fallback path 通用回退路径
    //
    // Held in a Loader that is only active when there is no usable declaration, so
    // the two paths never coexist: a declared page builds no generic skeleton
    // objects at all, and a fallback page builds nothing else.
    // 由仅在无可用声明时才激活的 Loader 持有, 因此两条路径永不共存: 有声明的页面完全
    // 不创建通用骨架对象, 回退页面也不创建其它东西。
    Loader {
        id: fallbackLoader

        objectName: "qmlPageSkeletonFallbackLoader"
        anchors.fill: parent
        active: !control._hasDeclaration
        sourceComponent: genericSkeleton
    }

    Component {
        id: genericSkeleton

        Column {
            id: layout

            objectName: "qmlPageSkeletonLayout"
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: control._margin
            spacing: control._gap

            // Header bar 标题条
            Skeleton {
                objectName: "qmlPageSkeletonHeader"
                width: layout.width * Enums.skeletonMetrics.pageHeaderWidthRatio
                height: control._headerHeight
                shape: Enums.skeleton.shape_rounded
                loading: control.loading
            }

            // Content rows 内容行
            Item {
                id: rowsRegion

                objectName: "qmlPageSkeletonRows"
                width: layout.width
                height: control._rowsHeight

                Repeater {
                    model: control._rowCount

                    delegate: Skeleton {
                        objectName: "qmlPageSkeletonRow"
                        y: index * control._rowPitch
                        width: layout.width * (index % 2 === 0
                            ? Enums.skeletonMetrics.pageRowLongRatio
                            : Enums.skeletonMetrics.pageRowShortRatio)
                        height: control._rowHeight
                        shape: Enums.skeleton.shape_rounded
                        loading: control.loading
                    }
                }
            }

            // Bottom card block 底部卡片块
            Skeleton {
                objectName: "qmlPageSkeletonCard"
                width: layout.width
                height: control._cardHeight
                shape: Enums.skeleton.shape_rounded
                loading: control.loading
            }
        }
    }
}
