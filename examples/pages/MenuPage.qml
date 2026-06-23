// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// 导入组件
import PrismQML as Fluent
import "../../fluentqml/FluentQML/controls/buttons"
import "../../fluentqml/FluentQML/controls/menus"
import "../../fluentqml/FluentQML/controls/data"
import "../../fluentqml/FluentQML/controls/containers"
import "../../fluentqml/FluentQML/controls/navigation"
import "../../fluentqml/FluentQML/controls/inputs"

// 菜单与列表页面
Item {
    id: root
    
    function iconPath(name) {
        return Qt.resolvedUrl("../../fluentqml/FluentQML/controls/icons/fluent/" + name + ".svg")
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
                Text { text: "菜单与列表"; font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
                Text { text: "fluentqml.controls.menus"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
            }
            
            // 右键菜单
            ExampleCard {
                title: "右键菜单"
                description: "ContextMenu - 自动绑定父组件右键事件"
                ComponentCard {
                    label: "ContextMenu"
                    Rectangle {
                        width: 180; height: 55; radius: Fluent.Enums.radius.small
                        color: Fluent.Enums.stateColor.controlBgHover
                        border.width: Fluent.Enums.border.thin; border.color: Fluent.Enums.stateColor.border
                        Text { anchors.centerIn: parent; text: "右键点击此区域"; color: Fluent.Enums.textColor.secondary }
                        ContextMenu {
                            Action { text: "剪切"; icon: "Cut" }
                            Action { text: "复制"; icon: "Copy" }
                            Action { text: "粘贴"; icon: "Clipboard" }
                            MenuSeparator {}
                            Action { text: "删除"; icon: "Delete" }
                        }
                    }
                }
            }
            
            // 滚动文字
            ExampleCard {
                title: "滚动文字"
                description: "Marquee"
                ComponentCard {
                    label: "Marquee"
                    Marquee { width: 280; text: "滚动文字 - FluentQML 组件库展示"; forceScroll: true }
                }
            }
            
            // 列表与表格组件
            ExampleCard {
                title: "列表与表格组件"
                description: "ListWidget / TableWidget / TreeWidget"
                Row {
                    spacing: Fluent.Enums.spacing.xl
                    ComponentCard { 
                        label: "ListWidget"
                        ListWidget { 
                            id: demoListWidget
                            width: 200; height: 360
                            Component.onCompleted: {
                                var items = []
                                for (var i = 1; i <= 100; i++) items.push("列表项" + i)
                                model = items
                            }
                        }
                    }
                    ComponentCard {
                        label: "TreeWidget"
                        TreeWidget {
                            id: demoTreeWidget
                            width: 280; height: 360
                            model: [
                                {
                                    text: "技术部",
                                    expanded: true,
                                    children: [
                                        { text: "前端组" },
                                        { text: "后端组" },
                                        { text: "测试组" }
                                    ]
                                },
                                {
                                    text: "产品部",
                                    expanded: true,
                                    children: [
                                        {
                                            text: "设计组",
                                            expanded: false,
                                            children: [
                                                { text: "视觉设计" },
                                                { text: "交互设计" },
                                                { text: "用户研究" }
                                            ]
                                        },
                                        {
                                            text: "运营组",
                                            expanded: false,
                                            children: [
                                                { text: "内容运营" },
                                                { text: "活动运营" }
                                            ]
                                        },
                                        { text: "项目经理" },
                                        { text: "数据分析师" }
                                    ]
                                },
                                {
                                    text: "市场部",
                                    expanded: false,
                                    children: [
                                        { text: "品牌推广" },
                                        { text: "渠道合作" },
                                        { text: "商务拓展" }
                                    ]
                                }
                            ]
                        }
                    }
                    ComponentCard {
                        label: "TableWidget"
                        TableWidget {
                            width: 380; height: 360
                            editable: true
                            showFooter: true
                            defaultContextMenuEnabled: true

                            columns: [{text: "名称", width: 0.4, role: "name"}, {text: "数量", width: 0.3, role: "count"}, {text: "价格", width: 0.3, role: "price"}]

                            Component.onCompleted: {
                                var newTableData = []
                                for (var i = 1; i <= 10; i++) {
                                    newTableData.push({name: "商品" + i, count: i * 2, price: "￥" + (i * 10)})
                                }
                                tableData = newTableData
                            }
                        }
                    }
                }
            }

            // 列表/表格视图 (低阶 View)
            ExampleCard {
                title: "列表/表格视图"
                description: "ListView / TableView / TreeView - 低阶 View,需自定义 delegate"
                Row {
                    spacing: Fluent.Enums.spacing.xl
                    ComponentCard {
                        label: "ListView"
                        Fluent.ListView {
                            id: demoFluentListView
                            width: 220; height: 360
                            framed: true
                            showFooter: true
                            Component.onCompleted: {
                                var items = []
                                for (var i = 1; i <= 100; i++) items.push("视图项 " + i)
                                model = items
                            }
                            delegate: Rectangle {
                                id: _lvDelegate
                                required property int index
                                required property var modelData
                                width: ListView.view.width
                                height: 36
                                color: _lvMa.containsMouse
                                       ? Fluent.Enums.stateColor.treeItemHover
                                       : Fluent.Enums.transparent
                                radius: Fluent.Enums.radius.small
                                Behavior on color { ColorAnimation { duration: 100 } }

                                scale: _lvMa.pressed ? 0.97 : 1.0
                                Behavior on scale { NumberAnimation { duration: 80; easing.type: Easing.OutCubic } }
                                transformOrigin: Item.Center

                                Fluent.Label {
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.left: parent.left
                                    anchors.leftMargin: Fluent.Enums.spacing.listItemPadding
                                    type: Fluent.Enums.label.type_caption
                                    text: _lvDelegate.modelData
                                }

                                MouseArea {
                                    id: _lvMa
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onClicked: demoFluentListView.currentIndex = _lvDelegate.index
                                }
                            }
                        }
                    }
                    ComponentCard {
                        label: "TableView"
                        Fluent.TableView {
                            id: demoFluentTableView
                            width: 380; height: 360
                            columns: [
                                { text: "ID", width: 60 },
                                { text: "名称", width: 0.4 },
                                { text: "状态", fillWidth: true }
                            ]
                            Component.onCompleted: {
                                var rows = []
                                for (var i = 1; i <= 50; i++) {
                                    rows.push({ id: i, name: "条目 " + i, status: i % 2 === 0 ? "启用" : "停用" })
                                }
                                model = rows
                            }
                            delegate: Rectangle {
                                id: _tvDelegate
                                required property int index
                                required property var modelData
                                width: ListView.view.width
                                height: 40
                                color: Fluent.Enums.transparent
                                radius: Fluent.Enums.radius.small

                                scale: _tvMa.pressed ? 0.98 : 1.0
                                Behavior on scale { NumberAnimation { duration: 80; easing.type: Easing.OutCubic } }
                                transformOrigin: Item.Center

                                // Hover overlay 悬浮叠加层
                                Rectangle {
                                    anchors.fill: parent
                                    radius: parent.radius
                                    color: Fluent.Enums.isDark ? Qt.rgba(1,1,1,0.06) : Qt.rgba(0,0,0,0.035)
                                    visible: _tvMa.containsMouse
                                }

                                // Bottom separator 底部分隔
                                Rectangle {
                                    anchors.bottom: parent.bottom
                                    anchors.left: parent.left
                                    anchors.right: parent.right
                                    anchors.leftMargin: 8
                                    anchors.rightMargin: 8
                                    height: 1
                                    color: Fluent.Enums.isDark ? Qt.rgba(1,1,1,0.06) : Qt.rgba(0,0,0,0.05)
                                }

                                Row {
                                    anchors.fill: parent
                                    anchors.leftMargin: 8
                                    anchors.rightMargin: 8

                                    Item {
                                        width: demoFluentTableView.columnWidth(0); height: parent.height
                                        Fluent.Label {
                                            anchors.centerIn: parent
                                            type: Fluent.Enums.label.type_caption
                                            text: _tvDelegate.modelData.id
                                            color: Fluent.Enums.textColor.tertiary
                                            font.pixelSize: 12
                                        }
                                    }
                                    Item {
                                        width: demoFluentTableView.columnWidth(1); height: parent.height
                                        Fluent.Label {
                                            anchors.verticalCenter: parent.verticalCenter
                                            anchors.left: parent.left
                                            anchors.leftMargin: Fluent.Enums.spacing.m
                                            type: Fluent.Enums.label.type_caption
                                            text: _tvDelegate.modelData.name
                                        }
                                    }
                                    Item {
                                        width: demoFluentTableView.columnWidth(2); height: parent.height
                                        Rectangle {
                                            anchors.centerIn: parent
                                            width: _statusLabel.implicitWidth + 16
                                            height: 22
                                            radius: 11
                                            color: _tvDelegate.modelData.status === "启用"
                                                   ? Qt.rgba(0.18, 0.75, 0.45, 0.12)
                                                   : Qt.rgba(0.85, 0.25, 0.25, 0.10)
                                            Fluent.Label {
                                                id: _statusLabel
                                                anchors.centerIn: parent
                                                type: Fluent.Enums.label.type_caption
                                                text: _tvDelegate.modelData.status
                                                color: _tvDelegate.modelData.status === "启用"
                                                       ? "#1fa84d" : "#c93c3c"
                                                font.pixelSize: 11
                                            }
                                        }
                                    }
                                }

                                MouseArea {
                                    id: _tvMa
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    acceptedButtons: Qt.NoButton
                                }
                            }
                        }
                    }
                    ComponentCard {
                        label: "TreeView"
                        Fluent.TreeView {
                            width: 280; height: 360
                            model: [
                                {
                                    text: "文档", expanded: true, children: [
                                        { text: "工作报告.docx" },
                                        { text: "会议纪要.pdf" },
                                        { text: "需求文档.md" }
                                    ]
                                },
                                {
                                    text: "图片", expanded: false, children: [
                                        { text: "截图", children: [
                                            { text: "bug-01.png" },
                                            { text: "bug-02.png" }
                                        ]},
                                        { text: "照片", children: [
                                            { text: "团建.jpg" }
                                        ]}
                                    ]
                                },
                                {
                                    text: "代码", expanded: true, children: [
                                        { text: "src", expanded: true, children: [
                                            { text: "main.py" },
                                            { text: "utils.py" }
                                        ]},
                                        { text: "tests", children: [
                                            { text: "test_main.py" }
                                        ]}
                                    ]
                                }
                            ]
                        }
                    }
                }
            }
            ExampleCard {
                title: "标签页"
                description: "TabWidget"
                Column {
                    spacing: Fluent.Enums.spacing.l
                    Row {
                        spacing: Fluent.Enums.spacing.xl
                        ComponentCard {
                            label: "TabWidget"
                            TabWidget {
                                id: defaultTabWidget
                                width: 320; height: 110
                                showAddButton: true
                                closable: true
                                tabs: [
                                    {title: "标签1", icon: "", content: tab1Content},
                                    {title: "标签2", icon: "", content: tab2Content},
                                    {title: "标签3", icon: "", content: tab3Content}
                                ]
                                onTabClosed: (index) => { removeTab(index); apiStatus.text = "已关闭标签 " + index }
                                onTabAddClicked: { addTab("新标签" + (count() + 1), "", tab4Content); apiStatus.text = "已添加新标签" }
                                onCurrentChanged: (index) => apiStatus.text = "切换到标签 " + index
                            }
                        }
                    }
                    // API演示
                    Row {
                        spacing: Fluent.Enums.spacing.m
                        Button { text: "添加标签"; onClicked: { defaultTabWidget.addTab("动态标签", "", tab4Content); apiStatus.text = "addTab() 已添加" } }
                        Button { text: "移除当前"; onClicked: { defaultTabWidget.removeTab(defaultTabWidget.currentIndex); apiStatus.text = "removeTab() 已移除" } }
                        Button { text: "修改文本"; onClicked: { defaultTabWidget.setTabText(defaultTabWidget.currentIndex, "已修改"); apiStatus.text = "setTabText() 已修改" } }
                        Button { text: "清空全部"; onClicked: { defaultTabWidget.clear(); apiStatus.text = "clear() 已清空" } }
                        Button { text: "重置"; onClicked: { defaultTabWidget.tabs = [{title: "标签1", icon: "", content: tab1Content}, {title: "标签2", icon: "", content: tab2Content}, {title: "标签3", icon: "", content: tab3Content}]; apiStatus.text = "已重置" } }
                        Text { id: apiStatus; text: "API状态"; color: Fluent.Enums.textColor.secondary; font.pixelSize: Fluent.Enums.typography.caption; anchors.verticalCenter: parent.verticalCenter }
                    }
                }
                Component { id: tab1Content; Rectangle { anchors.fill: parent; color: Fluent.Enums.demoPalette.blue; Text { anchors.centerIn: parent; text: "内容1"; color: Fluent.Enums.accentForeground } } }
                Component { id: tab2Content; Rectangle { anchors.fill: parent; color: Fluent.Enums.demoPalette.green; Text { anchors.centerIn: parent; text: "内容2"; color: Fluent.Enums.accentForeground } } }
                Component { id: tab3Content; Rectangle { anchors.fill: parent; color: Fluent.Enums.demoPalette.orange; Text { anchors.centerIn: parent; text: "内容3"; color: Fluent.Enums.accentForeground } } }
                Component { id: tab4Content; Rectangle { anchors.fill: parent; color: Fluent.Enums.demoPalette.purple; Text { anchors.centerIn: parent; text: "动态内容"; color: Fluent.Enums.accentForeground } } }
            }
            
            // 数据展示
            ExampleCard {
                title: "数据展示"
                description: "Timeline"
                Row {
                    spacing: Fluent.Enums.spacing.xl
                    ComponentCard { 
                        label: "Timeline"
                        Timeline { 
                            width: 320
                            items: [
                                {title: "已完成", status: "success", cards: [{text: "完成需求评审与设计稿", strikeOut: true}]},
                                {title: "今日安排", status: "info", cards: [{text: "开发首页组件", status: "warning"}, {text: "编写单元测试", status: "warning"}]},
                                {title: "待办事项", status: "error", cards: [{text: "提交代码评审", status: "error"}]}
                            ]
                        }
                    }
                }
            }
            
            // Image
            ExampleCard {
                title: "图片组件"
                description: "ImageWidget - 支持圆角、加载状态、点击事件"
                Row {
                    spacing: Fluent.Enums.spacing.xl
                    ComponentCard {
                        label: "ImageWidget"
                        ImageWidget {
                            id: apiImage
                            width: 320; height: 180
                            source: "qrc:/image/background.jpg"
                            onClicked: imageText.text = "clicked信号触发!"
                        }
                    }
                    Column {
                        spacing: Fluent.Enums.spacing.xs
                        Text { text: "点击图片测试clicked信号"; font.pixelSize: Fluent.Enums.typography.bodySmall; color: Fluent.Enums.textColor.primary }
                        Text { id: imageText; text: "状态: 未点击"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary }
                    }
                }
            }
            
            // 分页指示器
            ExampleCard {
                title: "分页指示器"
                description: "PipsPager - 支持翻页按钮、可见数量限制、平滑滚动"
                Column {
                    spacing: Fluent.Enums.spacing.l
                    Row {
                        spacing: Fluent.Enums.spacing.xl
                        ComponentCard { label: "基础 (5点)"; HorizontalPipsPager { count: 5; currentIndex: 2 } }
                        ComponentCard { label: "垂直"; VerticalPipsPager { count: 4; currentIndex: 1 } }
                        ComponentCard {
                            label: "带按钮 (始终显示)"
                            HorizontalPipsPager {
                                count: 10; currentIndex: 3; maxVisible: 5
                                prevButtonMode: Fluent.Enums.pipsPager.button_always
                                nextButtonMode: Fluent.Enums.pipsPager.button_always
                            }
                        }
                    }
                }
            }

        }
    }
}
