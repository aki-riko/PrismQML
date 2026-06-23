// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import ".."
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// ResizeArea - Window resize handle 窗口调整大小手柄
// Extracted from WindowsCore for modularity 从WindowsCore提取以模块化
MouseArea {
    id: resizeArea
    
    // ==================== Required Props 必需属性 ====================
    required property var targetWindow  // Parent window 父窗口
    required property int edge          // Qt.LeftEdge, Qt.RightEdge, Qt.TopEdge, Qt.BottomEdge or combinations
    
    // ==================== Computed Props 计算属性 ====================
    readonly property bool isL: edge & Qt.LeftEdge
    readonly property bool isR: edge & Qt.RightEdge
    readonly property bool isT: edge & Qt.TopEdge
    readonly property bool isB: edge & Qt.BottomEdge
    readonly property bool isCorner: (isL || isR) && (isT || isB)
    
    visible: targetWindow.visibility !== Window.Maximized
    
    width: isCorner ? Enums.window.resizeCorner : (isL || isR ? Enums.window.resizeEdge : parent.width)
    height: isCorner ? Enums.window.resizeCorner : (isT || isB ? Enums.window.resizeEdge : parent.height)
    
    anchors.left: isL ? parent.left : undefined
    anchors.right: isR ? parent.right : undefined
    anchors.top: isT ? parent.top : undefined
    anchors.bottom: isB ? parent.bottom : undefined
    anchors.horizontalCenter: !isL && !isR ? parent.horizontalCenter : undefined
    anchors.verticalCenter: !isT && !isB ? parent.verticalCenter : undefined
    
    cursorShape: {
        if (isCorner) return (isL && isT) || (isR && isB) ? Qt.SizeFDiagCursor : Qt.SizeBDiagCursor
        return (isL || isR) ? Qt.SizeHorCursor : Qt.SizeVerCursor
    }
    
    // Use native system resize for smooth operation 使用原生系统resize实现平滑
    onPressed: (mouse) => {
        targetWindow.startSystemResize(edge)
    }
}
