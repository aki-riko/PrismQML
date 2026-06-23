// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick

// SettingCard - Setting card type enums 设置卡片类型枚举
QtObject {
    // ==================== Type 类型 ====================
    readonly property int type_push: 0           // Push button 按钮
    readonly property int type_primary_push: 1   // Primary push button 主要按钮
    readonly property int type_hyperlink: 2      // Hyperlink 超链接
    readonly property int type_switch: 3         // Switch toggle 开关
    readonly property int type_combobox: 4       // ComboBox dropdown 下拉框
    readonly property int type_range: 5          // Range slider 滑块
    readonly property int type_shortcut: 6       // Shortcut picker 快捷键
    readonly property int type_multi_selection: 7 // Multi selection 多选
    readonly property int type_options: 8        // Options radio group 选项组
    readonly property int type_folder_list: 9    // Folder list 文件夹列表
    readonly property int type_color: 10         // Color picker (expand) 颜色选择（展开式）
    
    // ==================== Size 尺寸 ====================
    readonly property int height_with_content: 72  // Height with content 有内容时高度
    readonly property int height_no_content: 48    // Height without content 无内容时高度
    readonly property int icon_size: 16            // Icon size 图标尺寸
    readonly property int combobox_width: 200      // ComboBox width 下拉框宽度
    readonly property int slider_width: 200        // Slider width 滑块宽度
    readonly property int value_label_width: 40    // Value label width 数值标签宽度
    readonly property int color_block_width: 60    // Color block width 颜色块宽度
    readonly property int color_block_height: 32   // Color block height 颜色块高度
    readonly property int color_button_width: 100  // Color button width 颜色选择按钮宽度

    // ==================== Expand 展开 ====================
    readonly property int expand_button_size: 32   // Expand button size 展开按钮尺寸
    readonly property int expand_icon_size: 10     // Expand icon size 展开图标尺寸
    readonly property int group_item_height: 52    // Group item height 分组项高度
    readonly property int group_separator_height: 3 // Group separator height 分组分隔线高度
}
