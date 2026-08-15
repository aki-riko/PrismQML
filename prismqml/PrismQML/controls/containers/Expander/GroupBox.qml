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
    
    // ==================== Public Props 公开属性 ====================
    property string title: ""
    property bool checkable: false      // Show checkbox in title 标题显示复选框
    property bool checked: true         // Checkbox state (only when checkable) 复选框状态
    property bool flat: false           // Flat style (no border) 扁平样式
    property int alignment: Qt.AlignLeft // Title alignment 标题对齐
    default property alias content: contentArea.data
    // Title mask color must match its solid parent surface. 标题遮罩色必须匹配实色父级表面。
    // Dialog consumers should use Enums.dialogColor. 对话框调用方应使用 Enums.dialogColor。
    property color titleBgColor: Enums.backgroundColor

    // ==================== Readonly State 只读状态 ====================
    readonly property real _borderRadius: Enums.surfaceRadius(Enums.radius.small)
    // Title height - fixed value based on typography 标题高度 - 基于字体的固定值
    readonly property real _titleHeight: title !== "" ? Enums.typography.body + Enums.spacing.s : 0
    readonly property real _titleLeftMargin: {
        if (alignment === Qt.AlignHCenter) return (width - titleLoader.width) / 2
        if (alignment === Qt.AlignRight) return width - titleLoader.width - Enums.spacing.xl
        return Enums.spacing.xl
    }
    readonly property bool _contentEnabled: !checkable || checked
    readonly property real _titleY: _titleHeight / 2
    readonly property real _borderWidth: Enums.surfaceBorderWidth(Enums.border.thin)
    readonly property real _titleGapLeft: title !== ""
        ? Math.min(width, Math.max(0, _titleLeftMargin - Enums.spacing.xs))
        : 0
    readonly property real _titleGapRight: title !== ""
        ? Math.max(_titleGapLeft, Math.min(width,
            _titleLeftMargin + titleLoader.width + Enums.spacing.xs))
        : 0

    // ==================== Signals 信号 ====================
    signal toggled(bool checked)        // Emitted when checkbox toggled 复选框切换时触发
    signal clicked(bool checked)        // Emitted when checkbox clicked 复选框点击时触发

    // ==================== Public Methods 公开方法 ====================
    function setChecked(value) {
        if (checkable) {
            checked = value
            if (titleLoader.item) titleLoader.item.checked = value
        }
    }

    function isChecked() {
        return checkable ? checked : true
    }

    function getTitle() { return title }

    // ==================== Size 尺寸 ====================
    contentWidth: Enums.controlSize.cardContentWidth
    contentHeight: contentArea.childrenRect.height + _titleHeight + Enums.spacing.l * 2

    // ==================== Content 内容 ====================
    // Border 边框
    Rectangle {
        id: borderRect
        objectName: "groupBoxStandardBorder"
        anchors.fill: parent
        anchors.topMargin: control._titleY
        color: Enums.transparent
        radius: control._borderRadius
        border.width: control._borderWidth
        border.color: Enums.hasOutlinedSurfaces ? Enums.stateColor.border : Enums.stateColor.groupBorder
        visible: !control.flat && !Enums.isVintageTicket
    }

    // Title background covers the border gap for solid-background skins.
    // 实色背景皮肤用标题遮罩覆盖边框缺口，复古票据改用真实断开的顶边。
    Rectangle {
        id: titleBackground
        objectName: "groupBoxTitleBackground"
        visible: control.title !== "" && !control.flat && !Enums.isVintageTicket
        x: control._titleLeftMargin - Enums.spacing.xs
        y: 0
        width: titleLoader.width + Enums.spacing.xs * 2
        height: control._titleHeight
        color: control.titleBgColor
    }

    // Vintage ticket border leaves the title gap open so parent paper remains visible.
    // 复古票据边框在标题处真实断开，让父级纸纹自然透出。
    Item {
        id: ticketBorder

        readonly property real lineWidth: control._borderWidth
        readonly property color lineColor: Enums.hasOutlinedSurfaces
            ? Enums.stateColor.border : Enums.stateColor.groupBorder

        objectName: "groupBoxTicketBorder"
        x: 0
        y: control._titleY
        width: parent.width
        height: parent.height - control._titleY
        visible: !control.flat && Enums.isVintageTicket

        Rectangle {
            id: ticketTopLeft
            objectName: "groupBoxTicketTopLeft"
            x: 0
            y: 0
            width: control._titleGapLeft
            height: ticketBorder.lineWidth
            color: ticketBorder.lineColor
        }

        Rectangle {
            id: ticketTopRight
            objectName: "groupBoxTicketTopRight"
            x: control._titleGapRight
            y: 0
            width: Math.max(0, ticketBorder.width - x)
            height: ticketBorder.lineWidth
            color: ticketBorder.lineColor
        }

        Rectangle {
            id: ticketLeft
            objectName: "groupBoxTicketLeft"
            x: 0
            y: 0
            width: ticketBorder.lineWidth
            height: ticketBorder.height
            color: ticketBorder.lineColor
        }

        Rectangle {
            id: ticketRight
            objectName: "groupBoxTicketRight"
            x: ticketBorder.width - ticketBorder.lineWidth
            y: 0
            width: ticketBorder.lineWidth
            height: ticketBorder.height
            color: ticketBorder.lineColor
        }

        Rectangle {
            id: ticketBottom
            objectName: "groupBoxTicketBottom"
            x: 0
            y: ticketBorder.height - ticketBorder.lineWidth
            width: ticketBorder.width
            height: ticketBorder.lineWidth
            color: ticketBorder.lineColor
        }
    }
    
    // Title loader 标题加载器
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
    
    // Content area 内容区域
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
