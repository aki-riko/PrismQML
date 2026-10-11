// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "_internal" as LayoutInternal

// RelativePanel - Relation based layout 关系式相对布局
// Children are positioned by declarative relations instead of a grid:
// 子项通过声明式关系定位，而不是网格：
//   relations: [
//       { item: header, alignLeftWithPanel: true, alignTopWithPanel: true },
//       { item: body, below: header, alignLeftWith: header },
//       { item: actions, rightOf: body, alignTopWith: body }
//   ]
// Supported keys 支持的关系键: leftOf / rightOf / above / below,
// alignLeftWith / alignTopWith / alignRightWith / alignBottomWith,
// alignHorizontalCenterWith / alignVerticalCenterWith,
// alignLeftWithPanel / alignTopWithPanel / alignRightWithPanel /
// alignBottomWithPanel / alignHorizontalCenterWithPanel /
// alignVerticalCenterWithPanel.
// A child without relations keeps its natural position 未声明关系的子项保持自然位置。
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    // Relation rules 关系规则
    property var relations: []

    // Content 内容
    default property alias content: contentHolder.content

    // ==================== Readonly State 只读状态 ====================
    readonly property int itemCount: relativePanelContent.itemCount
    readonly property int unresolvedCount: relativePanelContent.unresolvedCount

    // ==================== Signals 信号 ====================
    signal layoutUpdated()

    // ==================== Public Methods 公开方法 ====================
    // count - Get the positioned child count 获取参与布局的子项数量
    function count() {
        return itemCount
    }

    // itemAt - Get the positioned child at index 获取指定索引的子项
    function itemAt(index) {
        return relativePanelContent.itemAt(index)
    }

    // indexOf - Get the index of a positioned child 获取子项索引
    function indexOf(item) {
        return relativePanelContent.indexOf(item)
    }

    // relayout - Force a relation pass 立即重新求解关系布局
    function relayout() {
        relativePanelContent.relayout()
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: Enums.flow.layout_implicit_width
    implicitHeight: Enums.flow.layout_implicit_height

    // ==================== Content 内容 ====================
    // Content holder keeps the entry free of the visual tree 内容持有者让入口不承载视觉树
    QtObject {
        id: contentHolder
        default property list<QtObject> content
    }

    LayoutInternal.RelativePanelContent {
        id: relativePanelContent
        objectName: "relativePanelSurface"
        anchors.fill: parent
        host: control
        content: contentHolder.content
        relations: control.relations
        onLayoutUpdated: control.layoutUpdated()
    }
}
