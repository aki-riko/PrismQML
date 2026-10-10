// CalendarPickerNav - Display-mode aware page stepping 按显示模式翻页
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

.pragma library

// previousPage - Step back one page of the active display mode 按当前显示模式后退一页
function previousPage(control, calendarPicker) {
    if (control.displayMode === calendarPicker.display_year) {
        control.year -= 1
        return
    }
    if (control.displayMode === calendarPicker.display_decade) {
        control.year -= calendarPicker.yearsPerDecade
        return
    }
    control.prevMonth()
}

// nextPage - Step forward one page of the active display mode 按当前显示模式前进一页
function nextPage(control, calendarPicker) {
    if (control.displayMode === calendarPicker.display_year) {
        control.year += 1
        return
    }
    if (control.displayMode === calendarPicker.display_decade) {
        control.year += calendarPicker.yearsPerDecade
        return
    }
    control.nextMonth()
}
