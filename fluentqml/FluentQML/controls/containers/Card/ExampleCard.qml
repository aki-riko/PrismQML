// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Effects
import "../../../"
import "../../../effects"
import "../../data/Label"

Item {
 id: control

 property string title: ""
 property string description: ""
 property string componentName: ""
 property int orientation: Qt.Horizontal // Qt.Horizontal=横向Flow / Qt.Vertical=纵向Column
 default property alias content: contentFlow.data

 // implicitWidth 不再绑 parent.width — 那让"自然尺寸"跟随父链抖动, N 个 ExampleCard
 // 实例同步抖动会冲击上层 ScrollArea contentHolder.childrenRect 触发重排, 是滚动卡顿放大器.
 // 正确做法: implicitWidth 给一个稳定兜底, width 由父链强绑(parent.width).
 implicitWidth: 600
 implicitHeight: mainColumn.implicitHeight
 width: parent ? parent.width : implicitWidth

 // 视口裁剪: 视口外不渲染内部 (ShadowedRectangle + 所有内容), 但保持占位高度不变.
 // Qt 场景图不做 CPU 侧裁剪, 手动 visible=false 是官方推荐做法.
 ViewportCulling { id: _vpc }

 Column {
 id: mainColumn
 x: 0 // 确保列左对齐
 width: parent.width
 spacing: Enums.spacing.l // 12px
 visible: _vpc.inViewport
 
 // Title 标题
 Label {
 type: Enums.label.type_body_strong
 text: control.title
 visible: text !== ""
 }
 
 // Card container - 用于圆角裁剪，留出阴影空间
 Item {
 id: cardContainer
 // Shadow needs space to extend outward - use level2 soft shadow 阴影需要向外扩展的空间 - 使用 level2 柔和阴影

 property int shadowMargin: Enums.shadow.level2.blur + Enums.shadow.level2.offset + 4
 
 // Leave enough space for shadow 为阴影留出足够的空间
 width: parent.width
 height: card.height + shadowMargin
 clip: false
 
 // Card 卡片 - 使用 ShadowedRectangle 高性能阴影
 ShadowedRectangle {
 id: card
 width: parent.width
 height: cardContent.implicitHeight
 radius: Enums.radius.dialog
 // Opaque background: light gray for light, dark gray for dark theme 不透明背景：浅色用浅灰，深色用深灰

 color: Enums.isDark ? Enums.exampleCardColors.bgDark : Enums.exampleCardColors.bgLight
 
 // Shadow: soft shadow, bottom-right direction 阴影：柔和阴影，右下角方向
 // neo: 关软阴影, 改用硬阴影 NeoShadow
 shadowVisible: !Enums.isNeobrutalism

 y: cardContainer.shadowMargin / 2
 shadowLevel: Enums.shadow.level2
 shadowOffsetX: Enums.shadow.level2.offset // 右偏移
 shadowOffsetY: Enums.shadow.level2.offset // 下偏移

 // neo 硬阴影
 NeoShadow {
 target: card
 visible: Enums.isNeobrutalism
 z: -1
 }

 Column {
 id: cardContent
 width: parent.width
 
 // Content area 内容区 - padding: 12px
 Item {
 width: parent.width
 height: contentFlow.height + (componentLabel.visible ? componentLabel.height + Enums.spacing.m : 0) + Enums.spacing.xxxl
 
 // Content layout: select horizontal/vertical based on orientation 内容区布局：根据 orientation 选择横向/纵向

 Flow {
 id: contentFlow
 objectName: "contentFlow"
 x: 12
 y: 12
 width: parent.width - 24
 spacing: control.orientation === Qt.Vertical ? Enums.spacing.s : Enums.spacing.l
 flow: control.orientation === Qt.Vertical ? Flow.TopToBottom : Flow.LeftToRight
 }
 
 // Component name label
 Label {
 id: componentLabel
 type: Enums.label.type_caption
 x: 12
 y: contentFlow.y + contentFlow.height + Enums.spacing.m
 text: control.componentName
 color: Enums.accentColor
 visible: control.componentName !== ""
 }
 }
 
 // Source widget 底部区域 - 底部圆角
 // Only render when description exists 仅在有描述时渲染
 Loader {
 active: control.description !== ""
 width: parent.width
 sourceComponent: Item {
 width: parent ? parent.width : 0
 height: descText.implicitHeight + 20
 clip: true
 
 // Bottom rounded background: offset rounded rect upward to show only bottom corners 底部圆角背景：利用圆角矩形向上偏移，只露出底部圆角

 Rectangle {
 width: parent.width
 height: parent.height + card.radius
 y: -card.radius
 radius: card.radius
 color: Enums.isDark ? Enums.exampleCardColors.descBgDark : Enums.exampleCardColors.descBgLight
 }
 
 // Top separator line 顶部分隔线
 Separator {
 width: parent.width
 // neo: 实黑 2px 硬分隔线(对齐偶数像素宽, 消除细黑线滚动抖动闪烁)
 lineColor: Enums.isNeobrutalism ? Enums.neo.borderColor : Enums.stateColor.divider
 lineWidth: Enums.isNeobrutalism ? Enums.neo.borderWidth : Enums.border.thin
 }
 
 Label {
 id: descText
 type: Enums.label.type_body
 x: 18
 anchors.verticalCenter: parent.verticalCenter
 width: parent.width - 36
 text: control.description
 color: Enums.textColor.secondary
 wrapMode: Text.WordWrap
 }
 }
 }
 }
 }
 
 // Border 边框 - 独立层，不受阴影影响
 Rectangle {
 id: borderRect
 anchors.fill: card
 radius: card.radius
 color: "transparent"
 border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth : 1
 border.color: Enums.isNeobrutalism ? Enums.neo.borderColor
 : (Enums.isDark ? Enums.exampleCardColors.borderDark : Enums.stateColor.borderSubtle)
 }
 }
 }
}