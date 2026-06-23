// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../inputs/Toggle"
import "../../data/Label"
import ".."

// GroupBox - Qt-style group box with optional checkbox 分组框（支持可选复选框）
// Compatible with QGroupBox API 兼容QGroupBox接口
Widget {
    id: control
    
    // ==================== QGroupBox Compatible Props QGroupBox兼容属性 ====================
    property string title: ""
    property bool checkable: false      // Show checkbox in title 标题显示复选框
    property bool checked: true         // Checkbox state (only when checkable) 复选框状态
    property bool flat: false           // Flat style (no border) 扁平样式
    property int alignment: Qt.AlignLeft // Title alignment 标题对齐
    
    // ==================== Content 内容 ====================
    default property alias content: contentArea.data
    
    // ==================== Signals 信号 ====================
    signal toggled(bool checked)        // Emitted when checkbox toggled 复选框切换时触发
    signal clicked(bool checked)        // Emitted when checkbox clicked 复选框点击时触发
    
    // ==================== Size 尺寸 ====================
    contentWidth: Enums.controlSize.cardContentWidth
    contentHeight: contentArea.childrenRect.height + _titleHeight + Enums.spacing.l * 2
    
    // ==================== Internal 内部属性 ====================
    // Title height - fixed value based on typography 标题高度 - 基于字体的固定值
    readonly property real _titleHeight: title !== "" ? Enums.typography.body + Enums.spacing.s : 0
    readonly property real _titleLeftMargin: {
        if (alignment === Qt.AlignHCenter) return (width - titleLoader.width) / 2
        if (alignment === Qt.AlignRight) return width - titleLoader.width - Enums.spacing.xl
        return Enums.spacing.xl
    }
    readonly property bool _contentEnabled: !checkable || checked
    readonly property real _borderRadius: Enums.radius.small
    readonly property real _titleY: _titleHeight / 2

    // Title 文字下方的"边框遮盖块"颜色 — 必须与父容器底色一致, 否则断口处显出
    // 不同色块. 默认 backgroundColor 适合主页面 (浅蓝灰), dialog 内应显式设
    // Enums.dialogColor (白) 才不会突兀.
    property color titleBgColor: Enums.backgroundColor

    // ==================== Methods 方法 ====================
    function setChecked(value) {
        if (checkable) {
            checked = value
            if (titleLoader.item) titleLoader.item.checked = value
        }
    }

    function isChecked() {
        return checkable ? checked : true
    }

    // ==================== Public Methods 公共方法 ====================
    function getTitle() { return title }

    // ==================== Border 边框 ====================
    Rectangle {
        id: borderRect
        anchors.fill: parent
        anchors.topMargin: control._titleY
        color: "transparent"
        radius: control._borderRadius
        border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth : Enums.border.thin
        border.color: Enums.isNeobrutalism ? Enums.stateColor.border : Enums.stateColor.groupBorder
        visible: !control.flat
    }

    // Title background to cover border gap 标题背景遮盖边框缺口
    // height 必须 = _titleHeight 完全覆盖 title 全部高度, 否则边框线 (在 _titleY
    // 处) 会从 title 文字下半部分穿过, 用户看到的"断口"
    Rectangle {
        visible: control.title !== "" && !control.flat
        x: control._titleLeftMargin - Enums.spacing.xs
        y: 0
        width: titleLoader.width + Enums.spacing.xs * 2
        height: control._titleHeight
        color: control.titleBgColor
    }
    
    // ==================== Title Loader 标题加载器 ====================
    Loader {
        id: titleLoader
        x: control._titleLeftMargin
        y: 0
        active: control.title !== ""
        sourceComponent: control.checkable ? checkboxTitle : labelTitle
    }
    
    // CheckBox title component 复选框标题组件
    Component {
        id: checkboxTitle
        CheckBox {
            text: control.title
            checked: control.checked
            type: Enums.toggle.type_default
            onToggled: {
                control.checked = checked
                control.toggled(checked)
                control.clicked(checked)
            }
        }
    }
    
    // Label title component 标签标题组件
    Component {
        id: labelTitle
        Label {
            text: control.title
            type: Enums.label.type_body
            color: Enums.stateColor.textStrong
        }
    }
    
    // ==================== Content Area 内容区域 ====================
    Item {
        id: contentArea
        objectName: "contentArea"
        x: Enums.spacing.l
        y: control._titleHeight + Enums.spacing.l
        width: parent.width - Enums.spacing.l * 2
        // 高度按 anchors 思路: 占满父级剩余空间。
        // 旧实现 height = childrenRect.height 会与 Layout.* 子元素形成 binding loop:
        //   父 Layout.preferredHeight 设了 → control 高度固定 →
        //   子 Layout 元素响应父 height 调整自己 → childrenRect 变 →
        //   contentArea.height 跟着变 → 子 Layout 又重 layout → loop
        height: parent.height - control._titleHeight - Enums.spacing.l * 2
        enabled: control._contentEnabled
        opacity: control._contentEnabled ? 1.0 : Enums.opacityLevel.disabled
    }
}
