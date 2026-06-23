// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import ".."
import "../controls/navigation/_internal"

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
    
    // ==================== Internal State 内部状态 ====================
    property int _prevIndex: -1
    
    // Scroll offset for indicator real-time tracking 指示器实时跟踪的滚动偏移
    property real scrollOffset: 0

    // 指示器裁剪下界(可滚动区底边的 y, control 坐标系)。跟踪顶部项滚动时, 指示器
    // 超过此 y 的部分被裁掉, 避免溢出到底部固定项区域露白(Mica 模式下遮盖层透明
    // 无法遮挡)。默认=全高(不裁); 子类(如 NavigationBar)按布局设为可滚动区底边。
    property real indicatorClipBottom: height
    
    // Current selected page key (for bottom page items) 当前选中的页面键（用于底部页面项）
    property string _currentKey: ""
    
    // Indicator animation pending state (for Python lazy loading) 指示器动画待处理状态（用于 Python 懒加载）
    property bool _pendingIndicatorAnimation: false
    property int _pendingTargetIndex: -1

    // 临时屏蔽 onCurrentIndexChanged 的动画路径(底部 item 点击时由
    // NavigationWindowCore 设 true,避免用页面索引(非导航项索引)算错指示器位置)
    property bool _skipIndicatorAnimation: false
    
    // Delay indicator animation (controlled by Python) 延迟指示器动画（由Python控制）
    property bool delayIndicatorAnimation: false
    
    // Subclass must provide these repeaters 子类必须提供这些Repeater
    property var topRepeater: null
    property var bottomRepeater: null
    
    // ==================== Signals 信号 ====================
    signal itemClicked(int index)
    signal bottomItemClicked(int index)
    signal currentItemChanged(string key)
    
    // ==================== Current Page Key 当前页面键 ====================
    readonly property string currentKey: {
        if (currentIndex >= 0 && currentIndex < model.length) {
            return model[currentIndex].key || model[currentIndex].text || ""
        }
        return ""
    }
    
    onCurrentIndexChanged: {
        if (currentKey) currentItemChanged(currentKey)

        // 跳过本次动画(底部 item 点击时由 NavigationWindowCore 设标志,
        // 避免用页面索引算错指示器位置;真正的动画交给 updateIndicatorForBottomItem 跑)
        if (_skipIndicatorAnimation) return

        // 指示器动画: currentIndex 在 _onItemClicked 删掉直接赋值后, 通过 Qt Binding
        // 从 window.currentIndex 异步同步过来. 由这里统一驱动动画, 既支持点击 (走 _onItemClicked)
        // 也支持外部直接改 window.currentIndex (Python 侧 setCurrentIndex / 程序化切换).
        if (delayIndicatorAnimation && _isPageLoading) {
            _pendingIndicatorAnimation = true
            _pendingTargetIndex = currentIndex
        } else {
            _pendingIndicatorAnimation = false
            _pendingTargetIndex = -1
            _updateIndicatorWithAnimation()
        }
    }
    
    // Track if current page switch is loading a new page 跟踪当前页面切换是否正在加载新页面
    property bool _isPageLoading: false
    
    // ==================== Background & Border 背景和边框 ====================
    // Right-side rounded corner radius 右侧圆角半径
    readonly property int _cornerRadius: Enums.radius.large

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
            var bottom = bottomItems.slice()
            bottom.push(item)
            bottomItems = bottom
        } else {
            var items = model.slice()
            _keyMap[key] = items.length
            items.push(item)
            model = items
        }
        return item
    }
    function removeWidget(key) {
        var idx = _keyMap[key]
        if (idx !== undefined && idx >= 0 && idx < model.length) {
            var items = model.slice()
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
            for (var i = 0; i < model.length; i++) {
                if (model[i].text === key || model[i].key === key) {
                    currentIndex = i
                    break
                }
            }
        }
    }

    function widget(key) {
        var idx = _keyMap[key]
        if (idx !== undefined && idx < model.length) return model[idx]
        return null
    }

    // ==================== Internal Methods 内部方法 ====================
    function _rebuildRouteMap(items) {
        _keyMap = {}
        for (var i = 0; i < items.length; i++) {
            if (items[i].key) _keyMap[items[i].key] = i
        }
    }

    function _getItemAt(index) {
        if (!topRepeater) return null

        if (index >= 0 && index < topRepeater.count) {
            return topRepeater.itemAt(index)
        } else if (bottomRepeater) {
            var bottomIdx = index - model.length
            if (bottomIdx >= 0 && bottomIdx < bottomRepeater.count) {
                return bottomRepeater.itemAt(bottomIdx)
            }
        }
        return null
    }

    // Get bottom item by key (for page items in bottom) 通过 key 获取底部项（用于底部页面项）
    function _getBottomItemByKey(key) {
        if (!bottomRepeater || !key) return null
        for (var i = 0; i < bottomItems.length; i++) {
            if (bottomItems[i].key === key) {
                return bottomRepeater.itemAt(i)
            }
        }
        return null
    }

    // Get bottom item index by key 通过 key 获取底部项索引
    function _getBottomIndexByKey(key) {
        if (!key) return -1
        for (var i = 0; i < bottomItems.length; i++) {
            if (bottomItems[i].key === key) {
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
        var targetIndex = model.length + bottomIndex

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
            _prevIndex = model.length + _getBottomIndexByKey(control._currentKey)
        } else {
            item = _getItemAt(currentIndex)
            _prevIndex = currentIndex
        }
        if (!item) return
        var rect = _computeIndicatorRect(item)
        navIndicator.setGeometry(rect)
    }

    // Layer A: opaque background with right-side rounded corners 层A：右侧圆角不透明背景
    Canvas {
        id: bgCanvas
        anchors.fill: parent
        z: -2  // Lowest layer 最底层
        
        onPaint: {
            var ctx = getContext("2d")
            var w = width, h = height, r = control._cornerRadius
            var topOffset = control.titleBarHeight  // Top-right corner starts below title bar 右上圆角从标题栏下方开始
            ctx.clearRect(0, 0, w, h)
            
            // Fill background 填充背景
            ctx.fillStyle = control.backgroundColor.toString()
            ctx.beginPath()
            ctx.moveTo(0, 0)
            ctx.lineTo(w, 0)  // Top edge (no corner, extends into title bar) 顶边（无圆角，延伸到标题栏）
            ctx.lineTo(w, topOffset)  // Right edge above title bar 标题栏上方的右边
            ctx.lineTo(w - r, topOffset)  // Move to top-right corner start 移动到右上圆角起点
            ctx.arcTo(w, topOffset, w, topOffset + r, r)  // Top-right corner below title bar 标题栏下方的右上圆角
            ctx.lineTo(w, h - r)
            ctx.arcTo(w, h, w - r, h, r)  // Bottom-right corner 右下圆角
            ctx.lineTo(0, h)
            ctx.closePath()
            ctx.fill()
        }
        
        // Repaint when size or color changes (debounced via Qt.callLater)
        // 尺寸或颜色变化时防抖重绘 — Qt.callLater 自动合并同一事件循环中的多次调用,
        // 不绑死 60fps 帧时长, 跟随事件循环节拍刷新一次
        function _scheduleBgRepaint() {
            Qt.callLater(bgCanvas.requestPaint)
        }
        onWidthChanged: _scheduleBgRepaint()
        onHeightChanged: _scheduleBgRepaint()
        
        Connections {
            target: control
            function onBackgroundColorChanged() { bgCanvas.requestPaint() }
        }
    }
    
    // Layer B: Acrylic blurred background 层B：亚克力模糊背景
    Rectangle {
        id: acrylicLayer
        anchors.fill: parent
        visible: control.acrylicEnabled && control.acrylicImageSource !== ""
        z: -1  // Below all content 在所有内容下方
        radius: control._cornerRadius
        clip: true
        color: "transparent"
        
        // Acrylic tint color: pure white/dark gray; keeps Mica tint 亚克力着色：纯白/深灰，保留云母色调
        readonly property color acrylicTintColor: Enums.stateColor.acrylicTintColor
        
        // Blurred background image 模糊背景图片
        Image {
            id: acrylicImage
            anchors.fill: parent
            source: control.acrylicImageSource
            fillMode: Image.PreserveAspectCrop
            cache: false  // Disable cache for dynamic updates 禁用缓存以支持动态更新
        }
        
        // Tint overlay (pure white/dark gray to preserve Mica tone) 着色叠加层（纯白/深灰保留云母色调）
        Rectangle {
            anchors.fill: parent
            color: acrylicLayer.acrylicTintColor
        }
        
        // Fill top-left corner (no radius) 填充左上角（无圆角）
        Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            width: parent.radius
            height: control.titleBarHeight + parent.radius
            color: "transparent"
            clip: true
            
            Image {
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                width: acrylicImage.width
                height: acrylicImage.height
                source: control.acrylicImageSource
                fillMode: Image.PreserveAspectCrop
                cache: false
            }
            Rectangle {
                anchors.fill: parent
                color: acrylicLayer.acrylicTintColor
            }
        }
        
        // Fill bottom-left corner (no radius) 填充左下角（无圆角）
        Rectangle {
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            width: parent.radius
            height: parent.radius
            color: "transparent"
            clip: true
            
            Image {
                anchors.right: parent.right
                anchors.top: parent.top
                width: acrylicImage.width
                height: acrylicImage.height
                source: control.acrylicImageSource
                fillMode: Image.PreserveAspectCrop
                cache: false
            }
            Rectangle {
                anchors.fill: parent
                color: acrylicLayer.acrylicTintColor
            }
        }
    }
    
    // Right border with rounded corners 带圆角的右侧边框
    Canvas {
        id: rightBorderCanvas
        anchors.fill: parent
        visible: control.borderEnabled && (control.backgroundColor.a > 0 || control.acrylicEnabled)  // Show when border enabled and bg visible 边框启用且背景可见时显示
        z: 0  // Above acrylic layer 在亚克力层之上
        
        onPaint: {
            var ctx = getContext("2d")
            var w = width, h = height, r = control._cornerRadius
            var topOffset = control.titleBarHeight
            var borderWidth = Enums.border.normal
            ctx.clearRect(0, 0, w, h)
            
            // Draw right border with rounded corners 绘制带圆角的右侧边框
            ctx.strokeStyle = Enums.stateColor.navDivider.toString()
            ctx.lineWidth = borderWidth
            
            var offset = borderWidth / 2
            ctx.beginPath()
            // Top-right corner (below title bar) 右上圆角（标题栏下方）
            ctx.moveTo(w - r, topOffset + offset)
            ctx.arcTo(w - offset, topOffset + offset, w - offset, topOffset + r, r - offset)
            // Right edge 右侧边
            ctx.lineTo(w - offset, h - r)
            // Bottom-right corner 右下圆角
            ctx.arcTo(w - offset, h - offset, w - r, h - offset, r - offset)
            ctx.stroke()
        }
        
        // Repaint right border on size change (debounced via Qt.callLater)
        // 尺寸变化时防抖重绘右边框 — 跟随事件循环节拍, 不绑 60fps
        function _scheduleBorderRepaint() {
            Qt.callLater(rightBorderCanvas.requestPaint)
        }
        onWidthChanged: _scheduleBorderRepaint()
        onHeightChanged: _scheduleBorderRepaint()
        
        Connections {
            target: ThemeManager
            function onThemeChanged() { rightBorderCanvas.requestPaint() }
        }
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
            indicatorWidth: control.indicatorWidth
            indicatorHeight: control.indicatorHeight
            animationEnabled: control.indicatorAnimationEnabled
            // neo: 隐藏滑动指示条(选中态用橙实心块代替, 避免双重标记)
            visible: !Enums.isNeobrutalism
        }
    }
    
    // Real-time indicator position tracking timer 实时指示器位置跟踪定时器
    Timer {
        id: indicatorTracker
        interval: Enums.duration.tick
        repeat: true
        running: _scrolling
        
        property bool _scrolling: false
        
        onTriggered: {
            if (!navIndicator.running) {
                _updateIndicatorPositionRealtime()
            }
        }
    }
    
    // Track scroll state changes 跟踪滚动状态变化
    onScrollOffsetChanged: {
        indicatorTracker._scrolling = true
        _scrollStopTimer.restart()
        if (!navIndicator.running) {
            _updateIndicatorPositionRealtime()
        }
    }
    
    // Stop tracking after scroll ends 滚动结束后停止跟踪
    Timer {
        id: _scrollStopTimer
        interval: Enums.duration.fast
        onTriggered: indicatorTracker._scrolling = false
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
    
    // Delayed init timer 延迟初始化定时器
    Timer {
        id: _initTimer
        interval: 50  // Small delay to ensure layout complete 小延迟确保布局完成
        onTriggered: _initIndicatorPosition()
    }
}
