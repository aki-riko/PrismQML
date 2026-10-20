// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

// QMLPageSkeletonLayout - Declared skeleton block layout maths 声明式骨架块布局计算
//
// Structure-only declaration maths shared by the skeleton dispatcher and the block
// renderer. Every size below is a token from `metrics` scaled by the area the block
// was given, so a page declaration never carries geometry and the engine still owns
// each size. Enum values arrive as the `types` object (`Enums.skeleton`) so this
// library stays pure data and never reads a singleton itself.
// 骨架分发器与块渲染器共用的"仅结构"声明计算。下面每个尺寸都是 metrics 令牌按块所获区域
// 缩放的结果，因此页面声明从不携带几何，尺寸仍由引擎掌握。枚举值经 types 对象
// (`Enums.skeleton`) 传入，使本库保持纯数据、自身不读单例。
.pragma library

// Return the declaration as a list when usable, otherwise null.
// 可用时把声明返回为列表, 否则返回 null。
function normalize(raw, maxType) {
    if (!raw || typeof raw !== "object" || typeof raw.length !== "number") return null
    if (raw.length <= 0) return null
    var result = []
    for (var index = 0; index < raw.length; index++) {
        var entry = raw[index]
        if (!entry || typeof entry !== "object") return null
        if (!isKnownType(entry.type, maxType)) return null
        result.push(entry)
    }
    return result
}

// A declaration is known only when its type is an in-range whole number.
// 仅当 type 是区间内的整数时才认为该声明已知。
function isKnownType(type, maxType) {
    if (typeof type !== "number" || isNaN(type)) return false
    if (type !== Math.floor(type)) return false
    return type >= 0 && type <= maxType
}

// Clamped integer parameter, falling back when absent or malformed.
// 夹紧的整数参数, 缺失或非法时回退默认值。
function intParam(entry, key, fallback, minimum, maximum) {
    var value = entry ? entry[key] : undefined
    if (typeof value !== "number" || isNaN(value)) return fallback
    if (value !== Math.floor(value)) return fallback
    return Math.max(minimum, Math.min(maximum, value))
}

// Clamped 0..1 height share; only image/chart/carousel may override their height.
// 夹紧到 0..1 的高度占比; 仅 image/chart/carousel 允许覆写高度。
function ratioParam(entry, fallback) {
    var value = entry ? entry.height : undefined
    if (typeof value !== "number" || isNaN(value) || value <= 0) return fallback
    return Math.max(0.05, Math.min(1, value))
}

// Valid nested children of a container block, or an empty list. Unknown children
// are dropped rather than invalidating the whole page declaration.
// 容器块的合法嵌套子块, 否则返回空列表。未知子块被丢弃, 不会让整页声明失效。
function childrenOf(entry, maxType) {
    var raw = entry ? entry.children : undefined
    if (!raw || typeof raw !== "object" || typeof raw.length !== "number") return []
    var result = []
    for (var index = 0; index < raw.length; index++) {
        var child = raw[index]
        if (child && typeof child === "object" && isKnownType(child.type, maxType)) {
            result.push(child)
        }
    }
    return result
}

// Blocks that lay their cells out horizontally, so their own height is one cell
// tall while their width spans the row.
// 单元横向排布的块: 自身高度等于单个单元高, 宽度铺满整行。
function isHorizontal(type, types) {
    return type === types.block_buttonRow || type === types.block_tabs
        || type === types.block_carousel
}

// Blocks that repeat a cell along one axis. 沿单一轴向重复单元的块。
function isRepeating(type, types) {
    return type === types.block_textLines || type === types.block_list
        || type === types.block_table || isHorizontal(type, types)
}

// Number of repeated cells (for a table, its body rows). 重复单元数(表格为主体行数)。
function repeatCount(entry, metrics, types) {
    if (!entry) return 1
    switch (entry.type) {
    case types.block_textLines:
        return intParam(entry, "lines", metrics.blockDefaultTextLines, 1,
                        metrics.blockMaxTextLines)
    case types.block_list:
        return intParam(entry, "items", metrics.blockDefaultItems, 1,
                        metrics.blockMaxItems)
    case types.block_table:
        return intParam(entry, "items", metrics.blockTableDefaultRows, 1,
                        metrics.blockTableMaxRows)
    case types.block_buttonRow:
        return intParam(entry, "buttons", metrics.blockDefaultButtons, 1,
                        metrics.blockMaxButtons)
    case types.block_carousel:
        return intParam(entry, "cards", metrics.blockCarouselCardCount, 1,
                        metrics.blockMaxCards)
    case types.block_tabs:
        return metrics.blockTabCount
    default:
        return 1
    }
}

// Table column count, driven by `columns`. 表格列数, 由 columns 决定。
function columnCount(entry, metrics) {
    return intParam(entry, "columns", metrics.blockDefaultColumns, 1,
                    metrics.blockMaxColumns)
}

// Gap between repeated cells. 重复单元之间的间距。
function cellGap(entry, metrics, types) {
    if (!entry) return 0
    switch (entry.type) {
    case types.block_textLines:
        return metrics.blockTextLineGap
    case types.block_list:
        return metrics.blockListGap
    case types.block_buttonRow:
        return metrics.blockButtonGap
    case types.block_tabs:
        return metrics.blockButtonGap
    case types.block_carousel:
        return metrics.blockCardGap
    default:
        return 0
    }
}

// Height of one cell of a block. 块内单个单元的高度。
function cellHeight(entry, availableHeight, metrics, types) {
    if (!entry) return 0
    var area = Math.max(availableHeight, 0)
    switch (entry.type) {
    case types.block_title:
        return metrics.blockTitleHeight
    case types.block_subtitle:
        return metrics.blockSubtitleHeight
    case types.block_text:
    case types.block_textLines:
        return metrics.blockTextHeight
    case types.block_divider:
        return metrics.blockDividerThickness
    case types.block_button:
    case types.block_buttonRow:
        return metrics.blockButtonHeight
    case types.block_icon:
        return metrics.blockIconSize
    case types.block_avatar:
        return metrics.blockAvatarSize
    case types.block_input:
        return metrics.blockInputHeight
    case types.block_tabs:
        return metrics.blockTabHeight
    case types.block_listItem:
    case types.block_list:
        return metrics.blockListItemHeight
    case types.block_table:
        return metrics.blockTableRowHeight
    case types.block_image:
        return ratioHeight(entry, area, metrics.blockImageHeightRatio,
                           metrics.blockImageMinHeight)
    case types.block_chart:
        return ratioHeight(entry, area, metrics.blockChartHeightRatio,
                           metrics.blockChartMinHeight)
    case types.block_carousel:
        return ratioHeight(entry, area, metrics.blockCarouselHeightRatio,
                           metrics.blockCarouselMinHeight)
    default:
        return metrics.blockTextHeight
    }
}

// Total height of a block. Horizontal rows are one cell tall; vertical stacks add
// their cells and gaps; cards and tables have their own composition.
// 块的总高度。横向行只有一个单元高; 纵向堆叠累加单元与间距; 卡片与表格各有组合方式。
function blockHeight(entry, availableHeight, metrics, types) {
    if (!entry) return 0
    if (entry.type === types.block_card) {
        return cardHeight(entry, availableHeight, metrics, types)
    }
    if (entry.type === types.block_table) {
        return tableHeight(entry, availableHeight, metrics, types)
    }
    var cell = cellHeight(entry, availableHeight, metrics, types)
    if (isHorizontal(entry.type, types)) return cell
    if (!isRepeating(entry.type, types)) return cell
    var count = repeatCount(entry, metrics, types)
    return count * cell + Math.max(count - 1, 0) * cellGap(entry, metrics, types)
}

// A table is a header row plus `items` body rows, all engine-sized.
// 表格由表头行加 items 行主体组成, 尺寸均由引擎决定。
function tableHeight(entry, availableHeight, metrics, types) {
    var rows = repeatCount(entry, metrics, types)
    return metrics.blockTableHeaderHeight + rows * metrics.blockTableRowHeight
}

// A card is its padding plus its children, or the engine's default interior.
// 卡片高度等于内边距加子块高度(未声明子块时用引擎默认内部结构)。
function cardHeight(entry, availableHeight, metrics, types) {
    var children = childrenOf(entry, types.block_table)
    var inner = 0
    var count = 0
    for (var index = 0; index < children.length; index++) {
        var childHeight = blockHeight(children[index], availableHeight, metrics, types)
        if (childHeight <= 0) continue
        inner += childHeight
        count += 1
    }
    if (count === 0) {
        // Documented default interior: breadcrumb, button row, paragraph. This is
        // what a document-style page shows inside its card.
        // 文档化的默认内部结构: 面包屑、按钮行、段落。文档型页面卡片内即为此。
        inner = metrics.blockBreadcrumbHeight
            + metrics.blockButtonHeight
            + metrics.blockDefaultTextLines * metrics.blockTextHeight
            + (metrics.blockDefaultTextLines - 1) * metrics.blockTextLineGap
        count = 3
    }
    return inner + Math.max(count - 1, 0) * metrics.blockCardGap
        + metrics.blockCardPadding * 2
}

function ratioHeight(entry, availableHeight, fallbackRatio, minimum) {
    var ratio = ratioParam(entry, fallbackRatio)
    return Math.max(minimum, availableHeight * ratio)
}

// Equal share of a row once the inter-cell gaps are removed.
// 扣除单元间距后每份均分宽度。
function dividedCellWidth(availableWidth, count, gap) {
    var area = Math.max(availableWidth, 0)
    var safeCount = Math.max(count, 1)
    return Math.max((area - Math.max(safeCount - 1, 0) * gap) / safeCount, 0)
}

// Width of one cell inside `availableWidth`. 单个单元在 availableWidth 内的宽度。
function cellWidth(entry, availableWidth, metrics, types) {
    if (!entry) return 0
    var area = Math.max(availableWidth, 0)
    switch (entry.type) {
    case types.block_title:
        return area * metrics.blockTitleWidthRatio
    case types.block_subtitle:
        return area * metrics.blockSubtitleWidthRatio
    case types.block_text:
        return area * metrics.blockTextShortWidthRatio
    case types.block_textLines:
        return area * metrics.blockTextWidthRatio
    case types.block_button:
        return Math.min(metrics.blockButtonWidth, area)
    case types.block_icon:
        return metrics.blockIconSize
    case types.block_avatar:
        return metrics.blockAvatarSize
    case types.block_buttonRow:
        return dividedCellWidth(area, repeatCount(entry, metrics, types),
                                metrics.blockButtonGap)
    case types.block_tabs:
        return Math.min(metrics.blockTabWidth,
                        dividedCellWidth(area, metrics.blockTabCount,
                                         metrics.blockButtonGap))
    case types.block_carousel:
        // The ratio is an upper bound; the engine divides the row when the ratio
        // would overflow it, so a carousel always fits its container.
        // 比例是上限; 溢出时由引擎按行均分, 因此轮播始终容纳于容器内。
        return Math.min(area * metrics.blockCarouselCardWidthRatio,
                        dividedCellWidth(area, repeatCount(entry, metrics, types),
                                         metrics.blockCardGap))
    default:
        return area
    }
}

// Width of one table column after the inter-column gaps. 扣除列间距后单列宽度。
function tableColumnWidth(availableWidth, columns, metrics) {
    return dividedCellWidth(availableWidth, columns, metrics.blockTableColumnGap)
}

// Inner width available to a card's children after its padding.
// 卡片子块可用的内部宽度(扣除内边距)。
function innerWidth(availableWidth, metrics) {
    return Math.max(availableWidth - metrics.blockCardPadding * 2, 0)
}

// Shape enum for one block. 单个块的形状枚举。
function blockShape(entry, types) {
    if (!entry) return types.shape_rounded
    if (entry.type === types.block_avatar) return types.shape_circle
    if (entry.type === types.block_divider) return types.shape_rect
    return types.shape_rounded
}

// Stable identifier of a block type, used for object names and test discovery.
// 块类型的稳定标识, 用于对象名与测试发现。
function typeName(type, types) {
    switch (type) {
    case types.block_title: return "title"
    case types.block_subtitle: return "subtitle"
    case types.block_text: return "text"
    case types.block_textLines: return "textLines"
    case types.block_card: return "card"
    case types.block_buttonRow: return "buttonRow"
    case types.block_button: return "button"
    case types.block_icon: return "icon"
    case types.block_avatar: return "avatar"
    case types.block_image: return "image"
    case types.block_list: return "list"
    case types.block_listItem: return "listItem"
    case types.block_input: return "input"
    case types.block_tabs: return "tabs"
    case types.block_divider: return "divider"
    case types.block_chart: return "chart"
    case types.block_carousel: return "carousel"
    case types.block_table: return "table"
    default: return "unknown"
    }
}
