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
 if (!action || !submenuComponent) return action
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
 if (!action || !submenuComponent) return
 if (_openSubmenu && _openSubmenuAction === action) return

 _closeOpenSubmenu()
 // A row may already own its level (data-built cascade, QAction::menu()); reuse that
 // instance so whatever was added to it is what actually opens.
 // 行可能已经持有自己的层级(数据构建的级联, 即 QAction::menu()); 复用该实例, 使加入其中的
 // 内容正是实际打开的内容。
 var submenu = action._level !== undefined && action._level !== null
  ? action._level
  : submenuComponent.createObject(null, initialProperties || {})
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

 // Add custom widget to menu 添加自定义组件
 // @param widget: Item - the widget to add
 // @param selectable: bool - whether clickable (default false)
 // @param onClick: function - click callback
 function addWidget(widget, selectable, onClick) {
 if (!widget) return
 widget.parent = menuContent.itemContainer
 _registerMenuItem(widget)
 widget.width = Qt.binding(function() { return menuContent.itemContainer.width })
 
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
 var separator = separatorComponent.createObject(menuContent.itemContainer)
 _registerMenuItem(separator)
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
 
 var action = actionComponent.createObject(menuContent.itemContainer, props)
 _registerMenuItem(action)
 // triggered → actionTriggered + close 由 MenuContent.onChildrenChanged 统一接管,
 // 这里不再 connect, 避免双发。
 Qt.callLater(_updateSize)
 return action
 }
 
 // Add multiple actions 批量添加动作
 // @param actions: array of {text, icon, shortcut, ...options}
 function addActions(actionsArray) {
 var actions = actionsArray && typeof actionsArray.length === "number" ? actionsArray : []
 for (var i = 0; i < actions.length; i++) {
 var a = actions[i]
 if (!a) continue
 addAction(a.text, a.icon, a.shortcut, a)
 }
 }
 
 // Get action by ID 按ID获取动作
 // @param actionId: string
 // @returns Action item or null
 function getAction(actionId) {
 var items = _menuItems()
 for (var i = 0; i < items.length; i++) {
 var child = items[i]
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
 _unregisterMenuItem(action)
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
 return _bindSubmenuAction(action, submenuComponent, {})
 }

 // Add data-backed submenu 添加数据驱动子菜单
 function addSubmenuActions(text, icon, actionsArray) {
 var action = addAction(text, icon, "", {
 "actionId": "_submenu_" + text,
 "hasSubmenu": true
 })
 var submenuComponent = Qt.createComponent(Qt.resolvedUrl("SystemTrayMenu.qml"))
 return _bindSubmenuAction(action, submenuComponent, {
 "initialActions": actionsArray || []
 })
 }
 
 // Path carried by a leaf action id 叶子 action id 携带的路径
 // A data-built level addresses its leaves by a namespaced id, so a commit at any depth
 // can be resolved back to the path the user actually walked.
 // 数据构建的层级以带命名空间的 id 寻址其叶子, 因此任意深度的提交都能还原为用户实际走过的路径。
 // @param actionId: string - id reported by actionTriggered 动作上报的 id
 // @returns array, or null when the id addresses no leaf 叶子路径; 非叶子返回 null
 function leafPath(actionId) {
  var id = String(actionId)
  if (id.indexOf("leaf:") !== 0) return null
  return id.slice(5).split("\u0001")
 }

 // Add a whole level from nested data 由嵌套数据添加一整层
 // A node carrying children becomes an owner row whose level is built by recursing into
 // the same children, so a caller feeds nested data straight into the menu stack and the
 // stack carries the cascade: anchored placement, hover opening and dismissal all come
 // from MenuCore rather than from the caller.
 // 带 children 的节点成为父行, 其层级由对同一批子节点的递归构建而来: 调用方把嵌套数据直接
 // 喂给菜单栈, 级联由栈承载 —— 锚定定位、悬停展开与收起都来自 MenuCore, 而非调用方。
 // @param nodes: array of string | { text, icon, enabled, children } 节点数组
 // @param basePath: array - path prefix of these nodes 这批节点的路径前缀
 // @returns array of created items 创建出的项
 function addNodes(nodes, basePath) {
  var created = []
  var list = nodes && typeof nodes.length === "number" ? nodes : []
  var prefix = basePath || []
  for (var i = 0; i < list.length; i++) {
  var node = list[i]
  if (node === null || node === undefined) continue
  var isText = typeof node === "string"
  var text = isText ? node : (node.text || "")
  var icon = isText ? "" : (node.icon || "")
  var enabled = isText ? true : (node.enabled === undefined ? true : !!node.enabled)
  var path = prefix.concat([text])
  var children = isText ? null : node.children

  if (children && typeof children.length === "number" && children.length > 0) {
  var branch = addSubmenuLevel(text, icon)
  if (!branch) continue
  if (branch.action) {
  branch.action.enabled = enabled
  created.push(branch.action)
  }
  branch.level.addNodes(children, path)
  continue
  }

  var leaf = addAction(text, icon, "", {
  "actionId": "leaf:" + path.join("\u0001"),
  "enabled": enabled
  })
  if (leaf) created.push(leaf)
  }
  Qt.callLater(_updateSize)
  return created
 }

 // Create a level and attach it to an owner row 创建层级并挂到父行上
 // Mirrors QMenu::addMenu(title, icon): the returned level is what this row opens, with
 // anchored placement, hover delay, the arrow request and dismissal already wired.
 // 对应 QMenu::addMenu(title, icon): 返回的层级即该行打开的层级, 锚定定位、悬停延迟、箭头
 // 请求与收起都已接好。
 // @returns object - { action: the owner row, level: the level it opens } 父行与其层级
 function addSubmenuLevel(text, icon) {
  var component = _levelComponent()
  if (!component) return null
  var action = addAction(text, icon, "", { "hasSubmenu": true })
  if (!action) return null
  var level = component.createObject(null, {})
  if (!level) return null
  action._level = level
  _bindSubmenuAction(action, component, {})
  Qt.callLater(_updateSize)
  return { "action": action, "level": level }
 }

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
 
 MenuContent {
 id: menuContent
 anchors.fill: parent
 menu: control
 }
}
