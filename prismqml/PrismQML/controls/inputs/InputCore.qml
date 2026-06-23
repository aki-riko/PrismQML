// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "../../effects"
import QtQuick.Effects
import "../containers"

// InputCore - Input control base class 输入控件基类
// TextInputCore/SpinBoxCore etc. extend this 继承此基类
// Provides: theme, focus line, background, clip, shadow 提供主题/聚焦底线/背景/圆角裁剪/阴影
// Note: Click outside to blur is handled by container MouseArea 点击空白失焦由容器背景MouseArea处理
Widget {
    id: control
    
    // 焦点代理属性，子类覆盖指向内部能实际接受输入的组件
    property Item focusTarget: null
    activeFocusOnTab: true
    onActiveFocusChanged: {
        if (activeFocus && focusTarget) {
            focusTarget.forceActiveFocus()
        }
    }
    
    // ==================== Base Props 基础属性 ====================
    
    // ==================== Focus Line 聚焦底线 ====================
    property bool showFocusedBorder: true
    property color focusedBorderColorLight: Enums.accentColor
    property color focusedBorderColorDark: Enums.accentColor

    readonly property color focusedBorderColor: Enums.isDark ? focusedBorderColorDark : focusedBorderColorLight
    
    // ==================== State (subclass override) 状态(子类覆盖) ====================
    property bool focused: false  // Bind to input's activeFocus 绑定到activeFocus
    property bool hovered: false  // Bind to HoverHandler's hovered 绑定到hovered
    
    // ==================== Size 尺寸 ====================
    // Content size (inherited from Widget) 内容尺寸（继承自Widget）
    contentWidth: Enums.controlSize.inputDefaultWidth
    contentHeight: Enums.controlSize.inputHeight
    property int radius: Enums.isNeobrutalism ? Enums.neo.radius : Enums.radius.small
    
    // ==================== Content Padding 内容边距 ====================
    // Unified padding for all input controls 所有输入控件统一边距
    readonly property int paddingLeft: Enums.spacing.l      // 12
    readonly property int paddingRight: Enums.spacing.m     // 8
    readonly property int paddingTop: Enums.spacing.s       // 6
    readonly property int paddingBottom: Enums.spacing.s    // 6
    
    // ==================== Text Style 文本样式 ====================
    // Unified text properties for TextInput/TextEdit 统一文本属性
    readonly property string fontFamily: Enums.fontFamily
    readonly property int fontSize: Enums.typography.body
    readonly property color selectionColor: Enums.accentColor
    readonly property color selectedTextColor: Enums.accentForeground
    
    // Input text color (enabled/disabled aware) 输入文本颜色(感知启用状态)
    readonly property color inputTextColor: !enabled ? Enums.textColor.disabled 
        : (Enums.isDark ? "white" : "black")
    
    // ==================== Inner Button Colors 内部按钮颜色 ====================
    // Unified colors for clear/action/spin buttons 清除/操作/加减按钮统一颜色
    readonly property color innerButtonHover: Enums.stateColor.controlBgHover
    readonly property color innerButtonPressed: Enums.stateColor.controlBgPressed
    
    // ==================== Transparent Background 背景透明控制 ====================
    property bool transparentBackground: false
    
    // ==================== Background Color (for subclass binding) 背景色 ====================
    // Use unified control colors 使用统一的控件颜色
    // Note: transparentBackground takes highest priority 透明背景优先级最高
    property color color: {
        if (transparentBackground) return Enums.transparent
        // 颜色由 token 层在 neo 下自动返回白面/muted, 无需控件分支。
        if (!enabled) return Enums.stateColor.controlBgDisabled
        if (focused) return Enums.cardColor  // InputgHover
        return Enums.stateColor.controlBg
    }
    
    // ==================== Border (for subclass binding) 边框 ====================
    property alias border: _bg.border

    // ==================== Mouse Cursor 鼠标光标 ====================
    property int cursorShape: Qt.IBeamCursor  // Subclass can override 子类可覆盖

    // ==================== Shadow Layer 阴影层 ====================
    // Fluent: 模糊阴影。Neobrutalism: 硬阴影(纯黑, 聚焦时转橙主色强调)。
    RectangularShadow {
        anchors.fill: _bg
        radius: _bg.radius
        color: Enums.shadow.level2.color
        blur: Enums.shadow.level2.blur
        offset: Qt.vector2d(0, Enums.shadow.level2.offset)
        visible: !control.transparentBackground && !Enums.isNeobrutalism
    }

    // Neobrutalism 硬阴影: 复用 NeoShadow 组件; 聚焦时 accent=true 转橙主色强调。
    NeoShadow {
        target: _bg
        visible: Enums.isNeobrutalism && !control.transparentBackground
        accent: control.focused
        z: _bg.z - 1
    }

    // ==================== Background Rectangle 背景矩形 ====================
    Rectangle {
        id: _bg
        anchors.fill: parent
        radius: control.radius
        color: control.color
        
        // ==================== Rounded Clip 圆角裁剪 ====================
        clip: true
        layer.enabled: radius > 0 && !control.transparentBackground
        layer.effect: OpacityMask {
            mask: Rectangle {
                width: _bg.width
                height: _bg.height
                radius: _bg.radius
            }
        }
        
        // ==================== Border 边框 ====================
        // Use unified border colors 使用统一边框颜色
        border.width: control.transparentBackground ? 0
            : (Enums.isNeobrutalism ? Enums.neo.borderWidth : Enums.border.thin)
        border.color: {
            if (control.transparentBackground) return Enums.transparent
            // neo 聚焦转橙(token 不含此交互, 属结构差异); 其余黑边由 token 自动返回
            if (Enums.isNeobrutalism && control.enabled && control.focused) return Enums.neo.primary
            if (!control.enabled) return Enums.stateColor.borderLight
            return Enums.stateColor.border
        }
    }

    // ==================== Mouse Cursor 鼠标光标 ====================
    MouseArea {
        // z 必须高于子 Loader/TextInput 内部 MouseArea, 否则鼠标 hover 进 padding 区域时
        // 子 MouseArea (无 hoverEnabled / cursorShape) 拦截掉, IBeam 光标只在 TextInput
        // 文字像素上有, padding 周围光标变默认箭头, 用户视觉感受为"没有光标"
        z: 10
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
            mouse.accepted = false
        }
        // Let wheel events pass through to subclass handlers (SpinBox, etc.)
        // 把 wheel 事件让给子类处理（SpinBox 等），避免被本层吞掉
        onWheel: function(wheel) { wheel.accepted = false }
    }
    
    // ==================== Focus Line 聚焦底线 ====================
    // z 值确保在子类 Loader 等内容之上渲染（子类子项在基类子项之后添加，z 默认更高）
    // Neobrutalism: 关闭蓝色聚焦底线(橙粗边+硬阴影已表达聚焦, 蓝线破坏 neo 配色)。
    FocusLine {
        z: 10
        showLine: !Enums.isNeobrutalism && control.focused && control.showFocusedBorder
        lineColor: control.focusedBorderColor
        parentRadius: control.radius
        visible: !Enums.isNeobrutalism && control.showFocusedBorder
    }
}
