// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// 导入组件
import PrismQML
import PrismQML as Fluent

// 菜单与列表页面
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
                Text { text: Fluent.Translator.tr("gallery_0f978a6dffcf9c4e", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
                Text { text: "prismqml.controls.menus"; font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary; font.family: Fluent.Enums.fontFamily }
            }
            
            // 右键菜单
            ExampleCard {
                title: Fluent.Translator.tr("gallery_8cbbf31c44ce3dba", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_b7d9e9d08c3dac12", Fluent.Translator._v)
                ComponentCard {
                    label: "ContextMenu"
                    Rectangle {
                        width: 180; height: 55; radius: Fluent.Enums.radius.small
                        color: Fluent.Enums.stateColor.controlBgHover
                        border.width: Fluent.Enums.border.thin; border.color: Fluent.Enums.stateColor.border
                        Text { anchors.centerIn: parent; text: Fluent.Translator.tr("gallery_8f5812a418105b65", Fluent.Translator._v); color: Fluent.Enums.textColor.secondary }
                        ContextMenu {
                            Action { text: Fluent.Translator.tr("gallery_410a8e8a6bf253ac", Fluent.Translator._v); icon: "Cut" }
                            Action { text: Fluent.Translator.tr("gallery_63d90d977348ab1f", Fluent.Translator._v); icon: "Copy" }
                            Action { text: Fluent.Translator.tr("gallery_33517926747180e6", Fluent.Translator._v); icon: "Clipboard" }
                            MenuSeparator {}
                            Action { text: Fluent.Translator.tr("gallery_2f9daa828907b93f", Fluent.Translator._v); icon: "Delete" }
                        }
                    }
                }
            }
            
            // 滚动文字
            ExampleCard {
                title: Fluent.Translator.tr("gallery_251a120b78b76504", Fluent.Translator._v)
                description: "Marquee"
                ComponentCard {
                    label: "Marquee"
                    Marquee { width: 280; text: Fluent.Translator.tr("gallery_6d6f1b5d7d8dcb73", Fluent.Translator._v); forceScroll: true }
                }
            }
            
            // 列表与表格组件
            ExampleCard {
                title: Fluent.Translator.tr("gallery_ee9fee3d038211be", Fluent.Translator._v)
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
                                for (var i = 1; i <= 100; i++) items.push(Fluent.Translator.tr("gallery_795dec6ac7650b6e") + i)
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
                                    text: Fluent.Translator.tr("gallery_1f7e2646130e9a9b", Fluent.Translator._v),
                                    expanded: true,
                                    children: [
                                        { text: Fluent.Translator.tr("gallery_f7a2b9c330141e74", Fluent.Translator._v) },
                                        { text: Fluent.Translator.tr("gallery_b24a00b60dae4662", Fluent.Translator._v) },
                                        { text: Fluent.Translator.tr("gallery_7c8ef03c3f78d9d2", Fluent.Translator._v) }
                                    ]
                                },
                                {
                                    text: Fluent.Translator.tr("gallery_46cf15a123d5abfb", Fluent.Translator._v),
                                    expanded: true,
                                    children: [
                                        {
                                            text: Fluent.Translator.tr("gallery_8f56450d0a5b9f4d", Fluent.Translator._v),
                                            expanded: false,
                                            children: [
                                                { text: Fluent.Translator.tr("gallery_eb8bb03c922871b3", Fluent.Translator._v) },
                                                { text: Fluent.Translator.tr("gallery_1175ec13252066a8", Fluent.Translator._v) },
                                                { text: Fluent.Translator.tr("gallery_eba180059a944e2a", Fluent.Translator._v) }
                                            ]
                                        },
                                        {
                                            text: Fluent.Translator.tr("gallery_f1cb456890d5171c", Fluent.Translator._v),
                                            expanded: false,
                                            children: [
                                                { text: Fluent.Translator.tr("gallery_70a3c398dfd4eab9", Fluent.Translator._v) },
                                                { text: Fluent.Translator.tr("gallery_c521d2a476a35d3c", Fluent.Translator._v) }
                                            ]
                                        },
                                        { text: Fluent.Translator.tr("gallery_11888e7c9cd66fe3", Fluent.Translator._v) },
                                        { text: Fluent.Translator.tr("gallery_32f619c0fc80a1fc", Fluent.Translator._v) }
                                    ]
                                },
                                {
                                    text: Fluent.Translator.tr("gallery_ce6bdd090825f25c", Fluent.Translator._v),
                                    expanded: false,
                                    children: [
                                        { text: Fluent.Translator.tr("gallery_9a5855b14903159c", Fluent.Translator._v) },
                                        { text: Fluent.Translator.tr("gallery_7826bf6e0b3b589b", Fluent.Translator._v) },
                                        { text: Fluent.Translator.tr("gallery_27a9b1bc3c7194af", Fluent.Translator._v) }
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

                            columns: [{text: Fluent.Translator.tr("gallery_d44e9b3d3b31d37b", Fluent.Translator._v), width: 0.4, role: "name"}, {text: Fluent.Translator.tr("gallery_5e29d121dda011c5", Fluent.Translator._v), width: 0.3, role: "count"}, {text: Fluent.Translator.tr("gallery_0f4371a7a9cf224a", Fluent.Translator._v), width: 0.3, role: "price"}]

                            Component.onCompleted: {
                                var newTableData = []
                                for (var i = 1; i <= 10; i++) {
                                    newTableData.push({name: Fluent.Translator.tr("gallery_58fdb0941f368f2b") + i, count: i * 2, price: "￥" + (i * 10)})
                                }
                                tableData = newTableData
                            }
                        }
                    }
                }
            }

            // 列表/表格视图 (低阶 View)
            ExampleCard {
                title: Fluent.Translator.tr("gallery_ccff6b9a85f87905", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_d8cae3421f371e22", Fluent.Translator._v)
                Row {
                    spacing: Fluent.Enums.spacing.xl
                    ComponentCard {
                        label: "ListView"
                        Fluent.ListView {
                            id: demoFluentListView
                            objectName: "galleryListViewDemo"
                            width: 220; height: 360
                            framed: true
                            showFooter: true
                            Component.onCompleted: {
                                var items = []
                                for (var i = 1; i <= 100; i++) items.push(Fluent.Translator.tr("gallery_b0eac693d60d649a") + i)
                                model = items
                            }
                            delegate: Rectangle {
                                id: _lvDelegate
                                required property int index
                                required property var modelData
                                readonly property bool _selected: demoFluentListView.currentIndex === index

                                objectName: "galleryListViewDelegate-" + index
                                width: ListView.view.width
                                height: Fluent.Enums.controlSize.listItemHeight
                                color: {
                                    if (_selected) {
                                        return _lvMa.containsMouse
                                            ? Fluent.Enums.stateColor.selectedHover
                                            : Fluent.Enums.stateColor.selected
                                    }
                                    return _lvMa.containsMouse
                                        ? Fluent.Enums.stateColor.treeItemHover
                                        : Fluent.Enums.transparent
                                }
                                radius: Fluent.Enums.radius.small
                                Behavior on color {
                                    ColorAnimation { duration: Fluent.Enums.duration.fast }
                                }

                                scale: _lvMa.pressed ? 0.97 : 1.0
                                Behavior on scale {
                                    NumberAnimation {
                                        duration: Fluent.Enums.duration.fast
                                        easing.type: Easing.OutCubic
                                    }
                                }
                                transformOrigin: Item.Center

                                Rectangle {
                                    anchors.left: parent.left
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: Fluent.Enums.border.thick
                                    height: parent.height * Fluent.Enums.listIndicator.normalRatio
                                    radius: Fluent.Enums.radius.micro
                                    color: Fluent.Enums.accentColor
                                    opacity: _lvDelegate._selected ? 1 : 0
                                    scale: _lvDelegate._selected ? 1 : 0
                                    transformOrigin: Item.Center

                                    Behavior on opacity {
                                        NumberAnimation { duration: Fluent.Enums.duration.fast }
                                    }
                                    Behavior on scale {
                                        NumberAnimation {
                                            duration: Fluent.Enums.duration.spring
                                            easing.type: Easing.OutBack
                                        }
                                    }
                                }

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
                                { text: Fluent.Translator.tr("gallery_d44e9b3d3b31d37b", Fluent.Translator._v), width: 0.4 },
                                { text: Fluent.Translator.tr("gallery_6320b4a8722a851f", Fluent.Translator._v), fillWidth: true }
                            ]
                            Component.onCompleted: {
                                var rows = []
                                for (var i = 1; i <= 50; i++) {
                                    rows.push({ id: i, name: Fluent.Translator.tr("gallery_1bef9f8b5e0b21fe") + i, status: i % 2 === 0 ? Fluent.Translator.tr("gallery_f4f0ead1116b5b62", Fluent.Translator._v) : Fluent.Translator.tr("gallery_4e6fd0e28c55860b", Fluent.Translator._v) })
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
                                    color: Fluent.Enums.stateColor.treeItemHover
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
                                    color: Fluent.Enums.examplePageColors.tableDivider
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
                                            color: _tvDelegate.modelData.status === Fluent.Translator.tr("gallery_f4f0ead1116b5b62", Fluent.Translator._v)
                                                   ? Fluent.Enums.examplePageColors.statusEnabledBg
                                                   : Fluent.Enums.examplePageColors.statusDisabledBg
                                            Fluent.Label {
                                                id: _statusLabel
                                                anchors.centerIn: parent
                                                type: Fluent.Enums.label.type_caption
                                                text: _tvDelegate.modelData.status
                                                color: _tvDelegate.modelData.status === Fluent.Translator.tr("gallery_f4f0ead1116b5b62", Fluent.Translator._v)
                                                       ? Fluent.Enums.examplePageColors.statusEnabledText
                                                       : Fluent.Enums.examplePageColors.statusDisabledText
                                                font.pixelSize: Fluent.Enums.typography.captionCompact
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
                                    text: Fluent.Translator.tr("gallery_2687ccdbb1d2288a", Fluent.Translator._v), expanded: true, children: [
                                        { text: Fluent.Translator.tr("gallery_ee332475c5e213a1", Fluent.Translator._v) },
                                        { text: Fluent.Translator.tr("gallery_97b3323f272a34d2", Fluent.Translator._v) },
                                        { text: Fluent.Translator.tr("gallery_93b6bdad23478090", Fluent.Translator._v) }
                                    ]
                                },
                                {
                                    text: Fluent.Translator.tr("gallery_d24c10d37db0feea", Fluent.Translator._v), expanded: false, children: [
                                        { text: Fluent.Translator.tr("gallery_c95dc99afe57b285", Fluent.Translator._v), children: [
                                            { text: "bug-01.png" },
                                            { text: "bug-02.png" }
                                        ]},
                                        { text: Fluent.Translator.tr("gallery_7b50017ae47eca32", Fluent.Translator._v), children: [
                                            { text: Fluent.Translator.tr("gallery_fe4003e1194c58cf", Fluent.Translator._v) }
                                        ]}
                                    ]
                                },
                                {
                                    text: Fluent.Translator.tr("gallery_e6f04ffbaa424001", Fluent.Translator._v), expanded: true, children: [
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
                title: Fluent.Translator.tr("gallery_a626aad412b751f1", Fluent.Translator._v)
                description: "TabBar / TabWidget"
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
                                    {title: Fluent.Translator.tr("gallery_6c273ecc79d229ed", Fluent.Translator._v), icon: "", content: tab1Content},
                                    {title: Fluent.Translator.tr("gallery_8d7f8612a58f664d", Fluent.Translator._v), icon: "", content: tab2Content},
                                    {title: Fluent.Translator.tr("gallery_222b33ef1adb6046", Fluent.Translator._v), icon: "", content: tab3Content}
                                ]
                                onTabClosed: (index) => { removeTab(index); apiStatus.text = Fluent.Translator.tr("gallery_2ef467443bfc1d59") + index }
                                onTabAddClicked: { addTab(Fluent.Translator.tr("gallery_7b545b05f46129d5", Fluent.Translator._v) + (count() + 1), "", tab4Content); apiStatus.text = Fluent.Translator.tr("gallery_d58198f696132ad1", Fluent.Translator._v) }
                                onCurrentChanged: (index) => apiStatus.text = Fluent.Translator.tr("gallery_b63e5b2e2fde167a") + index
                            }
                        }
                        // TabBar 独立标签栏：只渲染标签，页面内容由调用方承载
                        ComponentCard {
                            label: "TabBar"
                            Column {
                                spacing: Fluent.Enums.spacing.m
                                TabBar {
                                    id: standaloneTabBar
                                    width: 320
                                    closable: true
                                    movable: true
                                    showAddButton: true
                                    tabs: [
                                        {title: Fluent.Translator.tr("gallery_6c273ecc79d229ed", Fluent.Translator._v), icon: ""},
                                        {title: Fluent.Translator.tr("gallery_8d7f8612a58f664d", Fluent.Translator._v), icon: ""},
                                        {title: Fluent.Translator.tr("gallery_222b33ef1adb6046", Fluent.Translator._v), icon: ""}
                                    ]
                                    onTabClosed: (index) => { removeTab(index); apiStatus.text = Fluent.Translator.tr("gallery_2ef467443bfc1d59") + index }
                                    onTabAddClicked: { addTab(Fluent.Translator.tr("gallery_7b545b05f46129d5", Fluent.Translator._v) + (count() + 1), ""); apiStatus.text = Fluent.Translator.tr("gallery_d58198f696132ad1", Fluent.Translator._v) }
                                    onCurrentChanged: (index) => apiStatus.text = Fluent.Translator.tr("gallery_b63e5b2e2fde167a") + index
                                    onTabsReordered: (from, to) => {
                                        var reordered = tabs.slice()
                                        reordered.splice(to, 0, reordered.splice(from, 1)[0])
                                        tabs = reordered
                                    }
                                }
                                Rectangle {
                                    width: standaloneTabBar.width
                                    height: 60
                                    radius: Fluent.Enums.radius.small
                                    color: Fluent.Enums.cardColor
                                    border.width: Fluent.Enums.border.thin
                                    border.color: Fluent.Enums.borderColor
                                    Fluent.Label {
                                        anchors.centerIn: parent
                                        type: Fluent.Enums.label.type_caption
                                        text: standaloneTabBar.tabText(standaloneTabBar.currentIndex)
                                        color: Fluent.Enums.textColor.secondary
                                    }
                                }
                            }
                        }
                    }
                    // API演示
                    Row {
                        spacing: Fluent.Enums.spacing.m
                        Button { text: Fluent.Translator.tr("gallery_795cbff909c46891", Fluent.Translator._v); onClicked: { defaultTabWidget.addTab(Fluent.Translator.tr("gallery_de92c86f4334f894", Fluent.Translator._v), "", tab4Content); standaloneTabBar.addTab(Fluent.Translator.tr("gallery_de92c86f4334f894", Fluent.Translator._v), ""); apiStatus.text = Fluent.Translator.tr("gallery_d9823a8fc15af97a", Fluent.Translator._v) } }
                        Button { text: Fluent.Translator.tr("gallery_0c8a8bcb43c7e759", Fluent.Translator._v); onClicked: { defaultTabWidget.removeTab(defaultTabWidget.currentIndex); standaloneTabBar.removeTab(standaloneTabBar.currentIndex); apiStatus.text = Fluent.Translator.tr("gallery_de23e1d3bdb33279", Fluent.Translator._v) } }
                        Button { text: Fluent.Translator.tr("gallery_304bb8616c79fb9c", Fluent.Translator._v); onClicked: { defaultTabWidget.setTabText(defaultTabWidget.currentIndex, Fluent.Translator.tr("gallery_682d211b7142758a", Fluent.Translator._v)); standaloneTabBar.setTabText(standaloneTabBar.currentIndex, Fluent.Translator.tr("gallery_682d211b7142758a", Fluent.Translator._v)); apiStatus.text = Fluent.Translator.tr("gallery_b2fce17b9e453cf0", Fluent.Translator._v) } }
                        Button { text: Fluent.Translator.tr("gallery_1b590914091ca145", Fluent.Translator._v); onClicked: { defaultTabWidget.clear(); standaloneTabBar.clear(); apiStatus.text = Fluent.Translator.tr("gallery_ca775625638ee91c", Fluent.Translator._v) } }
                        Button { text: Fluent.Translator.tr("gallery_cb5d682bac3d1a2d", Fluent.Translator._v); onClicked: { defaultTabWidget.tabs = [{title: Fluent.Translator.tr("gallery_6c273ecc79d229ed", Fluent.Translator._v), icon: "", content: tab1Content}, {title: Fluent.Translator.tr("gallery_8d7f8612a58f664d", Fluent.Translator._v), icon: "", content: tab2Content}, {title: Fluent.Translator.tr("gallery_222b33ef1adb6046", Fluent.Translator._v), icon: "", content: tab3Content}]; standaloneTabBar.tabs = [{title: Fluent.Translator.tr("gallery_6c273ecc79d229ed", Fluent.Translator._v), icon: ""}, {title: Fluent.Translator.tr("gallery_8d7f8612a58f664d", Fluent.Translator._v), icon: ""}, {title: Fluent.Translator.tr("gallery_222b33ef1adb6046", Fluent.Translator._v), icon: ""}]; standaloneTabBar.currentIndex = 0; apiStatus.text = Fluent.Translator.tr("gallery_d2cd2e209c5fe4eb", Fluent.Translator._v) } }
                        Text { id: apiStatus; text: Fluent.Translator.tr("gallery_d79826f94092ff35", Fluent.Translator._v); color: Fluent.Enums.textColor.secondary; font.pixelSize: Fluent.Enums.typography.caption; anchors.verticalCenter: parent.verticalCenter }
                    }
                }
                Component { id: tab1Content; Rectangle { anchors.fill: parent; color: Fluent.Enums.demoPalette.blue; Text { anchors.centerIn: parent; text: Fluent.Translator.tr("gallery_b072d7a8ed7cae83", Fluent.Translator._v); color: Fluent.Enums.accentForeground } } }
                Component { id: tab2Content; Rectangle { anchors.fill: parent; color: Fluent.Enums.demoPalette.green; Text { anchors.centerIn: parent; text: Fluent.Translator.tr("gallery_66e3d2b49b5d3fcf", Fluent.Translator._v); color: Fluent.Enums.accentForeground } } }
                Component { id: tab3Content; Rectangle { anchors.fill: parent; color: Fluent.Enums.demoPalette.orange; Text { anchors.centerIn: parent; text: Fluent.Translator.tr("gallery_eac570e3ce1cf6a3", Fluent.Translator._v); color: Fluent.Enums.accentForeground } } }
                Component { id: tab4Content; Rectangle { anchors.fill: parent; color: Fluent.Enums.demoPalette.purple; Text { anchors.centerIn: parent; text: Fluent.Translator.tr("gallery_473e84592c3040cf", Fluent.Translator._v); color: Fluent.Enums.accentForeground } } }
            }
            
            // 数据展示
            ExampleCard {
                title: Fluent.Translator.tr("gallery_7b0b7388ec0c5902", Fluent.Translator._v)
                description: "Timeline"
                Row {
                    spacing: Fluent.Enums.spacing.xl
                    ComponentCard { 
                        label: "Timeline"
                        Timeline { 
                            width: 320
                            items: [
                                {title: Fluent.Translator.tr("gallery_f28461bb49c85647", Fluent.Translator._v), status: "success", cards: [{text: Fluent.Translator.tr("gallery_30282754460515c2", Fluent.Translator._v), strikeOut: true}]},
                                {title: Fluent.Translator.tr("gallery_8ecc1c9957a6e584", Fluent.Translator._v), status: "info", cards: [{text: Fluent.Translator.tr("gallery_112feed1bcbc4554", Fluent.Translator._v), status: "warning"}, {text: Fluent.Translator.tr("gallery_5a5b05be06f7e7e7", Fluent.Translator._v), status: "warning"}]},
                                {title: Fluent.Translator.tr("gallery_5e415ae2bb8630c1", Fluent.Translator._v), status: "error", cards: [{text: Fluent.Translator.tr("gallery_73cf53321aa44b97", Fluent.Translator._v), status: "error"}]}
                            ]
                        }
                    }
                    ComponentCard {
                        label: Fluent.Translator.tr("gallery_d00765cd31018c82", Fluent.Translator._v)
                        TimelineGitGraphDemo {}
                    }
                }
            }
            
            // Image
            ExampleCard {
                title: Fluent.Translator.tr("gallery_893dd28e165123b9", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_ca0dd5a280400c51", Fluent.Translator._v)
                Row {
                    spacing: Fluent.Enums.spacing.xl
                    ComponentCard {
                        label: "ImageWidget"
                        ImageWidget {
                            id: apiImage
                            width: 320; height: 180
                            source: "qrc:/image/background.jpg"
                            onClicked: imageText.text = Fluent.Translator.tr("gallery_800665bf2c53f968", Fluent.Translator._v)
                        }
                    }
                    Column {
                        spacing: Fluent.Enums.spacing.xs
                        Text { text: Fluent.Translator.tr("gallery_163f19a0af53019c", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.bodySmall; color: Fluent.Enums.textColor.primary }
                        Text { id: imageText; text: Fluent.Translator.tr("gallery_c3cf4e0ecdbbd776", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.caption; color: Fluent.Enums.textColor.secondary }
                    }
                }
            }
            
            // 分页指示器
            ExampleCard {
                title: Fluent.Translator.tr("gallery_0876e77f76f912ed", Fluent.Translator._v)
                description: Fluent.Translator.tr("gallery_f48abd0dc464735c", Fluent.Translator._v)
                Column {
                    spacing: Fluent.Enums.spacing.l
                    Row {
                        spacing: Fluent.Enums.spacing.xl
                        ComponentCard { label: Fluent.Translator.tr("gallery_0cadf1cdc6144b04", Fluent.Translator._v); HorizontalPipsPager { count: 5; currentIndex: 2 } }
                        ComponentCard { label: Fluent.Translator.tr("gallery_1777a1e5f3a54dee", Fluent.Translator._v); VerticalPipsPager { count: 4; currentIndex: 1 } }
                        ComponentCard {
                            label: Fluent.Translator.tr("gallery_50d8fc2f69be51e0", Fluent.Translator._v)
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
