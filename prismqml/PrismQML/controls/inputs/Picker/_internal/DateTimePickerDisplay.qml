// DateTimePickerDisplay - Date/time display delegate layer 日期时间显示委托层
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."
import "../../../containers/Separator"
import "../../../data"

// DateTimePickerDisplay - Owns the compact display row 承载紧凑显示行
Item {
    id: display

    // ==================== Required Props 必需属性 ====================
    required property var pickerControl

    anchors.fill: parent

    // ==================== Content 内容 ====================
    Row {
        anchors.fill: parent

        Repeater {
            model: display.pickerControl._buildDisplayModel()

            Item {
                width: parent ? parent.width / display.pickerControl._totalColCount : 0
                height: parent ? parent.height : 0

                Label {
                    anchors.centerIn: parent
                    type: Enums.label.type_body
                    text: modelData.text
                    color: modelData.hasValue
                           ? Enums.textColor.primary : Enums.textColor.disabled
                }

                // Separator 分隔线
                Separator {
                    type: Enums.separator.vertical
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    lineLength: parent.height - Enums.spacing.m
                    lineColor: Enums.stateColor.border
                    visible: index < display.pickerControl._totalColCount - 1
                }
            }
        }
    }
}
