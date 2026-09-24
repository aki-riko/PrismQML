// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "../containers/ScrollBar"
import "_internal" as NavigationInternal

// SelectorBar - Flat selector bar for switching between a small set of views
// 选择条 - 在一小组视图之间切换的扁平选择条
// A chrome-less sibling of SegmentedControl: the strip sits directly on the page and
// only the selected cell carries a sliding pill. 条带直接铺在页面上, 只有选中项带滑动胶囊。
// The horizontal strip scrolls when its cells overflow 横向条带在内容溢出时可横向滚动
// orientation picks the main axis  orientation 选择主轴
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var items: []
    property int currentIndex: 0
    property int orientation: Qt.Horizontal
    property int itemFontSize: Enums.typography.body
    property int iconSize: Enums.iconSize.m
    property bool pillAnimationEnabled: true
    // Duration of programmatic strip movement 程序化平移时长
    property int scrollDuration: Enums.duration.scroll

    // ==================== Internal Props 内部属性 ====================
    readonly property bool vertical: orientation === Qt.Vertical
    readonly property var _safeItems:
        items === null || items === undefined ? []
        : (typeof items.length === "number" ? items : [])
    // Only the matching strip owns delegates; the idle one is fed an empty model.
    // 只有匹配方向的条带持有委托, 闲置条带模型为空。
    readonly property var activeRepeater:
        control.vertical ? verticalRepeater : horizontalRepeater
    // Horizontal content that does not fit becomes scrollable 横向溢出时可滚动
    readonly property bool scrollable: !control.vertical && horizontalStrip.width > control.width
    readonly property real maxScrollOffset:
        Math.max(0, horizontalStrip.width - control.width)
    readonly property real scrollOffset: scrollArea.contentX
    // Latched after the first snap so the pill never animates in from the origin
    // 首次吸附后置位, 因此胶囊不会从原点动画滑入
    property bool _pillReady: false
    readonly property var activePill: control.vertical ? verticalPill : horizontalPill
    readonly property var idlePill: control.vertical ? horizontalPill : verticalPill

    // ==================== Signals 信号 ====================
    signal itemClicked(int index, bool byUser)
    signal currentItemChanged(string key)

    // ==================== Public Methods 公开方法 ====================
    function setCurrentIndex(idx) {
        if (idx < 0 || idx >= _safeItems.length) return
        if (idx === currentIndex) return

        // Only update the index; the pill owns its own geometry 只修改索引, 胶囊自持几何
        currentIndex = idx
        pillSyncTimer.schedule(true)

        var item = activeRepeater.itemAt(idx)
        if (item) currentItemChanged(item.key)
    }

    function setCurrentItem(key) {
        for (var i = 0; i < _safeItems.length; i++) {
            var item = activeRepeater.itemAt(i)
            if (item && item.key === key) {
                setCurrentIndex(i)
                return
            }
        }
    }

    // Add item 添加项目
    function addItem(key, text, icon) {
        items = _safeItems.concat([{ key: key, text: text, icon: icon || "" }])
    }

    // Get the current key 获取当前键
    function getCurrentKey() {
        var item = activeRepeater.itemAt(currentIndex)
        return item ? item.key : ""
    }

    // Bring the selected cell into view with the smallest scroll that fits it, and
    // prefer a cell boundary as the leading edge so the strip never leaves a half-cut
    // label behind. 以最小滚动量把选中单元移入可视区, 并优先让前缘落在单元格边界上,
    // 使条带不会留下被切开的半个标签。
    function revealCurrent() {
        if (!scrollable) return
        var item = horizontalRepeater.itemAt(currentIndex)
        if (!item) return

        var minOffset = Math.max(0, item.x + item.width - scrollArea.width)
        var maxOffset = Math.min(item.x, maxScrollOffset)
        var chosen = -1
        // Delegate order is ascending, so the first boundary in range is the smallest
        // 委托顺序即坐标升序, 因此第一个命中的边界就是最小位移
        for (var i = 0; i < _safeItems.length; i++) {
            var cell = horizontalRepeater.itemAt(i)
            if (!cell) continue
            if (cell.x >= minOffset && cell.x <= maxOffset) {
                chosen = cell.x
                break
            }
        }
        // No boundary can show the cell (e.g. the last one): clamp the minimal scroll
        // 没有边界能容纳该单元(例如最后一项): 退化为最小滚动量并夹紧
        if (chosen < 0) chosen = Math.min(minOffset, maxScrollOffset)
        scrollHelper.scrollTo(Math.max(0, chosen))
    }

    // ==================== Internal Methods 内部方法 ====================
    // Re-target the active pill; the idle one always drops its target so a rebuilt
    // strip can never leave a dangling reference.
    // 重新定位活动胶囊; 闲置胶囊始终清空目标, 避免条带重建后留下悬空引用。
    function _updateSlidePosition(animate) {
        var pill = activePill
        idlePill.target = null

        var item = activeRepeater.itemAt(currentIndex)
        if (!item) {
            pill.target = null
            if (currentIndex >= 0 && currentIndex < _safeItems.length) {
                pillSyncTimer.restart()
            }
            return
        }

        pillSyncTimer.stop()
        pill.target = item
        // Latch only after the geometry above has snapped into place 上面几何吸附后才置位
        if (animate) _pillReady = true
    }

    // Drop every target before a rebuild touches the delegates 重建委托前清空所有目标
    function _clearPills() {
        horizontalPill.target = null
        verticalPill.target = null
    }

    // Delegate-facing hook: the selected cell calls this when its own box settles
    // 委托侧钩子: 选中单元在自身几何落定时调用
    function _schedulePillSync(shouldAnimate) {
        pillSyncTimer.schedule(shouldAnimate)
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: control.vertical
        ? verticalStrip.implicitWidth
        : horizontalStrip.implicitWidth
    implicitHeight: control.vertical
        ? verticalStrip.implicitHeight
        : Enums.controlSize.selectorBarHeight

    Component.onCompleted: pillSyncTimer.schedule(false)
    onItemsChanged: {
        _clearPills()
        pillSyncTimer.schedule(false)
    }
    onWidthChanged: pillSyncTimer.schedule(false)
    onOrientationChanged: {
        _clearPills()
        pillSyncTimer.schedule(false)
    }
    onCurrentIndexChanged: {
        pillSyncTimer.schedule(true)
        revealCurrent()
    }

    // ==================== Content 内容 ====================
    // Horizontal strip: scrollable when the cells overflow 横向条带: 溢出时可滚动
    Flickable {
        id: scrollArea
        visible: !control.vertical
        anchors.fill: parent
        contentWidth: horizontalStrip.width
        contentHeight: height
        interactive: control.scrollable
        boundsBehavior: Flickable.StopAtBounds
        clip: true

        // The repository's smooth-scroll engine drives every programmatic move, so a
        // wheel notch or an auto-reveal glides instead of jumping. Native drag/flick
        // stays on the Flickable and is synced back by the helper's own sync child.
        // 所有程序化位移都交给仓库的平滑滚动引擎, 因此滚轮与自动滚入是滑行而不是瞬跳。
        // 原生拖拽/惯性仍由 Flickable 负责, 由助手自带的同步子对象回写。
        SmoothScrollHelper {
            id: scrollHelper
            target: scrollArea
            orientation: Qt.Horizontal
            enabled: true
            duration: control.scrollDuration
            bounceEnabled: true
            // Ownership stays with the handler below: it is the one that knows both
            // wheel axes. 归属仍由下面的处理器决定: 只有它同时识别两个滚轮轴。
            handleWheel: false
        }

        // Measured: a horizontal Flickable never hands a vertical wheel to its
        // ancestor scroll area, and Qt drops that wheel instead of panning the strip.
        // The handler is therefore required, not optional: it pans the strip, so a
        // wheel over an overflowing bar still moves something.
        // 实测: 横向 Flickable 不会把纵向滚轮交给祖先滚动区, Qt 会丢弃它而不是平移条带。
        // 因此这里的处理器是必需的: 它平移条带, 使溢出的条带在滚轮下仍有响应。
        WheelHandler {
            enabled: control.scrollable

            onWheel: (event) => {
                // A vertical wheel pans the overflow strip 纵向滚轮用于平移溢出条带
                var delta = WheelEventUtils.verticalDelta(event)
                    + WheelEventUtils.horizontalDelta(event)
                if (delta === 0) {
                    event.accepted = false
                    return
                }
                scrollHelper.scrollBy(-delta / 120 * scrollHelper.step)
                event.accepted = true
            }
        }

        // Declared before the positioner so the strip paints above it; a Row never
        // lays out a sibling as a cell. 先于定位器声明, 使条带绘制在其上; Row 不会把平级项当单元。
        NavigationInternal.SelectorBarPill {
            id: horizontalPill
            selectorBar: control
            strip: horizontalStrip
        }

        Row {
            id: horizontalStrip
            height: scrollArea.height
            spacing: Enums.spacing.none
            onXChanged: pillSyncTimer.schedule(false)

            Repeater {
                id: horizontalRepeater
                model: control.vertical ? [] : control._safeItems

                NavigationInternal.SelectorBarItem {
                    selectorBar: control
                }
            }
        }
    }

    // Vertical strip: content-sized, so the implicit width never depends on the
    // control's own width 纵向条带按内容定宽, 隐式宽度不依赖控件自身宽度
    Item {
        id: verticalHost
        visible: control.vertical
        width: verticalStrip.implicitWidth
        height: verticalStrip.implicitHeight

        NavigationInternal.SelectorBarPill {
            id: verticalPill
            selectorBar: control
            strip: verticalStrip
        }

        Column {
            id: verticalStrip
            spacing: Enums.spacing.none
            onYChanged: pillSyncTimer.schedule(false)

            Repeater {
                id: verticalRepeater
                model: control.vertical ? control._safeItems : []

                NavigationInternal.SelectorBarItem {
                    selectorBar: control
                }
            }
        }
    }

    NavigationInternal.SelectorBarPillSyncTimer {
        id: pillSyncTimer

        host: control
        itemRepeater: control.activeRepeater
    }
}
