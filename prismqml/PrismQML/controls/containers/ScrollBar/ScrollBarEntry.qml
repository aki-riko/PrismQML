// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."

// ScrollBar - Pure QtQuick implementation 滚动条
Rectangle {
 id: control

 // ==================== Public Props 公开属性 ====================
 property Flickable flickable: null
 property bool horizontal: false
 property int minThumbSize: 30

 // ==================== Internal Props 内部属性 ====================
 // Prevent flash: disable animation until ready 防止闪现：初始化完成前禁用动画
 property bool _animEnabled: false

 // ==================== Readonly State 只读状态 ====================
 readonly property bool hovered: mouseArea.containsMouse
 readonly property bool active: flickable && (horizontal ? flickable.contentWidth > flickable.width : flickable.contentHeight > flickable.height)
 readonly property color _scrollTrackColor: Enums.stateColor.scrollTrack
 readonly property color _scrollThumbDefaultColor: Enums.stateColor.scrollHandleDefault
 readonly property color _scrollThumbHoverColor: Enums.stateColor.scrollHandleHover
 readonly property color _scrollThumbPressedColor: Enums.accentColor
 readonly property color _scrollThumbColor: thumbArea.pressed ? _scrollThumbPressedColor : (hovered ? _scrollThumbHoverColor : _scrollThumbDefaultColor)

 // ==================== Signals 信号 ====================
 signal valueChanged(int value)
 signal sliderPressed()
 signal sliderReleased()
 signal sliderMoved()

 // ==================== Internal Methods 内部方法 ====================
 function _safeRatio(viewSize, contentSize) {
  if (!isFinite(viewSize) || !isFinite(contentSize) || contentSize <= 0) return 0
  return Math.max(0, Math.min(1, viewSize / contentSize))
 }

 function _safePosition(contentPos, origin, contentSize, viewSize) {
  var maxScroll = contentSize - viewSize
  if (!isFinite(contentPos) || !isFinite(origin) || !isFinite(maxScroll) || maxScroll <= 0) return 0
  return Math.max(0, Math.min(1, (contentPos - origin) / maxScroll))
 }

 Component.onCompleted: Qt.callLater(() => { _animEnabled = true })

 // ==================== Size 尺寸 ====================
 implicitWidth: horizontal ? 200 : 8
 implicitHeight: horizontal ? 8 : 200
 radius: width / 2
 color: Enums.transparent
 visible: active // Only visible when needed 仅需要时可见
 opacity: (hovered || thumbArea.pressed) ? 1 : 0.6
 
 Behavior on opacity {
 enabled: control._animEnabled
 NumberAnimation { duration: Enums.duration.normal }
 }

 // ==================== Content 内容 ====================
 // Track 轨道
 Rectangle {
 anchors.fill: parent
 radius: parent.radius
 color: control._scrollTrackColor
 }
 
 // Thumb 滑块
 Rectangle {
 id: thumb
 
 property real ratio: horizontal ?
 (flickable ? control._safeRatio(flickable.width, flickable.contentWidth) : 0) :
 (flickable ? control._safeRatio(flickable.height, flickable.contentHeight) : 0)
 
 property real position: horizontal ?
 (flickable ? control._safePosition(flickable.contentX, flickable.originX, flickable.contentWidth, flickable.width) : 0) :
 (flickable ? control._safePosition(flickable.contentY, flickable.originY, flickable.contentHeight, flickable.height) : 0)
 
 x: horizontal ? position * (parent.width - width) : 0
 y: horizontal ? 0 : position * (parent.height - height)
 width: horizontal ? Math.max(control.minThumbSize, parent.width * ratio) : parent.width
 height: horizontal ? parent.height : Math.max(control.minThumbSize, parent.height * ratio)
 radius: width / 2
 
 color: control._scrollThumbColor
 
 Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
 
 MouseArea {
 id: thumbArea

 property real startPos: 0
 property real startScroll: 0

 anchors.fill: parent
 hoverEnabled: true
 
 onPressed: {
 startPos = horizontal ? mouseX : mouseY
 startScroll = horizontal ? flickable.contentX : flickable.contentY
 control.sliderPressed()
 }
 
 onReleased: {
 control.sliderReleased()
 }
 
 onPositionChanged: {
  if (pressed && flickable) {
  var delta = horizontal ? (mouseX - startPos) : (mouseY - startPos)
  var travel = horizontal ? (control.width - thumb.width) : (control.height - thumb.height)
  if (!isFinite(travel) || travel <= 0) return
  var scrollDelta = delta / travel
  var maxScroll = horizontal ? (flickable.contentWidth - flickable.width) : (flickable.contentHeight - flickable.height)
  if (!isFinite(maxScroll) || maxScroll <= 0) return
  var minScroll = horizontal ? flickable.originX : flickable.originY
 var newScroll = startScroll + scrollDelta * maxScroll

 if (horizontal) {
 flickable.contentX = Math.max(minScroll, Math.min(minScroll + maxScroll, newScroll))
 control.valueChanged(Math.round(flickable.contentX))
 } else {
 flickable.contentY = Math.max(minScroll, Math.min(minScroll + maxScroll, newScroll))
 control.valueChanged(Math.round(flickable.contentY))
 }
 control.sliderMoved()
 }
 }
 }
 }
 
 MouseArea {
 id: mouseArea
 anchors.fill: parent
 hoverEnabled: true
 propagateComposedEvents: true
 onPressed: (mouse) => { mouse.accepted = false }
 }
}
