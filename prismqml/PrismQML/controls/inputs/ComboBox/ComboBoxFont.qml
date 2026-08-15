// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import "../../.."
import ".."
import "../../data/Label"
import QtQuick  // Keep after library imports so native types win 去前缀后保原生类型不被库覆盖

// ComboBoxFont - Font picker extending ComboBoxCore 字体选择框
ComboBoxCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    property var fonts: Enums.comboBox.fontFamilies.slice()
    property string currentFont: ""

    // ==================== Internal Props 内部属性 ====================
    property bool _syncingFontSelection: false

    // ==================== Signals 信号 ====================
    signal fontSelected(string fontName)

    // ==================== Internal Methods 内部方法 ====================
    function _syncFontFromIndex() {
        if (_syncingFontSelection) return
        _syncingFontSelection = true
        var safeModel = _safeModel || []
        var nextFont = currentIndex >= 0 && currentIndex < safeModel.length
            ? _getItemText(currentIndex) : ""
        if (currentFont !== nextFont) currentFont = nextFont
        _syncingFontSelection = false
    }

    function _syncIndexFromFont() {
        if (_syncingFontSelection) return
        _syncingFontSelection = true
        var nextIndex = currentFont === "" ? -1 : findText(currentFont)
        if (currentIndex !== nextIndex) currentIndex = nextIndex
        var normalizedFont = nextIndex >= 0 ? _getItemText(nextIndex) : ""
        if (currentFont !== normalizedFont) currentFont = normalizedFont
        _syncingFontSelection = false
    }

    function _selectFont(index) {
        var safeModel = _safeModel || []
        if (index < 0 || index >= safeModel.length) return
        currentIndex = index
        fontSelected(currentFont)
        closePopup()
    }

    // Use fonts as model 使用fonts作为model
    model: fonts
    popupItemHeight: Enums.controlSize.calendarCellHeight

    onCurrentIndexChanged: {
        _syncCurrentTextFromSelection()
        _syncFontFromIndex()
    }
    onCurrentFontChanged: _syncIndexFromFont()
    on_SafeModelChanged: {
        _syncCurrentTextFromSelection()
        _syncFontFromIndex()
    }
    Component.onCompleted: {
        _syncCurrentTextFromSelection()
        _syncFontFromIndex()
    }

    // ==================== Content 内容 ====================
    popupDelegate: Component {
        Rectangle {
            id: fontItemBg
            property bool selected: index === control.currentIndex

            width: ListView.view ? ListView.view.width : Enums.comboBox.fontDelegateFallbackWidth
            height: control.popupItemHeight
            radius: Enums.radius.small

            color: {
                if (fontItemArea.pressed) return Enums.stateColor.menuItemPressed
                if (selected) return Enums.stateColor.menuItemPressed
                if (fontItemArea.containsMouse) return Enums.stateColor.menuItemHover
                return Enums.transparent
            }

            // Selection indicator 选中指示器
            Rectangle {
                anchors.left: parent.left
                anchors.leftMargin: Enums.spacing.xxs
                anchors.verticalCenter: parent.verticalCenter
                width: Enums.controlSize.topNavIndicatorHeight
                height: Enums.spacing.xl
                radius: Enums.radius.micro
                color: Enums.accentColor
                visible: fontItemBg.selected
            }

            Label {
                type: Enums.label.type_body
                anchors.left: parent.left
                anchors.leftMargin: Enums.spacing.l
                anchors.verticalCenter: parent.verticalCenter
                text: modelData
                font.family: modelData
            }

            MouseArea {
                id: fontItemArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: control._selectFont(index)
            }
        }
    }
}
