// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// DateTimePickerInitTimer - Retry wheel initialization after popup loading 日期时间选择器弹层加载后重试滚轮初始化
Timer {
    id: initTimer

    // ==================== Required Props 必需属性 ====================
    required property var host

    objectName: "dateTimePickerInitTimer"
    interval: 50  // Wait for components to fully load 等待组件完全加载
    repeat: false
    onTriggered: host._initWheelPositions()
}
