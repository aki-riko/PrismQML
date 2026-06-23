// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import "../../.."
import ".."
import "../../data/Label"
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// ComboBoxFont - Font picker extending ComboBoxCore 字体选择框
ComboBoxCore {
    id: control
    
    // ==================== 字体特有属性 ====================
    property var fonts: ["Arial", "Segoe UI", "Microsoft YaHei", "SimSun", "SimHei", "KaiTi", "FangSong", "Consolas", "Courier New", "Times New Roman"]
    property string currentFont: "Segoe UI"
    
    signal fontSelected(string fontName)
    
    // Use fonts as model 使用fonts作为model
    model: fonts
    popupItemHeight: Enums.controlSize.calendarCellHeight
    
    // ==================== 覆盖delegate(复用基类滚动条) ====================
    popupDelegate: Component {
        Rectangle {
            id: fontItemBg
            width: ListView.view ? ListView.view.width : 100
            height: control.popupItemHeight
            radius: Enums.radius.small
            
            property bool selected: modelData === control.currentFont
            
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
                onClicked: {
                    control.currentFont = modelData
                    control.currentIndex = index
                    control.fontSelected(modelData)
                    control.closePopup()
                }
            }
        }
    }
}
