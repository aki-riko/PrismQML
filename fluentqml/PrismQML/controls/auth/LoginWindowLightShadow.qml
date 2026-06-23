// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import "../.."
import "../../effects"
import "../inputs"

// LoginWindowLightShadow - Light and Shadow login card 光影登录卡片
// Faithful recreation of HTML design 忠实还原HTML设计
// Features 特点:
//   - Rotating conic gradient border (red + cyan beams) 旋转锥形渐变边框
//   - Hover to expand 悬停展开
//   - Deep glass card background 深色玻璃背景

Rectangle {
    id: root
    color: "transparent"
    
    // ==================== Public Props 公开属性 ====================
    property string title: qsTr("Login")
    
    // Matrix rain settings 矩阵雨设置
    property bool matrixEnabled: true
    property string matrixTheme: "classic"
    property real matrixSpeed: 1.0
    property real matrixDensity: 1.0
    property bool matrixGlow: true
    
    // Card settings 卡片设置
    property int cardWidth: 400
    property int cardCollapsedHeight: 100
    property int cardExpandedHeight: 300
    
    // Animation 动画
    property int rotationDuration: 4000  // 4s per rotation 每圈4秒
    
    // State 状态
    property bool loading: false
    property string errorMessage: ""
    
    // ==================== Signals 信号 ====================
    signal loginRequested(string username, string password)
    
    // ==================== Internal 内部 ====================
    property bool _expanded: hoverArea.containsMouse || userInput.activeFocus || passInput.activeFocus

    // ==================== Private Functions 私有函数 ====================
    function _canSubmit() {
        return userInput.text.length > 0 && passInput.text.length > 0
    }

    // ==================== Public Methods 公开方法 ====================
    function clearForm() {
        userInput.text = ""
        passInput.text = ""
        errorMessage = ""
    }

    function clearError() { errorMessage = "" }
    function focusUsername() { userInput.forceActiveFocus() }

    // ==================== Matrix Rain Background 矩阵雨背景 ====================
    MatrixRain {
        id: matrixRain
        anchors.fill: parent
        running: root.matrixEnabled && root.visible
        speed: root.matrixSpeed
        density: root.matrixDensity
        glowEnabled: root.matrixGlow
        
        Component.onCompleted: setTheme(root.matrixTheme)
    }
    
    // ==================== Card 卡片 ====================
    Item {
        id: cardWrapper
        width: root.cardWidth
        height: root._expanded ? root.cardExpandedHeight : root.cardCollapsedHeight
        anchors.centerIn: parent
        anchors.verticalCenterOffset: root._expanded ? 0 : -15
        
        Behavior on height { NumberAnimation { duration: 500; easing.type: Easing.OutCubic } }
        Behavior on anchors.verticalCenterOffset { NumberAnimation { duration: 500; easing.type: Easing.OutCubic } }
        
        // ==================== Rotating Conic Gradient Border 旋转锥形渐变边框 ====================
        Item {
            id: borderContainer
            anchors.fill: parent
            
            property real angle: 0
            
            NumberAnimation on angle {
                from: 0
                to: 360
                duration: root.rotationDuration
                loops: Animation.Infinite
                running: true
            }
            
            // Conic gradient border using Canvas 使用Canvas实现锥形渐变边框
            Canvas {
                id: borderCanvas
                anchors.fill: parent
                antialiasing: true
                renderStrategy: Canvas.Threaded
                
                onPaint: {
                    var ctx = getContext("2d")
                    ctx.reset()
                    
                    var w = width
                    var h = height
                    var cx = w / 2
                    var cy = h / 2
                    var r = 20  // Border radius 圆角半径
                    var diag = Math.sqrt(w * w + h * h) / 2
                    
                    // Draw conic gradient segments 绘制锥形渐变分段
                    var segments = 72
                    var angleRad = borderContainer.angle * Math.PI / 180
                    
                    for (var i = 0; i < segments; i++) {
                        var segAngle = (i / segments) * Math.PI * 2
                        var nextAngle = ((i + 1) / segments) * Math.PI * 2
                        
                        // Calculate beam intensity 计算光束强度
                        var normalizedAngle = i / segments
                        var rotatedAngle = (normalizedAngle + borderContainer.angle / 360) % 1
                        
                        // Red beams at 0 and 0.5 红色光束在0和0.5
                        var redDist1 = Math.abs(rotatedAngle)
                        var redDist2 = Math.abs(rotatedAngle - 0.5)
                        var redDist3 = Math.abs(rotatedAngle - 1.0)
                        var redDist = Math.min(redDist1, redDist2, redDist3)
                        var redAlpha = Math.max(0, 1 - redDist / 0.08)
                        
                        // Cyan beams at 0.25 and 0.75 青色光束在0.25和0.75
                        var cyanDist1 = Math.abs(rotatedAngle - 0.25)
                        var cyanDist2 = Math.abs(rotatedAngle - 0.75)
                        var cyanDist = Math.min(cyanDist1, cyanDist2)
                        var cyanAlpha = Math.max(0, 1 - cyanDist / 0.08)
                        
                        if (redAlpha > 0.01 || cyanAlpha > 0.01) {
                            ctx.beginPath()
                            ctx.moveTo(cx, cy)
                            ctx.arc(cx, cy, diag, segAngle, nextAngle + 0.02)
                            ctx.closePath()
                            
                            // Mix colors 混合颜色
                            var rr = redAlpha
                            var rg = redAlpha * 0.15
                            var rb = redAlpha * 0.44
                            var cr = cyanAlpha * 0.27
                            var cg = cyanAlpha * 0.95
                            var cb = cyanAlpha
                            
                            var finalR = Math.min(1, rr + cr)
                            var finalG = Math.min(1, rg + cg)
                            var finalB = Math.min(1, rb + cb)
                            var finalA = Math.max(redAlpha, cyanAlpha) * 0.9
                            
                            ctx.fillStyle = Qt.rgba(finalR, finalG, finalB, finalA)
                            ctx.fill()
                        }
                    }
                    
                    // Clip to rounded rectangle shape 裁剪为圆角矩形
                    ctx.globalCompositeOperation = "destination-in"
                    ctx.beginPath()
                    ctx.roundedRect(0, 0, w, h, r, r)
                    ctx.fill()
                    
                    // Cut out inner area (make it a border) 挖空内部区域
                    ctx.globalCompositeOperation = "destination-out"
                    ctx.beginPath()
                    ctx.roundedRect(4, 4, w - 8, h - 8, r - 4, r - 4)
                    ctx.fill()
                }
                
                // Repaint on angle change 角度变化时重绘
                Connections {
                    target: borderContainer
                    function onAngleChanged() { borderCanvas.requestPaint() }
                }
                
                // Repaint on size change 尺寸变化时重绘
                onWidthChanged: requestPaint()
                onHeightChanged: requestPaint()
            }
            
            // Glow effect 发光效果
            layer.enabled: true
            layer.effect: Shadow {
                blur: 0.6
                color: "#000000cc"
            }
        }
        
        // ==================== Card Background 卡片背景 ====================
        Rectangle {
            id: cardBg
            anchors.fill: parent
            anchors.margins: 4
            radius: 16
            color: "#0f0f0f"
            border.width: 8
            border.color: "#0e171c"
        }
        
        // ==================== Hover Area 悬停区域 ====================
        MouseArea {
            id: hoverArea
            anchors.fill: parent
            hoverEnabled: true
            propagateComposedEvents: true
            onClicked: (m) => m.accepted = false
            onPressed: (m) => m.accepted = false
        }
        
        // ==================== Content 内容 ====================
        ColumnLayout {
            anchors.fill: cardBg
            anchors.margins: 20
            spacing: 12
            
            // Title 标题
            Text {
                Layout.fillWidth: true
                text: root.title
                font.family: "Consolas, monospace"
                font.pixelSize: 43
                font.bold: true
                color: "#49beff"
                horizontalAlignment: Text.AlignHCenter
                
                opacity: root._expanded ? 0.7 : 1.0
                Behavior on opacity { NumberAnimation { duration: 300 } }
            }
            
            // Form 表单
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 12
                opacity: root._expanded ? 1 : 0
                visible: opacity > 0
                
                transform: Translate { y: root._expanded ? 0 : 20 }
                
                Behavior on opacity { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }
                
                // Error 错误
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 32
                    radius: 5
                    color: Qt.rgba(1, 0.2, 0.2, 0.15)
                    border.width: 1
                    border.color: "#f44"
                    visible: root.errorMessage !== ""
                    
                    Text {
                        anchors.centerIn: parent
                        text: root.errorMessage
                        color: "#f66"
                        font.pixelSize: 12
                    }
                }
                
                // Username 用户名
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 44
                    radius: 5
                    color: "#000"
                    border.width: 1
                    border.color: userInput.activeFocus ? "#ff3333" : "#ffffff26"
                    
                    Behavior on border.color { ColorAnimation { duration: 200 } }
                    
                    layer.enabled: userInput.activeFocus
                    layer.effect: Shadow { blur: 0.3; color: "#00ccff" }
                    
                    TextInput {
                        id: userInput
                        anchors.fill: parent
                        anchors.margins: 12
                        verticalAlignment: Text.AlignVCenter
                        color: "#fff"
                        font.pixelSize: 14
                        selectByMouse: true
                        
                        Text {
                            anchors.fill: parent
                            verticalAlignment: Text.AlignVCenter
                            text: qsTr("User ID")
                            color: "#888"
                            font: parent.font
                            visible: !parent.text && !parent.activeFocus
                        }
                        
                        onAccepted: passInput.forceActiveFocus()
                    }
                }
                
                // Password 密码
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 44
                    radius: 5
                    color: "#000"
                    border.width: 1
                    border.color: passInput.activeFocus ? "#ff3333" : "#ffffff26"
                    
                    Behavior on border.color { ColorAnimation { duration: 200 } }
                    
                    layer.enabled: passInput.activeFocus
                    layer.effect: Shadow { blur: 0.3; color: "#00ccff" }
                    
                    TextInput {
                        id: passInput
                        anchors.fill: parent
                        anchors.margins: 12
                        verticalAlignment: Text.AlignVCenter
                        color: "#fff"
                        font.pixelSize: 14
                        echoMode: TextInput.Password
                        selectByMouse: true
                        
                        Text {
                            anchors.fill: parent
                            verticalAlignment: Text.AlignVCenter
                            text: qsTr("Password")
                            color: "#888"
                            font: parent.font
                            visible: !parent.text && !parent.activeFocus
                        }
                        
                        onAccepted: if (_canSubmit()) root.loginRequested(userInput.text, passInput.text)
                    }
                }
                
                // Login Button 登录按钮
                Rectangle {
                    id: loginBtn
                    Layout.fillWidth: true
                    Layout.preferredHeight: 44
                    Layout.topMargin: 6
                    radius: 5
                    color: loginArea.containsMouse ? "#00ccff" : "#c8f31d"
                    border.width: 1
                    border.color: "#000"
                    
                    Behavior on color { ColorAnimation { duration: 200 } }
                    
                    layer.enabled: loginArea.containsMouse
                    layer.effect: Shadow { blur: 0.3; color: "#00ccff" }
                    
                    Text {
                        anchors.centerIn: parent
                        text: root.loading ? qsTr("LOADING...") : qsTr("LOGIN")
                        font.pixelSize: 14
                        font.bold: true
                        font.letterSpacing: 1
                        color: "#000"
                    }
                    
                    MouseArea {
                        id: loginArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        enabled: !root.loading && _canSubmit()
                        
                        onClicked: root.loginRequested(userInput.text, passInput.text)
                    }
                }
            }
            
            Item { Layout.fillHeight: true }
        }
    }
}
