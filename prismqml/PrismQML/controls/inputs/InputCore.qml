// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "../../effects"
import QtQuick.Effects
import "../containers"

// InputCore - Input control base class 输入控件基类
// LineEditCore/SpinBoxCore/TextEditCore etc. extend this 这些控件继承此基类
// Provides: theme, focus line, background, clip, shadow 提供主题/聚焦底线/背景/圆角裁剪/阴影
// Note: Click outside to blur is handled by container MouseArea 点击空白失焦由容器背景MouseArea处理
Widget {
    id: control

    // ==================== Public Props 公开属性 ====================
    // 焦点代理属性，子类覆盖指向内部能实际接受输入的组件
    property Item focusTarget: null
    // FocusScope 语义: 容器本身不持有焦点(不设 activeFocusOnTab 自聚焦), 焦点直接
    // 落在 focusTarget 上, 消除"容器接焦点再 onActiveFocusChanged 转发"的竞态
    // (旧设计在边缘点击时容器/child 焦点反复横跳导致进焦→立刻失焦)。
    // Tab 键导航由 focusTarget 自身的 activeFocusOnTab 承担。

    property bool showFocusedBorder: true
    property color focusedBorderColorLight: Enums.accentColor
    property color focusedBorderColorDark: Enums.accentColor
    property bool focused: false  // Bind to input's activeFocus 绑定到activeFocus
    property bool hovered: false  // Bind to HoverHandler's hovered 绑定到hovered
    property int radius: Enums.isNeobrutalism ? Enums.neo.radius
                         : (Enums.isPrismDesign ? Enums.prismDesign.radiusControl : Enums.radius.small)
    property bool transparentBackground: false
    property bool folderDropEnabled: false  // Enable one-folder drop 启用单文件夹拖放

    // Use unified control colors 使用统一的控件颜色
    // Note: transparentBackground takes highest priority 透明背景优先级最高
    property color color: {
        if (transparentBackground) return Enums.transparent
        // 颜色由 token 层在 neo 下自动返回白面/muted, 无需控件分支。
        if (!enabled) return Enums.stateColor.controlBgDisabled
        if (focused) return Enums.cardColor  // InputgHover
        return Enums.stateColor.controlBg
    }

    property alias border: _bg.border
    property int cursorShape: Qt.IBeamCursor  // Subclass can override 子类可覆盖

    // ==================== Internal Props 内部属性 ====================
    property Item _folderDropTarget: null
    property bool _folderDropWritable: true

    // ==================== Readonly State 只读状态 ====================
    readonly property color focusedBorderColor: Enums.isDark ? focusedBorderColorDark : focusedBorderColorLight

    // Unified padding for all input controls 所有输入控件统一边距
    readonly property int paddingLeft: Enums.spacing.l      // 12
    readonly property int paddingRight: Enums.spacing.m     // 8
    readonly property int paddingTop: Enums.spacing.s       // 6
    readonly property int paddingBottom: Enums.spacing.s    // 6

    // Unified text properties for TextInput/TextEdit 统一文本属性
    readonly property int fontSize: Enums.typography.body
    readonly property color selectionColor: Enums.accentColor
    readonly property color selectedTextColor: Enums.accentForeground
    
    // Input text color (enabled/disabled aware) 输入文本颜色(感知启用状态)
    readonly property color inputTextColor: !enabled ? Enums.textColor.disabled 
        : Enums.textColor.primary

    // Unified colors for clear/action/spin buttons 清除/操作/加减按钮统一颜色
    readonly property color innerButtonHover: Enums.stateColor.controlBgHover
    readonly property color innerButtonPressed: Enums.stateColor.controlBgPressed

    // ==================== Signals 信号 ====================
    signal folderDropped(string path)

    // ==================== Internal Methods 内部方法 ====================
    function _acceptsFolderDrag(dragEvent) {
        return dragEvent && dragEvent.hasUrls && dragEvent.urls.length === 1
            && (dragEvent.supportedActions & Qt.CopyAction) !== 0
    }

    function _resolveDroppedFolder(dragEvent) {
        if (!_acceptsFolderDrag(dragEvent)) return ""
        if (typeof WindowHelper === "undefined"
                || typeof WindowHelper.resolveDroppedFolderPath !== "function") return ""
        return WindowHelper.resolveDroppedFolderPath(dragEvent.urls[0])
    }

    function _applyDroppedFolder(folderPath) {
        if (_folderDropTarget) _folderDropTarget.text = folderPath
        folderDropped(folderPath)
    }

    // ==================== Size 尺寸 ====================
    // Content size (inherited from Widget) 内容尺寸（继承自Widget）
    contentWidth: Enums.controlSize.inputDefaultWidth
    contentHeight: Enums.controlSize.inputHeight

    // ==================== Content 内容 ====================
    // Shadow layer 阴影层
    // Fluent: 模糊阴影。Neobrutalism: 硬阴影。Prism Design: 纯边界层级。
    RectangularShadow {
        anchors.fill: _bg
        radius: _bg.radius
        color: Enums.shadow.level2.color
        blur: Enums.shadow.level2.blur
        offset.x: 0
        offset.y: Enums.shadow.level2.offset
        visible: !control.transparentBackground && !Enums.isNeobrutalism && !Enums.isPrismDesign
    }

    // Neobrutalism 硬阴影: 复用 NeoShadow 组件; 聚焦时 accent=true 转橙主色强调。
    NeoShadow {
        target: _bg
        visible: Enums.isNeobrutalism && !control.transparentBackground
        accent: control.focused
        z: _bg.z - 1
    }

    // Background rectangle 背景矩形
    Rectangle {
        id: _bg
        anchors.fill: parent
        radius: control.radius
        color: control.color
        
        // Rounded clip 圆角裁剪
        clip: true
        layer.enabled: radius > 0 && !control.transparentBackground
        layer.effect: OpacityMask {
            mask: Rectangle {
                width: _bg.width
                height: _bg.height
                radius: _bg.radius
            }
        }
        
        // Border 边框
        // Use unified border colors 使用统一边框颜色
        border.width: control.transparentBackground ? 0
            : (Enums.isNeobrutalism ? Enums.neo.borderWidth
               : (Enums.isPrismDesign && control.focused && control.showFocusedBorder ? Enums.prismDesign.focusBorderWidth
                  : (Enums.isPrismDesign ? Enums.prismDesign.borderWidth : Enums.border.thin)))
        border.color: {
            if (control.transparentBackground) return Enums.transparent
            // neo 聚焦转橙(token 不含此交互, 属结构差异); 其余黑边由 token 自动返回
            if (Enums.isNeobrutalism && control.enabled && control.focused) return Enums.neo.primary
            if (Enums.isPrismDesign && control.enabled && control.focused && control.showFocusedBorder) return Enums.prismDesign.primary
            if (Enums.isPrismDesign && control.enabled && control.hovered) return Enums.prismDesign.borderStrong
            if (!control.enabled) return Enums.stateColor.borderLight
            return Enums.stateColor.border
        }

        // Prism glass rim Prism玻璃边缘
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: Enums.prismDesign.borderWidth
            color: Enums.prismDesign.glassRimLight
            visible: Enums.isPrismDesign && !control.transparentBackground && control.enabled
        }

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: Enums.prismDesign.borderWidth
            color: Enums.prismDesign.glassRimShadow
            visible: Enums.isPrismDesign && !control.transparentBackground && control.enabled
        }

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: Enums.prismDesign.focusBorderWidth
            color: Enums.prismDesign.spectralEdge
            opacity: control.focused ? 0.75 : (control.hovered ? 0.35 : 0.0)
            visible: Enums.isPrismDesign && !control.transparentBackground && control.enabled

            Behavior on opacity { NumberAnimation { duration: Enums.duration.fast } }
        }
    }

    // Mouse cursor 鼠标光标
    MouseArea {
        // z 必须高于子 Loader/TextInput 内部 MouseArea, 否则鼠标 hover 进 padding 区域时
        // 子 MouseArea (无 hoverEnabled / cursorShape) 拦截掉, IBeam 光标只在 TextInput
        // 文字像素上有, padding 周围光标变默认箭头, 用户视觉感受为"没有光标"
        z: Enums.zIndex.inputInteraction
        anchors.fill: parent
        cursorShape: control.enabled ? control.cursorShape : Qt.ArrowCursor
        acceptedButtons: Qt.LeftButton
        hoverEnabled: true
        // mouse.accepted = false 让按下事件继续传给子 TextInput, 不影响光标定位
        propagateComposedEvents: true
        onPressed: function(mouse) {
            if (control.enabled && control.focusTarget) {
                control.focusTarget.forceActiveFocus()
            }
            // 根因修复: 点击落在 focusTarget(TextInput) 区域内 → 放行(accepted=false),
            // 让 TextInput 自己 selectByMouse 定位光标; 落在 padding 边缘区(TextInput
            // 接不住) → 消费(accepted=true), 不冒泡到下层"点空白失焦"MouseArea 夺焦
            // (旧 bug: 边缘点击 accepted=false 冒泡到 blur 层 → 进焦立刻失焦)。
            if (control.focusTarget) {
                var p = mapToItem(control.focusTarget, mouse.x, mouse.y)
                var inside = p.x >= 0 && p.y >= 0
                            && p.x <= control.focusTarget.width && p.y <= control.focusTarget.height
                mouse.accepted = !inside   // 命中输入区放行(TextInput定位光标), 边缘消费
            } else {
                mouse.accepted = false
            }
        }
        // Let wheel events pass through to subclass handlers (SpinBox, etc.)
        // 把 wheel 事件让给子类处理（SpinBox 等），避免被本层吞掉
        onWheel: function(wheel) { wheel.accepted = false }
        // 根因修复: 消费 composed clicked, 阻止其经 propagateComposedEvents 穿透到
        // 下层"点空白失焦"MouseArea。旧 bug: 按住进焦→松开时 clicked 穿透到 blur 层
        // onClicked 清焦点→松开瞬间失焦。控件内点击的 clicked 不该触发"点空白"逻辑。
        onClicked: function(mouse) { mouse.accepted = true }
    }
    
    // Focus line 聚焦底线
    // z 值确保在子类 Loader 等内容之上渲染（子类子项在基类子项之后添加，z 默认更高）
    // Neobrutalism/Prism: 关闭底线，改由整圈边界表达聚焦。
    FocusLine {
        z: Enums.zIndex.inputInteraction
        showLine: !Enums.isNeobrutalism && !Enums.isPrismDesign && control.focused && control.showFocusedBorder
        lineColor: control.focusedBorderColor
        parentRadius: control.radius
        visible: !Enums.isNeobrutalism && !Enums.isPrismDesign && control.showFocusedBorder
    }

    // Folder drop surface 文件夹拖放区域
    DropArea {
        anchors.fill: parent
        enabled: control.folderDropEnabled && control.enabled && control._folderDropWritable

        onEntered: function(drag) {
            if (!control._acceptsFolderDrag(drag)) {
                drag.accepted = false
                return
            }
            drag.accept(Qt.CopyAction)
        }

        onDropped: function(drop) {
            var folderPath = control._resolveDroppedFolder(drop)
            if (!folderPath) {
                drop.accepted = false
                return
            }
            control._applyDroppedFolder(folderPath)
            drop.accept(Qt.CopyAction)
        }
    }
}
