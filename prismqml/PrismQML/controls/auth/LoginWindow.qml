// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

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

    // ==================== Public Props 公开属性 ====================
    // Mode 模式
    property int mode: Enums.auth.mode_login
    
    // Content 内容
    property string title: {
        _translationVersion
        return mode === Enums.auth.mode_login
            ? Translator.tr("welcome_back") : Translator.tr("create_account")
    }
    property string subtitle: {
        _translationVersion
        return mode === Enums.auth.mode_login
            ? Translator.tr("sign_in_to_continue")
            : Translator.tr("sign_up_to_get_started")
    }
    property string logoSource: ""
    property string logoText: "PrismQML"
    
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
    property string loadingText: {
        _translationVersion
        return Translator.tr("please_wait")
    }
    
    // Error state 错误状态
    property string errorMessage: ""
    
    // Card style 卡片样式
    property int cardWidth: 400
    property real cardOpacity: 0.92

    // ==================== Internal Props 内部属性 ====================
    readonly property int _translationVersion: Translator._v
    readonly property var _safeOauthProviders:
        oauthProviders === null || oauthProviders === undefined ? []
        : (typeof oauthProviders.length === "number" ? oauthProviders : [])
    readonly property bool _isLogin: mode === Enums.auth.mode_login
    readonly property int _cardRadius: Enums.radius.large
    readonly property int _errorRadius: Enums.radius.small
    readonly property color _cardColor: Enums.cardColor
    readonly property color _cardBackgroundColor: Qt.rgba(
        root._cardColor.r,
        root._cardColor.g,
        root._cardColor.b,
        root.cardOpacity
    )
    readonly property int _cardBorderWidth: Enums.border.thin
    readonly property color _cardBorderColor: Enums.stateColor.border
    readonly property color _errorBackgroundColor: Enums.statusLevel.getBgColor(Enums.statusLevel.errorStr)
    readonly property int _errorBorderWidth: Enums.border.thin
    readonly property color _errorBorderColor: Enums.statusLevel.getColor(Enums.statusLevel.errorStr)
    readonly property color _errorTextColor: _errorBorderColor
    property bool _registerContentRequested: false
    property bool _loginContentRequested: false
    readonly property var _emailInput: emailInputLoader.item
    readonly property var _confirmPasswordInput: confirmPasswordInputLoader.item
    readonly property var _rememberMeCheck: loginOptionsLoader.item
        ? loginOptionsLoader.item.rememberMeCheck : null
    
    // ==================== Signals 信号 ====================
    signal loginRequested(string username, string password, bool rememberMe)
    signal registerRequested(string username, string email, string password)
    signal oauthRequested(int provider)
    signal forgotPasswordClicked()
    signal modeToggled(int newMode)  // Renamed to avoid conflict with property change signal 重命名避免与属性变化信号冲突

    // ==================== Internal Methods 内部方法 ====================
    function _isFormValid() {
        if (_isLogin) {
            return usernameInput.text.length > 0 && passwordInput.text.length > 0
        }
        if (!root._emailInput || !root._confirmPasswordInput) return false
        return usernameInput.text.length > 0 &&
               root._emailInput.text.length > 0 &&
               passwordInput.text.length > 0 &&
               root._confirmPasswordInput.text.length > 0 &&
               passwordInput.text === root._confirmPasswordInput.text
    }

    function _submitForm() {
        if (!_isFormValid()) return

        if (_isLogin) {
            loginRequested(
                usernameInput.text,
                passwordInput.text,
                root._rememberMeCheck ? root._rememberMeCheck.checked : false
            )
        } else {
            registerRequested(usernameInput.text, root._emailInput.text, passwordInput.text)
        }
    }

    function _prewarmRegisterContent() {
        root._registerContentRequested = true
    }

    function _prewarmLoginContent() {
        root._loginContentRequested = true
    }

    function _prewarmAlternateModeContent() {
        if (root._isLogin) root._prewarmRegisterContent()
        else root._prewarmLoginContent()
    }

    function _toggleMode() {
        root._prewarmAlternateModeContent()
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
        if (root._emailInput) root._emailInput.setText("")
        passwordInput.setText("")
        if (root._confirmPasswordInput) root._confirmPasswordInput.setText("")
        if (root._rememberMeCheck) root._rememberMeCheck.checked = false
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
            email: root._emailInput ? root._emailInput.text : "",
            password: passwordInput.text,
            rememberMe: root._rememberMeCheck
                ? root._rememberMeCheck.checked : false
        }
    }

    color: Enums.transparent

    onModeChanged: {
        if (!root._isLogin) root._prewarmRegisterContent()
        else root._prewarmLoginContent()
    }

    // ==================== Content 内容 ====================
    // Matrix rain background. 矩阵雨背景。
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
    
    // Center card. 中心卡片。
    ShadowedRectangle {
        id: card
        width: root.cardWidth
        height: cardContent.height + Enums.spacing.xxl * 2
        anchors.centerIn: parent
        radius: root._cardRadius
        color: root._cardBackgroundColor
        border.width: root._cardBorderWidth
        border.color: root._cardBorderColor
        
        // Card shadow 卡片阴影
        shadowLevel: Enums.shadow.level8
        
        // Card content. 卡片内容。
        ColumnLayout {
            id: cardContent
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: Enums.spacing.xxl
            spacing: Enums.spacing.l
            
            // Logo area. 标志区域。
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
            
            // Title area. 标题区域。
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
            
            // Error message. 错误消息。
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: errorText.height + Enums.spacing.m
                radius: root._errorRadius
                color: root._errorBackgroundColor
                border.width: root._errorBorderWidth
                border.color: root._errorBorderColor
                visible: root.errorMessage !== ""
                
                Text {
                    id: errorText
                    anchors.centerIn: parent
                    width: parent.width - Enums.spacing.m * 2
                    text: root.errorMessage
                    font.family: Enums.fontFamily
                    font.pixelSize: Enums.typography.bodySmall
                    color: root._errorTextColor
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                }
            }
            
            // Form fields. 表单字段。
            ColumnLayout {
                Layout.fillWidth: true
                spacing: Enums.spacing.m
                
                // Username field 用户名字段
                LineEditCore {
                    id: usernameInput
                    Layout.fillWidth: true
                    inputType: Enums.input.type_normal
                    placeholderText: {
                        root._translationVersion
                        return root._isLogin
                            ? Translator.tr("username_or_email")
                            : Translator.tr("username")
                    }
                    enabled: !root.loading
                    
                    onAccepted: {
                        if (root._isLogin) passwordInput.forceActiveFocus()
                        else emailInput.forceActiveFocus()
                    }
                }
                
                // Email field (register only) 邮箱字段（仅注册）
                Loader {
                    id: emailInputLoader

                    objectName: "loginEmailInputLoader"
                    Layout.fillWidth: true
                    active: root._registerContentRequested || !root._isLogin
                    visible: !root._isLogin
                    sourceComponent: LineEditCore {
                        inputType: Enums.input.type_normal
                        placeholderText: {
                            root._translationVersion
                            return Translator.tr("email")
                        }
                        enabled: !root.loading

                        onAccepted: passwordInput.forceActiveFocus()
                    }
                }
                
                // Password field 密码字段
                LineEditCore {
                    id: passwordInput
                    Layout.fillWidth: true
                    inputType: Enums.input.type_password
                    placeholderText: {
                        root._translationVersion
                        return Translator.tr("password")
                    }
                    enabled: !root.loading
                    
                    onAccepted: {
                        if (root._isLogin) root._submitForm()
                        else if (root._confirmPasswordInput) {
                            root._confirmPasswordInput.forceActiveFocus()
                        }
                    }
                }
                
                // Confirm password (register only) 确认密码（仅注册）
                Loader {
                    id: confirmPasswordInputLoader

                    objectName: "loginConfirmPasswordInputLoader"
                    Layout.fillWidth: true
                    active: root._registerContentRequested || !root._isLogin
                    visible: !root._isLogin
                    sourceComponent: LineEditCore {
                        inputType: Enums.input.type_password
                        placeholderText: {
                            root._translationVersion
                            return Translator.tr("confirm_password")
                        }
                        enabled: !root.loading

                        onAccepted: root._submitForm()
                    }
                }
                
                // Password strength indicator 密码强度指示器
                Loader {
                    id: passwordStrengthLoader

                    objectName: "loginPasswordStrengthLoader"
                    Layout.fillWidth: true
                    active: root._registerContentRequested || !root._isLogin
                    visible: !root._isLogin && root.showPasswordStrength && passwordInput.text.length > 0
                    sourceComponent: PasswordStrengthIndicator {
                        password: passwordInput.text
                    }
                }
            }
            
            // Remember-me and forgot-password actions. 记住我与忘记密码操作。
            Loader {
                id: loginOptionsLoader

                objectName: "loginOptionsLoader"
                Layout.fillWidth: true
                Layout.minimumWidth: implicitWidth
                active: root._isLogin || root._loginContentRequested
                visible: root._isLogin
                sourceComponent: RowLayout {
                    property alias rememberMeCheck: rememberMeCheck

                    // Remember me 记住我
                    CheckBox {
                        id: rememberMeCheck
                        text: {
                            root._translationVersion
                            return Translator.tr("remember_me")
                        }
                        visible: root.rememberMeEnabled
                        enabled: !root.loading
                    }

                    Item { Layout.fillWidth: true }

                    // Forgot password 忘记密码
                    Text {
                        text: {
                            root._translationVersion
                            return Translator.tr("forgot_password")
                        }
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

                onLoaded: root._loginContentRequested = true
            }
            
            // Submit button. 提交按钮。
            ButtonCore {
                Layout.fillWidth: true
                Layout.preferredHeight: Enums.controlSize.buttonHeight
                text: {
                    root._translationVersion
                    return root.loading ? root.loadingText
                        : (root._isLogin ? Translator.tr("sign_in")
                                         : Translator.tr("sign_up"))
                }
                style: Enums.button.style_primary
                loading: root.loading
                enabled: !root.loading && root._isFormValid()
                
                onClicked: root._submitForm()
            }
            
            // OAuth divider. OAuth 分隔线。
            RowLayout {
                Layout.fillWidth: true
                visible: root._safeOauthProviders.length > 0
                spacing: Enums.spacing.m

                Separator {
                    Layout.fillWidth: true
                }

                Text {
                    text: {
                        root._translationVersion
                        return Translator.tr("or_continue_with")
                    }
                    font.family: Enums.fontFamily
                    font.pixelSize: Enums.typography.caption
                    color: Enums.secondaryForeground
                }

                Separator {
                    Layout.fillWidth: true
                }
            }
            
            // OAuth buttons. OAuth 按钮。
            RowLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignHCenter
                spacing: Enums.spacing.m
                visible: root._safeOauthProviders.length > 0
                
                Repeater {
                    model: root._safeOauthProviders
                    
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
            
            // Mode switch. 模式切换。
            RowLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignHCenter
                spacing: Enums.spacing.xs
                
                Text {
                    text: {
                        root._translationVersion
                        return root._isLogin
                            ? Translator.tr("no_account")
                            : Translator.tr("already_have_account")
                    }
                    font.family: Enums.fontFamily
                    font.pixelSize: Enums.typography.bodySmall
                    color: Enums.secondaryForeground
                }
                
                Text {
                    text: {
                        root._translationVersion
                        return root._isLogin ? Translator.tr("sign_up")
                                             : Translator.tr("sign_in")
                    }
                    font.family: Enums.fontFamily
                    font.pixelSize: Enums.typography.bodySmall
                    font.bold: true
                    color: Enums.accentColor
                    
                    MouseArea {
                        objectName: "loginModeToggleArea"
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        enabled: !root.loading
                        hoverEnabled: true

                        onEntered: root._prewarmAlternateModeContent()
                        onClicked: root._toggleMode()
                    }
                }
            }
        }
    }
    
    // Mode-switch animation. 模式切换动画。
    Behavior on mode {
        NumberAnimation { duration: Enums.duration.fast }
    }
}
