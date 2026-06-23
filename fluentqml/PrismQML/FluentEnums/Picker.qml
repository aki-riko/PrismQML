// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// Picker - Date/Time picker type enums 日期时间选择器类型枚举
QtObject {
    // Type 类型
    readonly property int type_date: 0       // Date only (Y-M-D wheels) 仅日期
    readonly property int type_time: 1       // Time only (H-M-S wheels) 仅时间
    readonly property int type_datetime: 2   // Date + Time 日期+时间
    // Date precision 日期精度
    readonly property int date_year: 0       // Year only 仅年
    readonly property int date_month: 1      // Year-Month 年月
    readonly property int date_day: 2        // Year-Month-Day 年月日 (default)
    // Time precision 时间精度
    readonly property int time_hour: 0       // Hour only 仅时
    readonly property int time_minute: 1     // Hour-Minute 时分 (default)
    readonly property int time_second: 2     // Hour-Minute-Second 时分秒
    // Time format 时间格式
    readonly property int format_24h: 0      // 24-hour format 24小时制
    readonly property int format_12h: 1      // 12-hour AM/PM format 12小时制
}
