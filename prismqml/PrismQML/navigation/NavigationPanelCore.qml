// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import "../controls/navigation/_internal"
import "_internal"

// NavigationPanelCore - Base class for navigation panels 导航面板基类
// Provides common navigation logic: indicator animation, top/bottom items, route mapping 提供公共导航逻辑：指示器动画、上下项、路由映射
Item {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property int currentIndex: 0
    property var model: []
    property var bottomItems: []
    property bool indicatorAnimationEnabled: true
    property color backgroundColor: Enums.transparent
    property bool ticketPaperEnabled: true
    property real paperOriginX: 0
    property real paperOriginY: 0
    
    // Acrylic effect control 亚克力效果控制
    property bool acrylicEnabled: false
    property string acrylicImageSource: ""
    
    // Border visibility control (Window needs it, compact-nav window doesn't) 边框可见性控制（Window 需要，compact-nav window 不需要）
    property bool borderEnabled: true
    
    // Indicator config (subclass can override) 指示器配置（子类可覆盖）
    property int indicatorX: 0
    property int indicatorWidth: Enums.controlSize.navIndicatorWidth
    property int indicatorHeight: Enums.controlSize.navIndicatorHeight
    
    // Title bar height for corner offset (subclass can override) 标题栏高度用于圆角偏移（子类可覆盖）
    property int titleBarHeight: 0
    
    // Page key mapping 页面键映射
    property var _keyMap: ({})
    
    // ==================== Internal Props 内部属性 ====================
    property int _prevIndex: -1
    
    // Scroll offset for indicator real-time tracking 指示器实时跟踪的滚动偏移
    property real scrollOffset: 0

    // 指示器裁剪下界(可滚动区底边的 y, control 坐标系)。跟踪顶部项滚动时, 指示器
    // 超过此 y 的部分被裁掉, 避免溢出到底部固定项区域露白(Mica 模式下遮盖层透明
    // 无法遮挡)。默认=全高(不裁); 子类(如 NavigationBar)按布局设为可滚动区底边。
    property real indicatorClipBottom: height
    
    // Current selected page key (for bottom page items) 当前选中的页面键（用于底部页面项）
    property string _currentKey: ""
    
    // Indicator animation pending state for lazy loading 懒加载期间的指示器动画待处理状态
    property bool _pendingIndicatorAnimation: false
    property int _pendingTargetIndex: -1
    property int _indicatorUpdateGeneration: 0

    // 临时屏蔽 onCurrentIndexChanged 的动画路径(底部 item 点击时由
    // NavigationWindowCore 设 true,避免用页面索引(非导航项索引)算错指示器位置)
    property bool _skipIndicatorAnimation: false
    
    // Delay indicator animation until the target page is ready 指示器动画延迟到目标页就绪后执行
    property bool delayIndicatorAnimation: false
    
    // Subclass must provide these repeaters 子类必须提供这些Repeater
    property var topRepeater: null
    property var bottomRepeater: null

    // Track if current page switch is loading a new page 跟踪当前页面切换是否正在加载新页面
    property bool _isPageLoading: false

    // ==================== Readonly State 只读状态 ====================
    // Right-side rounded corner radius 右侧圆角半径
    readonly property int _cornerRadius: Enums.surfaceRadius(Enums.radius.large)

    // Current selected page key 当前选中的页面键
    readonly property string currentKey: {
        var safeModel = _safeModel || []
        var item = currentIndex >= 0 && currentIndex < safeModel.length ? safeModel[currentIndex] : null
        if (item) {
            return item.key || item.text || ""
        }
        return ""
    }

    readonly property var _safeModel:
        model === null || model === undefined ? []
        : (typeof model.length === "number" ? model : [])
    readonly property var _safeBottomItems:
        bottomItems === null || bottomItems === undefined ? []
        : (typeof bottomItems.length === "number" ? bottomItems : [])

    // ==================== Signals 信号 ====================
    signal itemClicked(int index)
    signal bottomItemClicked(int index)
    signal currentItemChanged(string key)
    
    // ==================== Internal Methods 内部方法 ====================
    // Update indicator position in real-time (no animation) 实时更新指示器位置（无动画）
    function _updateIndicatorPositionRealtime() {
        var item
        if (control._currentKey !== "") {
            item = _getBottomItemByKey(control._currentKey)
        } else {
            item = _getItemAt(currentIndex)
        }
        if (!item) return
        var rect = _computeIndicatorRect(item)
        navIndicator.setGeometry(rect)
    }

    // ==================== Public Methods 公开方法 ====================
    // Play pending indicator animation (called after lazy loading completes) 播放待处理的指示器动画（懒加载完成后调用）
    function playPendingIndicatorAnimation() {
        if (_pendingIndicatorAnimation && _pendingTargetIndex >= 0) {
            _pendingIndicatorAnimation = false
            var targetIndex = _pendingTargetIndex
            _pendingTargetIndex = -1

            // Ensure currentIndex matches pending target 确保currentIndex与待处理目标匹配
            if (currentIndex === targetIndex) {
                _updateIndicatorWithAnimation()
            }
        }
    }

    function _scheduleIndicatorUpdate(targetIndex) {
        _indicatorUpdateGeneration += 1
        var generation = _indicatorUpdateGeneration
        Qt.callLater(function() {
            if (generation !== control._indicatorUpdateGeneration ||
                    targetIndex !== control.currentIndex) return

            if (control.delayIndicatorAnimation && control._isPageLoading) {
                control._pendingIndicatorAnimation = true
                control._pendingTargetIndex = targetIndex
                return
            }

            control._pendingIndicatorAnimation = false
            control._pendingTargetIndex = -1
            control._updateIndicatorWithAnimation()
        })
    }

    function addItem(key, icon, text, onClick, selectable, selectedIcon, position) {
        var pos = position || "top"
        var item = {
            "key": key,
            "icon": icon || "",
            "text": text || "",
            "selectedIcon": selectedIcon || icon || "",
            "selectable": selectable !== false,
            "onClick": onClick
        }

        if (pos === "bottom") {
            var bottom = (_safeBottomItems || []).slice()
            bottom.push(item)
            bottomItems = bottom
        } else {
            var items = (_safeModel || []).slice()
            _keyMap[key] = items.length
            items.push(item)
            model = items
        }
        return item
    }
    function removeWidget(key) {
        var idx = _keyMap[key]
        if (idx !== undefined && idx >= 0 && idx < (_safeModel || []).length) {
            var items = (_safeModel || []).slice()
            items.splice(idx, 1)
            delete _keyMap[key]
            _rebuildRouteMap(items)
            model = items
        }
    }

    function setCurrentItem(key) {
        var idx = _keyMap[key]
        if (idx !== undefined) {
            currentIndex = idx
        } else {
            for (var i = 0; i < (_safeModel || []).length; i++) {
                var item = (_safeModel || [])[i]
                if (item && (item.text === key || item.key === key)) {
                    currentIndex = i
                    break
                }
            }
        }
    }

    function widget(key) {
        var idx = _keyMap[key]
        if (idx !== undefined && idx < (_safeModel || []).length) return (_safeModel || [])[idx]
        return null
    }

    // ==================== Internal Methods 内部方法 ====================
    function _rebuildRouteMap(items) {
        _keyMap = {}
        for (var i = 0; i < items.length; i++) {
            if (items[i] && items[i].key) _keyMap[items[i].key] = i
        }
    }

    function _getItemAt(index) {
        if (!topRepeater) return null

        if (index >= 0 && index < topRepeater.count) {
            return topRepeater.itemAt(index)
        } else if (bottomRepeater) {
            var bottomIdx = index - (_safeModel || []).length
            if (bottomIdx >= 0 && bottomIdx < bottomRepeater.count) {
                return bottomRepeater.itemAt(bottomIdx)
            }
        }
        return null
    }

    // Get bottom item by key (for page items in bottom) 通过 key 获取底部项（用于底部页面项）
    function _getBottomItemByKey(key) {
        if (!bottomRepeater || !key) return null
        for (var i = 0; i < (_safeBottomItems || []).length; i++) {
            var item = (_safeBottomItems || [])[i]
            if (item && item.key === key) {
                return bottomRepeater.itemAt(i)
            }
        }
        return null
    }

    // Get bottom item index by key 通过 key 获取底部项索引
    function _getBottomIndexByKey(key) {
        if (!key) return -1
        for (var i = 0; i < (_safeBottomItems || []).length; i++) {
            var item = (_safeBottomItems || [])[i]
            if (item && item.key === key) {
                return i
            }
        }
        return -1
    }
    // Update indicator for bottom page item by key 通过key更新底部页面项的指示器
    function updateIndicatorForBottomItem(key) {
        var item = _getBottomItemByKey(key)
        if (!item) return

        var endRect = _computeIndicatorRect(item)
        var bottomIndex = _getBottomIndexByKey(key)
        var targetIndex = (_safeModel || []).length + bottomIndex

        // Get previous item for animation 获取上一个项用于动画
        var prevItem = null
        if (_prevIndex >= 0) {
            prevItem = _getItemAt(_prevIndex)
        }

        if (prevItem && _prevIndex !== targetIndex) {
            var startRect = _computeIndicatorRect(prevItem)
            if (navIndicator.startAnimation) {
                navIndicator.startAnimation(startRect, endRect)
            } else {
                navIndicator.setGeometry(endRect)
            }
        } else {
            navIndicator.setGeometry(endRect)
        }

        // Update state 更新状态
        _prevIndex = targetIndex
        _currentKey = key
    }

    function _computeIndicatorRect(item) {
        if (!item) return Qt.rect(0, 0, 0, 0)

        // 关键点：使用 mapToItem 映射到 control 的坐标系
        var mappedPos = item.mapToItem(control, 0, 0)

        // y坐标需要在项的居中位置
        var y = mappedPos.y + (item.height - indicatorHeight) / 2

        return Qt.rect(indicatorX, y, indicatorWidth, indicatorHeight)
    }

    function _updateIndicatorWithAnimation() {
        // 如果当前是底部选中项，由于动画已经被 updateIndicatorForBottomItem 处理过，直接返回避免错乱
        if (control._currentKey !== "") return

        var newItem = _getItemAt(currentIndex)
        if (!newItem) return

        var endRect = _computeIndicatorRect(newItem)

        if (_prevIndex < 0 || _prevIndex === currentIndex) {
            navIndicator.setGeometry(endRect)
            _prevIndex = currentIndex
            return
        }


        var prevItem = _getItemAt(_prevIndex)
        if (prevItem) {
            var startRect = _computeIndicatorRect(prevItem)
            if (navIndicator.startAnimation) {
                navIndicator.startAnimation(startRect, endRect)
            } else {
                navIndicator.setGeometry(endRect)
            }
        } else {
            navIndicator.setGeometry(endRect)
        }

        _prevIndex = currentIndex
    }
    // Called when item clicked (for subclass to use) 项点击时调用
    // 不再直接改 currentIndex (会破坏 window→nav 单向 binding),也不在这里触发指示器动画
    // (改由 onCurrentIndexChanged 统一处理, 程序化切换也走同一路径).
    function _onItemClicked(index, isBottom) {
        // Clear bottom page key when clicking top item 点击顶部项时清除底部页面键
        if (!isBottom) {
            _currentKey = ""
        }

        // Emit signals 发送信号 (上层 window 接收后改 window.currentIndex,
        // 通过 Qt Binding 反向同步 control.currentIndex, 触发 onCurrentIndexChanged 跑动画)
        if (isBottom) {
            itemClicked(index)
            bottomItemClicked(index)
        } else {
            itemClicked(index)
        }
    }

    // Init indicator position without animation 初始化指示器位置（无动画）
    function _initIndicatorPosition() {
        var item
        if (control._currentKey !== "") {
            item = _getBottomItemByKey(control._currentKey)
            _prevIndex = (_safeModel || []).length + _getBottomIndexByKey(control._currentKey)
        } else {
            item = _getItemAt(currentIndex)
            _prevIndex = currentIndex
        }
        if (!item) return
        var rect = _computeIndicatorRect(item)
        navIndicator.setGeometry(rect)
    }

    onCurrentIndexChanged: {
        var changedKey = ""
        var safeModel = _safeModel || []
        var changedItem = currentIndex >= 0 && currentIndex < safeModel.length ? safeModel[currentIndex] : null
        if (changedItem) {
            changedKey = changedItem.key || changedItem.text || ""
        }
        if (changedKey) currentItemChanged(changedKey)

        // 跳过本次动画(底部 item 点击时由 NavigationWindowCore 设标志,
        // 避免用页面索引算错指示器位置;真正的动画交给 updateIndicatorForBottomItem 跑)
        if (_skipIndicatorAnimation) return

        // 指示器动画: currentIndex 在 _onItemClicked 删掉直接赋值后, 通过 Qt Binding
        // 从 window.currentIndex 异步同步过来. 由这里统一驱动动画, 既支持点击 (走 _onItemClicked)
        // 也支持外部直接改 window.currentIndex (Python 侧 setCurrentIndex / 程序化切换).
        // Defer one event-loop turn so the window can publish the lazy-loading
        // state before animation starts. This also keeps synchronous QML
        // incubation from freezing an already-running indicator animation.
        // 延后一轮事件循环，等待窗口发布懒加载状态；同时避免同步 QML
        // 孵化冻结已经开始的指示器动画。
        _scheduleIndicatorUpdate(currentIndex)
    }

    // Track scroll state changes 跟踪滚动状态变化
    onScrollOffsetChanged: {
        indicatorTracker._scrolling = true
        _scrollStopTimer.restart()
        if (!navIndicator.running) {
            _updateIndicatorPositionRealtime()
        }
    }

    // Initialize indicator after component loaded 组件加载后初始化指示器
    Component.onCompleted: {
        // Delay init to ensure layout is complete 延迟初始化以确保布局完成
        _initTimer.start()
    }

    // Re-init when model changes 模型变化时重新初始化
    onModelChanged: {
        _initTimer.restart()
    }

    // ==================== Content 内容 ====================

    NavigationPanelBackground {
        id: backgroundLayer
        anchors.fill: parent
        panel: control
    }
    NavigationPanelBorder {
        id: borderLayer
        anchors.fill: parent
        panel: control
    }
    // 指示器裁剪容器: top/left/right 贴 control(容器内坐标系原点 == control 原点,
    // 故 navIndicator 的 x/y 仍按 control 坐标系算, _computeIndicatorRect 无需改)。
    // height 动态: 跟踪底部项或动画进行中 → 全高不裁(指示器要能显示在底部区/动画
    // 全程可见); 跟踪顶部项滚动 → 裁到 indicatorClipBottom(可滚动区底边), 溢出
    // 底部固定项区的部分被 clip 裁掉。替代原 bottomCover 遮盖(Mica 下透明遮不住)。
    Item {
        id: indicatorClip
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: (control._currentKey !== "" || navIndicator.running)
                ? control.height
                : control.indicatorClipBottom
        clip: true
        // ⚠️ 动画进行中保持高 Z(controlsAbove+1),否则 backward 动画(底→顶)启动时
        // _currentKey 已清空, Z 立即降到 controls-1 被底部项遮住, 看到"下半段动画消失"。
        z: (control._currentKey !== "" || navIndicator.running)
            ? (Enums.zIndex.controlsAbove + 1)
            : (Enums.zIndex.controls - 1)

        SlidingIndicator {
            id: navIndicator
            x: control.indicatorX
            orientation: Qt.Vertical
            mode: "stretch"
            indicatorWidth: control.indicatorWidth
            indicatorHeight: control.indicatorHeight
            radius: Enums.radius.micro
            animationEnabled: control.indicatorAnimationEnabled
            // Outlined skins use the selected paper block instead of a second accent strip.
            // 描边皮肤使用选中纸面块，不再叠加第二条强调指示线。
            visible: !Enums.hasOutlinedSurfaces
        }
    }
    
    // Real-time indicator position tracking timer 实时指示器位置跟踪定时器
    NavigationIndicatorTrackerTimer {
        id: indicatorTracker
        host: control
        indicator: navIndicator
    }
    
    // Stop tracking after scroll ends 滚动结束后停止跟踪
    NavigationIndicatorScrollStopTimer {
        id: _scrollStopTimer
        tracker: indicatorTracker
    }
    // Delayed init timer 延迟初始化定时器
    NavigationIndicatorInitTimer {
        id: _initTimer
        host: control
    }
}
