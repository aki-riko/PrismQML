// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick.Effects
import "../../.."
import "../../icons"
import "../../data"
import QtQuick  // 置于库import后:去前缀后保原生类型不被库覆盖

// SplashScreen - Application splash screen overlay 应用启动画面覆盖层
// Usage 用法:
//   Window {
//       id: mainWindow
//       SplashScreen {
//           id: splashScreen
//           iconSource: "qrc:/logo.png"  // or icon: Enums.icon.home
//           title: "My App"
//           subtitle: "Loading..."
//       }
//       Component.onCompleted: {
//           // Load your content...
//           splashScreen.finish()
//       }
//   }
Rectangle {
    id: control
    
    // ==================== Public Props 公开属性 ====================
    property var icon: null                          // Icon enum value 图标枚举值
    property string iconSource: ""                   // Image path (png/svg/qrc) 图片路径
    property int iconSize: 102                       // Icon size 图标尺寸
    property bool enableShadow: true                 // Enable icon shadow 启用图标阴影
    property alias titleBar: titleBarLoader.sourceComponent  // Custom title bar 自定义标题栏
    property bool showTitleBar: Qt.platform.os !== "osx"  // Show title bar (hidden on macOS) 显示标题栏
    
    // New: Text props 新增文本属性
    property string title: ""                        // App title 应用标题
    property string subtitle: ""                     // Subtitle or loading text 副标题或加载文字
    property bool showProgress: true                 // Show progress ring 显示进度环
    
    // ==================== Signals 信号 ====================
    signal finished()  // Emitted when splash screen is closed 启动画面关闭时触发
    
    // ==================== Component Settings 组件设置 ====================
    anchors.fill: parent
    z: Enums.zIndex.tooltip  // Always on top 始终在最上层
    color: Enums.backgroundColor
    visible: true
    opacity: 0  // Start invisible for fade-in 初始不可见用于淡入
    
    Component.onCompleted: fadeInAnim.start()
    
    // ==================== Public Methods 公开方法 ====================
    // Close splash screen 关闭启动画面
    function finish() {
        breatheAnim.stop()
        fadeOutAnim.start()
    }
    
    // Set icon (Icon enum or string) 设置图标
    function setIcon(iconValue) {
        if (typeof iconValue === "number") {
            control.icon = iconValue
            control.iconSource = ""
        } else if (typeof iconValue === "string") {
            control.iconSource = iconValue
            control.icon = null
        }
    }
    
    
    // ==================== Fade In Animation 淡入动画 ====================
    ParallelAnimation {
        id: fadeInAnim
        
        NumberAnimation {
            target: control
            property: "opacity"
            from: 0; to: 1
            duration: Enums.duration.slow
            easing.type: Easing.OutCubic
        }
        
        NumberAnimation {
            target: contentColumn
            property: "scale"
            from: 0.8; to: 1
            duration: Enums.duration.slow
            easing.type: Easing.OutBack
        }
        
        onFinished: breatheAnim.start()
    }
    
    // ==================== Fade Out Animation 淡出动画 ====================
    SequentialAnimation {
        id: fadeOutAnim
        
        ParallelAnimation {
            NumberAnimation {
                target: control
                property: "opacity"
                to: 0
                duration: Enums.duration.medium
                easing.type: Easing.InCubic
            }
            NumberAnimation {
                target: contentColumn
                property: "scale"
                to: 1.1
                duration: Enums.duration.medium
                easing.type: Easing.InCubic
            }
        }
        
        ScriptAction {
            script: {
                control.visible = false
                control.finished()
            }
        }
    }
    
    // ==================== Breathe Animation 呼吸动画 ====================
    SequentialAnimation {
        id: breatheAnim
        loops: Animation.Infinite
        
        NumberAnimation {
            target: iconContainer
            property: "scale"
            from: 1.0; to: 1.03
            duration: 1200  // Enums.duration.xslow
            easing.type: Easing.InOutSine
        }
        NumberAnimation {
            target: iconContainer
            property: "scale"
            from: 1.03; to: 1.0
            duration: 1200  // Enums.duration.xslow
            easing.type: Easing.InOutSine
        }
    }
    
    // ==================== Title Bar 标题栏 ====================
    Loader {
        id: titleBarLoader
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        z: 1
        active: control.showTitleBar
        sourceComponent: defaultTitleBar
    }
    
    Component {
        id: defaultTitleBar
        
        // Default transparent title bar 默认透明标题栏
        Rectangle {
            height: Enums.controlSize.titleBarHeight
            color: Enums.transparent
        }
    }
    
    // ==================== Main Content 主要内容 ====================
    Column {
        id: contentColumn
        anchors.centerIn: parent
        spacing: Enums.spacing.xl
        transformOrigin: Item.Center
        
        // Icon Container 图标容器
        Item {
            id: iconContainer
            anchors.horizontalCenter: parent.horizontalCenter
            width: control.iconSize
            height: control.iconSize
            transformOrigin: Item.Center
            
            // Icon display (for icon enum) Icon显示
            Icon {
                id: fluentIconDisplay
                anchors.centerIn: parent
                icon: (control.icon !== null && control.icon !== undefined) ? control.icon : Enums.icon.home
                iconSize: control.iconSize
                visible: control.icon !== null && control.icon !== undefined && control.iconSource === ""
            }
            
            // Image display (for iconSource) 图片显示
            Image {
                id: imageDisplay
                anchors.centerIn: parent
                width: control.iconSize
                height: control.iconSize
                source: control.iconSource
                fillMode: Image.PreserveAspectFit
                visible: control.iconSource !== ""
                smooth: true
                mipmap: true
            }
            
            // Shadow effect 阴影效果
            layer.enabled: control.enableShadow
            layer.effect: MultiEffect {
                shadowEnabled: true
                shadowColor: Enums.shadowStrongColor
                shadowBlur: 0.8
                shadowVerticalOffset: 6
            }
        }
        
        // Title 标题
        Label {
            anchors.horizontalCenter: parent.horizontalCenter
            text: control.title
            type: Enums.label.type_subtitle
            visible: control.title !== ""
        }
        
        // Progress + Subtitle row 进度环+副标题行
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: Enums.spacing.m
            visible: control.showProgress || control.subtitle !== ""
            
            // Progress Ring 进度环
            Item {
                width: Enums.iconSize.xl
                height: Enums.iconSize.xl
                visible: control.showProgress
                anchors.verticalCenter: parent.verticalCenter
                
                // Spinning ring 旋转环
                Rectangle {
                    id: progressRing
                    anchors.fill: parent
                    radius: width / 2
                    color: Enums.transparent
                    border.width: 2
                    border.color: Enums.accentColor
                    opacity: 0.3  // Enums.opacity.medium
                }
                
                // Arc indicator 弧形指示器
                Rectangle {
                    width: parent.width
                    height: parent.height
                    radius: width / 2
                    color: Enums.transparent
                    
                    Rectangle {
                        width: 6
                        height: 6
                        radius: Enums.radius.tiny  // 3
                        color: Enums.accentColor
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.top: parent.top
                        anchors.topMargin: -1
                    }
                    
                    RotationAnimation on rotation {
                        from: 0
                        to: 360
                        duration: 1000  // Enums.duration.verySlow
                        loops: Animation.Infinite
                    }
                }
            }
            
            // Subtitle 副标题
            Label {
                text: control.subtitle
                type: Enums.label.type_body
                color: Enums.textColor.secondary
                visible: control.subtitle !== ""
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }
}
