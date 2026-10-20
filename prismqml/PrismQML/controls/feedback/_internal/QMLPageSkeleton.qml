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
// 1. A page may declare its structure through `blocks`; a Python host can also
//    supply it automatically from the page source (the engine reads it before the
//    page itself is instantiated). Each declared block is rendered by
//    QMLPageSkeletonBlock.
// 2. Without a usable declaration the generic document skeleton below is used.
// Either way every size and count is derived from this item's own available
// width/height plus Enums tokens, so the host passes no geometry at all.
// 两条渲染路径共用本入口:
// 1. 页面可通过 `blocks` 声明结构; Python 宿主也可从页面源码自动提供(引擎在页面实例化前
//    读取)。每个声明块由 QMLPageSkeletonBlock 渲染。
// 2. 没有可用声明时使用下面的通用文档骨架。
// 两种情况下每个尺寸与数量都由本项自身可用宽高加 Enums 令牌推导, 宿主完全不传几何。
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property bool loading: true
    // Declared structure, structure-only and geometry-free. 声明的结构, 仅结构不含几何。
    property var blocks: []

    // ==================== Readonly State 只读状态 ====================
    // The `Enums` singleton resolves lazily on first access, and the very first
    // skeleton can be requested while a window is still being constructed. Reading
    // enum members before they exist throws and spams QML runtime errors (the public
    // `Skeleton` component reads them too), so nothing here is built until the enum
    // set is actually ready. Empty stand-ins keep the reads harmless in the meantime,
    // and every binding below re-evaluates on its own once the singleton completes.
    // `Enums` 单例在首次访问时惰性解析, 而首个骨架可能在窗口仍在构建时就被请求。在枚举成员
    // 存在之前读取它们会抛错并刷出 QML 运行时错误(公开的 `Skeleton` 组件也会读它们), 因此
    // 在枚举集真正就绪前不构建任何内容。空占位对象让期间的读取无害, 单例完成后下面每个绑定
    // 都会自动重新求值。
    // Every category the skeleton touches must be present. Note that a partially
    // built singleton yields `null` for members that are not ready yet, and
    // `null !== undefined` is true, so plain undefined checks are not enough.
    // 骨架涉及的每个分类都必须就位。注意未就绪的成员在构建中的单例里是 `null`, 而
    // `null !== undefined` 为真, 因此仅用 undefined 判断并不够。
    readonly property bool _enumsReady: !!Enums.skeleton && !!Enums.skeletonMetrics
        && !!Enums.spacing && !!Enums.stateColor && !!Enums.radius
    readonly property var _types: _enumsReady ? Enums.skeleton : ({})
    readonly property var _metrics: _enumsReady ? Enums.skeletonMetrics : ({})
    readonly property var _spacing: _enumsReady ? Enums.spacing : ({})
    // Normalized declaration; null means "no usable declaration, use the generic
    // skeleton". Unknown types, non-arrays and empty declarations all land here.
    // 归一化声明; null 表示"无可用声明, 用通用骨架"。未知类型、非数组、空声明都会落到这里。
    readonly property var _declared: _enumsReady
        ? SkeletonLayout.normalize(blocks, _types.block_table) : null
    readonly property bool _hasDeclaration: _declared !== null
    // Outer margin and the single structural gap between the three sections.
    // 外边距，以及三个区段之间的统一结构间距。
    readonly property real _margin: _spacing.xl
    readonly property real _gap: _spacing.xl
    // The inferred structure can be taller than the overlay (a real page holds far
    // more than one screen). A skeleton that overflows would draw cards running past
    // the bottom edge, so the whole declaration is scaled down until it fits.
    // 推断结构可能高于遮罩(真实页面远不止一屏)。溢出的骨架会把卡片画到边界之外,
    // 因此整份声明会等比缩小到恰好放得下。
    readonly property real _fitRatio: _hasDeclaration
        ? SkeletonLayout.fitRatio(
            _declared, height - _margin * 2, _metrics.blockGap, _metrics, _types)
        : 1
    readonly property real _headerHeight: _metrics.pageHeaderHeight
    readonly property real _rowHeight: _metrics.pageRowHeight
    readonly property real _cardHeight: _metrics.pageCardHeight
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
        _metrics.pageRowMinCount || 0,
        Math.min(_metrics.pageRowMaxCount || 0,
                 Math.floor((_rowsBudget + _gap) / Math.max(_rowPitch, 1))))
    readonly property real _rowsHeight: _rowCount > 0
        ? _rowCount * _rowHeight + (_rowCount - 1) * _gap : 0

    // ==================== Content 内容 ====================
    // The one compiled block type every nesting level reuses. Declared here, above
    // the layouts that consume it, so the block itself needs no self-reference.
    // 每一层嵌套复用的唯一已编译块类型。声明在消费它的布局之前, 使块自身无需自引用。
    Component {
        id: declaredBlockComponent

        QMLPageSkeletonBlock {}
    }

    // Declared structure path 声明结构路径
    Column {
        id: declaredLayout

        objectName: "qmlPageSkeletonDeclaredLayout"
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: control._margin
        spacing: control._metrics.blockGap
        visible: control._hasDeclaration

        Repeater {
            objectName: "qmlPageSkeletonDeclaredRepeater"
            model: control._hasDeclaration ? control._declared.length : 0

            delegate: QMLPageSkeletonBlock {
                // Type-suffixed name so every declared block type is addressable.
                // 带类型后缀的名称, 使每种声明块都可被定位。
                objectName: "qmlPageSkeletonBlock-" + SkeletonLayout.typeName(
                    control._declared[index].type, control._types)
                width: declaredLayout.width
                entry: control._declared[index]
                availableHeight: control.height - control._margin * 2
                // Shrinks with the declaration so a long page still fits one screen.
                // 随整份声明一起缩小, 使长页面仍能放进一屏。
                fitRatio: control._fitRatio
                // One compiled type reused by every nesting level; see the property
                // documentation in QMLPageSkeletonBlock.
                // 每一层嵌套复用的同一个已编译类型; 见 QMLPageSkeletonBlock 中的属性说明。
                blockComponent: declaredBlockComponent
                loading: control.loading
            }
        }
    }

    // Generic fallback path 通用回退路径
    //
    // Held in a Loader that is only active when there is no usable declaration, so
    // the two paths never coexist: a declared page builds no generic skeleton
    // objects at all, and a fallback page builds nothing else. It also waits for the
    // enum set, which is what keeps the public `Skeleton` component from being built
    // against an unfinished `Enums` singleton.
    // 由仅在无可用声明时才激活的 Loader 持有, 因此两条路径永不共存: 有声明的页面完全
    // 不创建通用骨架对象, 回退页面也不创建其它东西。它同样等待枚举集就绪, 这正是避免公开
    // `Skeleton` 组件在 `Enums` 单例未完成时被构建的原因。
    Loader {
        id: fallbackLoader

        objectName: "qmlPageSkeletonFallbackLoader"
        anchors.fill: parent
        active: control._enumsReady && !control._hasDeclaration
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
                width: layout.width * control._metrics.pageHeaderWidthRatio
                height: control._headerHeight
                shape: control._types.shape_rounded
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
                            ? control._metrics.pageRowLongRatio
                            : control._metrics.pageRowShortRatio)
                        height: control._rowHeight
                        shape: control._types.shape_rounded
                        loading: control.loading
                    }
                }
            }

            // Bottom card block 底部卡片块
            Skeleton {
                objectName: "qmlPageSkeletonCard"
                width: layout.width
                height: control._cardHeight
                shape: control._types.shape_rounded
                loading: control.loading
            }
        }
    }
}
