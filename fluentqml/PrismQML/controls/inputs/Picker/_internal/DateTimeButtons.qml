// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../buttons"

// DateTimeButtons - Button area for DateTimePicker popup 日期时间选择器弹窗按钮区域
// Uses Button for consistent styling 使用Button保持样式一致
Item {
    id: buttonArea
    
    // ==================== Props 属性 ====================
    property var control  // Parent DateTimePicker 父日期时间选择器
    
    width: parent ? parent.width : 200
    height: 52
    
    Row {
        anchors.centerIn: parent
        spacing: Enums.spacing.l
        
        // Confirm 确定
        Button {
            style: Enums.button.style_primary
            text: buttonArea.control ? buttonArea.control._confirmText : ""
            width: (buttonArea.width - Enums.spacing.l - Enums.spacing.xl) / 2
            onClicked: {
                var c = buttonArea.control
                if (!c) return
                if (c._hasDate) { c.year = c._tempYear; c.month = c._tempMonth; c.day = c._tempDay }
                if (c._hasTime) { c.hour = c._tempHour; c.minute = c._tempMinute; c.second = c._showSecond ? c._tempSecond : 0 }
                if (c._hasDate && c._hasTime) c.dateTimeChanged(c.year, c.month, c.day, c.hour, c.minute, c.second)
                else if (c._hasDate) c.dateChanged(c.year, c.month, c.day)
                else if (c._hasTime) c.timeChanged(c.hour, c.minute, c.second)
                c.closePopup()
            }
        }
        
        // Cancel 取消
        Button {
            style: Enums.button.style_default
            text: buttonArea.control ? buttonArea.control._cancelText : ""
            width: (buttonArea.width - Enums.spacing.l - Enums.spacing.xl) / 2
            onClicked: { if (buttonArea.control) buttonArea.control.closePopup() }
        }
    }
}
