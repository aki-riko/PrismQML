// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "../utils"
import "../containers/ScrollBar"
import "." // For MenuSeparator, Action 引入同目录组件
import "_internal"

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
 
 // ==================== Public Props 公开属性 ====================
 property int minWidth: Enums.controlSize.menuMinWidth
 property int maxHeight: Enums.comboBoxMetrics.popupMaxHeight // Max menu height 菜单最大高度
 default property alias actions: menuContent.actions

 // ==================== Internal Props 内部属性 ====================
 property bool _needsScroll: false
 property int _cachedWidth: minWidth // Cached width to break binding loop 缓存宽度打破绑定循环
 property int _cachedContentHeight: Math.max(
 0, Enums.controlSize.emptyStateButtonHeight - 2 * contentPadding
 ) // Cached content height 缓存内容高度
 property bool _isDestroyed: false // Destruction flag 销毁标记
 property var _openSubmenu: null
 property var _openSubmenuAction: null
 property var _pendingSubmenuAction: null
 property var _pendingSubmenuComponent: null
 property var _pendingSubmenuProperties: null
 property MenuItemRegistry _itemRegistry: MenuItemRegistry {}
 property alias _actions: menuActions
 // The level component is loaded on demand rather than declared inline: a component that
 // instantiates MenuCore cannot live inside MenuCore itself, or every menu would recurse
 // into another menu while being built.
 // 层级组件按需加载而非内联声明: 实例化 MenuCore 的组件不能定义在 MenuCore 内部, 否则每个
 // 菜单在构建时都会递归地再建一个菜单。
 property Component _menuLevelComponent: null

 // ==================== Signals 信号 ====================
 signal dismissed()
 signal actionTriggered(string text) // Action triggered signal 动作触发信号
 
 // ==================== Internal Methods 内部方法 ====================
 function _registerMenuItem(item) {
 _itemRegistry.registerItem(item)
 }

 function _unregisterMenuItem(item) {
 _itemRegistry.unregisterItem(item)
 }

 function _syncMenuItems() {
 // Persist visual menu items before popup reparenting makes children mode-dependent. 弹层重挂载前持久记录视觉菜单项
 var children = menuContent.itemContainer.children
 for (var i = 0; i < children.length; i++) {
 _registerMenuItem(children[i])
 }
 }

 function _menuItems() {
 return _itemRegistry.liveItems()
 }

 function _createDataSubmenuComponent() {
 return Qt.createComponent(Qt.resolvedUrl("SystemTrayMenu.qml"))
 }

 function _calcWidth() {
 // Guard against destroyed object or invalid context 防止对象已销毁或上下文无效
 if (_isDestroyed || typeof Math === 'undefined') return minWidth
 return _itemRegistry.measuredWidth(minWidth)
 }
 
 function _calcHeight() {
 // Guard against destroyed object or invalid context 防止对象已销毁或上下文无效
 if (_isDestroyed || typeof Math === 'undefined') return Enums ? Enums.controlSize.emptyStateButtonHeight : 0
 if (!Enums || !Enums.spacing) return 0
 return _itemRegistry.measuredHeight()
 }
 
 function _updateSize() {
 // Guard against destroyed object or uninitialized context 防止对象已销毁或上下文未初始化
 if (_isDestroyed || typeof Math === 'undefined') return
 if (!Enums || !Enums.controlSize) return
 _cachedWidth = Math.max(minWidth, _calcWidth())
 var calcH = _calcHeight()
 var minContentHeight = Math.max(
  0, Enums.controlSize.emptyStateButtonHeight - 2 * contentPadding)
 var maxContentHeight = Math.max(0, maxHeight - 2 * contentPadding)
 _cachedContentHeight = Math.min(Math.max(minContentHeight, calcH), maxContentHeight)
 _needsScroll = calcH > maxContentHeight
 }

 function _closeOpenSubmenu() {
 submenuOpenTimer.stop()
 _pendingSubmenuAction = null
 _pendingSubmenuComponent = null
 _pendingSubmenuProperties = null
 _openSubmenuAction = null
 if (!_openSubmenu) return

 var submenu = _openSubmenu
 _openSubmenu = null
 if (!submenu || typeof submenu.destroy !== "function") return
 if (submenu.close) submenu.close()
 submenu.destroy(Enums.popupMetrics.closingDelayMs)
 }

 function _bindSubmenuAction(action, submenuComponent, initialProperties) {
 if (!action) return action
 var hasDataSubmenu = action._submenuData !== undefined
  && action._submenuData !== null
 if (!submenuComponent && !hasDataSubmenu) return action
 action.hoveredChanged.connect(function() {
 if (!action.hovered) return
 _pendingSubmenuAction = action
 _pendingSubmenuComponent = submenuComponent
 _pendingSubmenuProperties = initialProperties
 submenuOpenTimer.restart()
 })
 action.submenuRequested.connect(function() {
 _openSubmenuForAction(action, submenuComponent, initialProperties)
 })
 return action
 }

 function _openSubmenuForAction(action, submenuComponent, initialProperties) {
 if (!action) return
 if (_openSubmenu && _openSubmenuAction === action) return
 // A data-built row carries its own nodes and needs no component; every other row must
 // bring the component that produces its level.
 // 数据构建的父行自带节点, 不需要组件; 其余父行必须带上产出其层级的组件。
 var buildsFromData = action._submenuData !== undefined && action._submenuData !== null
 if (!buildsFromData && !submenuComponent) return

 _closeOpenSubmenu()
 // A data-built row rebuilds its level from its own data every time it opens: the previous
 // instance is destroyed when another branch takes over, and a destroyed QML object is
 // still a non-null reference, so reusing it would open an empty panel.
 // 数据构建的父行每次打开都按自身数据重建层级: 上一个实例在分支被接管时已销毁, 而已销毁的
 // QML 对象引用仍非 null, 复用它只会开出空面板。
 var submenu = null
 if (buildsFromData) {
  var levelComponent = _levelComponent()
  if (!levelComponent) return
  submenu = levelComponent.createObject(null, {})
  if (!submenu) return
  submenu.addNodes(action._submenuData.nodes, action._submenuData.basePath)
 } else {
  submenu = action._level !== undefined && action._level !== null
  ? action._level
  : submenuComponent.createObject(null, initialProperties || {})
 }
 if (!submenu) return

 submenu.stealFocus = false
 if (submenu.actionTriggered) {
 submenu.actionTriggered.connect(function(actionId) {
 control.actionTriggered(actionId)
 Qt.callLater(function() {
 if (!control._isDestroyed) control.close()
 })
 })
 }

 if (submenu.dismissed) {
 submenu.dismissed.connect(function() {
 if (control._openSubmenu === submenu) {
 control._openSubmenu = null
 control._openSubmenuAction = null
 submenu.destroy(Enums.popupMetrics.closingDelayMs)
 }
 })
 }

 _openSubmenu = submenu
 _openSubmenuAction = action
 if (submenu.openAsSubmenu) {
 submenu.openAsSubmenu(action)
 } else {
 var globalPos = action.mapToGlobal(action.width - Enums.popupMetrics.controlGap, 0)
 if (submenu.showAtPosition) {
 submenu.showAtPosition(globalPos.x, globalPos.y)
 } else if (submenu.open) {
 submenu.open(globalPos.x, globalPos.y)
 }
 }
 }
 
 // ==================== Public Methods 公开方法 ====================
 // Stop native surfaces without scheduling child destruction before engine teardown.
 // 引擎析构前停止原生弹层，且不为子项排入延迟销毁。
 function prepareForEngineRelease() {
 submenuOpenTimer.stop()
 _pendingSubmenuAction = null
 _pendingSubmenuComponent = null
 _pendingSubmenuProperties = null
 _openSubmenuAction = null
 var submenu = _openSubmenu
 _openSubmenu = null
 if (submenu) {
 if (submenu.prepareForEngineRelease) submenu.prepareForEngineRelease()
 else if (submenu.forceReset) submenu.forceReset()
 }
 forceReset()
 _nativeWindowRequested = false
 }

 // Open as a child menu with both first action rows aligned 作为子菜单打开，并对齐父子首行
 function openAsSubmenu(parentAction) {
 if (!parentAction) return
 targetControl = parentAction
 _submenuPlacement = true
 _updateSize()
 var windowPos = _calcSubmenuPosition()
 _openAtPosition(windowPos.x, windowPos.y, true)
 }

  function addWidget(widget, selectable, onClick) { return menuActions.addWidget(widget, selectable, onClick) }
 
  function addSeparator() { return menuActions.addSeparator() }
 
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
 
 var action = actionComponent.createObject(menuContent.itemContainer, props)
 _registerMenuItem(action)
 // triggered → actionTriggered + close 由 MenuContent.onChildrenChanged 统一接管,
 // 这里不再 connect, 避免双发。
 Qt.callLater(_updateSize)
 return action
 }
 
  function addActions(actionsArray) { return menuActions.addActions(actionsArray) }
 
  function getAction(actionId) { return menuActions.getAction(actionId) }
 
  function updateAction(actionId, props) { return menuActions.updateAction(actionId, props) }
 
  function removeAction(actionId) { return menuActions.removeAction(actionId) }
 
  function addSubmenu(text, icon, submenuComponent) { return menuActions.addSubmenu(text, icon, submenuComponent) }

  function addSubmenuActions(text, icon, actionsArray) { return menuActions.addSubmenuActions(text, icon, actionsArray) }
 
  function leafPath(actionId) { return menuActions.leafPath(actionId) }

  function addNodes(nodes, basePath) { return menuActions.addNodes(nodes, basePath) }

 // The level component is loaded on demand rather than declared inline: a component that
 // instantiates MenuCore cannot live inside MenuCore itself, or every menu would recurse
 // into another menu while being built.
 // 层级组件按需加载而非内联声明: 实例化 MenuCore 的组件不能定义在 MenuCore 内部, 否则每个
 // 菜单在构建时都会递归地再建一个菜单。
 function _levelComponent() {
  if (_menuLevelComponent && _menuLevelComponent.status === Component.Ready) {
  return _menuLevelComponent
  }
  _menuLevelComponent = Qt.createComponent(Qt.resolvedUrl("MenuCore.qml"))
  if (_menuLevelComponent.status === Component.Error) {
  console.warn("MenuCore level failed to load: "
  + _menuLevelComponent.errorString())
  return null
  }
  return _menuLevelComponent
 }

 // Clear all items 清空所有项
 function clear() {
 _closeOpenSubmenu()
 var items = _itemRegistry.clear()
 for (var i = items.length - 1; i >= 0; i--) {
 var child = items[i]
 // A failed submenu build can leave a thrown value where an item was expected;
 // skipping it keeps one failure from cascading into a second one here.
 // 子菜单构建失败可能在被当作项的位置留下抛出值; 跳过它可避免一次失败在此二次扩散。
 if (!child || typeof child.destroy !== "function") continue
 // destroy() 是延迟执行的，先设 visible=false 防止 _calcHeight 计入
 child.visible = false
 child.height = 0
 child.destroy()
 }
 Qt.callLater(_updateSize)
 }

 // ==================== Size 尺寸 ====================
 // Use cached values to avoid binding loop 使用缓存值避免绑定循环
 popupWidth: _cachedWidth
 implicitContentHeight: _cachedContentHeight

 Component.onDestruction: {
 _isDestroyed = true
 _closeOpenSubmenu()
 }

 Component.onCompleted: {
 _syncMenuItems()
 Qt.callLater(_updateSize)
 }
 onClosed: {
 _closeOpenSubmenu()
 dismissed()
 }
 onAboutToShow: {
 _updateSize()
 // Popup.Item exposes its reparented visual content after open() returns; refresh before the next frame. Popup.Item在open返回后才暴露重挂载内容，下一帧前重算
 if (_usesControlsPopup) Qt.callLater(_updateSize)
 }

 // ==================== Content 内容 ====================
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
 // Selectable custom widgets only need the click; hover is pointer-only
 // 可点自定义组件只需要点击; hover 属纯指针语义, 触摸端关闭追踪
 hoverEnabled: !Touch.isTouch
 cursorShape: Qt.ArrowCursor
 }
 }

 MenuSubmenuOpenTimer {
 id: submenuOpenTimer
 host: control
 }

  MenuActions {
  id: menuActions
  host: control
  itemContainer: menuContent.itemContainer
  separatorFactory: separatorComponent
  mouseAreaFactory: mouseAreaComponent
  }
 
 MenuContent {
 id: menuContent
 anchors.fill: parent
 menu: control
 }
}
