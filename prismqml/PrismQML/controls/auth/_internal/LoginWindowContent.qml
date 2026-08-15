// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Layouts
import "../../.."
import "../../../effects"
import "../../buttons/Button"
import "../../inputs/LineEdit"
import "../../inputs/Toggle"
import "../../inputs"
import "../../icons"

// LoginWindowContent - Login window visual and form content 登录窗口视觉与表单内容
Item {
    id: contentLayer

    // ==================== Required Props 必需属性 ====================
    required property var loginControl

    // ==================== Public Props 公开属性 ====================
    property alias matrixRain: matrixRain
    property alias usernameInput: usernameInput
    property alias emailInputLoader: emailInputLoader
    property alias passwordInput: passwordInput
    property alias confirmPasswordInputLoader: confirmPasswordInputLoader
    property alias passwordStrengthLoader: passwordStrengthLoader
    property alias loginOptionsLoader: loginOptionsLoader

    // ==================== Readonly State 只读状态 ====================
    readonly property var control: loginControl

    anchors.fill: parent

    // Matrix rain background. 矩阵雨背景。
    MatrixRain {
        id: matrixRain

        objectName: "loginMatrixRain"
        anchors.fill: parent
        running: control.matrixEnabled && control.visible && !Enums.isVintageTicket
        visible: !Enums.isVintageTicket
        speed: control.matrixSpeed
        density: control.matrixDensity
        glowEnabled: control.matrixGlow
        glowIntensity: 1.2

        Component.onCompleted: setTheme(control.matrixTheme)
    }

    // Center card. 中心卡片。
    ShadowedRectangle {
        id: card

        width: control.cardWidth
        height: cardContent.height + Enums.spacing.xxl * 2
        anchors.centerIn: parent
        radius: control._cardRadius
        color: control._cardBackgroundColor
        border.width: control._cardBorderWidth
        border.color: control._cardBorderColor

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
                    source: control.logoSource
                    visible: control.logoSource !== ""
                    fillMode: Image.PreserveAspectFit
                }

                // Logo text 标志文字
                Text {
                    anchors.centerIn: parent
                    text: control.logoText
                    font.family: Enums.fontFamily
                    font.pixelSize: Enums.typography.display
                    font.bold: true
                    color: Enums.accentColor
                    visible: control.logoSource === ""
                }
            }

            // Title area. 标题区域。
            ColumnLayout {
                Layout.fillWidth: true
                spacing: Enums.spacing.xs

                Text {
                    Layout.fillWidth: true
                    text: control.title
                    font.family: Enums.fontFamily
                    font.pixelSize: Enums.typography.title
                    font.bold: true
                    color: Enums.foregroundColor
                    horizontalAlignment: Text.AlignHCenter
                }

                Text {
                    Layout.fillWidth: true
                    text: control.subtitle
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
                radius: control._errorRadius
                color: control._errorBackgroundColor
                border.width: control._errorBorderWidth
                border.color: control._errorBorderColor
                visible: control.errorMessage !== ""

                Text {
                    id: errorText

                    anchors.centerIn: parent
                    width: parent.width - Enums.spacing.m * 2
                    text: control.errorMessage
                    font.family: Enums.fontFamily
                    font.pixelSize: Enums.typography.bodySmall
                    color: control._errorTextColor
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
                        control._translationVersion
                        return control._isLogin
                            ? Translator.tr("username_or_email")
                            : Translator.tr("username")
                    }
                    enabled: !control.loading

                    onAccepted: {
                        if (control._isLogin) passwordInput.forceActiveFocus()
                        else emailInput.forceActiveFocus()
                    }
                }

                // Email field (register only) 邮箱字段（仅注册）
                Loader {
                    id: emailInputLoader

                    objectName: "loginEmailInputLoader"
                    Layout.fillWidth: true
                    active: control._registerContentRequested || !control._isLogin
                    visible: !control._isLogin
                    sourceComponent: LineEditCore {
                        inputType: Enums.input.type_normal
                        placeholderText: {
                            control._translationVersion
                            return Translator.tr("email")
                        }
                        enabled: !control.loading

                        onAccepted: passwordInput.forceActiveFocus()
                    }
                }

                // Password field 密码字段
                LineEditCore {
                    id: passwordInput

                    Layout.fillWidth: true
                    inputType: Enums.input.type_password
                    placeholderText: {
                        control._translationVersion
                        return Translator.tr("password")
                    }
                    enabled: !control.loading

                    onAccepted: {
                        if (control._isLogin) control._submitForm()
                        else if (control._confirmPasswordInput) {
                            control._confirmPasswordInput.forceActiveFocus()
                        }
                    }
                }

                // Confirm password (register only) 确认密码（仅注册）
                Loader {
                    id: confirmPasswordInputLoader

                    objectName: "loginConfirmPasswordInputLoader"
                    Layout.fillWidth: true
                    active: control._registerContentRequested || !control._isLogin
                    visible: !control._isLogin
                    sourceComponent: LineEditCore {
                        inputType: Enums.input.type_password
                        placeholderText: {
                            control._translationVersion
                            return Translator.tr("confirm_password")
                        }
                        enabled: !control.loading

                        onAccepted: control._submitForm()
                    }
                }

                // Password strength indicator 密码强度指示器
                Loader {
                    id: passwordStrengthLoader

                    objectName: "loginPasswordStrengthLoader"
                    Layout.fillWidth: true
                    active: control._registerContentRequested || !control._isLogin
                    visible: !control._isLogin && control.showPasswordStrength &&
                        passwordInput.text.length > 0
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
                active: control._isLogin || control._loginContentRequested
                visible: control._isLogin
                sourceComponent: RowLayout {
                    property alias rememberMeCheck: rememberMeCheck

                    // Remember me 记住我
                    CheckBox {
                        id: rememberMeCheck

                        text: {
                            control._translationVersion
                            return Translator.tr("remember_me")
                        }
                        visible: control.rememberMeEnabled
                        enabled: !control.loading
                    }

                    Item { Layout.fillWidth: true }

                    // Forgot password 忘记密码
                    Text {
                        text: {
                            control._translationVersion
                            return Translator.tr("forgot_password")
                        }
                        font.family: Enums.fontFamily
                        font.pixelSize: Enums.typography.bodySmall
                        color: Enums.accentColor
                        visible: control.forgotPasswordEnabled

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            enabled: !control.loading
                            onClicked: control.forgotPasswordClicked()
                        }
                    }
                }

                onLoaded: control._loginContentRequested = true
            }

            // Submit button. 提交按钮。
            ButtonCore {
                Layout.fillWidth: true
                Layout.preferredHeight: Enums.controlSize.buttonHeight
                text: {
                    control._translationVersion
                    return control.loading ? control.loadingText
                        : (control._isLogin ? Translator.tr("sign_in")
                                            : Translator.tr("sign_up"))
                }
                style: Enums.button.style_primary
                loading: control.loading
                enabled: !control.loading && control._isFormValid()

                onClicked: control._submitForm()
            }

            // OAuth divider. OAuth 分隔线。
            RowLayout {
                Layout.fillWidth: true
                visible: control._safeOauthProviders.length > 0
                spacing: Enums.spacing.m

                Separator {
                    Layout.fillWidth: true
                }

                Text {
                    text: {
                        control._translationVersion
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
                visible: control._safeOauthProviders.length > 0

                Repeater {
                    model: control._safeOauthProviders

                    ButtonCore {
                        required property int modelData

                        Layout.preferredWidth: 100
                        Layout.preferredHeight: Enums.controlSize.buttonHeight
                        text: Enums.auth.getOAuthName(modelData)
                        icon: Enums.auth.getOAuthIcon(modelData)
                        style: Enums.button.style_default
                        enabled: !control.loading

                        onClicked: control.oauthRequested(modelData)
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
                        control._translationVersion
                        return control._isLogin
                            ? Translator.tr("no_account")
                            : Translator.tr("already_have_account")
                    }
                    font.family: Enums.fontFamily
                    font.pixelSize: Enums.typography.bodySmall
                    color: Enums.secondaryForeground
                }

                Text {
                    text: {
                        control._translationVersion
                        return control._isLogin ? Translator.tr("sign_up")
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
                        enabled: !control.loading
                        hoverEnabled: true

                        onEntered: control._prewarmAlternateModeContent()
                        onClicked: control._toggleMode()
                    }
                }
            }
        }
    }
}
