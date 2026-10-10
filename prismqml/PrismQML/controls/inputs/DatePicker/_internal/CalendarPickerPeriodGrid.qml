// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../../.."

// CalendarPickerPeriodGrid - Month/decade selection grid 月份/十年选择网格
// Only instantiated while the calendar shows the year or decade display mode.
// 仅在日历处于年/十年显示模式时创建。
Item {
    id: periodGrid

    // ==================== Required Props 必需属性 ====================
    required property var calendarControl

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _decadeMode:
        calendarControl.displayMode === Enums.calendarPicker.display_decade
    readonly property int _firstValue: _decadeMode
        ? calendarControl._decadeStart : Enums.calendarPicker.monthMinimum
    readonly property int _count: _decadeMode
        ? Enums.calendarPicker.yearsPerDecade
        : Enums.calendarPicker.monthsPerYear
    readonly property int _columns: _decadeMode
        ? Enums.calendarPicker.decadeGridColumns
        : Enums.calendarPicker.periodGridColumns
    readonly property var _monthKeys: [
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december"
    ]

    // ==================== Public Methods 公开方法 ====================
    // Period value behind one grid offset 某个网格偏移对应的周期值
    function valueFor(offset) { return _firstValue + offset }

    // Localised caption for one grid offset 某个网格偏移的本地化标题
    function labelFor(offset) {
        if (_decadeMode) return String(valueFor(offset))
        Translator._v
        return Translator.tr(_monthKeys[offset])
    }

    // Enter the finer display mode for the chosen period 进入所选周期的更细显示模式
    function selectPeriod(offset) {
        if (_decadeMode) {
            calendarControl.year = valueFor(offset)
            calendarControl.setDisplayMode(Enums.calendarPicker.display_year)
        } else {
            calendarControl.month = valueFor(offset)
            calendarControl.setDisplayMode(Enums.calendarPicker.display_month)
        }
    }

    // ==================== Content 内容 ====================
    Grid {
        anchors.fill: parent
        columns: periodGrid._columns

        Repeater {
            model: periodGrid._count

            Rectangle {
                id: periodCell

                // ==================== Readonly State 只读状态 ====================
                // Touch has no hover preview: on touch the hover treatment follows the press
                // 触摸没有 hover 预览: 触摸端 hover 视觉只在按压时生效, 避免松手后残留
                readonly property bool _touchActive:
                    Touch.feedback(periodArea.containsMouse, periodArea.pressed)
                readonly property bool _activePeriod: periodGrid.valueFor(index)
                    === (periodGrid._decadeMode
                        ? periodGrid.calendarControl.year
                        : periodGrid.calendarControl.month)

                width: parent.width / periodGrid._columns
                height: Enums.controlSize.calendarCellHeight
                color: _touchActive
                    ? Enums.stateColor.transparentHover : Enums.transparent

                Label {
                    anchors.centerIn: parent
                    type: Enums.label.type_body
                    text: periodGrid.labelFor(index)
                    color: periodCell._activePeriod
                        ? periodGrid.calendarControl.accentColor
                        : Enums.textColor.primary
                }

                MouseArea {
                    id: periodArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: periodGrid.selectPeriod(index)
                }
            }
        }
    }
}
