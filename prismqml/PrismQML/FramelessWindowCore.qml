// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Window
import "./_internal"
import "./controls/utils"

// FramelessWindowCore - Lightweight frameless window 轻量无边框窗口基类
// Startup-oriented sibling of WindowsCore. 面向启动期的 WindowsCore 同级基类。
//
// 为什么需要它 why this exists:
//   WindowsCore 是给主窗口用的重型基类, 它把整套应用窗口镶边都拖进来:
//   WindowsCoreFrame(标题栏 + 窗口图标 + 系统按钮 + resize 手柄)、RTL 镜像、
//   关闭收拢动画(PageTransition + FrameWaiter)、QML 阴影宿主、DWM 原生阴影
//   助手、启动动画助手。实测一个空壳 WindowsCore 就创建 104 个 QObject,
//   而登录窗这种 "一块面板 + 几个输入框" 的窗口并不需要其中任何一项。
//   本类只保留无边框窗口的最小职责: 圆角面板 + 拖动 + 缩放 + 关闭语义,
//   不引入标题栏体系(它要求调用方再摆一排系统按钮), 不引入动画助手,
//   不引入阴影宿主。
//
// 适用场景 / when to use:
//   登录窗、协议确认窗、向导首屏等**启动期轻量窗口**。
//   需要标题栏/导航栏/系统按钮的常规应用窗口请继续用 WindowsCore。
//
// 与 WindowsCore 的兼容面 / compatibility surface:
//   同名属性 closeRequestAccepted / closeRequestHideOnly
//   同名信号 closeRequested / nativeCloseAccepted,
//   宿主可以按同一套关闭语义迁移, 不必重写生命周期代码。
//
// 已知边界 / known limits:
//   * 没有标题栏: 窗口拖动靠 contentArea 里"没有被交互控件覆盖"的区域,
//     需要拖动时自己放 WindowDragHandle 或依赖本类默认的 surface 拖动层。
//   * 没有原生阴影: 需要阴影请自己 getShadowManager().enableShadow(winId)。
//   * 没有显示动画: 首帧直接可见, 适合"要立刻看到界面"的启动期窗口。
Window {
    id: root

    // ==================== Public Props 公开属性 ====================
    default property alias content: contentArea.data
    property bool closeRequestAccepted: true
    // Hide-only close: an accepted close hides the window instead of destroying it.
    // 隐藏式关闭: 被接受的关闭请求隐藏窗口而非销毁。
    property bool closeRequestHideOnly: false
    // Allow dragging the window by its empty surface area. 允许拖动窗口空白区域。
    property bool draggable: true
    // Create resize handles on all eight edges. 在四边四角创建缩放手柄。
    property bool resizable: true
    // Panel corner radius; 0 keeps a square window. 面板圆角, 0 为直角。
    property int windowRadius: Enums.surfaceRadius(Enums.radius.large)
    property color windowColor: Enums.backgroundColor
    property color borderColor: Enums.stateColor.border
    property int borderWidth: Enums.surfaceBorderWidth(Enums.border.thin)

    // ---- WindowsCore 迁移兼容位 migration shims ----
    // 这些属性在本类里**不产生任何视觉效果**, 只是为了让从 WindowsCore 迁过来的
    // 窗口源码可以原样保留写法而不报 "Cannot assign to non-existent property"。
    // 它们不是本类的功能, 不要在这里实现阴影/标题栏/动画。
    // These carry no visual effect here. They exist only so source migrated from
    // WindowsCore keeps parsing; do not implement shadow/titlebar/animation.
    property var shadowMode: Enums.windowShadow.mode_none
    property int titleBarHeight: 0
    property string windowTitle: ""
    property int titleBarPosition: Enums.windowType.title_bar_top
    property string windowIcon: ""
    property int shadowSize: 0
    property bool startupProfilingVerbose: false

    // ==================== Internal Props 内部属性 ====================
    property bool _closeInProgress: false
    property bool _closeHideOnlyLatched: false

    // ==================== Readonly State 只读状态 ====================
    readonly property bool isMaximized: root.visibility === Window.Maximized

    // ==================== Signals 信号 ====================
    // Fired before a user/system close request is accepted. Handlers may set
    // closeRequestAccepted to false to keep the window alive.
    // 用户/系统关闭请求被接受前触发; 置 closeRequestAccepted=false 可保持窗口存活。
    signal closeRequested()
    // Fired after an accepted close has been latched, before the window goes away.
    // 已接受的关闭定案后、窗口消失前触发。
    signal nativeCloseAccepted()

    // ==================== Public Methods 公开方法 ====================
    function requestClose() {
        if (_closeInProgress) return
        closeRequestAccepted = true
        closeRequestHideOnly = false
        // requestClose() is the programmatic入口; it must run the same pre-close
        // veto as a native close so hosts see closeRequested exactly once.
        // requestClose() 是程序化入口, 必须与原生关闭走同一套否决流程,
        // 保证宿主拿到的 closeRequested 恰好一次。
        closeRequested()
        _finishAcceptedClose()
    }

    // ==================== Internal Methods 内部方法 ====================
    function _finishAcceptedClose() {
        if (!closeRequestAccepted) {
            _closeInProgress = false
            return
        }
        _closeInProgress = true
        _closeHideOnlyLatched = closeRequestHideOnly
        nativeCloseAccepted()
        // Hide-only keeps the object alive for a later show(); a real close
        // finishes through close(), whose accepted delivery is the last step a
        // QML-owned window can take on its own. destroy() is NOT used here:
        // a component instance is not destructible from its own code.
        // 隐藏式关闭保留对象以便再次 show(); 真正关闭走 close(), 它的已接受
        // 关闭投递就是 QML 自有窗口能自己做的最后一步。这里不用 destroy():
        // 组件实例不能从自身代码里销毁自己。
        if (_closeHideOnlyLatched) {
            root.visible = false
            _closeInProgress = false
            return
        }
        root.close()
    }

    // ==================== Size 尺寸 ====================
    width: Enums.window.defaultWidth
    height: Enums.window.defaultHeight
    minimumWidth: Enums.window.minimumWidth
    minimumHeight: Enums.window.minimumHeight
    visible: true
    // The rounded panel paints itself; the native window surface stays clear.
    // 圆角面板由内容区自绘, 原生窗口表面保持透明。
    color: Enums.transparent
    flags: Qt.Window | Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint

    onClosing: (close) => {
        if (_closeInProgress) {
            close.accepted = true
            return
        }
        closeRequestAccepted = true
        closeRequestHideOnly = false
        closeRequested()
        if (!closeRequestAccepted) {
            close.accepted = false
            return
        }
        // Leave the native close delivery before running the accepted close.
        // 先退出本次原生关闭分发, 再执行已接受的关闭。
        close.accepted = false
        _finishAcceptedClose()
    }

    // ==================== Content 内容 ====================
    Rectangle {
        id: surface

        anchors.fill: parent
        radius: root.windowRadius
        color: root.windowColor
        border.width: root.borderWidth
        border.color: root.borderColor
        antialiasing: true

        // Drag layer sits directly on the panel, below user content. User content
        // added through the default property is parented here, so anything with
        // its own MouseArea naturally receives the click first.
        // 拖动层贴在面板上、位于用户内容之下; 自带 MouseArea 的控件会先拿到点击。
        WindowDragHandle {
            anchors.fill: parent
            enableDrag: root.draggable && !root.isMaximized
        }

        Item {
            id: contentArea

            anchors.fill: parent
            anchors.margins: root.borderWidth
        }
    }

    // Resize handles are absent entirely when the window is not resizable.
    // 不可调整大小时完全不创建缩放手柄。
    Loader {
        id: resizeHandlesLoader

        anchors.fill: parent
        active: root.resizable
        sourceComponent: resizeHandlesComponent
    }

    Component {
        id: resizeHandlesComponent

        Item {
            anchors.fill: parent

            ResizeArea { targetWindow: root; edge: Qt.LeftEdge }
            ResizeArea { targetWindow: root; edge: Qt.RightEdge }
            ResizeArea { targetWindow: root; edge: Qt.TopEdge }
            ResizeArea { targetWindow: root; edge: Qt.BottomEdge }
            ResizeArea { targetWindow: root; edge: Qt.LeftEdge | Qt.TopEdge }
            ResizeArea { targetWindow: root; edge: Qt.RightEdge | Qt.TopEdge }
            ResizeArea { targetWindow: root; edge: Qt.LeftEdge | Qt.BottomEdge }
            ResizeArea { targetWindow: root; edge: Qt.RightEdge | Qt.BottomEdge }
        }
    }
}
