// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."

// ListView - 通用 ListView (QListView 等价物) 低阶 View 级组件
// 继承 DataWidgetCore,轻量模式(无阴影/无margin)
//
// Usage 用法:
//   Fluent.ListView {
//       model: myAbstractListModel
//       delegate: Rectangle { ... }
//   }
//
// 与 ListWidget (高阶) 区别 vs ListWidget:
//   ListView = QListView 等价物,只渲染,适合 QAbstractListModel 等自带 model 的场景
//   ListWidget     = QListWidget 等价物,自带 model + addItem/insertItem 等便利 API
DataWidgetCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    property bool framed: true
    property alias model: control.listModel
    property alias delegate: control.contentDelegate
    // spacing 由父类 DataWidgetCore 暴露(本地id alias合法),此处勿重复三级alias control.listView.spacing(非法)
    // count 指向基类自维护的 itemCount(可靠跟踪延迟注入的 model); 不写
    // control.listView.count —— 那是对 ListView.count 的绑定, 延迟 model 下不更新。
    readonly property int count: itemCount
    property int currentIndex: -1

    onCurrentIndexChanged: {
        if (control.listView && control.listView.currentIndex !== currentIndex)
            control.listView.currentIndex = currentIndex
    }
    Binding {
        target: control
        property: "currentIndex"
        value: control.listView.currentIndex
        when: control.listView
    }

    // ==================== Lightweight mode 轻量模式 ====================
    showShadow: false
    cardMargin: 0
    borderVisible: framed
    // showFooter 不在此硬编码: 基类默认 false (轻量模式), 但保留给用户/demo 覆盖
    showHeader: false
    // itemCount 由基类 DataWidgetCore 自维护(Connections 跟踪 model 信号), 此处不再赋值

    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.controlSize.listDefaultWidth
    implicitHeight: Enums.controlSize.listDefaultHeight
}
