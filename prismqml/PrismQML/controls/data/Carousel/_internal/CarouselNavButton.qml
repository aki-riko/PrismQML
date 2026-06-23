// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../buttons"

// CarouselNavButton - Carousel navigation button 轮播导航按钮
Button {
    id: control
    
    // ==================== Props 属性 ====================
    property bool isNext: true  // true=next, false=prev 是否为下一个按钮
    property bool isVertical: false  // Vertical mode 垂直模式
    
    // ==================== Button Config 按钮配置 ====================
    style: Enums.button.style_default
    shape: Enums.button.shape_default
    
    icon: {
        if (control.isVertical) {
            return control.isNext ? Enums.icon.chevron_down : Enums.icon.chevron_up
        }
        return control.isNext ? Enums.icon.chevron_right : Enums.icon.chevron_left
    }
    
    width: Enums.controlSize.flipViewNavButton
    height: Enums.controlSize.flipViewNavButton
}
