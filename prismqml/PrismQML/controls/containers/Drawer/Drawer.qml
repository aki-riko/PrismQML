// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

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
    property int mode: Enums.drawer.mode_inside  // Inside/outside placement 内侧/外侧放置模式
    property int position: Enums.position.right
    property int drawerWidth: 320
    property int drawerHeight: 400
    property bool modal: true  // Inside mode scrim only 仅控制内侧模式遮罩
    /// 抽屉滑入/滑出动画时长 (毫秒)。默认与全局慢速一致;
    /// 紧凑场景可调小,例如 200。
    property int animationDuration: Enums.duration.slow
    default property alias content: contentItem.data
    readonly property bool isHorizontal: position === Enums.position.left || position === Enums.position.right
    
    // Qt-style state alias Qt风格状态别名
    property alias opened: control._isOpen

    // Panel corner radius 面板圆角
    property int radius: Enums.isPrismDesign ? Enums.prismDesign.radiusPopup : Enums.radius.none

    // ==================== Internal Props 内部属性 ====================
    property bool _outsideResetting: false

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _isOutside: mode === Enums.drawer.mode_outside
    readonly property var _hostWindow: control.Window.window
    readonly property int _outsideShadowExtent: Enums.shadow.level28.blur + Enums.shadow.level28.offset
    readonly property color _drawerBackground: Enums.isPrismDesign ? Enums.dialogColor : Enums.cardColor
    readonly property int _drawerBorderWidth: Enums.isNeobrutalism ? Enums.neo.borderWidth : (Enums.isPrismDesign ? Enums.prismDesign.borderWidth : 0)
    readonly property color _drawerBorderColor: Enums.isNeobrutalism ? Enums.stateColor.border : (Enums.isPrismDesign ? Enums.borderColor : Enums.transparent)

    // ==================== Public Methods 公开方法 ====================
    // Override open to use base class mechanism 重写open使用基类机制
    function open() {
        // Save original parent 保存原始父组件
        if (!_originalParent) {
            _originalParent = control.parent
        }

        // Auto-find window contentItem if not already there 自动找到窗口 contentItem（如果还不在那里）
        if (!control._isOutside && control.Window && control.Window.window) {
            var windowContent = control.Window.window.contentItem
            if (windowContent && control.parent !== windowContent) {
                control.parent = windowContent
            }
        }

        outsideVisibilityTimer.stop()
        _isClosing = false
        _isOpen = true
    }

    function toggle() { _isOpen ? close() : open() }

    // Check if open 检查是否打开
    function isOpen() {
        return _isOpen
    }

    // Reset both render paths when switching mode or closing the host window
    // 切换模式或宿主窗口关闭时重置两条渲染路径
    function _resetDrawerState() {
        _outsideResetting = true
        outsideVisibilityTimer.stop()
        _isOpen = false
        _isClosing = false
        _outsideResetting = false
    }

    // Overlay overrides 覆盖层配置
    dismissOnScrimClick: modal  // Close when scrim is clicked in modal mode 模态时点击遮罩关闭
    maskColor: !_isOutside && modal ? Enums.stateColor.dialogOverlay : Enums.transparent
    visible: !_isOutside && (_isOpen || _isClosing)

    onModeChanged: _resetDrawerState()
    onOpenedChanged: {
        if (!control._isOutside || control._outsideResetting) return
        if (control._isOpen) {
            outsideVisibilityTimer.stop()
        } else if (control._isClosing || outsideDrawerWindow.visible) {
            outsideVisibilityTimer.restart()
        }
    }

    // ==================== Content 内容 ====================
    // Native host for the outside mode 外侧模式的原生承载窗口
    Window {
        id: outsideDrawerWindow
        readonly property bool horizontal: control.isHorizontal

        objectName: "outsideDrawerWindow"
        x: {
            if (!control._hostWindow) return 0
            if (control.position === Enums.position.left) {
                return control._hostWindow.x - control.drawerWidth - control._outsideShadowExtent
            }
            if (control.position === Enums.position.right) {
                return control._hostWindow.x + control._hostWindow.width
            }
            return control._hostWindow.x - control._outsideShadowExtent
        }
        y: {
            if (!control._hostWindow) return 0
            if (control.position === Enums.position.top) {
                return control._hostWindow.y - control.drawerHeight - control._outsideShadowExtent
            }
            if (control.position === Enums.position.bottom) {
                return control._hostWindow.y + control._hostWindow.height
            }
            return control._hostWindow.y - control._outsideShadowExtent
        }
        width: horizontal
            ? control.drawerWidth + control._outsideShadowExtent
            : (control._hostWindow
                ? control._hostWindow.width + control._outsideShadowExtent * 2
                : 0)
        height: horizontal
            ? (control._hostWindow
                ? control._hostWindow.height + control._outsideShadowExtent * 2
                : 0)
            : control.drawerHeight + control._outsideShadowExtent
        visible: control._isOutside
            && (control._isOpen || control._isClosing || outsideVisibilityTimer.running)
            && control._hostWindow !== null
        flags: Qt.Tool | Qt.FramelessWindowHint | Qt.NoFluentShadowWindowHint
        color: Enums.transparent
        transientParent: control._hostWindow

        onVisibleChanged: {
            if (visible && control._isOpen) {
                outsideDrawerWindow.requestActivate()
            }
        }
        onClosing: (close) => control._resetDrawerState()

        RectangularShadow {
            anchors.fill: outsideDrawerPanel
            radius: control.radius
            color: Enums.shadow.level28.color
            blur: Enums.shadow.level28.blur
            offset.x: 0
            offset.y: Enums.shadow.level28.offset
        }

        Rectangle {
            id: outsideDrawerPanel
            objectName: "outsideDrawerPanel"

            width: control.isHorizontal
                ? control.drawerWidth
                : (control._hostWindow ? control._hostWindow.width : 0)
            height: control.isHorizontal
                ? (control._hostWindow ? control._hostWindow.height : 0)
                : control.drawerHeight
            color: control._drawerBackground
            radius: control.radius
            border.width: control._drawerBorderWidth
            border.color: control._drawerBorderColor

            MouseArea {
                anchors.fill: parent
            }

            states: [
                State {
                    name: "open"
                    when: control._isOpen
                    PropertyChanges {
                        target: outsideDrawerPanel
                        x: control.position === Enums.position.right
                            ? 0
                            : control._outsideShadowExtent
                        y: control.position === Enums.position.bottom
                            ? 0
                            : control._outsideShadowExtent
                    }
                },
                State {
                    name: "closed"
                    when: !control._isOpen
                    PropertyChanges {
                        target: outsideDrawerPanel
                        x: control.position === Enums.position.left
                            ? outsideDrawerWindow.width
                            : (control.position === Enums.position.right
                                ? -outsideDrawerPanel.width
                                : control._outsideShadowExtent)
                        y: control.position === Enums.position.top
                            ? outsideDrawerWindow.height
                            : (control.position === Enums.position.bottom
                                ? -outsideDrawerPanel.height
                                : control._outsideShadowExtent)
                    }
                }
            ]

            transitions: Transition {
                NumberAnimation {
                    properties: "x,y"
                    duration: control.animationDuration
                    easing.type: Easing.OutCubic
                }
            }
        }
    }

    // Drawer shadow 抽屉阴影
    // Shadow for drawer 抽屉阴影
    RectangularShadow {
        anchors.fill: drawer
        radius: control.radius
        color: Enums.shadow.level28.color
        blur: Enums.shadow.level28.blur
        offset.x: 0
        offset.y: Enums.shadow.level28.offset
        visible: control._isOpen || control._isClosing
    }
    
    // Drawer panel 抽屉面板
    Rectangle {
        id: drawer

        readonly property real effectiveWidth: control.width > 0 ? control.width : (control.parent ? control.parent.width : 0)
        readonly property real effectiveHeight: control.height > 0 ? control.height : (control.parent ? control.parent.height : 0)

        color: control._drawerBackground
        radius: control.radius
        // Drawer boundary for non-Fluent skins 非 Fluent 皮肤抽屉边界
        border.width: control._drawerBorderWidth
        border.color: control._drawerBorderColor
        
        // Use parent size directly when control size is 0 (Python setParentItem timing issue) 当 control 尺寸为 0 时直接使用 parent 尺寸（Python setParentItem 时序问题）

        width: isHorizontal ? control.drawerWidth : effectiveWidth
        height: isHorizontal ? effectiveHeight : control.drawerHeight

        // Block clicks from reaching the overlay mask 阻止点击穿透到遮罩层
        MouseArea {
            anchors.fill: parent
            // Consume all clicks so they don't propagate to the mask 消费点击防止穿透
        }
        
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
    }

    // Shared content host moves between inside and outside panels
    // 共享内容宿主在内侧与外侧面板间移动
    Item {
        id: contentItem
        objectName: "contentItem"  // For Python findChild 供Python查找

        parent: control._isOutside ? outsideDrawerPanel : drawer
        anchors.fill: parent
        anchors.margins: Enums.spacing.xl

        // Clear input focus when clicking empty content area 点击内容空白处清除输入焦点
        MouseArea {
            anchors.fill: parent
            z: Enums.zIndex.background
            onClicked: contentItem.forceActiveFocus()
        }
    }

    Timer {
        id: outsideVisibilityTimer
        interval: control.animationDuration
        repeat: false
    }

    Connections {
        function onClosing(close) { control._resetDrawerState() }
        function onVisibleChanged() {
            if (control._isOutside && control._hostWindow
                    && !control._hostWindow.visible) {
                control._resetDrawerState()
            }
        }

        target: control._hostWindow
        ignoreUnknownSignals: true
    }
}
