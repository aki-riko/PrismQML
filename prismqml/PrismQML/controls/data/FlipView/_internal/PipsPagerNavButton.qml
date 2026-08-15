// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../buttons"

// PipsPagerNavButton - Dynamic pager navigation button 分页器动态翻页按钮
// Owns button visuals while PipsPagerCore retains creation and lifetime control.
// 承载按钮视觉，PipsPagerCore 保留创建与生命周期控制。
ButtonCore {
    id: button

    // ==================== Required Props 必需属性 ====================
    required property var pagerControl
    required property bool isNext

    // ==================== Size 尺寸 ====================
    objectName: isNext ? "pipsNextButton" : "pipsPrevButton"
    visible: isNext
        ? pagerControl._isNextButtonVisible()
        : pagerControl._isPrevButtonVisible()
    style: Enums.button.style_transparent
    shape: Enums.button.shape_pill
    icon: pagerControl.vertical
        ? (isNext ? Enums.icon.chevron_down : Enums.icon.chevron_up)
        : (isNext ? Enums.icon.chevron_right : Enums.icon.chevron_left)
    iconSize: Enums.iconSize.micro
    width: pagerControl._buttonSize
    height: pagerControl._buttonSize

    anchors {
        left: !pagerControl.vertical && !isNext ? parent.left : undefined
        right: !pagerControl.vertical && isNext ? parent.right : undefined
        top: pagerControl.vertical && !isNext ? parent.top : undefined
        bottom: pagerControl.vertical && isNext ? parent.bottom : undefined
        horizontalCenter: pagerControl.vertical ? parent.horizontalCenter : undefined
        verticalCenter: pagerControl.vertical ? undefined : parent.verticalCenter
    }

    // ==================== Signals 信号 ====================
    onClicked: {
        if (isNext) pagerControl.next()
        else pagerControl.previous()
    }
}
