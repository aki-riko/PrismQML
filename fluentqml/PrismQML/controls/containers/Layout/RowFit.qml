// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

// RowFit - Row + 可选自动缩放属性
//
// 普通 Row 用法:
//   RowFit {
//       Label{} ; Image{} ; Label{}
//   }
//   行为同原生 Row。
//
// 启用自动缩放 (子项超出容器时整体缩):
//   RowFit {
//       autoFit: true              // ← 一个属性开启
//       anchors.fill: parent       // 必须有外部尺寸 (anchors.fill / 显式 width)
//       horizontalAlign: RowFit.Center  // 默认 Center
//       Label{}; Image{}; Label{}
//   }
//
// 实现:
//   - 默认 autoFit=false 时,完全等价于原生 Row
//   - autoFit=true 时,把 Row 包进 Item,根据 implicitWidth vs Item.width 动态 scale
//
// 这种写法是纯 QML,因 Row 本身不支持外部测量 width 来决定 scale,
// autoFit 模式必须有外层 Item 提供 width 锚点。
//
import QtQuick

Item {
    id: root

    // ==================== Public Props ====================
    enum Align { Left, Center, Right }

    // 关闭自动缩放时,行为 = 原生 Row (root 透传 implicit 尺寸)
    property bool autoFit: false
    property real minScale: 0.6
    property real padding: 8
    property int horizontalAlign: RowFit.Center
    property alias spacing: row.spacing
    // 让用户直接 RowFit { Label{}; ... } 把子项写在里面
    default property alias content: row.data

    // 不开 autoFit 时, root 的尺寸 = Row 实际尺寸
    implicitWidth: autoFit ? row.implicitWidth + 2 * padding : row.implicitWidth
    implicitHeight: row.implicitHeight

    Row {
        id: row
        spacing: 6

        // 不 autoFit: 直接靠左排,不管尺寸 (= 原生 Row 行为)
        // autoFit: 跟 horizontalAlign 切锚点
        anchors.verticalCenter: root.autoFit ? parent.verticalCenter : undefined

        anchors.horizontalCenter:
            root.autoFit && root.horizontalAlign === RowFit.Center
            ? parent.horizontalCenter : undefined
        anchors.left:
            root.autoFit && root.horizontalAlign === RowFit.Left
            ? parent.left : undefined
        anchors.leftMargin:
            root.autoFit && root.horizontalAlign === RowFit.Left ? root.padding : 0
        anchors.right:
            root.autoFit && root.horizontalAlign === RowFit.Right
            ? parent.right : undefined
        anchors.rightMargin:
            root.autoFit && root.horizontalAlign === RowFit.Right ? root.padding : 0

        // autoFit 时按比例缩
        scale: {
            if (!root.autoFit) return 1.0
            if (root.width <= 0 || implicitWidth <= 0) return 1.0
            var avail = root.width - 2 * root.padding
            if (implicitWidth <= avail) return 1.0
            return Math.max(avail / implicitWidth, root.minScale)
        }
        transformOrigin: {
            if (!root.autoFit) return Item.TopLeft
            switch (root.horizontalAlign) {
            case RowFit.Left:   return Item.Left
            case RowFit.Right:  return Item.Right
            default:               return Item.Center
            }
        }
    }
}
