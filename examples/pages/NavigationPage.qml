// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// 导入组件
import PrismQML as Fluent
import "../../prismqml/PrismQML/controls/buttons"
import "../../prismqml/PrismQML/controls/navigation"
import "../../prismqml/PrismQML/controls/containers"
import "../../prismqml/PrismQML/controls/data"

// 导航组件页面
Item {
    id: root
    
    function iconPath(name) {
        return Qt.resolvedUrl("../../prismqml/PrismQML/controls/icons/fluent/" + name + ".svg")
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
                Text { text: "导航组件"; font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
                Text { text: "prismqml.controls.navigation"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
            }
            
            // 面包屑
            ExampleCard {
                title: "面包屑导航"
                description: "BreadcrumbBar - 流畅动画、图标支持、主题色指示器"
                Column {
                    spacing: Fluent.Enums.spacing.l
                    
                    // Basic breadcrumb 基础面包屑
                    ComponentCard {
                        label: "基础面包屑"
                        Column {
                            spacing: Fluent.Enums.spacing.m
                            Breadcrumb { 
                                id: basicBreadcrumb
                                showIcons: false
                                Component.onCompleted: {
                                    addItem("home", "首页")
                                    addItem("docs", "文档")
                                    addItem("components", "组件")
                                    addItem("navigation", "导航")
                                }
                                onCurrentItemChanged: (key) => basicText.text = "当前: " + key
                            }
                            Row {
                                spacing: Fluent.Enums.spacing.s
                                Button { text: "添加子页"; onClicked: basicBreadcrumb.addItem("sub" + basicBreadcrumb.count, "子页" + basicBreadcrumb.count) }
                                Button { text: "返回上级"; onClicked: basicBreadcrumb.popItem() }
                            }
                            Text { id: basicText; text: "点击面包屑项测试截断"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
                        }
                    }
                    
                    // Breadcrumb with icons 带图标面包屑
                    ComponentCard {
                        label: "带图标面包屑"
                        Column {
                            spacing: Fluent.Enums.spacing.m
                            Breadcrumb { 
                                id: iconBreadcrumb
                                showIcons: true
                                Component.onCompleted: {
                                    addItem("home", "首页", Fluent.Enums.icon.home)
                                    addItem("folder", "文件夹", Fluent.Enums.icon.folder)
                                    addItem("docs", "文档", Fluent.Enums.icon.document)
                                    addItem("file", "文件", Fluent.Enums.icon.document_text)
                                }
                                onCurrentItemChanged: (key) => iconText.text = "当前: " + key
                            }
                            Row {
                                spacing: Fluent.Enums.spacing.s
                                Button { text: "添加图片"; onClicked: iconBreadcrumb.addItem("img" + iconBreadcrumb.count, "图片" + iconBreadcrumb.count, Fluent.Enums.icon.image) }
                                Button { text: "返回上级"; onClicked: iconBreadcrumb.popItem() }
                            }
                            Text { id: iconText; text: "带图标的面包屑导航"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
                        }
                    }
                    
                    // Overflow demo 溢出演示
                    ComponentCard {
                        label: "溢出省略 (maxVisibleItems: 4)"
                        Column {
                            spacing: Fluent.Enums.spacing.m
                            Breadcrumb { 
                                id: overflowBreadcrumb
                                maxVisibleItems: 4
                                showIcons: true
                                Component.onCompleted: {
                                    addItem("root", "根目录", Fluent.Enums.icon.home)
                                    addItem("level1", "一级目录", Fluent.Enums.icon.folder)
                                    addItem("level2", "二级目录", Fluent.Enums.icon.folder)
                                    addItem("level3", "三级目录", Fluent.Enums.icon.folder)
                                    addItem("level4", "四级目录", Fluent.Enums.icon.folder)
                                    addItem("current", "当前位置", Fluent.Enums.icon.location)
                                }
                            }
                            Row {
                                spacing: Fluent.Enums.spacing.s
                                Button { text: "添加层级"; onClicked: overflowBreadcrumb.addItem("deep" + overflowBreadcrumb.count, "深层" + overflowBreadcrumb.count, Fluent.Enums.icon.folder) }
                                Button { text: "返回上级"; onClicked: overflowBreadcrumb.popItem() }
                                Button { text: "重置"; onClicked: { overflowBreadcrumb.clear(); overflowBreadcrumb.addItem("root", "根目录", Fluent.Enums.icon.home) } }
                            }
                            Text { text: "超过4项时自动折叠中间项到省略菜单"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
                        }
                    }
                }
            }
            
            // 分段控件
            ExampleCard {
                title: "分段/切换控件"
                description: "SegmentedControl / Pivot"
                Column {
                    spacing: Fluent.Enums.spacing.l
                    ComponentCard { label: "SegmentedControl"; SegmentedControl { items: ["选项1", "选项2", "选项3"] } }
                    ComponentCard { label: "Pivot"; Pivot { items: ["全部", "文档", "图片", "视频"] } }
                }
            }
            
            // 步骤进度条
            ExampleCard {
                title: "步骤进度条"
                description: "Stepper - 支持图标和文字"
                ComponentCard {
                    label: "Stepper"
                    Column {
                        spacing: Fluent.Enums.spacing.m
                        Stepper { 
                            id: stepProgress
                            width: 500
                            steps: [
                                {text: "订单", icon: "Clipboard"},
                                {text: "购物车", icon: "Cart"},
                                {text: "账户信息", icon: "Person"},
                                {text: "配送", icon: ""},
                                {text: "支付", icon: ""}
                            ]
                            currentStep: 2
                        }
                        Row {
                            spacing: Fluent.Enums.spacing.s
                            Button { text: "上一步"; onClicked: stepProgress.stepBack() }
                            Button { text: "下一步"; onClicked: stepProgress.stepNext() }
                        }
                    }
                }
            }
            
            // StackedWidget 动画类型展示
            ExampleCard {
                title: "StackedWidget (animationType枚举)"
                description: "StackedWidget - 通过animationType切换动画类型"
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
                title: "命令栏视图"
                description: "CommandBar (type_view)"
                ComponentCard {
                    label: "CommandBar View"
                    CommandBar { 
                        type: Fluent.Enums.commandBar.type_view
                        primaryCommands: [{text: "新建", icon: iconPath("DocumentAdd")}, {text: "打开", icon: iconPath("FolderOpen")}, {text: "保存", icon: iconPath("Save")}, {separator: true}, {text: "剪切", icon: iconPath("Cut")}, {text: "复制", icon: iconPath("Copy")}]
                    }
                }
            }
            
            // CommandBar
            ExampleCard {
                title: "命令栏"
                description: "CommandBar"
                ComponentCard {
                    label: "CommandBar"
                    CommandBar { 
                        width: 380
                        primaryCommands: [
                            {icon: iconPath("DocumentAdd"), text: "新建"},
                            {icon: iconPath("FolderOpen"), text: "打开"},
                            {icon: iconPath("Save"), text: "保存"}
                        ]
                        secondaryCommands: [
                            {icon: iconPath("Settings"), text: "设置"},
                            {icon: iconPath("QuestionCircle"), text: "帮助"},
                            {icon: iconPath("QuestionCircle"), text: "帮助2"},
                            {icon: iconPath("QuestionCircle"), text: "帮助3"},
                            {icon: iconPath("QuestionCircle"), text: "帮助4"},
                            {icon: iconPath("QuestionCircle"), text: "帮助5"}
                        ]
                    }
                }
            }
            
            // 分页器
            ExampleCard {
                title: "分页器"
                description: "Paginator"
                ComponentCard {
                    label: "Paginator"
                    Paginator { totalPages: 10; currentPage: 3 }
                }
            }
            
            // 菜单栏
            ExampleCard {
                title: "菜单栏"
                description: "MenuBar"
                ComponentCard {
                    label: "MenuBar"
                    MenuBar {
                        width: 400
                        items: [
                            {text: "文件", children: [{text: "新建"}, {text: "打开"}, {text: "保存"}]},
                            {text: "编辑", children: [{text: "撤销"}, {text: "重做"}]},
                            {text: "帮助", children: [{text: "关于"}]}
                        ]
                    }
                }
            }

        }
    }
}
