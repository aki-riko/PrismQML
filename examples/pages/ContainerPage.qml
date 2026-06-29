// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// 导入组件
import PrismQML
import PrismQML as Fluent

// 容器组件页面
Item {
    id: root
    
    function iconPath(name) {
        return Fluent.Enums.iconPath + name + ".svg"
    }
    
    ScrollArea {
        anchors.fill: parent
        
        Column {
            width: parent ? parent.width : 0
            spacing: Fluent.Enums.spacing.xxl
            
            // 页面标题
            Column {
                width: parent ? parent.width : 0
                spacing: Fluent.Enums.spacing.xs
                Text { text: "容器组件"; font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
                Text { text: "prismqml.controls.containers"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
            }
            
            // 布局组件
            ExampleCard {
                title: "布局组件"
                description: "Layout(mode=mode_horizontal/mode_vertical/mode_grid)"
                Row {
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard {
                        label: "mode_horizontal"
                        Rectangle {
                            width: 140; height: 50; color: Fluent.Enums.hoverColor; radius: Fluent.Enums.radius.small
                            HBoxLayout {
                                anchors.fill: parent; margins: Fluent.Enums.spacing.s; spacing_: Fluent.Enums.spacing.s
                                Rectangle { width: 35; height: 35; color: Fluent.Enums.demoPalette.blue; radius: Fluent.Enums.radius.small }
                                Rectangle { width: 35; height: 35; color: Fluent.Enums.demoPalette.green; radius: Fluent.Enums.radius.small }
                                Rectangle { width: 35; height: 35; color: Fluent.Enums.demoPalette.orange; radius: Fluent.Enums.radius.small }
                            }
                        }
                    }
                    ComponentCard {
                        label: "mode_vertical"
                        Rectangle {
                            width: 50; height: 90; color: Fluent.Enums.hoverColor; radius: Fluent.Enums.radius.small
                            VBoxLayout {
                                anchors.fill: parent; margins: Fluent.Enums.spacing.s; spacing_: Fluent.Enums.spacing.s
                                Rectangle { width: 35; height: 25; color: Fluent.Enums.demoPalette.red; radius: Fluent.Enums.radius.small }
                                Rectangle { width: 35; height: 25; color: Fluent.Enums.demoPalette.purple; radius: Fluent.Enums.radius.small }
                            }
                        }
                    }
                    ComponentCard {
                        label: "mode_grid"
                        Rectangle {
                            width: 95; height: 95; color: Fluent.Enums.hoverColor; radius: Fluent.Enums.radius.small
                            GridLayout {
                                anchors.fill: parent; anchors.margins: Fluent.Enums.spacing.s; columns: 2; verticalSpacing: Fluent.Enums.spacing.s; horizontalSpacing: Fluent.Enums.spacing.s
                                Rectangle { width: 35; height: 35; color: Fluent.Enums.demoPalette.cyan; radius: Fluent.Enums.radius.small }
                                Rectangle { width: 35; height: 35; color: Fluent.Enums.demoPalette.lime; radius: Fluent.Enums.radius.small }
                                Rectangle { width: 35; height: 35; color: Fluent.Enums.demoPalette.orange; radius: Fluent.Enums.radius.small }
                                Rectangle { width: 35; height: 35; color: Fluent.Enums.demoPalette.pink; radius: Fluent.Enums.radius.small }
                            }
                        }
                    }
                }
            }
            
            // 流式布局
            ExampleCard {
                title: "流式布局"
                description: "Layout(mode=mode_default) - FlowLayout内部模式切换"
                Column {
                    spacing: Fluent.Enums.spacing.l
                    width: parent ? parent.width : 0
                    
                    // 模式切换控制 Mode switch controls
                    Row {
                        spacing: Fluent.Enums.spacing.m
                        Text { text: "模式切换："; color: Fluent.Enums.textColor.primary; anchors.verticalCenter: parent.verticalCenter }
                        Button { text: "默认"; style: flowDemo.mode === Fluent.Enums.flow.default_ ? Fluent.Enums.button.style_primary : Fluent.Enums.button.style_default; onClicked: flowDemo.mode = Fluent.Enums.flow.default_ }
                        Button { text: "水平(等高)"; style: flowDemo.mode === Fluent.Enums.flow.horizontal ? Fluent.Enums.button.style_primary : Fluent.Enums.button.style_default; onClicked: flowDemo.mode = Fluent.Enums.flow.horizontal }
                        Button { text: "垂直(等宽)"; style: flowDemo.mode === Fluent.Enums.flow.vertical ? Fluent.Enums.button.style_primary : Fluent.Enums.button.style_default; onClicked: flowDemo.mode = Fluent.Enums.flow.vertical }
                    }
                    
                    // 演示区域
                    Rectangle {
                        width: 500; height: 500
                        color: Fluent.Enums.hoverColor
                        radius: Fluent.Enums.radius.large
                        border.color: Fluent.Enums.borderColor
                        clip: true
                        
                        ScrollArea {
                            anchors.fill: parent
                            anchors.margins: Fluent.Enums.spacing.m
                            
                            FlowLayout {
                                id: flowDemo
                                width: parent ? parent.width : 0
                                spacing: Fluent.Enums.spacing.s
                                rowSpacing: Fluent.Enums.spacing.s
                                mode: Fluent.Enums.flow.default_
                                columnCount: 6
                                
                                // 获取颜色函数
                                function getColor(idx) {
                                    var colors = [
                                        Fluent.Enums.demoPalette.blue,
                                        Fluent.Enums.demoPalette.green,
                                        Fluent.Enums.demoPalette.orange,
                                        Fluent.Enums.demoPalette.purple,
                                        Fluent.Enums.demoPalette.teal,
                                        Fluent.Enums.demoPalette.red,
                                        Fluent.Enums.demoPalette.cyan,
                                        Fluent.Enums.demoPalette.pink,
                                        Fluent.Enums.demoPalette.lime,
                                        Fluent.Enums.demoPalette.sky
                                    ]
                                    return colors[idx % colors.length]
                                }
                                
                                // 50个彩色方块 - 随机尺寸（垂直模式下高度差异更明显）
                                Repeater {
                                    model: 50
                                    Rectangle {
                                        width: 40 + (index % 7) * 12
                                        height: 30 + (index * 17 % 80)  // 高度范围 30~110，差异更明显
                                        color: flowDemo.getColor(index)
                                        radius: Fluent.Enums.radius.small
                                        Text {
                                            anchors.centerIn: parent
                                            text: (index + 1)
                                            color: Fluent.Enums.accentForeground
                                            font.pixelSize: Fluent.Enums.typography.bodySmall
                                            font.bold: true
                                        }
                                    }
                                }
                            }
                        }
                    }
                    
                    // 说明文字
                    Text {
                        text: flowDemo.mode === Fluent.Enums.flow.default_ ? "默认模式：保持每个子项的原始尺寸，自动换行" :
                              flowDemo.mode === Fluent.Enums.flow.horizontal ? "水平模式：同一行内所有子项等高（取该行最大高度）" :
                              "垂直模式：所有子项等宽（按列数平分宽度）"
                        color: Fluent.Enums.textColor.secondary
                        font.pixelSize: Fluent.Enums.typography.caption
                    }
                }
            }
            
            // 分隔线
            ExampleCard {
                title: "分隔线"
                description: "Separator"
                ComponentCard {
                    label: "Separator"
                    Column {
                        spacing: Fluent.Enums.spacing.l
                        width: 250
                        Text { text: "上方内容"; color: Fluent.Enums.textColor.primary }
                        Separator { type: 0; lineLength: parent ? parent.width : 0 }  // 0=horizontal
                        Text { text: "下方内容"; color: Fluent.Enums.textColor.primary }
                    }
                }
            }
            
            // 分组框
            ExampleCard {
                title: "分组框"
                description: "GroupBox"
                ComponentCard {
                    label: "GroupBox"
                    GroupBox { title: "分组标题"; width: 250; Text { text: "分组内容"; color: Fluent.Enums.textColor.primary } }
                }
            }
            
            // 滚动组件
            ExampleCard {
                title: "滚动组件"
                description: "ScrollArea"
                ComponentCard {
                    label: "ScrollArea"
                    ScrollArea {
                        width: 220; height: 100
                        Column {
                            spacing: Fluent.Enums.spacing.xs
                            Repeater { model: 20; Text { text: "滚动项 " + (index + 1); color: Fluent.Enums.textColor.primary } }
                        }
                    }
                }
            }
            
            // 分割器
            ExampleCard {
                title: "分割器"
                description: "SplitPane"
                Row {
                    spacing: Fluent.Enums.spacing.xl
                    ComponentCard {
                        label: "horizontal"
                        SplitPane {
                            width: 280; height: 100
                            orientation: Qt.Horizontal
                            firstContent: Rectangle { anchors.fill: parent; color: Fluent.Enums.demoPalette.blue; Text { anchors.centerIn: parent; text: "左"; color: Fluent.Enums.accentForeground } }
                            secondContent: Rectangle { anchors.fill: parent; color: Fluent.Enums.demoPalette.green; Text { anchors.centerIn: parent; text: "右"; color: Fluent.Enums.accentForeground } }
                        }
                    }
                    ComponentCard {
                        label: "vertical"
                        SplitPane {
                            width: 150; height: 120
                            orientation: Qt.Vertical
                            firstContent: Rectangle { anchors.fill: parent; color: Fluent.Enums.demoPalette.orange; Text { anchors.centerIn: parent; text: "上"; color: Fluent.Enums.accentForeground } }
                            secondContent: Rectangle { anchors.fill: parent; color: Fluent.Enums.demoPalette.purple; Text { anchors.centerIn: parent; text: "下"; color: Fluent.Enums.accentForeground } }
                        }
                    }
                }
            }
            
            // 抽屉
            ExampleCard {
                title: "抽屉"
                description: "Drawer"
                Row {
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard { label: "position.left"; Button { text: "左侧抽屉"; onClicked: leftDrawer.open() } }
                    ComponentCard { label: "position.right"; Button { text: "右侧抽屉"; onClicked: rightDrawer.open() } }
                    ComponentCard { label: "position.top"; Button { text: "顶部抽屉"; onClicked: topDrawer.open() } }
                    ComponentCard { label: "position.bottom"; Button { text: "底部抽屉"; onClicked: bottomDrawer.open() } }
                }
            }
            
            
            // 二维码
            ExampleCard {
                title: "二维码"
                description: "QRCode"
                Row {
                    spacing: Fluent.Enums.spacing.xxxl
                    ComponentCard { label: "size: 120"; QRCode { content: "https://github.com"; size: 120 } }
                    ComponentCard { label: "size: 150"; QRCode { content: "PrismQML 组件库"; size: 150 } }
                    ComponentCard { label: "errorLevel: H"; QRCode { content: "高纠错"; size: 120; errorLevel: "H" } }
                }
            }
            
            // 水印
            ExampleCard {
                title: "水印"
                description: "Watermark"
                ComponentCard {
                    label: "Watermark"
                    Watermark {
                        width: 280; height: 100
                        text: "机密文档"
                        Rectangle { anchors.fill: parent; color: Fluent.Enums.surfaceColor; z: Fluent.Enums.zIndex.background }
                    }
                }
            }
            
            // 文件拖放
            ExampleCard {
                title: "文件拖放"
                description: "DropZone"
                ComponentCard {
                    label: "DropZone"
                    DropZone { width: 220; height: 120 }
                }
            }
        }
    }
    
    // 抽屉组件
    Drawer {
        id: leftDrawer
        position: Fluent.Enums.position.left
        drawerWidth: 280
        Column {
            anchors.centerIn: parent; spacing: Fluent.Enums.spacing.l
            Text { text: "左侧抽屉"; font.bold: true; font.pixelSize: Fluent.Enums.typography.subtitle; color: Fluent.Enums.textColor.primary }
            Button { text: "关闭"; onClicked: leftDrawer.close() }
        }
    }
    
    Drawer {
        id: rightDrawer
        position: Fluent.Enums.position.right
        drawerWidth: 280
        Column {
            anchors.centerIn: parent; spacing: Fluent.Enums.spacing.l
            Text { text: "右侧抽屉"; font.bold: true; font.pixelSize: Fluent.Enums.typography.subtitle; color: Fluent.Enums.textColor.primary }
            Button { text: "关闭"; onClicked: rightDrawer.close() }
        }
    }
    
    Drawer {
        id: topDrawer
        position: Fluent.Enums.position.top
        drawerHeight: 200
        Column {
            anchors.centerIn: parent; spacing: Fluent.Enums.spacing.l
            Text { text: "顶部抽屉"; font.bold: true; font.pixelSize: Fluent.Enums.typography.subtitle; color: Fluent.Enums.textColor.primary }
            Button { text: "关闭"; onClicked: topDrawer.close() }
        }
    }
    
    Drawer {
        id: bottomDrawer
        position: Fluent.Enums.position.bottom
        drawerHeight: 200
        Column {
            anchors.centerIn: parent; spacing: Fluent.Enums.spacing.l
            Text { text: "底部抽屉"; font.bold: true; font.pixelSize: Fluent.Enums.typography.subtitle; color: Fluent.Enums.textColor.primary }
            Button { text: "关闭"; onClicked: bottomDrawer.close() }
        }
    }
}
