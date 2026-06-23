// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import QtQuick.Effects
import "../../.."
import "../../../effects"
import "../../dialogs"

// Drawer - Drawer component 抽屉组件
// Inherits OverlayDialogCore for overlay functionality 继承OverlayDialogCore获得覆盖功能
// Place as Window direct child, auto cover entire window 放在Window子级自动覆盖窗口
OverlayDialogCore {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property int position: Enums.position.right
    property int drawerWidth: 320
    property int drawerHeight: 400
    property bool modal: true
    /// 抽屉滑入/滑出动画时长 (毫秒)。默认与全局慢速一致;
    /// 紧凑场景可调小,例如 200。
    property int animationDuration: Enums.duration.slow
    default property alias content: contentItem.data
    readonly property bool isHorizontal: position === Enums.position.left || position === Enums.position.right
    
    // Qt-style state alias Qt风格状态别名
    property alias opened: control._isOpen

    // Panel corner radius 面板圆角
    property int radius: Enums.radius.none

    // ==================== Public Methods 公开方法 ====================
    // Override open to use base class mechanism 重写open使用基类机制
    function open() {
        // Save original parent 保存原始父组件
        if (!_originalParent) {
            _originalParent = control.parent
        }

        // Auto-find window contentItem if not already there 自动找到窗口 contentItem（如果还不在那里）

        if (control.Window && control.Window.window) {
            var windowContent = control.Window.window.contentItem
            if (windowContent && control.parent !== windowContent) {
                control.parent = windowContent
            }
        }

        _isOpen = true
    }

    function toggle() { _isOpen ? close() : open() }

    // Check if open 检查是否打开
    function isOpen() {
        return _isOpen
    }

    // ==================== Override Props 覆盖属性 ====================
    dismissOnScrimClick: modal  // Close when scrim is clicked in modal mode 模态时点击遮罩关闭
    maskColor: modal ? Enums.stateColor.dialogOverlay : Enums.transparent

    // ==================== Shadow 阴影 ====================
    // Shadow for drawer 抽屉阴影
    RectangularShadow {
        anchors.fill: drawer
        radius: Enums.radius.none
        color: Enums.shadow.level28.color
        blur: Enums.shadow.level28.blur
        offset: Qt.vector2d(0, Enums.shadow.level28.offset)
        visible: control._isOpen || control._isClosing
    }
    
    // Drawer panel 抽屉面板
    Rectangle {
        id: drawer
        color: Enums.cardColor
        radius: control.radius
        // neo: 抽屉面板加黑边(与内容区分隔)
        border.width: Enums.isNeobrutalism ? Enums.neo.borderWidth : 0
        border.color: Enums.isNeobrutalism ? Enums.stateColor.border : Enums.transparent
        
        // Use parent size directly when control size is 0 (Python setParentItem timing issue) 当 control 尺寸为 0 时直接使用 parent 尺寸（Python setParentItem 时序问题）

        readonly property real effectiveWidth: control.width > 0 ? control.width : (control.parent ? control.parent.width : 0)
        readonly property real effectiveHeight: control.height > 0 ? control.height : (control.parent ? control.parent.height : 0)
        
        width: isHorizontal ? control.drawerWidth : effectiveWidth
        height: isHorizontal ? effectiveHeight : control.drawerHeight
        
        // Use states to manage position 使用states管理位置
        states: [
            State {
                name: "open"
                when: control._isOpen
                PropertyChanges {
                    target: drawer
                    x: position === Enums.position.left ? 0 : 
                       (position === Enums.position.right ? drawer.effectiveWidth - drawer.width : 0)
                    y: position === Enums.position.top ? 0 :
                       (position === Enums.position.bottom ? drawer.effectiveHeight - drawer.height : 0)
                }
            },
            State {
                name: "closed"
                when: !control._isOpen
                PropertyChanges {
                    target: drawer
                    x: position === Enums.position.left ? -drawer.width :
                       (position === Enums.position.right ? drawer.effectiveWidth : 0)
                    y: position === Enums.position.top ? -drawer.height :
                       (position === Enums.position.bottom ? drawer.effectiveHeight : 0)
                }
            }
        ]
        
        transitions: Transition {
            NumberAnimation { properties: "x,y"; duration: control.animationDuration; easing.type: Easing.OutCubic }
        }
        
        // Block clicks from reaching the overlay mask 阻止点击穿透到遮罩层
        MouseArea {
            anchors.fill: parent
            // Consume all clicks so they don't propagate to the mask 消费点击防止穿透
        }
        
        // Content container 内容容器
        Item {
            id: contentItem
            objectName: "contentItem"  // For Python findChild 供Python查找
            anchors.fill: parent
            anchors.margins: Enums.spacing.xl

            // 点击内容区域空白处清除输入焦点
            MouseArea {
                anchors.fill: parent
                z: Enums.zIndex.background
                onClicked: contentItem.forceActiveFocus()
            }
        }
    }
}
