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
                Text { text: Fluent.Translator.tr("gallery_ece4a638e075fe2d", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
                Text { text: "prismqml.controls.containers"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
            }
            
            // 布局组件
            ExampleCard {
                title: Fluent.Translator.tr("gallery_047006167c1e7f73", Fluent.Translator._v)
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
                title: Fluent.Translator.tr("gallery_49967e9c544605f9", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_0057bf9f1eab521a", Fluent.Translator._v)
                Column {
                    spacing: Fluent.Enums.spacing.l
                    width: parent ? parent.width : 0
                    
                    // 模式切换控制 Mode switch controls
                    Row {
                        spacing: Fluent.Enums.spacing.m
                        Text { text: Fluent.Translator.tr("gallery_ad23faff8799802b", Fluent.Translator._v); color: Fluent.Enums.textColor.primary; anchors.verticalCenter: parent.verticalCenter }
                        Button { text: Fluent.Translator.tr("gallery_844b8cc8dff7c1d8", Fluent.Translator._v); style: flowDemo.mode === Fluent.Enums.flow.default_ ? Fluent.Enums.button.style_primary : Fluent.Enums.button.style_default; onClicked: flowDemo.mode = Fluent.Enums.flow.default_ }
                        Button { text: Fluent.Translator.tr("gallery_0d92873337101494", Fluent.Translator._v); style: flowDemo.mode === Fluent.Enums.flow.horizontal ? Fluent.Enums.button.style_primary : Fluent.Enums.button.style_default; onClicked: flowDemo.mode = Fluent.Enums.flow.horizontal }
                        Button { text: Fluent.Translator.tr("gallery_161909ed3a63d957", Fluent.Translator._v); style: flowDemo.mode === Fluent.Enums.flow.vertical ? Fluent.Enums.button.style_primary : Fluent.Enums.button.style_default; onClicked: flowDemo.mode = Fluent.Enums.flow.vertical }
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
                        text: flowDemo.mode === Fluent.Enums.flow.default_ ? Fluent.Translator.tr("gallery_f7d09fb46f23e857", Fluent.Translator._v) :
                              flowDemo.mode === Fluent.Enums.flow.horizontal ? Fluent.Translator.tr("gallery_67355d877cd81630", Fluent.Translator._v) :
                              Fluent.Translator.tr("gallery_04ad03a8d3134451", Fluent.Translator._v)
                        color: Fluent.Enums.textColor.secondary
                        font.pixelSize: Fluent.Enums.typography.caption
                    }
                }
            }
            
            // 分隔线
            ExampleCard {
                title: Fluent.Translator.tr("gallery_c64dd5eb2135d0ba", Fluent.Translator._v)
                description: "Separator"
                ComponentCard {
                    label: "Separator"
                    Column {
                        spacing: Fluent.Enums.spacing.l
                        width: 250
                        Text { text: Fluent.Translator.tr("gallery_be583c92f424149d", Fluent.Translator._v); color: Fluent.Enums.textColor.primary }
                        Separator { type: 0; lineLength: parent ? parent.width : 0 }  // 0=horizontal
                        Text { text: Fluent.Translator.tr("gallery_4b404edb0e246217", Fluent.Translator._v); color: Fluent.Enums.textColor.primary }
                    }
                }
            }
            
            // 分组框
            ExampleCard {
                title: Fluent.Translator.tr("gallery_e05a542493aa6e37", Fluent.Translator._v)
                description: "GroupBox"
                ComponentCard {
                    label: "GroupBox"
                    GroupBox { title: Fluent.Translator.tr("gallery_b257b86285540bce", Fluent.Translator._v); width: 250; Text { text: Fluent.Translator.tr("gallery_8df30761e5aab1cc", Fluent.Translator._v); color: Fluent.Enums.textColor.primary } }
                }
            }
            
            // 滚动组件
            ExampleCard {
                title: Fluent.Translator.tr("gallery_dc4ef2ff18e2a748", Fluent.Translator._v)
                description: "ScrollArea"
                ComponentCard {
                    label: "ScrollArea"
                    ScrollArea {
                        width: 220; height: 100
                        Column {
                            spacing: Fluent.Enums.spacing.xs
                            Repeater { model: 20; Text { text: Fluent.Translator.tr("gallery_33d76fa741442f73", Fluent.Translator._v) + (index + 1); color: Fluent.Enums.textColor.primary } }
                        }
                    }
                }
            }
            
            // 分割器
            ExampleCard {
                title: Fluent.Translator.tr("gallery_94e5ca260bd07309", Fluent.Translator._v)
                description: "SplitPane"
                Row {
                    spacing: Fluent.Enums.spacing.xl
                    ComponentCard {
                        label: "horizontal"
                        SplitPane {
                            width: 280; height: 100
                            orientation: Qt.Horizontal
                            firstContent: Rectangle { anchors.fill: parent; color: Fluent.Enums.demoPalette.blue; Text { anchors.centerIn: parent; text: Fluent.Translator.tr("gallery_e2e0c454e5d53186", Fluent.Translator._v); color: Fluent.Enums.accentForeground } }
                            secondContent: Rectangle { anchors.fill: parent; color: Fluent.Enums.demoPalette.green; Text { anchors.centerIn: parent; text: Fluent.Translator.tr("gallery_14ab1f2bce0a8777", Fluent.Translator._v); color: Fluent.Enums.accentForeground } }
                        }
                    }
                    ComponentCard {
                        label: "vertical"
                        SplitPane {
                            width: 150; height: 120
                            orientation: Qt.Vertical
                            firstContent: Rectangle { anchors.fill: parent; color: Fluent.Enums.demoPalette.orange; Text { anchors.centerIn: parent; text: Fluent.Translator.tr("gallery_db5ba671d244ee82", Fluent.Translator._v); color: Fluent.Enums.accentForeground } }
                            secondContent: Rectangle { anchors.fill: parent; color: Fluent.Enums.demoPalette.purple; Text { anchors.centerIn: parent; text: Fluent.Translator.tr("gallery_13c12b064b635e06", Fluent.Translator._v); color: Fluent.Enums.accentForeground } }
                        }
                    }
                }
            }
            
            // 抽屉
            ExampleCard {
                title: Fluent.Translator.tr("gallery_3bf97e9265673fb5", Fluent.Translator._v)
                description: "Drawer (mode_inside)"
                Row {
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard { label: "position.left"; Button { text: Fluent.Translator.tr("gallery_e5646ede46742a0b", Fluent.Translator._v); onClicked: leftDrawer.open() } }
                    ComponentCard { label: "position.right"; Button { text: Fluent.Translator.tr("gallery_8d768501ecb25a2b", Fluent.Translator._v); onClicked: rightDrawer.open() } }
                    ComponentCard { label: "position.top"; Button { text: Fluent.Translator.tr("gallery_5f24728a1463f050", Fluent.Translator._v); onClicked: topDrawer.open() } }
                    ComponentCard { label: "position.bottom"; Button { text: Fluent.Translator.tr("gallery_8c4f369c0ee4bc8d", Fluent.Translator._v); onClicked: bottomDrawer.open() } }
                }
            }

            ExampleCard {
                title: Fluent.Translator.tr("gallery_ba59d151d3d96219", Fluent.Translator._v)
                description: "Drawer (mode_outside)"
                Row {
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard { label: "position.left"; Button { text: Fluent.Translator.tr("gallery_86d5449130890834", Fluent.Translator._v); onClicked: outsideLeftDrawer.open() } }
                    ComponentCard { label: "position.right"; Button { text: Fluent.Translator.tr("gallery_8013ac3b2f8ddbe7", Fluent.Translator._v); onClicked: outsideRightDrawer.open() } }
                    ComponentCard { label: "position.top"; Button { text: Fluent.Translator.tr("gallery_2d9684736007999f", Fluent.Translator._v); onClicked: outsideTopDrawer.open() } }
                    ComponentCard { label: "position.bottom"; Button { text: Fluent.Translator.tr("gallery_c9cd0c54442b0a16", Fluent.Translator._v); onClicked: outsideBottomDrawer.open() } }
                }
            }
            
            
            // 二维码
            ExampleCard {
                title: Fluent.Translator.tr("gallery_9b1cd3668052b24b", Fluent.Translator._v)
                description: "QRCode"
                Row {
                    spacing: Fluent.Enums.spacing.xxxl
                    ComponentCard { label: "size: 120"; QRCode { content: "https://github.com"; size: 120 } }
                    ComponentCard { label: "size: 150"; QRCode { content: Fluent.Translator.tr("gallery_3534dd4f90ae9616", Fluent.Translator._v); size: 150 } }
                    ComponentCard { label: "errorLevel: H"; QRCode { content: Fluent.Translator.tr("gallery_304f337d9663c528", Fluent.Translator._v); size: 120; errorLevel: "H" } }
                }
            }
            
            // 水印
            ExampleCard {
                title: Fluent.Translator.tr("gallery_aa9f217c81861768", Fluent.Translator._v)
                description: "Watermark"
                ComponentCard {
                    label: "Watermark"
                    Watermark {
                        width: 280; height: 100
                        text: Fluent.Translator.tr("gallery_79b8782c06e0964e", Fluent.Translator._v)
                        Rectangle { anchors.fill: parent; color: Fluent.Enums.surfaceColor; z: Fluent.Enums.zIndex.background }
                    }
                }
            }
            
            // 文件拖放
            ExampleCard {
                title: Fluent.Translator.tr("gallery_0c8f29023557e79a", Fluent.Translator._v)
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
            Text { text: Fluent.Translator.tr("gallery_e5646ede46742a0b", Fluent.Translator._v); font.bold: true; font.pixelSize: Fluent.Enums.typography.subtitle; color: Fluent.Enums.textColor.primary }
            Button { text: Fluent.Translator.tr("gallery_3fd47edce45b3603", Fluent.Translator._v); onClicked: leftDrawer.close() }
        }
    }
    
    Drawer {
        id: rightDrawer
        position: Fluent.Enums.position.right
        drawerWidth: 280
        Column {
            anchors.centerIn: parent; spacing: Fluent.Enums.spacing.l
            Text { text: Fluent.Translator.tr("gallery_8d768501ecb25a2b", Fluent.Translator._v); font.bold: true; font.pixelSize: Fluent.Enums.typography.subtitle; color: Fluent.Enums.textColor.primary }
            Button { text: Fluent.Translator.tr("gallery_3fd47edce45b3603", Fluent.Translator._v); onClicked: rightDrawer.close() }
        }
    }
    
    Drawer {
        id: topDrawer
        position: Fluent.Enums.position.top
        drawerHeight: 200
        Column {
            anchors.centerIn: parent; spacing: Fluent.Enums.spacing.l
            Text { text: Fluent.Translator.tr("gallery_5f24728a1463f050", Fluent.Translator._v); font.bold: true; font.pixelSize: Fluent.Enums.typography.subtitle; color: Fluent.Enums.textColor.primary }
            Button { text: Fluent.Translator.tr("gallery_3fd47edce45b3603", Fluent.Translator._v); onClicked: topDrawer.close() }
        }
    }
    
    Drawer {
        id: bottomDrawer
        position: Fluent.Enums.position.bottom
        drawerHeight: 200
        Column {
            anchors.centerIn: parent; spacing: Fluent.Enums.spacing.l
            Text { text: Fluent.Translator.tr("gallery_8c4f369c0ee4bc8d", Fluent.Translator._v); font.bold: true; font.pixelSize: Fluent.Enums.typography.subtitle; color: Fluent.Enums.textColor.primary }
            Button { text: Fluent.Translator.tr("gallery_3fd47edce45b3603", Fluent.Translator._v); onClicked: bottomDrawer.close() }
        }
    }

    // Reusable outside Drawer demo 独立外层抽屉演示组件
    component OutsideDrawer: Drawer {
        id: outsideControl

        mode: Fluent.Enums.drawer.mode_outside
        drawerWidth: rightDrawer.drawerWidth
        drawerHeight: bottomDrawer.drawerHeight

        Column {
            anchors.centerIn: parent; spacing: Fluent.Enums.spacing.l
            Text { text: Fluent.Translator.tr("gallery_ba59d151d3d96219", Fluent.Translator._v); font.bold: true; font.pixelSize: Fluent.Enums.typography.subtitle; color: Fluent.Enums.textColor.primary }
            Button { text: Fluent.Translator.tr("gallery_3fd47edce45b3603", Fluent.Translator._v); onClicked: outsideControl.close() }
        }
    }

    OutsideDrawer {
        id: outsideLeftDrawer

        objectName: "galleryOutsideLeftDrawer"
        position: Fluent.Enums.position.left
    }

    OutsideDrawer {
        id: outsideRightDrawer

        objectName: "galleryOutsideRightDrawer"
        position: Fluent.Enums.position.right
    }

    OutsideDrawer {
        id: outsideTopDrawer

        objectName: "galleryOutsideTopDrawer"
        position: Fluent.Enums.position.top
    }

    OutsideDrawer {
        id: outsideBottomDrawer

        objectName: "galleryOutsideBottomDrawer"
        position: Fluent.Enums.position.bottom
    }
}
