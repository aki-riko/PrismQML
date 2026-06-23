// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "../utils"
import "../containers/ScrollBar"
import "." // For MenuSeparator, Action 引入同目录组件

// MenuCore - Menu base class (Qt-style, children only) 菜单基类
// Usage 用法:
// Method 1: Declarative (recommended) 方式1：声明式（推荐）

// Menu {
// Action { text: "剪切"; icon: "Cut" }
// Action { text: "复制"; icon: "Copy" }
// MenuSeparator {}
// Action { text: "粘贴"; icon: "Clipboard" }
// }
// Method 2: Imperative 方式2：命令式（兼容 ）

// Menu {
// id: menu
// Component.onCompleted: {
// menu.addWidget(profileCard)
// menu.addSeparator()
// menu.addAction("设置", "Settings")
// }
// }
PopupWindowCore {
 id: control
 
 // ==================== Menu Props 菜单属性 ====================
 property int minWidth: Enums.controlSize.menuMinWidth
 property int maxHeight: Enums.comboBoxMetrics.popupMaxHeight // Max menu height 菜单最大高度
 
 // ==================== Child Items 子元素 ====================
 default property alias actions: itemsColumn.data
 
 // ==================== Signals 信号 ====================
 signal dismissed()
 signal actionTriggered(string text) // Action triggered signal 动作触发信号
 
 // ==================== Internal State 内部状态 ====================
 property bool _needsScroll: false
 property int _cachedWidth: minWidth // Cached width to break binding loop 缓存宽度打破绑定循环
 property int _cachedHeight: Enums.controlSize.emptyStateButtonHeight // Cached height 缓存高度
 property bool _isDestroyed: false // Destruction flag 销毁标记
 
 Component.onDestruction: _isDestroyed = true
 
 // ==================== Size Calculation 尺寸计算 ====================
 // Use cached values to avoid binding loop 使用缓存值避免绑定循环
 popupWidth: _cachedWidth
 popupHeight: _cachedHeight
 
 function _calcWidth() {
 // Guard against destroyed object or invalid context 防止对象已销毁或上下文无效
 if (_isDestroyed || typeof Math === 'undefined') return minWidth
 var maxW = minWidth
 for (var i = 0; i < itemsColumn.children.length; i++) {
 var child = itemsColumn.children[i]
 if (child && child.implicitWidth) {
 maxW = Math.max(maxW, child.implicitWidth)
 }
 }
 return maxW
 }
 
 function _calcHeight() {
 // Guard against destroyed object or invalid context 防止对象已销毁或上下文无效
 if (_isDestroyed || typeof Math === 'undefined') return Enums ? Enums.controlSize.emptyStateButtonHeight : 0
 if (!Enums || !Enums.spacing) return 0
 var h = Enums.spacing.xs * 2 // contentContainer margins 容器边距
 for (var i = 0; i < itemsColumn.children.length; i++) {
 var child = itemsColumn.children[i]
 if (child && child.visible !== false) {
 // Use height if set, otherwise implicitHeight 优先使用height
 var itemH = child.height > 0 ? child.height : child.implicitHeight
 if (itemH > 0) {
 h += itemH
 }
 }
 }
 return h
 }
 
 function _updateSize() {
 // Guard against destroyed object or uninitialized context 防止对象已销毁或上下文未初始化
 if (_isDestroyed || typeof Math === 'undefined') return
 if (!Enums || !Enums.controlSize) return
 _cachedWidth = Math.max(minWidth, _calcWidth())
 var calcH = _calcHeight()
 _cachedHeight = Math.min(Math.max(Enums.controlSize.emptyStateButtonHeight, calcH), maxHeight)
 _needsScroll = calcH > maxHeight
 }
 
 // ==================== Public Methods 公开方法 ====================
 // Add custom widget to menu 添加自定义组件
 // @param widget: Item - the widget to add
 // @param selectable: bool - whether clickable (default false)
 // @param onClick: function - click callback
 function addWidget(widget, selectable, onClick) {
 if (!widget) return
 widget.parent = itemsColumn
 widget.width = Qt.binding(function() { return itemsColumn.width })
 
 if (selectable && onClick) {
 // Create mouse area for selectable widgets 为可选组件创建鼠标区域
 var ma = mouseAreaComponent.createObject(widget, {
 "anchors.fill": widget,
 "onClicked": onClick
 })
 }
 Qt.callLater(_updateSize)
 }
 
 // Add separator to menu 添加分隔线
 function addSeparator() {
 separatorComponent.createObject(itemsColumn)
 Qt.callLater(_updateSize)
 }
 
 // Add action to menu 添加动作
 // @param text: string - action text
 // @param icon: string - icon name (optional)
 // @param shortcut: string - shortcut key (optional)
 // @param options: object - {actionId, checkable, checked, enabled, toolTip, hasSubmenu} (optional)
 function addAction(text, icon, shortcut, options) {
 var props = { "text": text || "" }
 if (icon) props.icon = icon
 if (shortcut) props.shortcut = shortcut
 
 // Extended options 扩展选项
 if (options) {
 if (options.actionId !== undefined) props.actionId = options.actionId
 if (options.checkable !== undefined) props.checkable = options.checkable
 if (options.checked !== undefined) props.checked = options.checked
 if (options.enabled !== undefined) props.enabled = options.enabled
 if (options.toolTip !== undefined) props.toolTip = options.toolTip
 if (options.hasSubmenu !== undefined) props.hasSubmenu = options.hasSubmenu
 }
 
 var action = actionComponent.createObject(itemsColumn, props)
 // triggered → actionTriggered + close 由 itemsColumn.onChildrenChanged 统一接管,
 // 这里不再 connect, 避免双发。
 Qt.callLater(_updateSize)
 return action
 }
 
 // Add multiple actions 批量添加动作
 // @param actions: array of {text, icon, shortcut, ...options}
 function addActions(actionsArray) {
 for (var i = 0; i < actionsArray.length; i++) {
 var a = actionsArray[i]
 addAction(a.text, a.icon, a.shortcut, a)
 }
 }
 
 // Get action by ID 按ID获取动作
 // @param actionId: string
 // @returns Action item or null
 function getAction(actionId) {
 for (var i = 0; i < itemsColumn.children.length; i++) {
 var child = itemsColumn.children[i]
 if (child && child.actionId === actionId) return child
 }
 return null
 }
 
 // Update action properties by ID 按ID更新动作属性
 // @param actionId: string
 // @param props: object - {text, icon, shortcut, checkable, checked, enabled, toolTip}
 function updateAction(actionId, props) {
 var action = getAction(actionId)
 if (!action) return false
 if (props.text !== undefined) action.text = props.text
 if (props.icon !== undefined) action.icon = props.icon
 if (props.shortcut !== undefined) action.shortcut = props.shortcut
 if (props.checkable !== undefined) action.checkable = props.checkable
 if (props.checked !== undefined) action.checked = props.checked
 if (props.enabled !== undefined) action.enabled = props.enabled
 if (props.toolTip !== undefined) action.toolTip = props.toolTip
 Qt.callLater(_updateSize)
 return true
 }
 
 // Remove action by ID 按ID删除动作
 // @param actionId: string
 function removeAction(actionId) {
 var action = getAction(actionId)
 if (action) {
 action.destroy()
 Qt.callLater(_updateSize)
 return true
 }
 return false
 }
 
 // Add submenu 添加子菜单
 // @param text: string - parent action text
 // @param icon: string - icon name
 // @param submenuComponent: Component - the submenu component to show
 // @returns Action item
 function addSubmenu(text, icon, submenuComponent) {
 var action = addAction(text, icon, "", { hasSubmenu: true })
 if (action && submenuComponent) {
 action.submenuRequested.connect(function() {
 // Position submenu to the right of this action
 var globalPos = action.mapToGlobal(action.width, 0)
 var submenu = submenuComponent.createObject(null)
 if (submenu && submenu.showAtPosition) {
 submenu.showAtPosition(globalPos.x, globalPos.y)
 } else if (submenu && submenu.open) {
 submenu.open(globalPos.x, globalPos.y)
 }
 control.close()
 })
 }
 return action
 }
 
 // Clear all items 清空所有项
 function clear() {
 for (var i = itemsColumn.children.length - 1; i >= 0; i--) {
 var child = itemsColumn.children[i]
 // destroy() 是延迟执行的，先设 visible=false 防止 _calcHeight 计入
 child.visible = false
 child.height = 0
 child.destroy()
 }
 Qt.callLater(_updateSize)
 }
 
 // ==================== Internal Components 内部组件 ====================
 Component {
 id: separatorComponent
 MenuSeparator {}
 }
 
 Component {
 id: actionComponent
 Action {}
 }
 
 Component {
 id: mouseAreaComponent
 MouseArea {
 hoverEnabled: true
 cursorShape: Qt.ArrowCursor
 }
 }
 
 // ==================== Lifecycle 生命周期 ====================
 Component.onCompleted: Qt.callLater(_updateSize)
 onClosed: dismissed()
 onAboutToShow: _updateSize() // Recalculate before showing 显示前重新计算
 
 // ==================== Menu Content 菜单内容 ====================
 Flickable {
 id: menuFlickable
 anchors.fill: parent
 anchors.rightMargin: control._needsScroll ? Enums.comboBoxMetrics.scrollBarRightMargin : 0
 contentWidth: width
 contentHeight: itemsColumn.height
 clip: true
 boundsBehavior: Flickable.StopAtBounds
 interactive: false // Disable native scroll, use smooth scroll 禁用原生滚动，使用平滑滚动
 
 // Smooth scroll 平滑滚动
 PopupSmoothScroll { flickable: menuFlickable; enabled: control._needsScroll }
 
 Column {
 id: itemsColumn
 width: parent.width

 // 已自动绑定的 Action 列表 (用 objectName 做去重 key 不可靠, 直接缓存对象引用)
 property var _autoBoundActions: []

 onChildrenChanged: {
 // 声明式子项 Action 不走 addAction(那条路径会显式 connect),所以 triggered
 // 后菜单不会自动关。这里统一在 children 变化时给所有 Action 补 connect。
 for (var i = 0; i < itemsColumn.children.length; i++) {
 var c = itemsColumn.children[i]
 if (c && c.triggered && _autoBoundActions.indexOf(c) === -1) {
 _autoBoundActions.push(c)
 c.triggered.connect((function(child) {
 return function() {
 control.actionTriggered(child.actionId || child.text || "")
 control.close()
 }
 })(c))
 }
 }
 Qt.callLater(control._updateSize)
 }
 }
 }
 
 // Scrollbar 滚动条
 Loader {
 anchors.right: parent.right
 anchors.top: parent.top
 anchors.bottom: parent.bottom
 anchors.margins: Enums.spacing.xxs
 width: Enums.comboBoxMetrics.scrollBarWidth
 active: control._needsScroll
 sourceComponent: ScrollBarEntry {
 flickable: menuFlickable
 width: Enums.comboBoxMetrics.scrollBarWidth
 }
 }
}
