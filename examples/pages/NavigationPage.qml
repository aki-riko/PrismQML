// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// 导入组件
import PrismQML
import PrismQML as Fluent

// 导航组件页面
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
                Text { text: Fluent.Translator.tr("gallery_416a19daaaa5e27a", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
                Text { text: "prismqml.controls.navigation"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
            }
            
            // 面包屑
            ExampleCard {
                title: Fluent.Translator.tr("gallery_6c3f7b6a12a97468", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_aefd232185a863d6", Fluent.Translator._v)
                Column {
                    spacing: Fluent.Enums.spacing.l
                    
                    // Basic breadcrumb 基础面包屑
                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_71fd13b9ab679678", Fluent.Translator._v)
                        Column {
                            spacing: Fluent.Enums.spacing.m
                            Breadcrumb { 
                                id: basicBreadcrumb
                                showIcons: false
                                Component.onCompleted: {
                                    addItem("home", Fluent.Translator.tr("gallery_203c08e0d44ac375", Fluent.Translator._v))
                                    addItem("docs", Fluent.Translator.tr("gallery_2687ccdbb1d2288a", Fluent.Translator._v))
                                    addItem("components", Fluent.Translator.tr("gallery_783d638053ea1897", Fluent.Translator._v))
                                    addItem("navigation", Fluent.Translator.tr("gallery_e72622fe470d04bc", Fluent.Translator._v))
                                }
                                onCurrentItemChanged: (key) => basicText.text = Fluent.Translator.tr("gallery_6245bfb449a7e29a") + key
                            }
                            Row {
                                spacing: Fluent.Enums.spacing.s
                                Button { text: Fluent.Translator.tr("gallery_9f63b859185cc52e", Fluent.Translator._v); onClicked: basicBreadcrumb.addItem("sub" + basicBreadcrumb.count, Fluent.Translator.tr("gallery_6fc800788812ce20") + basicBreadcrumb.count) }
                                Button { text: Fluent.Translator.tr("gallery_6e280f54e3f9a1b5", Fluent.Translator._v); onClicked: basicBreadcrumb.popItem() }
                            }
                            Text { id: basicText; text: Fluent.Translator.tr("gallery_af28875a2bfd7a3c", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
                        }
                    }
                    
                    // Breadcrumb with icons 带图标面包屑
                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_098537ecdc81e809", Fluent.Translator._v)
                        Column {
                            spacing: Fluent.Enums.spacing.m
                            Breadcrumb { 
                                id: iconBreadcrumb
                                showIcons: true
                                Component.onCompleted: {
                                    addItem("home", Fluent.Translator.tr("gallery_203c08e0d44ac375", Fluent.Translator._v), Fluent.Enums.icon.home)
                                    addItem("folder", Fluent.Translator.tr("gallery_7c7802d8adaed72e", Fluent.Translator._v), Fluent.Enums.icon.folder)
                                    addItem("docs", Fluent.Translator.tr("gallery_2687ccdbb1d2288a", Fluent.Translator._v), Fluent.Enums.icon.document)
                                    addItem("file", Fluent.Translator.tr("gallery_39932f24fe11a6ba", Fluent.Translator._v), Fluent.Enums.icon.document_text)
                                }
                                onCurrentItemChanged: (key) => iconText.text = Fluent.Translator.tr("gallery_6245bfb449a7e29a") + key
                            }
                            Row {
                                spacing: Fluent.Enums.spacing.s
                                Button { text: Fluent.Translator.tr("gallery_9f0d4e4656ee5dbc", Fluent.Translator._v); onClicked: iconBreadcrumb.addItem("img" + iconBreadcrumb.count, Fluent.Translator.tr("gallery_d24c10d37db0feea") + iconBreadcrumb.count, Fluent.Enums.icon.image) }
                                Button { text: Fluent.Translator.tr("gallery_6e280f54e3f9a1b5", Fluent.Translator._v); onClicked: iconBreadcrumb.popItem() }
                            }
                            Text { id: iconText; text: Fluent.Translator.tr("gallery_9931589c64452c89", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
                        }
                    }
                    
                    // Overflow demo 溢出演示
                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_3f8772eda407feb6", Fluent.Translator._v)
                        Column {
                            spacing: Fluent.Enums.spacing.m
                            Breadcrumb { 
                                id: overflowBreadcrumb
                                maxVisibleItems: 4
                                showIcons: true
                                Component.onCompleted: {
                                    addItem("root", Fluent.Translator.tr("gallery_42ee2863b6d776ff", Fluent.Translator._v), Fluent.Enums.icon.home)
                                    addItem("level1", Fluent.Translator.tr("gallery_a64ef18ab49bdc3d", Fluent.Translator._v), Fluent.Enums.icon.folder)
                                    addItem("level2", Fluent.Translator.tr("gallery_d5335a84faaada38", Fluent.Translator._v), Fluent.Enums.icon.folder)
                                    addItem("level3", Fluent.Translator.tr("gallery_646dd7daa0ffcf85", Fluent.Translator._v), Fluent.Enums.icon.folder)
                                    addItem("level4", Fluent.Translator.tr("gallery_4f4ceee94c6d268a", Fluent.Translator._v), Fluent.Enums.icon.folder)
                                    addItem("current", Fluent.Translator.tr("gallery_6be6c8248ec61181", Fluent.Translator._v), Fluent.Enums.icon.location)
                                }
                            }
                            Row {
                                spacing: Fluent.Enums.spacing.s
                                Button { text: Fluent.Translator.tr("gallery_65b1aa217f342c3b", Fluent.Translator._v); onClicked: overflowBreadcrumb.addItem("deep" + overflowBreadcrumb.count, Fluent.Translator.tr("gallery_e88300b4a20a8512") + overflowBreadcrumb.count, Fluent.Enums.icon.folder) }
                                Button { text: Fluent.Translator.tr("gallery_6e280f54e3f9a1b5", Fluent.Translator._v); onClicked: overflowBreadcrumb.popItem() }
                                Button { text: Fluent.Translator.tr("gallery_cb5d682bac3d1a2d", Fluent.Translator._v); onClicked: { overflowBreadcrumb.clear(); overflowBreadcrumb.addItem("root", Fluent.Translator.tr("gallery_42ee2863b6d776ff", Fluent.Translator._v), Fluent.Enums.icon.home) } }
                            }
                            Text { text: Fluent.Translator.tr("gallery_ef08bff1a9823248", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
                        }
                    }
                }
            }
            
            // 分段控件
            ExampleCard {
                title: Fluent.Translator.tr("gallery_e998714a526683d7", Fluent.Translator._v)
                description: "SegmentedControl / Pivot"
                Column {
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard { label: "SegmentedControl"; SegmentedControl { items: [Fluent.Translator.tr("gallery_96198518dab609f0", Fluent.Translator._v), Fluent.Translator.tr("gallery_5f04a01fe105bb4d", Fluent.Translator._v), Fluent.Translator.tr("gallery_74b97119bee5c66d", Fluent.Translator._v)] } }
                    ComponentCard { label: "Pivot"; Pivot { items: [Fluent.Translator.tr("gallery_5c55a67935af8f45", Fluent.Translator._v), Fluent.Translator.tr("gallery_2687ccdbb1d2288a", Fluent.Translator._v), Fluent.Translator.tr("gallery_d24c10d37db0feea", Fluent.Translator._v), Fluent.Translator.tr("gallery_c20f7618d330a854", Fluent.Translator._v)] } }
                }
            }
            
            // 步骤进度条
            ExampleCard {
                title: Fluent.Translator.tr("gallery_ae9e675a583eeb35", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_e8ac692d3cae2e98", Fluent.Translator._v)
                ComponentCard {
                    label: "Stepper"
                    Column {
                        spacing: Fluent.Enums.spacing.m
                        Stepper { 
                            id: stepProgress
                            width: 500
                            steps: [
                                {text: Fluent.Translator.tr("gallery_3d5436ea23d2e9a2", Fluent.Translator._v), icon: "Clipboard"},
                                {text: Fluent.Translator.tr("gallery_f5e1243b0aa8c3c3", Fluent.Translator._v), icon: "Cart"},
                                {text: Fluent.Translator.tr("gallery_34e5636c63cc8f78", Fluent.Translator._v), icon: "Person"},
                                {text: Fluent.Translator.tr("gallery_a662b954e297a878", Fluent.Translator._v), icon: ""},
                                {text: Fluent.Translator.tr("gallery_5d3ba34cc66cea45", Fluent.Translator._v), icon: ""}
                            ]
                            currentStep: 2
                        }
                        Row {
                            spacing: Fluent.Enums.spacing.s
                            Button { text: Fluent.Translator.tr("gallery_da336fdc0dbd1818", Fluent.Translator._v); onClicked: stepProgress.stepBack() }
                            Button { text: Fluent.Translator.tr("gallery_acfc4e74a650e7df", Fluent.Translator._v); onClicked: stepProgress.stepNext() }
                        }
                    }
                }
            }
            
            // StackedWidget 动画类型展示
            ExampleCard {
                title: Fluent.Translator.tr("gallery_ee1f55ea470c1fb0", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_9f6fc091d21f095d", Fluent.Translator._v)
                Row {
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard {
                        label: "opacity"
                        Column {
                            spacing: Fluent.Enums.spacing.xs
                            StackedWidget {
                                id: opacityStack; width: 110; height: 55
                                animationType: Fluent.Enums.animation.opacity
                                Rectangle { color: Fluent.Enums.demoPalette.blue; Text { anchors.centerIn: parent; text: "1"; color: Fluent.Enums.accentForeground } }
                                Rectangle { color: Fluent.Enums.demoPalette.green; Text { anchors.centerIn: parent; text: "2"; color: Fluent.Enums.accentForeground } }
                            }
                            Row {
                                spacing: Fluent.Enums.spacing.xs
                                Button { text: "1"; width: 26; onClicked: opacityStack.currentIndex = 0 }
                                Button { text: "2"; width: 26; onClicked: opacityStack.currentIndex = 1 }
                            }
                        }
                    }
                    ComponentCard {
                        label: "popup"
                        Column {
                            spacing: Fluent.Enums.spacing.xs
                            StackedWidget {
                                id: popupStack; width: 110; height: 55
                                animationType: Fluent.Enums.animation.popup
                                Rectangle { color: Fluent.Enums.demoPalette.orange; Text { anchors.centerIn: parent; text: "1"; color: Fluent.Enums.accentForeground } }
                                Rectangle { color: Fluent.Enums.demoPalette.red; Text { anchors.centerIn: parent; text: "2"; color: Fluent.Enums.accentForeground } }
                            }
                            Row {
                                spacing: Fluent.Enums.spacing.xs
                                Button { text: "1"; width: 26; onClicked: popupStack.currentIndex = 0 }
                                Button { text: "2"; width: 26; onClicked: popupStack.currentIndex = 1 }
                            }
                        }
                    }
                    ComponentCard {
                        label: "popdown"
                        Column {
                            spacing: Fluent.Enums.spacing.xs
                            StackedWidget {
                                id: popdownStack; width: 110; height: 55
                                animationType: Fluent.Enums.animation.popdown
                                Rectangle { color: Fluent.Enums.demoPalette.sky; Text { anchors.centerIn: parent; text: "1"; color: Fluent.Enums.accentForeground } }
                                Rectangle { color: Fluent.Enums.demoPalette.lime; Text { anchors.centerIn: parent; text: "2"; color: Fluent.Enums.accentForeground } }
                            }
                            Row {
                                spacing: Fluent.Enums.spacing.xs
                                Button { text: "1"; width: 26; onClicked: popdownStack.currentIndex = 0 }
                                Button { text: "2"; width: 26; onClicked: popdownStack.currentIndex = 1 }
                            }
                        }
                    }
                    ComponentCard {
                        label: "slide"
                        Column {
                            spacing: Fluent.Enums.spacing.xs
                            StackedWidget {
                                id: slideStack; width: 110; height: 55
                                animationType: Fluent.Enums.animation.slide
                                Rectangle { color: Fluent.Enums.demoPalette.purple; Text { anchors.centerIn: parent; text: "1"; color: Fluent.Enums.accentForeground } }
                                Rectangle { color: Fluent.Enums.demoPalette.pink; Text { anchors.centerIn: parent; text: "2"; color: Fluent.Enums.accentForeground } }
                            }
                            Row {
                                spacing: Fluent.Enums.spacing.xs
                                Button { text: "1"; width: 26; onClicked: slideStack.currentIndex = 0 }
                                Button { text: "2"; width: 26; onClicked: slideStack.currentIndex = 1 }
                            }
                        }
                    }
                    ComponentCard {
                        label: "card"
                        Column {
                            spacing: Fluent.Enums.spacing.xs
                            StackedWidget {
                                id: cardStack; width: 110; height: 55
                                animationType: Fluent.Enums.animation.card
                                Rectangle { color: Fluent.Enums.demoPalette.cyan; Text { anchors.centerIn: parent; text: "1"; color: Fluent.Enums.accentForeground } }
                                Rectangle { color: Fluent.Enums.demoPalette.teal; Text { anchors.centerIn: parent; text: "2"; color: Fluent.Enums.accentForeground } }
                            }
                            Row {
                                spacing: Fluent.Enums.spacing.xs
                                Button { text: "1"; width: 26; onClicked: cardStack.currentIndex = 0 }
                                Button { text: "2"; width: 26; onClicked: cardStack.currentIndex = 1 }
                            }
                        }
                    }
                    ComponentCard {
                        label: "zoom"
                        Column {
                            spacing: Fluent.Enums.spacing.xs
                            StackedWidget {
                                id: zoomStack; width: 110; height: 55
                                animationType: Fluent.Enums.animation.zoom
                                Rectangle { color: Fluent.Enums.demoPalette.sky; Text { anchors.centerIn: parent; text: "1"; color: Fluent.Enums.accentForeground } }
                                Rectangle { color: Fluent.Enums.demoPalette.lime; Text { anchors.centerIn: parent; text: "2"; color: Fluent.Enums.accentForeground } }
                            }
                            Row {
                                spacing: Fluent.Enums.spacing.xs
                                Button { text: "1"; width: 26; onClicked: zoomStack.currentIndex = 0 }
                                Button { text: "2"; width: 26; onClicked: zoomStack.currentIndex = 1 }
                            }
                        }
                    }
                }
            }
            
            // 命令栏视图
            ExampleCard {
                title: Fluent.Translator.tr("gallery_1b2a34ab3faa47a8", Fluent.Translator._v)
                description: "CommandBar (type_view)"
                ComponentCard {
                    label: "CommandBar View"
                    CommandBar { 
                        type: Fluent.Enums.commandBar.type_view
                        primaryCommands: [{text: Fluent.Translator.tr("gallery_50ef2f4cf6a46924", Fluent.Translator._v), icon: iconPath("DocumentAdd")}, {text: Fluent.Translator.tr("gallery_c771248e511fbf93", Fluent.Translator._v), icon: iconPath("FolderOpen")}, {text: Fluent.Translator.tr("gallery_a3030bf8f16dc63c", Fluent.Translator._v), icon: iconPath("Save")}, {separator: true}, {text: Fluent.Translator.tr("gallery_410a8e8a6bf253ac", Fluent.Translator._v), icon: iconPath("Cut")}, {text: Fluent.Translator.tr("gallery_63d90d977348ab1f", Fluent.Translator._v), icon: iconPath("Copy")}]
                    }
                }
            }
            
            // CommandBar
            ExampleCard {
                title: Fluent.Translator.tr("gallery_7e97e91f3221fc25", Fluent.Translator._v)
                description: "CommandBar"
                ComponentCard {
                    label: "CommandBar"
                    CommandBar { 
                        width: 380
                        primaryCommands: [
                            {icon: iconPath("DocumentAdd"), text: Fluent.Translator.tr("gallery_50ef2f4cf6a46924", Fluent.Translator._v)},
                            {icon: iconPath("FolderOpen"), text: Fluent.Translator.tr("gallery_c771248e511fbf93", Fluent.Translator._v)},
                            {icon: iconPath("Save"), text: Fluent.Translator.tr("gallery_a3030bf8f16dc63c", Fluent.Translator._v)}
                        ]
                        secondaryCommands: [
                            {icon: iconPath("Settings"), text: Fluent.Translator.tr("gallery_df3d58c7d84b85f2", Fluent.Translator._v)},
                            {icon: iconPath("QuestionCircle"), text: Fluent.Translator.tr("gallery_a57cfcb8428da408", Fluent.Translator._v)},
                            {icon: iconPath("QuestionCircle"), text: Fluent.Translator.tr("gallery_b5857e11ccce5cae", Fluent.Translator._v)},
                            {icon: iconPath("QuestionCircle"), text: Fluent.Translator.tr("gallery_e758fedc5fa97363", Fluent.Translator._v)},
                            {icon: iconPath("QuestionCircle"), text: Fluent.Translator.tr("gallery_8bdbd7f81a95dd3f", Fluent.Translator._v)},
                            {icon: iconPath("QuestionCircle"), text: Fluent.Translator.tr("gallery_11cf409424a0de6d", Fluent.Translator._v)}
                        ]
                    }
                }
            }
            
            // 分页器
            ExampleCard {
                title: Fluent.Translator.tr("gallery_4bf9ffa772b28b9d", Fluent.Translator._v)
                description: "Paginator"
                ComponentCard {
                    label: "Paginator"
                    Paginator { totalPages: 10; currentPage: 3 }
                }
            }
            
            // 菜单栏
            ExampleCard {
                title: Fluent.Translator.tr("gallery_a304cb9cd6c523bb", Fluent.Translator._v)
                description: "MenuBar"
                ComponentCard {
                    label: "MenuBar"
                    MenuBar {
                        width: 400
                        items: [
                            {text: Fluent.Translator.tr("gallery_39932f24fe11a6ba", Fluent.Translator._v), children: [{text: Fluent.Translator.tr("gallery_50ef2f4cf6a46924", Fluent.Translator._v)}, {text: Fluent.Translator.tr("gallery_c771248e511fbf93", Fluent.Translator._v)}, {text: Fluent.Translator.tr("gallery_a3030bf8f16dc63c", Fluent.Translator._v)}]},
                            {text: Fluent.Translator.tr("gallery_051836569928a9f9", Fluent.Translator._v), children: [{text: Fluent.Translator.tr("gallery_926a50b98ece2667", Fluent.Translator._v)}, {text: Fluent.Translator.tr("gallery_03717b6f10700f87", Fluent.Translator._v)}]},
                            {text: Fluent.Translator.tr("gallery_a57cfcb8428da408", Fluent.Translator._v), children: [{text: Fluent.Translator.tr("gallery_52d25a9e30ba94f1", Fluent.Translator._v)}]}
                        ]
                    }
                }
            }

        }
    }
}
