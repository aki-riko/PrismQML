// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "QMLPageSkeletonLayout.js" as SkeletonLayout

// QMLPageSkeletonBlock - One declared skeleton block 单个声明式骨架块
//
// Renders exactly one entry of a page's `skeleton` declaration. The entry carries
// structure only (type plus optional counts); every width and height below comes
// from QMLPageSkeletonLayout applied to this item's own available area, so the
// host passes no geometry and the engine owns every size.
// 渲染页面 `skeleton` 声明中的一项。声明项只携带结构(类型与可选数量)；下面所有宽高都由
// QMLPageSkeletonLayout 作用在本项自身可用区域上得到，因此宿主不传几何，
// 每个尺寸都由引擎掌握。
//
// The four branches (card, horizontal row, vertical stack, single cell) are held in
// Loaders so a block only ever builds the objects its own type needs: a title must
// not pay for a card interior or a table grid.
// 四个分支(卡片、横向行、纵向堆叠、单块)都由 Loader 持有, 因此每个块只创建自身类型需要的
// 对象: 一个标题不应为卡片内部结构或表格网格付出代价。
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var entry: null
    property real availableHeight: 0
    // Scales this block down together with the rest of the declaration so a page
    // holding more than one screen of structure still fits the overlay.
    // 与整份声明一起缩小本块, 使结构超过一屏的页面仍能放进遮罩。
    property real fitRatio: 1
    // Compiled nested-block component supplied by the entry point. Passing it in
    // keeps one compiled type for every nesting level: a direct self-reference would
    // be a compile-time cycle, and a URL string recompiles the file per child on
    // every switch, which cost ~13ms of UI thread time on a four-card page.
    // 由入口传入的已编译嵌套块组件。传入它可让每一层嵌套复用同一个已编译类型: 直接
    // 自引用会形成编译期环, 而按 URL 字符串加载会在每次切换为每个子块重新编译文件,
    // 在四卡片页面上花掉约 13ms 的 UI 线程时间。
    property Component blockComponent: null
    property bool loading: true

    // ==================== Readonly State 只读状态 ====================
    readonly property var _metrics: Enums.skeletonMetrics
    // Stand-in used only while the `Enums` singleton is still resolving: member reads
    // on it yield undefined instead of throwing, so the first skeleton built during
    // window construction cannot spam QML runtime errors. The binding re-evaluates
    // with the real enum set as soon as it is available.
    // 仅在 `Enums` 单例仍在解析时使用的占位对象: 读它的成员得到 undefined 而不是抛错, 因此
    // 窗口构建期构建的首个骨架不会刷出 QML 运行时错误。枚举集可用后绑定会立即重新求值。
    readonly property var _pendingTypes: ({})
    readonly property var _types: Enums.skeleton ? Enums.skeleton : _pendingTypes
    readonly property int _type: entry ? entry.type : -1
    readonly property int _count: SkeletonLayout.repeatCount(entry, _metrics, _types)
    readonly property int _columns: SkeletonLayout.columnCount(entry, _metrics)
    readonly property var _children: SkeletonLayout.childrenOf(
        entry, _types.block_table)
    readonly property bool _isCard: _type === _types.block_card
    readonly property bool _isRepeating: SkeletonLayout.isRepeating(_type, _types)
    // Horizontal rows (button row, tabs, carousel) lay cells side by side and are
    // one cell tall; vertical stacks add their cells down the column.
    // 横向行(按钮行、标签栏、轮播)并排排布且只有一个单元高; 纵向堆叠沿列累加单元。
    readonly property bool _isRow: SkeletonLayout.isHorizontal(_type, _types)
    readonly property bool _isTable: _type === _types.block_table
    readonly property bool _isStack: _isRepeating && !_isRow && !_isTable
    readonly property bool _isSingle: !_isCard && !_isRepeating
    // Every internal size is scaled by `fitRatio` as well, so the drawn cells match
    // the height the block reserved. Scaling only `implicitHeight` left a
    // ratio-sized block (chart, image) drawing taller than its slot and overlapping
    // the block below it.
    // 内部每个尺寸同样按 `fitRatio` 缩放, 使绘制的单元与块预留的高度一致。只缩放
    // `implicitHeight` 会让按比例定高的块(图表、图片)画得比自己的槽位更高, 压到下方块上。
    readonly property real _cellHeight: SkeletonLayout.cellHeight(
        entry, availableHeight, _metrics, _types) * control.fitRatio
    readonly property real _cellWidth: SkeletonLayout.cellWidth(
        entry, width, _metrics, _types)
    readonly property int _cellShape: SkeletonLayout.blockShape(entry, _types)

    // ==================== Size 尺寸 ====================
    implicitHeight: SkeletonLayout.blockHeight(
        entry, availableHeight, _metrics, _types) * control.fitRatio

    // ==================== Content 内容 ====================
    // Card: an outlined surface holding the declared children, or the engine's
    // default document interior when the declaration lists none.
    // 卡片: 承载声明子块的描边表面; 未声明子块时使用引擎默认文档内部结构。
    Loader {
        id: cardLoader

        objectName: "qmlPageSkeletonCardLoader"
        anchors.fill: parent
        active: control._isCard
        sourceComponent: cardComponent
    }

    Component {
        id: cardComponent

        // A card is a layout grouping only, not a block of its own. Drawing a surface
        // here invented a kind of block the preset skeleton does not have: a plain
        // rectangle cannot shimmer, so the card sat still while the bars animated.
        // Everything visible inside a declared skeleton is therefore an animated
        // `Skeleton`, exactly like the preset one, and the card merely arranges them.
        // 卡片只是布局分组, 本身不是一种块。在这里画表面等于发明了预设骨架没有的块:
        // 普通矩形无法闪烁, 于是卡片静止而占位条在动。因此声明式骨架中一切可见内容都是
        // 会动画的 `Skeleton`, 与预设骨架完全一致, 卡片只负责排布它们。
        Item {
            id: cardBody

            Column {
                id: cardColumn

                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: Enums.skeletonMetrics.blockCardPadding
                    * control.fitRatio
                spacing: Enums.skeletonMetrics.blockCardGap * control.fitRatio

                Repeater {
                    objectName: "qmlPageSkeletonCardChildren"
                    model: control._children.length

                    delegate: Loader {
                        objectName: "qmlPageSkeletonCardChildLoader"
                        width: cardColumn.width
                        sourceComponent: control.blockComponent
                        onLoaded: {
                            item.entry = control._children[index]
                            item.availableHeight = control.availableHeight
                            item.blockComponent = control.blockComponent
                            // Nested blocks shrink with their card so the interior
                            // cannot overflow the surface it was scaled into.
                            // 嵌套块随卡片一起缩小, 使内部结构不会溢出被缩放后的表面。
                            item.fitRatio = control.fitRatio
                            item.loading = control.loading
                        }
                    }
                }

                QMLPageSkeletonCardDefault {
                    width: parent.width
                    visible: control._children.length === 0
                    loading: control.loading
                }
            }
        }
    }

    // Horizontal row: button row, tabs and carousel place their cells side by side.
    // 横向行: 按钮行、标签栏与轮播并排排布单元。
    Loader {
        id: rowLoader

        objectName: "qmlPageSkeletonRowLoader"
        width: parent.width
        anchors.left: parent.left
        anchors.top: parent.top
        active: control._isRepeating && control._isRow
        sourceComponent: rowComponent
    }

    Component {
        id: rowComponent

        Row {
            id: repeatRow

            objectName: "qmlPageSkeletonBlockRow"
            spacing: SkeletonLayout.cellGap(control.entry, control._metrics,
                                           control._types) * control.fitRatio

            Repeater {
                objectName: "qmlPageSkeletonBlockCells"
                model: control._count

                delegate: Skeleton {
                    objectName: "qmlPageSkeletonBlockCell"
                    width: SkeletonLayout.cellWidth(
                        control.entry, repeatRow.width, control._metrics,
                        control._types)
                    height: control._cellHeight
                    shape: control._cellShape
                    loading: control.loading
                }
            }
        }
    }

    // Vertical stack: paragraphs and lists add their cells down the column.
    // 纵向堆叠: 段落与列表沿列累加单元。
    Loader {
        id: stackLoader

        objectName: "qmlPageSkeletonStackLoader"
        width: parent.width
        anchors.left: parent.left
        anchors.top: parent.top
        active: control._isStack
        sourceComponent: stackComponent
    }

    Component {
        id: stackComponent

        Column {
            objectName: "qmlPageSkeletonBlockColumn"
            spacing: SkeletonLayout.cellGap(control.entry, control._metrics,
                                           control._types) * control.fitRatio

            Repeater {
                objectName: "qmlPageSkeletonBlockCells"
                model: control._count

                delegate: Skeleton {
                    objectName: "qmlPageSkeletonBlockCell"
                    width: SkeletonLayout.cellWidth(
                        control.entry, parent.width, control._metrics, control._types)
                    height: control._cellHeight
                    shape: control._cellShape
                    loading: control.loading
                }
            }
        }
    }

    // Table: a header row plus body rows, each divided into declared columns.
    // 表格: 表头行加主体行, 每行按声明列数均分。
    Loader {
        id: tableLoader

        objectName: "qmlPageSkeletonTableLoader"
        width: parent.width
        anchors.left: parent.left
        anchors.top: parent.top
        active: control._isTable
        sourceComponent: tableComponent
    }

    Component {
        id: tableComponent

        Column {
            id: tableColumn

            objectName: "qmlPageSkeletonTable"
            spacing: Enums.skeletonMetrics.blockListGap * control.fitRatio

            Skeleton {
                objectName: "qmlPageSkeletonTableHeader"
                width: tableColumn.width
                height: Enums.skeletonMetrics.blockTableHeaderHeight
                    * control.fitRatio
                shape: control._types.shape_rounded
                loading: control.loading
            }

            Repeater {
                objectName: "qmlPageSkeletonTableRows"
                model: control._count

                delegate: Row {
                    width: tableColumn.width
                    spacing: Enums.skeletonMetrics.blockTableColumnGap
                        * control.fitRatio

                    Repeater {
                        objectName: "qmlPageSkeletonTableColumns"
                        model: control._columns

                        delegate: Skeleton {
                            objectName: "qmlPageSkeletonBlockCell"
                            width: SkeletonLayout.tableColumnWidth(
                                tableColumn.width, control._columns, control._metrics)
                            height: Enums.skeletonMetrics.blockTableRowHeight
                                * control.fitRatio
                            shape: control._types.shape_rounded
                            loading: control.loading
                        }
                    }
                }
            }
        }
    }

    // Single cell: title, subtitle, text, button, icon, avatar, image, chart,
    // divider, input and list item.
    // 单个单元: 标题、分节标题、文本、按钮、图标、头像、图片、图表、分隔线、输入框与列表项。
    Loader {
        objectName: "qmlPageSkeletonSingleLoader"
        active: control._isSingle
        sourceComponent: singleComponent
    }

    Component {
        id: singleComponent

        Skeleton {
            objectName: "qmlPageSkeletonBlockCell"
            width: control._cellWidth
            height: control._cellHeight
            shape: control._cellShape
            loading: control.loading
        }
    }
}
