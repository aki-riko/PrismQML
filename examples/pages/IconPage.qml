// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

import PrismQML
import PrismQML as Fluent

Item {
    id: root
    property var allIcons: []
    property string searchText: ""
    property string selectedIcon: Fluent.Enums.icon.calendar  // Default selected icon 默认选中
    // Leaf icon components led by the grid cells: name to glyph, single source of truth
    // 由网格最前面单元格承载的图标叶子组件: 名称到图形的唯一数据源
    readonly property var leafGlyphs: ({
        "CheckIcon": checkIconGlyph,
        "ChevronIcon": chevronIconGlyph,
        "ChevronIcon (open)": chevronOpenGlyph,
        "CloseIcon": closeIconGlyph
    })
    readonly property var leafComponentNames: Object.keys(leafGlyphs)

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

    // Leaf components lead the grid, enum icons follow; search filters both
    // 叶子组件排在网格最前, 枚举图标随后; 搜索同时过滤两者
    readonly property var filteredIcons: {
        var lowerSearch = searchText.toLowerCase()
        var matchAll = searchText === ""
        var names = leafComponentNames.concat(allIcons)
        var result = []
        for (var index = 0; index < names.length; ++index) {
            if (matchAll || names[index].toLowerCase().indexOf(lowerSearch) >= 0)
                result.push(names[index])
        }
        return result
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
                text: Fluent.Translator.tr("gallery_0d720eeea26466dd", Fluent.Translator._v)
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
                placeholderText: Fluent.Translator.tr("gallery_ebb240a1930e8bfb", Fluent.Translator._v)
                onTextChanged: root.searchText = text
            }

            // Icon grid, led by the leaf component cells 图标网格, 最前面的单元格是叶子组件
            ScrollArea {
                width: parent.width
                height: parent.height - y
                
                type: Fluent.Enums.scroll.type_grid
                model: filteredIcons
                cellWidth: 112
                cellHeight: 100
                selectable: false
                
                delegate: Card {
                    id: gridCard

                    readonly property bool leafComponent: root.leafGlyphs[modelData] !== undefined

                    objectName: gridCard.leafComponent ? "leafComponentCell" : ""
                    cardType: Fluent.Enums.card.type_elevated
                    borderRadius: Fluent.Enums.radius.large
                    // Card ignores clicks unless enabled; leaf cells demo a component, not a selection
                    // 卡片需显式启用点击; 叶子单元格演示组件本身, 不参与选中
                    clickEnabled: !gridCard.leafComponent
                    width: 100
                    height: 88
                    border.width: !gridCard.leafComponent && modelData === root.selectedIcon ? 1 : 0
                    border.color: Fluent.Enums.accentColor

                    Column {
                        anchors.centerIn: parent
                        spacing: Fluent.Enums.spacing.m

                        Icon {
                            anchors.horizontalCenter: parent.horizontalCenter
                            visible: !gridCard.leafComponent
                            iconSize: Fluent.Enums.iconSize.xl
                            color: Fluent.Enums.textColor.primary
                            icon: gridCard.leafComponent ? "" : modelData
                        }

                        // Leaf glyph occupies the enum icon slot so labels stay aligned
                        // 叶子图形占据与枚举图标一致的槽位, 保证标签对齐
                        Item {
                            anchors.horizontalCenter: parent.horizontalCenter
                            visible: gridCard.leafComponent
                            width: Fluent.Enums.iconSize.xl
                            height: Fluent.Enums.iconSize.xl

                            Loader {
                                anchors.centerIn: parent
                                sourceComponent: gridCard.leafComponent ? root.leafGlyphs[modelData] : null
                            }
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
            color: Fluent.Enums.transparent

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
                        text: Fluent.Translator.tr("gallery_f4b8d441609401a3", Fluent.Translator._v)
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
                        text: Fluent.Translator.tr("gallery_650ba83c6a8425e7", Fluent.Translator._v)
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
                        text: Fluent.Translator.tr("gallery_bd94d92b7cdcee2d", Fluent.Translator._v)
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

    // ==================== Leaf Component Glyphs 叶子组件图形 ====================
    Component {
        id: checkIconGlyph
        CheckIcon { }
    }

    Component {
        id: chevronIconGlyph
        ChevronIcon { }
    }

    Component {
        id: chevronOpenGlyph
        ChevronIcon {
            direction: "right"
            animated: true
            isOpen: true
        }
    }

    Component {
        id: closeIconGlyph
        CloseIcon { }
    }
}
