// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."

// ScrollBar - Pure QtQuick implementation 滚动条
Rectangle {
 id: control
 
 property Flickable flickable: null
 property bool horizontal: false
 property int minThumbSize: 30
 signal valueChanged(int value)
 signal sliderPressed()
 signal sliderReleased()
 signal sliderMoved()
 readonly property bool hovered: mouseArea.containsMouse
 readonly property bool active: flickable && (horizontal ? flickable.contentWidth > flickable.width : flickable.contentHeight > flickable.height)
 
 // Prevent flash: disable animation until ready 防止闪现：初始化完成前禁用动画
 property bool _animEnabled: false
 Component.onCompleted: Qt.callLater(() => { _animEnabled = true })
 
 implicitWidth: horizontal ? 200 : 8
 implicitHeight: horizontal ? 8 : 200
 radius: width / 2
 color: "transparent"
 visible: active // Only visible when needed 仅需要时可见
 opacity: (hovered || thumbArea.pressed) ? 1 : 0.6
 
 Behavior on opacity {
 enabled: control._animEnabled
 NumberAnimation { duration: Enums.duration.normal }
 }
 
 // Track 轨道
 Rectangle {
 anchors.fill: parent
 radius: parent.radius
 color: Enums.stateColor.scrollTrack
 }
 
 // Thumb 滑块
 Rectangle {
 id: thumb
 
 property real ratio: horizontal ? 
 (flickable ? flickable.width / flickable.contentWidth : 0) :
 (flickable ? flickable.height / flickable.contentHeight : 0)
 
 property real position: horizontal ?
 (flickable ? flickable.contentX / (flickable.contentWidth - flickable.width) : 0) :
 (flickable ? flickable.contentY / (flickable.contentHeight - flickable.height) : 0)
 
 x: horizontal ? position * (parent.width - width) : 0
 y: horizontal ? 0 : position * (parent.height - height)
 width: horizontal ? Math.max(control.minThumbSize, parent.width * ratio) : parent.width
 height: horizontal ? parent.height : Math.max(control.minThumbSize, parent.height * ratio)
 radius: width / 2
 
 color: thumbArea.pressed ? Enums.accentColor : (hovered ? (Enums.stateColor.scrollHandleHover) : (Enums.stateColor.dropBorderHover))
 
 Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
 
 MouseArea {
 id: thumbArea
 anchors.fill: parent
 hoverEnabled: true
 
 property real startPos: 0
 property real startScroll: 0
 
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
 var scrollDelta = delta / (horizontal ? (control.width - thumb.width) : (control.height - thumb.height))
 var maxScroll = horizontal ? (flickable.contentWidth - flickable.width) : (flickable.contentHeight - flickable.height)
 var newScroll = startScroll + scrollDelta * maxScroll
 
 if (horizontal) {
 flickable.contentX = Math.max(0, Math.min(maxScroll, newScroll))
 control.valueChanged(Math.round(flickable.contentX))
 } else {
 flickable.contentY = Math.max(0, Math.min(maxScroll, newScroll))
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
