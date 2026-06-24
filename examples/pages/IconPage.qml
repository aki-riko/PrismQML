// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

import PrismQML as Fluent
import "../../prismqml/PrismQML/controls/containers"
import "../../prismqml/PrismQML/controls/inputs"
import "../../prismqml/PrismQML/controls/icons"
import "../../prismqml/PrismQML/controls/buttons"

Item {
    id: root
    property var allIcons: []
    property string searchText: ""
    property string selectedIcon: Fluent.Enums.icon.calendar  // Default selected icon 默认选中

    Component.onCompleted: { allIcons = getIconList() }

    // Get all icons from Enums.icons singleton 从PrismEnums获取完整图标列表
    function getIconList() {
        var icons = Fluent.Enums.icons.iconList
        var result = []
        for (var key in icons) {
            result.push(icons[key])
        }
        result.sort()
        return result
    }

    // Convert icon name to enum member name 转换为枚举成员名
    function toEnumName(name) {
        // CamelCase to UPPER_SNAKE_CASE
        return name.replace(/([A-Z])/g, '_$1').toUpperCase().replace(/^_/, '')
    }

    readonly property var filteredIcons: {
        if (searchText === "") return allIcons
        var lowerSearch = searchText.toLowerCase()
        return allIcons.filter(function(icon) {
            return icon.toLowerCase().indexOf(lowerSearch) >= 0
        })
    }

    Row {
        anchors.fill: parent
        anchors.margins: Fluent.Enums.spacing.xl
        spacing: Fluent.Enums.spacing.xxxl

        // ==================== Left: Icon Grid 左侧图标网格 ====================
        Column {
            width: parent.width - detailPanel.width - Fluent.Enums.spacing.xxxl
            height: parent.height
            spacing: Fluent.Enums.spacing.xl

            // Title 标题
            Text {
                text: "图标"
                font.pixelSize: Fluent.Enums.typography.display
                font.bold: true
                color: Fluent.Enums.textColor.primary
                font.family: Fluent.Enums.fontFamily
            }

            // Search box 搜索框
            LineEdit {
                id: searchBox
                width: Math.min(parent.width, 400)
                inputType: Fluent.Enums.input.type_search
                placeholderText: "搜索图标"
                onTextChanged: root.searchText = text
            }

            // Icon grid 图标网格
            ScrollArea {
                width: parent.width
                height: parent.height - 80
                
                type: Fluent.Enums.scroll.type_grid
                model: filteredIcons
                cellWidth: 112
                cellHeight: 100
                selectable: false
                
                delegate: Card {
                    cardType: Fluent.Enums.card.type_elevated
                    borderRadius: Fluent.Enums.radius.large
                    width: 100
                    height: 88
                    border.width: modelData === root.selectedIcon ? 1 : 0
                    border.color: Fluent.Enums.accentColor

                    Column {
                        anchors.centerIn: parent
                        spacing: Fluent.Enums.spacing.m

                        Icon {
                            anchors.horizontalCenter: parent.horizontalCenter
                            iconSize: Fluent.Enums.iconSize.xl
                            color: Fluent.Enums.textColor.primary
                            icon: modelData
                        }

                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: modelData
                            font.pixelSize: Fluent.Enums.typography.caption
                            font.family: Fluent.Enums.fontFamily
                            color: Fluent.Enums.textColor.secondary
                            width: 90
                            horizontalAlignment: Text.AlignHCenter
                            elide: Text.ElideMiddle
                        }
                    }

                    onClicked: root.selectedIcon = modelData
                }
            }
        }

        // ==================== Right: Detail Panel 右侧详情面板 ====================
        Rectangle {
            id: detailPanel
            width: 240
            height: parent.height
            color: "transparent"

            Column {
                anchors.fill: parent
                spacing: Fluent.Enums.spacing.xxxl

                // Selected icon name 选中图标名
                Text {
                    text: root.selectedIcon
                    font.pixelSize: Fluent.Enums.typography.title
                    font.bold: true
                    color: Fluent.Enums.textColor.primary
                    font.family: Fluent.Enums.fontFamily
                }

                // Large icon preview 大图标预览
                Icon {
                    iconSize: 64
                    color: Fluent.Enums.textColor.primary
                    icon: root.selectedIcon
                }

                // Divider 分隔线
                Rectangle {
                    width: parent.width
                    height: 1
                    color: Fluent.Enums.stateColor.divider
                }

                // Icon name row 图标名行
                Column {
                    width: parent.width
                    spacing: Fluent.Enums.spacing.xs
                    
                    Text {
                        text: "图标名"
                        font.pixelSize: Fluent.Enums.typography.caption
                        color: Fluent.Enums.textColor.secondary
                        font.family: Fluent.Enums.fontFamily
                    }
                    
                    Row {
                        width: parent.width
                        spacing: Fluent.Enums.spacing.m
                        
                        Text {
                            text: root.selectedIcon
                            font.pixelSize: Fluent.Enums.typography.body
                            color: Fluent.Enums.textColor.primary
                            font.family: Fluent.Enums.fontFamily
                            width: parent.width - copyBtn1.width - 8
                        }
                        
                        Button {
                            id: copyBtn1
                            icon: Fluent.Enums.icon.copy
                            onClicked: ClipboardHelper.copy(root.selectedIcon)
                        }
                    }
                }

                // Enum member name row 枚举成员名行
                Column {
                    width: parent.width
                    spacing: Fluent.Enums.spacing.xs
                    
                    Text {
                        text: "枚举成员名"
                        font.pixelSize: Fluent.Enums.typography.caption
                        color: Fluent.Enums.textColor.secondary
                        font.family: Fluent.Enums.fontFamily
                    }
                    
                    Row {
                        width: parent.width
                        spacing: Fluent.Enums.spacing.m
                        
                        Text {
                            text: root.toEnumName(root.selectedIcon)
                            font.pixelSize: Fluent.Enums.typography.body
                            color: Fluent.Enums.textColor.primary
                            font.family: Fluent.Enums.fontFamily
                            width: parent.width - copyBtn2.width - 8
                        }
                        
                        Button {
                            id: copyBtn2
                            icon: Fluent.Enums.icon.copy
                            onClicked: ClipboardHelper.copy(root.toEnumName(root.selectedIcon))
                        }
                    }
                }

                // Python code row Python代码行
                Column {
                    width: parent.width
                    spacing: Fluent.Enums.spacing.xs
                    
                    Text {
                        text: "Python 代码"
                        font.pixelSize: Fluent.Enums.typography.caption
                        color: Fluent.Enums.textColor.secondary
                        font.family: Fluent.Enums.fontFamily
                    }
                    
                    Row {
                        width: parent.width
                        spacing: Fluent.Enums.spacing.m
                        
                        Text {
                            text: "Icon." + root.toEnumName(root.selectedIcon)
                            font.pixelSize: Fluent.Enums.typography.body
                            color: Fluent.Enums.textColor.primary
                            font.family: Fluent.Enums.fontFamily
                            width: parent.width - copyBtn3.width - 8
                        }
                        
                        Button {
                            id: copyBtn3
                            icon: Fluent.Enums.icon.copy
                            onClicked: ClipboardHelper.copy("Icon." + root.toEnumName(root.selectedIcon))
                        }
                    }
                }
            }
        }
    }
}
