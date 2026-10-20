// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// QMLPageSkeletonCardDefault - Default document interior for a card 卡片默认文档内部结构
//
// Used when a page declares a card without listing its children. It renders the
// documented document-style interior (breadcrumb, button row, paragraph) so a
// card-only declaration still reads as a real page instead of a blank surface.
// Sizes come from Enums.skeletonMetrics only; the host passes none.
// 页面声明了卡片但未列出子块时使用。渲染文档化的文档型内部结构(面包屑、按钮行、段落)，
// 使仅声明卡片的页面依然像真实页面而不是空白表面。尺寸只取自 Enums.skeletonMetrics，
// 宿主不传任何尺寸。
Column {
    id: control

    // ==================== Public Props 公开属性 ====================
    property bool loading: true

    // ==================== Content 内容 ====================
    spacing: Enums.skeletonMetrics.blockCardGap

    Skeleton {
        objectName: "qmlPageSkeletonCardBreadcrumb"
        width: control.width * Enums.skeletonMetrics.blockBreadcrumbWidthRatio
        height: Enums.skeletonMetrics.blockBreadcrumbHeight
        shape: Enums.skeleton.shape_rounded
        loading: control.loading
    }

    Row {
        objectName: "qmlPageSkeletonCardButtonRow"
        spacing: Enums.skeletonMetrics.blockButtonGap

        Repeater {
            objectName: "qmlPageSkeletonCardButtons"
            model: Enums.skeletonMetrics.blockDefaultButtons

            delegate: Skeleton {
                objectName: "qmlPageSkeletonBlockCell"
                width: Enums.skeletonMetrics.blockButtonWidth
                height: Enums.skeletonMetrics.blockButtonHeight
                shape: Enums.skeleton.shape_rounded
                loading: control.loading
            }
        }
    }

    Column {
        objectName: "qmlPageSkeletonCardText"
        width: parent.width
        spacing: Enums.skeletonMetrics.blockTextLineGap

        Repeater {
            objectName: "qmlPageSkeletonCardTextLines"
            model: Enums.skeletonMetrics.blockDefaultTextLines

            delegate: Skeleton {
                objectName: "qmlPageSkeletonBlockCell"
                // The last line runs short, the way a real paragraph ends.
                // 末行较短, 与真实段落一致。
                width: parent.width
                    * (index === Enums.skeletonMetrics.blockDefaultTextLines - 1
                        ? Enums.skeletonMetrics.blockTextShortWidthRatio
                        : Enums.skeletonMetrics.blockTextWidthRatio)
                height: Enums.skeletonMetrics.blockTextHeight
                shape: Enums.skeleton.shape_rounded
                loading: control.loading
            }
        }
    }
}
