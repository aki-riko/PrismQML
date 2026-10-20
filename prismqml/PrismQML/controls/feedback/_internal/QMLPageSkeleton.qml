// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// QMLPageSkeleton - Self-sizing skeleton layout for the lazy-loading page
// QMLPageSkeleton - 懒加载页面自适应骨架布局
//
// Every block size and the row count are derived from this item's own available
// width/height plus Enums tokens, so the host passes no geometry at all: the
// engine decides each skeleton block from the area it is given.
// 每个骨架块尺寸与行数都由本项自身可用宽高加 Enums 令牌推导，宿主不传任何几何，
// 引擎按拿到的可用区域自行决定每个骨架块。
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property bool loading: true

    // ==================== Readonly State 只读状态 ====================
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
