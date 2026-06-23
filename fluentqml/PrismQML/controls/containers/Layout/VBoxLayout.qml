// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import "../../.."

// VBoxLayout - 垂直布局（继承 Widget 基类）
// 与 Button 等组件保持一致的架构：Widget { ColumnLayout { ... } }
Widget {
    id: control
    
    // ==================== Properties 属性 ====================
    property int margins: 0
    property int leftMargin: margins
    property int topMargin: margins
    property int rightMargin: margins
    property int bottomMargin: margins
    property int spacing_: Enums.spacing.m
    property alias spacing: col.spacing
    
    // Content container 内容容器
    default property alias content: col.data

    // Padding aliases 内边距别名
    property int leftPadding: leftMargin
    property int rightPadding: rightMargin
    property int topPadding: topMargin
    property int bottomPadding: bottomMargin

    // Layout attached properties for parent layout 用于父布局的附加属性
    property int layoutAlignment: 0

    // ==================== Qt-Style Layout Methods Qt风格布局方法 ====================
    function addWidget(widget, stretch) {
        if (widget) {
            widget.parent = col
            // Set Layout attached properties 设置布局附加属性
            widget.Layout.fillWidth = true
        }
    }

    function insertWidget(index, widget) {
        if (widget) {
            widget.parent = col
        }
    }

    function removeWidget(widget) {
        if (widget && widget.parent === col) {
            widget.parent = null
        }
    }


    function setContentsMargins(left, top, right, bottom) {
        leftPadding = left
        topPadding = top
        rightPadding = right
        bottomPadding = bottom
    }

    function count() {
        return col.children.length
    }

    // itemAt - 获取指定索引的子组件
    function itemAt(index) {
        if (index >= 0 && index < col.children.length) {
            return col.children[index]
        }
        return null
    }

    // indexOf - 获取组件索引
    function indexOf(widget) {
        for (var i = 0; i < col.children.length; i++) {
            if (col.children[i] === widget) {
                return i
            }
        }
        return -1
    }

    // isEmpty - 检查布局是否为空
    function isEmpty() {
        return col.children.length === 0
    }

    // clear - 清空所有子组件
    function clear() {
        for (var i = col.children.length - 1; i >= 0; i--) {
            col.children[i].parent = null
        }
    }

    // ==================== Size 尺寸 ====================
    // contentWidth/contentHeight 驱动 Widget 的 implicitWidth/implicitHeight
    contentWidth: col.implicitWidth + leftPadding + rightPadding
    contentHeight: col.implicitHeight + topPadding + bottomPadding
    
    // 覆盖 Widget 默认 width：Layout 必须填充父容器宽度（保持原 Item 行为）
    // Widget 默认 width 优先使用 contentWidth，但 Layout 应该填充父宽度
    width: preferredWidth > 0 ? preferredWidth : (parent ? parent.width : implicitWidth)
    
    // 条件性高度绑定：仅在不使用 Layout.fillHeight 时绑定高度
    Binding {
        target: control
        property: "height"
        value: control.preferredHeight > 0 ? control.preferredHeight : control.implicitHeight
        when: !control.layoutFillHeight
    }
    
    // 让 Layout 系统处理尺寸
    Layout.preferredWidth: preferredWidth > 0 ? preferredWidth : -1
    Layout.preferredHeight: preferredHeight > 0 ? preferredHeight : -1
    
    // Layout 核心职责：向父 Widget 传播尺寸
    // Layout 核心职责：向父 Widget 传播尺寸 (使用 Binding 更稳健)
    Binding {
        target: parent
        property: "contentWidth"
        value: contentWidth
        when: parent && parent.contentWidth !== undefined
    }
    Binding {
        target: parent
        property: "contentHeight"
        value: contentHeight
        when: parent && parent.contentHeight !== undefined
    }
    
    // 覆盖 Widget 默认值：VBoxLayout 默认填充宽度和高度
    layoutFillWidth: true
    layoutFillHeight: true

    Layout.alignment: layoutAlignment

    // Internal ColumnLayout 内部 ColumnLayout
    ColumnLayout {
        id: col
        objectName: "layout"
        anchors.fill: parent
        anchors.leftMargin: control.leftPadding
        anchors.rightMargin: control.rightPadding
        anchors.topMargin: control.topPadding
        anchors.bottomMargin: control.bottomMargin
        spacing: control.spacing_
    }
}
