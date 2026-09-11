# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Startup splash QML template data owned by _fast_splash_qml.

Pure `.format` template strings only; logic stays in fast_splash.py.
启动闪屏的 .format 模板字符串数据；逻辑仍归 fast_splash.py。
"""

_SPLASH_QML = """
import QtQuick

Window {{
    id: win
    width: {splash_width}; height: {splash_height}
    flags: Qt.SplashScreen | Qt.FramelessWindowHint
    color: "transparent"
    // The controller shows the window after the object tree and metadata are ready.
    // 由控制器在对象树和元数据准备完成后显示窗口，避免构造期间提交空白帧。
    visible: false

    property string splashIcon: ""
    property string splashTitle: "PrismQML"
    property string splashSubtitle: "{splash_subtitle}"

    property Item revealRoot: revealSurface
    readonly property string layerState:
        "enabled=" + revealSurface.layer.enabled
        + " effect=" + (revealSurface.layer.effect ? "set" : "null")
        + " smooth=" + revealSurface.layer.smooth
    property var revealTransition: null
    readonly property bool revealRingActive:
        revealTransition ? revealTransition.active : false

    Item {{
        id: revealSurface
        anchors.fill: parent
        property bool spinnerVisible: true

        Rectangle {{
            anchors.fill: parent
            radius: 8
            color: "{background}"
        }}

        Column {{
            anchors.centerIn: parent
            spacing: 16

            Item {{
                id: iconContainer
                anchors.horizontalCenter: parent.horizontalCenter
                width: 102; height: 102

                Image {{
                    anchors.centerIn: parent
                    width: 102; height: 102
                    source: win.splashIcon
                    sourceSize.width: 102
                    sourceSize.height: 102
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                    asynchronous: false
                    visible: source !== ""
                }}

                SequentialAnimation {{
                    running: true
                    loops: Animation.Infinite
                    NumberAnimation {{
                        target: iconContainer; property: "scale"
                        to: 1.1; duration: 1200
                        easing.type: Easing.InOutQuad
                    }}
                    NumberAnimation {{
                        target: iconContainer; property: "scale"
                        to: 0.9; duration: 1200
                        easing.type: Easing.InOutQuad
                    }}
                }}
            }}

            Text {{
                anchors.horizontalCenter: parent.horizontalCenter
                text: win.splashTitle
                color: "{title_color}"
                font.family: "Microsoft YaHei UI"
                font.pixelSize: 20
                font.weight: 600
            }}

            Row {{
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 8

                Item {{
                    width: 20; height: 20
                    anchors.verticalCenter: parent.verticalCenter

                    Rectangle {{
                        anchors.fill: parent
                        radius: width / 2
                        color: "transparent"
                        border.width: 2
                        border.color: "#ff0e5a9c"
                        opacity: 0.3
                    }}

                    Item {{
                        id: spinner
                        anchors.fill: parent
                        visible: revealSurface.spinnerVisible

                        Rectangle {{
                            width: 6; height: 6
                            radius: 2
                            color: "#ff0e5a9c"
                            x: parent.width / 2 - width / 2
                            y: -1
                        }}

                        // Render-thread animation keeps moving while the main
                        // QML engine creates its page tree.
                        // 渲染线程动画确保主 QML 引擎创建页面树时小圈仍在转动。
                        RotationAnimator on rotation {{
                            running: true
                            loops: Animation.Infinite
                            from: 0; to: 360; duration: 1000
                        }}
                    }}
                }}

                Text {{
                    anchors.verticalCenter: parent.verticalCenter
                    text: win.splashSubtitle
                    color: "{body_color}"
                    font.family: "Microsoft YaHei UI"
                    font.pixelSize: 14
                }}
            }}
        }}
    }}

    Rectangle {{
        id: revealRing
        property real radiusPx: win.revealTransition
            ? win.revealTransition.revealRadiusPixels : 8
        x: parent.width * 0.5 - radiusPx
        y: parent.height * 0.5 - radiusPx
        width: radiusPx * 2
        height: radiusPx * 2
        radius: width * 0.5
        color: "transparent"
        border.width: 2
        border.color: "#ff0e5a9c"
        opacity: 0.72
        visible: win.revealRingActive
        z: 100
    }}
}}
"""

_REVEAL_QML = """
import QtQuick
import "{root_url}"

PageTransition {{
    id: transition
    objectName: "fastStartupReveal"
    anchors.fill: parent
    revealTarget: true
    // revealDuration and revealEasing intentionally unset: inherit the shared
    // lazy switch exit pacing from PageTransition instead of pinning private
    // values here, so the splash exit and the page switch exit stay identical.
    // 故意不设时长与缓动两个属性, 改为继承 PageTransition 的共用懒加载退场节奏,
    // 不在此另立私有值, 使启动画面退场与页面切换退场完全一致。
    keepSourceHiddenOnExpand: true
    property Item revealTargetItem: null
    signal revealDone()

    onExpandFinished: {{
        transition.revealDone()
    }}

    function go() {{ return transition.expand(transition.revealTargetItem) }}
}}
"""
