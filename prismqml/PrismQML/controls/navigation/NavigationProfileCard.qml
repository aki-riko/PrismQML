// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../.."
import "../data/Avatar"
import "../data/Label"

// NavigationProfileCard - Navigation bar user profile card 导航栏用户资料卡片
// Props: avatar, title, subtitle 属性：头像、用户名、副标题
Item {
 id: control
 
 // ==================== Props 属性 ====================
 property string avatar: "" // Avatar image path or icon name 头像图片路径或图标名
 property string title: "" // Username/title 用户名/标题
 property string subtitle: "" // Subtitle (e.g. email) 副标题（如邮箱）
 property bool isCompacted: true // Compact mode 是否紧凑模式
 
 // ==================== Internal 内部属性 ====================
 property int _avatarSizeCompact: Enums.spacing.xxxl
 property int _avatarSizeExpanded: Enums.controlSize.navBarHeight
 property int _currentAvatarSize: isCompacted ? _avatarSizeCompact : _avatarSizeExpanded
 
 // Size 尺寸
 width: isCompacted ? Enums.controlSize.navItemHeight : Enums.controlSize.navFilledItemWidth + Enums.spacing.xxxl
 height: isCompacted ? Enums.controlSize.topNavItemHeight : Enums.controlSize.cardHeight
 
 // ==================== Background 背景 ====================
 Rectangle {
 id: background
 anchors.fill: parent
 radius: Enums.radius.small
 color: mouseArea.containsMouse ? 
 (Enums.isDark ? Qt.rgba(1, 1, 1, 0.05) : Qt.rgba(0, 0, 0, 0.03)) : 
 Enums.transparent
 
 Behavior on color { ColorAnimation { duration: Enums.duration.fast } }
 }
 
 // ==================== Avatar 头像 ====================
 Avatar {
 id: avatarWidget
 size: _currentAvatarSize
 source: control.avatar.startsWith("image://") || control.avatar.includes("/") || control.avatar.includes("\\") ? 
 control.avatar : ""
 text: control.title
 
 // Position 位置
 x: isCompacted ? (parent.width - size) / 2 : Enums.spacing.m
 anchors.verticalCenter: parent.verticalCenter
 
 Behavior on size { NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutCubic } }
 Behavior on x { NumberAnimation { duration: Enums.duration.medium; easing.type: Easing.OutCubic } }
 }
 
 // ==================== Text Area 文本区域 ====================
 Column {
 id: textColumn
 anchors.left: avatarWidget.right
 anchors.leftMargin: Enums.spacing.l
 anchors.verticalCenter: parent.verticalCenter
 anchors.right: parent.right
 anchors.rightMargin: Enums.spacing.l
 spacing: Enums.spacing.xxs
 opacity: isCompacted ? 0 : 1
 visible: !isCompacted
 
 Behavior on opacity { NumberAnimation { duration: Enums.duration.normal } }
 
 // Title 标题
 Label {
 type: Enums.label.type_body_strong
 text: control.title
 width: parent.width
 elide: Text.ElideRight
 color: Enums.textColor.primary
 }
 
 // Subtitle 副标题
 Label {
 type: Enums.label.type_caption
 text: control.subtitle
 width: parent.width
 elide: Text.ElideRight
 color: Enums.textColor.secondary
 visible: control.subtitle !== ""
 }
 }
 
 // ==================== Interaction 交互 ====================
 MouseArea {
 id: mouseArea
 anchors.fill: parent
 hoverEnabled: true
 cursorShape: Qt.PointingHandCursor
 
 onPressed: {
 background.color = Enums.isDark ? 
 Qt.rgba(1, 1, 1, 0.08) : Qt.rgba(0, 0, 0, 0.05)
 }
 
 onReleased: {
 background.color = containsMouse ? 
 (Enums.isDark ? Qt.rgba(1, 1, 1, 0.05) : Qt.rgba(0, 0, 0, 0.03)) : 
 Enums.transparent
 }
 
 onClicked: {
 control.clicked()
 }
 }
 
 // ==================== Signals 信号 ====================
 signal clicked()
}
