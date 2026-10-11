// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import QtQuick.Effects

// Import components 导入组件
import PrismQML
import PrismQML as Fluent

// Auth components page 认证组件页面
Item {
    id: root

    ScrollArea {
        anchors.fill: parent

        Column {
            width: parent ? parent.width : 0
            spacing: Fluent.Enums.spacing.xxl

            // Page title 页面标题
            Column {
                width: parent ? parent.width : 0
                spacing: Fluent.Enums.spacing.xs
                Text { text: Fluent.Translator.tr("gallery_d2d648bd1c94b7f9", Fluent.Translator._v); font.pixelSize: Fluent.Enums.typography.displayLarge; font.bold: true; color: Fluent.Enums.textColor.primary; font.family: Fluent.Enums.fontFamily }
            }

            // LoginWindow 登录窗口
            ExampleCard {
                title: Fluent.Translator.tr("gallery_bbf70d40c7b0af6a", Fluent.Translator._v)
                description: "mode / oauthProviders / onLoginRequested / onRegisterRequested"
                ComponentCard {
                    label: Fluent.Translator.tr("gallery_9d256f4ecb417949", Fluent.Translator._v)
                    Column {
                        spacing: Fluent.Enums.spacing.s
                        Button {
                            text: Fluent.Translator.tr("gallery_86f1b8e676e219eb", Fluent.Translator._v)
                            onClicked: loginWindowDemo.visible = true
                        }
                        Text {
                            text: Fluent.Translator.tr("gallery_e6fdcfb8a83eac0f", Fluent.Translator._v)
                            color: Fluent.Enums.textColor.secondary
                            font.family: Fluent.Enums.fontFamily
                            font.pixelSize: Fluent.Enums.typography.caption
                        }
                    }
                }
            }
        }
    }

    // Login window stays hidden until the button opens it 登录窗口在按钮打开前保持隐藏
    LoginWindow {
        id: loginWindowDemo

        visible: false
        onLoginRequested: function(username, password, rememberMe) { loginWindowDemo.visible = false }
        onRegisterRequested: function(username, email, password) { loginWindowDemo.visible = false }
        onOauthRequested: function(provider) { loginWindowDemo.visible = false }
        onForgotPasswordClicked: loginWindowDemo.visible = false
    }
}
