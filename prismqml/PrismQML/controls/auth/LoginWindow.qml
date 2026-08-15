// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../.."
import "_internal"

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
    readonly property int _cardRadius: Enums.surfaceRadius(Enums.radius.large)
    readonly property int _errorRadius: Enums.surfaceRadius(Enums.radius.small)
    readonly property color _cardColor: Enums.cardColor
    readonly property color _cardBackgroundColor: Qt.rgba(
        root._cardColor.r,
        root._cardColor.g,
        root._cardColor.b,
        root.cardOpacity
    )
    readonly property real _cardBorderWidth: Enums.surfaceBorderWidth(Enums.border.thin)
    readonly property color _cardBorderColor: Enums.stateColor.border
    readonly property color _errorBackgroundColor: Enums.statusLevel.getBgColor(Enums.statusLevel.errorStr)
    readonly property real _errorBorderWidth: Enums.border.thin
    readonly property color _errorBorderColor: Enums.statusLevel.getColor(Enums.statusLevel.errorStr)
    readonly property color _errorTextColor: _errorBorderColor
    property bool _registerContentRequested: false
    property bool _loginContentRequested: false
    readonly property var _usernameInput: contentLayer.usernameInput
    readonly property var _emailInput: contentLayer.emailInputLoader.item
    readonly property var _passwordInput: contentLayer.passwordInput
    readonly property var _confirmPasswordInput:
        contentLayer.confirmPasswordInputLoader.item
    readonly property var _rememberMeCheck: contentLayer.loginOptionsLoader.item
        ? contentLayer.loginOptionsLoader.item.rememberMeCheck : null
    
    // ==================== Signals 信号 ====================
    signal loginRequested(string username, string password, bool rememberMe)
    signal registerRequested(string username, string email, string password)
    signal oauthRequested(int provider)
    signal forgotPasswordClicked()
    signal modeToggled(int newMode)  // Renamed to avoid conflict with property change signal 重命名避免与属性变化信号冲突

    // ==================== Internal Methods 内部方法 ====================
    function _isFormValid() {
        if (_isLogin) {
            return root._usernameInput.text.length > 0 &&
                root._passwordInput.text.length > 0
        }
        if (!root._emailInput || !root._confirmPasswordInput) return false
        return root._usernameInput.text.length > 0 &&
               root._emailInput.text.length > 0 &&
               root._passwordInput.text.length > 0 &&
               root._confirmPasswordInput.text.length > 0 &&
               root._passwordInput.text === root._confirmPasswordInput.text
    }

    function _submitForm() {
        if (!_isFormValid()) return

        if (_isLogin) {
            loginRequested(
                root._usernameInput.text,
                root._passwordInput.text,
                root._rememberMeCheck ? root._rememberMeCheck.checked : false
            )
        } else {
            registerRequested(
                root._usernameInput.text,
                root._emailInput.text,
                root._passwordInput.text
            )
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
        root._usernameInput.setText("")
        if (root._emailInput) root._emailInput.setText("")
        root._passwordInput.setText("")
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
        contentLayer.matrixRain.setTheme(theme)
    }

    // Focus username input 聚焦用户名输入框
    function focusUsername() {
        root._usernameInput.forceActiveFocus()
    }

    // Get form data 获取表单数据
    function getFormData() {
        return {
            username: root._usernameInput.text,
            email: root._emailInput ? root._emailInput.text : "",
            password: root._passwordInput.text,
            rememberMe: root._rememberMeCheck
                ? root._rememberMeCheck.checked : false
        }
    }

    color: Enums.isVintageTicket ? Enums.backgroundColor : Enums.transparent

    onModeChanged: {
        if (!root._isLogin) root._prewarmRegisterContent()
        else root._prewarmLoginContent()
    }

    // ==================== Content 内容 ====================
    LoginWindowContent {
        id: contentLayer

        anchors.fill: parent
        loginControl: root
    }

    // Mode-switch animation. 模式切换动画。
    Behavior on mode {
        NumberAnimation { duration: Enums.duration.fast }
    }
}
