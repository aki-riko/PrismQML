// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import "../.."
import "../../effects"
import "../buttons/Button"
import "../inputs/LineEdit"
import "../inputs/Toggle"
import "../inputs"
import "../icons"

// LoginWindow - Login window with MatrixRain background 带矩阵雨背景的登录窗口
// Usage 用法:
//   LoginWindow {
//       onLoginRequested: (username, password) => handleLogin(username, password)
//       onRegisterRequested: (username, email, password) => handleRegister(...)
//       onOAuthRequested: (provider) => handleOAuth(provider)
//   }

Rectangle {
    id: root
    color: Enums.transparent
    
    // ==================== Public Props 公开属性 ====================
    // Mode 模式
    property int mode: Enums.auth.mode_login
    
    // Content 内容
    property string title: mode === Enums.auth.mode_login ? qsTr("Welcome Back") : qsTr("Create Account")
    property string subtitle: mode === Enums.auth.mode_login ? qsTr("Sign in to continue") : qsTr("Sign up to get started")
    property string logoSource: ""
    property string logoText: "FluentQML"
    
    // OAuth providers 支持的OAuth提供商
    property var oauthProviders: [
        Enums.auth.oauth_github,
        Enums.auth.oauth_google,
        Enums.auth.oauth_microsoft
    ]
    
    // Matrix rain settings 矩阵雨设置
    property string matrixTheme: "classic"
    property bool matrixEnabled: true
    property real matrixSpeed: 1.0
    property real matrixDensity: 1.0
    property bool matrixGlow: true
    
    // Form settings 表单设置
    property bool rememberMeEnabled: true
    property bool forgotPasswordEnabled: true
    property string forgotPasswordUrl: ""
    property bool showPasswordStrength: true
    
    // Loading state 加载状态
    property bool loading: false
    property string loadingText: qsTr("Please wait...")
    
    // Error state 错误状态
    property string errorMessage: ""
    
    // Card style 卡片样式
    property int cardWidth: 400
    property real cardOpacity: 0.92
    
    // ==================== Signals 信号 ====================
    signal loginRequested(string username, string password, bool rememberMe)
    signal registerRequested(string username, string email, string password)
    signal oauthRequested(int provider)
    signal forgotPasswordClicked()
    signal modeToggled(int newMode)  // Renamed to avoid conflict with property change signal 重命名避免与属性变化信号冲突
    
    // ==================== Internal 内部 ====================
    readonly property bool _isLogin: mode === Enums.auth.mode_login

    // ==================== Private Functions 私有函数 ====================
    function _isFormValid() {
        if (_isLogin) {
            return usernameInput.text.length > 0 && passwordInput.text.length > 0
        } else {
            return usernameInput.text.length > 0 &&
                   emailInput.text.length > 0 &&
                   passwordInput.text.length > 0 &&
                   confirmPasswordInput.text.length > 0 &&
                   passwordInput.text === confirmPasswordInput.text
        }
    }

    function _submitForm() {
        if (!_isFormValid()) return

        if (_isLogin) {
            loginRequested(usernameInput.text, passwordInput.text, rememberMeCheck.checked)
        } else {
            registerRequested(usernameInput.text, emailInput.text, passwordInput.text)
        }
    }

    function _toggleMode() {
        if (_isLogin) {
            mode = Enums.auth.mode_register
        } else {
            mode = Enums.auth.mode_login
        }
        // Clear form 清空表单
        errorMessage = ""
        modeToggled(mode)
    }

    // ==================== Public Methods 公开方法 ====================
    // Clear form 清空表单
    function clearForm() {
        usernameInput.setText("")
        emailInput.setText("")
        passwordInput.setText("")
        confirmPasswordInput.setText("")
        rememberMeCheck.checked = false
        errorMessage = ""
    }


    // Clear error 清除错误
    function clearError() {
        errorMessage = ""
    }

    // Set loading 设置加载状态
    function setLoading(isLoading, text) {
        loading = isLoading
        if (text) loadingText = text
    }


    // Set matrix theme 设置矩阵雨主题
    function setMatrixTheme(theme) {
        matrixTheme = theme
        matrixRain.setTheme(theme)
    }

    // Focus username input 聚焦用户名输入框
    function focusUsername() {
        usernameInput.forceActiveFocus()
    }

    // Get form data 获取表单数据
    function getFormData() {
        return {
            username: usernameInput.text,
            email: emailInput.text,
            password: passwordInput.text,
            rememberMe: rememberMeCheck.checked
        }
    }

    // ==================== Matrix Rain Background 矩阵雨背景 ====================
    MatrixRain {
        id: matrixRain
        anchors.fill: parent
        running: root.matrixEnabled && root.visible
        speed: root.matrixSpeed
        density: root.matrixDensity
        glowEnabled: root.matrixGlow
        glowIntensity: 1.2
        
        Component.onCompleted: setTheme(root.matrixTheme)
    }
    
    // ==================== Center Card 中心卡片 ====================
    ShadowedRectangle {
        id: card
        width: root.cardWidth
        height: cardContent.height + Enums.spacing.xxl * 2
        anchors.centerIn: parent
        radius: Enums.radius.large
        color: Qt.rgba(
            Enums.cardColor.r,
            Enums.cardColor.g,
            Enums.cardColor.b,
            root.cardOpacity
        )
        border.width: Enums.border.thin
        border.color: Enums.stateColor.border
        
        // Card shadow 卡片阴影
        shadowLevel: Enums.shadow.level8
        
        // ==================== Card Content 卡片内容 ====================
        ColumnLayout {
            id: cardContent
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: Enums.spacing.xxl
            spacing: Enums.spacing.l
            
            // ==================== Logo Area 标志区域 ====================
            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 60
                
                // Logo image 标志图片
                Image {
                    id: logoImage
                    anchors.centerIn: parent
                    width: 48
                    height: 48
                    source: root.logoSource
                    visible: root.logoSource !== ""
                    fillMode: Image.PreserveAspectFit
                }
                
                // Logo text 标志文字
                Text {
                    anchors.centerIn: parent
                    text: root.logoText
                    font.family: Enums.fontFamily
                    font.pixelSize: Enums.typography.display
                    font.bold: true
                    color: Enums.accentColor
                    visible: root.logoSource === ""
                }
            }
            
            // ==================== Title Area 标题区域 ====================
            ColumnLayout {
                Layout.fillWidth: true
                spacing: Enums.spacing.xs
                
                Text {
                    Layout.fillWidth: true
                    text: root.title
                    font.family: Enums.fontFamily
                    font.pixelSize: Enums.typography.title
                    font.bold: true
                    color: Enums.foregroundColor
                    horizontalAlignment: Text.AlignHCenter
                }
                
                Text {
                    Layout.fillWidth: true
                    text: root.subtitle
                    font.family: Enums.fontFamily
                    font.pixelSize: Enums.typography.body
                    color: Enums.secondaryForeground
                    horizontalAlignment: Text.AlignHCenter
                }
            }
            
            // ==================== Error Message 错误消息 ====================
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: errorText.height + Enums.spacing.m
                radius: Enums.radius.small
                color: Qt.rgba(Enums.statusLevel.errorColor.r, Enums.statusLevel.errorColor.g, Enums.statusLevel.errorColor.b, 0.1)
                border.width: Enums.border.thin
                border.color: Enums.statusLevel.errorColor
                visible: root.errorMessage !== ""
                
                Text {
                    id: errorText
                    anchors.centerIn: parent
                    width: parent.width - Enums.spacing.m * 2
                    text: root.errorMessage
                    font.family: Enums.fontFamily
                    font.pixelSize: Enums.typography.bodySmall
                    color: Enums.statusLevel.errorColor
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                }
            }
            
            // ==================== Form Fields 表单字段 ====================
            ColumnLayout {
                Layout.fillWidth: true
                spacing: Enums.spacing.m
                
                // Username field 用户名字段
                LineEditCore {
                    id: usernameInput
                    Layout.fillWidth: true
                    inputType: Enums.input.type_normal
                    placeholderText: root._isLogin ? qsTr("Username or Email") : qsTr("Username")
                    enabled: !root.loading
                    
                    onAccepted: {
                        if (root._isLogin) passwordInput.forceActiveFocus()
                        else emailInput.forceActiveFocus()
                    }
                }
                
                // Email field (register only) 邮箱字段（仅注册）
                LineEditCore {
                    id: emailInput
                    Layout.fillWidth: true
                    inputType: Enums.input.type_normal
                    placeholderText: qsTr("Email")
                    visible: !root._isLogin
                    enabled: !root.loading
                    
                    onAccepted: passwordInput.forceActiveFocus()
                }
                
                // Password field 密码字段
                LineEditCore {
                    id: passwordInput
                    Layout.fillWidth: true
                    inputType: Enums.input.type_password
                    placeholderText: qsTr("Password")
                    enabled: !root.loading
                    
                    onAccepted: {
                        if (root._isLogin) root._submitForm()
                        else confirmPasswordInput.forceActiveFocus()
                    }
                }
                
                // Confirm password (register only) 确认密码（仅注册）
                LineEditCore {
                    id: confirmPasswordInput
                    Layout.fillWidth: true
                    inputType: Enums.input.type_password
                    placeholderText: qsTr("Confirm Password")
                    visible: !root._isLogin
                    enabled: !root.loading
                    
                    onAccepted: root._submitForm()
                }
                
                // Password strength indicator 密码强度指示器
                PasswordStrengthIndicator {
                    Layout.fillWidth: true
                    password: passwordInput.text
                    visible: !root._isLogin && root.showPasswordStrength && passwordInput.text.length > 0
                }
            }
            
            // ==================== Remember Me & Forgot Password 记住我和忘记密码 ====================
            RowLayout {
                Layout.fillWidth: true
                visible: root._isLogin
                
                // Remember me 记住我
                CheckBox {
                    id: rememberMeCheck
                    text: qsTr("Remember me")
                    visible: root.rememberMeEnabled
                    enabled: !root.loading
                }
                
                Item { Layout.fillWidth: true }
                
                // Forgot password 忘记密码
                Text {
                    text: qsTr("Forgot password?")
                    font.family: Enums.fontFamily
                    font.pixelSize: Enums.typography.bodySmall
                    color: Enums.accentColor
                    visible: root.forgotPasswordEnabled
                    
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        enabled: !root.loading
                        onClicked: root.forgotPasswordClicked()
                    }
                }
            }
            
            // ==================== Submit Button 提交按钮 ====================
            ButtonCore {
                Layout.fillWidth: true
                Layout.preferredHeight: Enums.controlSize.buttonHeight
                text: root.loading ? root.loadingText : (root._isLogin ? qsTr("Sign In") : qsTr("Sign Up"))
                style: Enums.button.style_primary
                loading: root.loading
                enabled: !root.loading && root._isFormValid()
                
                onClicked: root._submitForm()
            }
            
            // ==================== OAuth Divider OAuth分隔线 ====================
            RowLayout {
                Layout.fillWidth: true
                visible: root.oauthProviders.length > 0
                spacing: Enums.spacing.m

                Separator {
                    Layout.fillWidth: true
                }

                Text {
                    text: qsTr("or continue with")
                    font.family: Enums.fontFamily
                    font.pixelSize: Enums.typography.caption
                    color: Enums.secondaryForeground
                }

                Separator {
                    Layout.fillWidth: true
                }
            }
            
            // ==================== OAuth Buttons OAuth按钮 ====================
            RowLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignHCenter
                spacing: Enums.spacing.m
                visible: root.oauthProviders.length > 0
                
                Repeater {
                    model: root.oauthProviders
                    
                    ButtonCore {
                        required property int modelData
                        
                        Layout.preferredWidth: 100
                        Layout.preferredHeight: Enums.controlSize.buttonHeight
                        text: Enums.auth.getOAuthName(modelData)
                        icon: Enums.auth.getOAuthIcon(modelData)
                        style: Enums.button.style_default
                        enabled: !root.loading
                        
                        onClicked: root.oauthRequested(modelData)
                    }
                }
            }
            
            // ==================== Mode Switch 模式切换 ====================
            RowLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignHCenter
                spacing: Enums.spacing.xs
                
                Text {
                    text: root._isLogin ? qsTr("Don't have an account?") : qsTr("Already have an account?")
                    font.family: Enums.fontFamily
                    font.pixelSize: Enums.typography.bodySmall
                    color: Enums.secondaryForeground
                }
                
                Text {
                    text: root._isLogin ? qsTr("Sign Up") : qsTr("Sign In")
                    font.family: Enums.fontFamily
                    font.pixelSize: Enums.typography.bodySmall
                    font.bold: true
                    color: Enums.accentColor
                    
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        enabled: !root.loading
                        onClicked: root._toggleMode()
                    }
                }
            }
        }
    }
    
    // ==================== Mode Switch Animation 模式切换动画 ====================
    Behavior on mode {
        NumberAnimation { duration: Enums.duration.fast }
    }
}
