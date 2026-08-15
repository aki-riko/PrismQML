// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick.Effects
import "../../.."
import "../../navigation/_internal" as NavigationInternal
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
    property int iconSize: Enums.splashScreenMetrics.iconSize  // Icon size 图标尺寸
    property bool enableShadow: true                 // Enable icon shadow 启用图标阴影
    property alias titleBar: titleBarLoader.sourceComponent  // Custom title bar 自定义标题栏
    property bool showTitleBar: Qt.platform.os !== "osx"  // Show title bar (hidden on macOS) 显示标题栏

    // New: Text props 新增文本属性
    property string title: ""                        // App title 应用标题
    property string subtitle: ""                     // Subtitle or loading text 副标题或加载文字
    property bool showProgress: true                 // Show progress ring 显示进度环

    // ==================== Internal Props 内部属性 ====================
    readonly property color _splashBackground: Enums.backgroundColor
    readonly property color _progressColor: Enums.accentColor
    readonly property int _progressRingSize: Enums.splashScreenMetrics.progressRingSize
    readonly property real _progressRingBorderWidth: Enums.splashScreenMetrics.progressRingBorderWidth
    readonly property real _progressTrackOpacity: Enums.splashScreenMetrics.progressTrackOpacity
    readonly property int _progressDotSize: Enums.splashScreenMetrics.progressDotSize
    readonly property int _progressDotRadius: Enums.splashScreenMetrics.progressDotRadius
    readonly property int _progressDotTopMargin: Enums.splashScreenMetrics.progressDotTopMargin
    readonly property real _iconShadowBlur: Enums.splashScreenMetrics.iconShadowBlur
    readonly property int _iconShadowOffset: Enums.splashScreenMetrics.iconShadowOffset
    readonly property real _iconBreatheMinScale: Enums.splashScreenMetrics.iconBreatheMinScale
    readonly property real _iconBreatheMaxScale: Enums.splashScreenMetrics.iconBreatheMaxScale
    property bool _finishing: false

    // ==================== Signals 信号 ====================
    signal finished()  // Emitted when splash screen is closed 启动画面关闭时触发

    // ==================== Public Methods 公开方法 ====================
    // Close splash screen 关闭启动画面
    function finish() {
        if (control._finishing)
            return
        lazyExitLoader.active = true
        if (!lazyExitLoader.item) {
            console.error('SplashScreen: failed to create the lazy switch exit')
            return
        }
        control._finishing = true
        breatheAnim.stop()
        lazyExitLoader.item.collapse(control)
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

    // ==================== Size 尺寸 ====================
    anchors.fill: parent
    // Match the Gallery host: cover the whole window shell during startup.
    // 与 Gallery 宿主保持一致：启动期间覆盖整个窗口壳。
    z: Enums.zIndex.splash
    color: Enums.transparent
    visible: true
    clip: true
    // Keep the complete splash stable from the first rendered frame; only
    // the icon participates in the continuous breathing animation.
    // 从首个渲染帧起稳定显示完整启动画面；仅图标参与循环呼吸动画。
    opacity: 1
    Component.onCompleted: breatheAnim.start()

    // A single rectangle preserves the complete first frame before exit.
    // 单个矩形在退场前保持完整首帧背景。
    Rectangle {
        id: solidBackground

        objectName: "splashSolidBackground"
        anchors.fill: parent
        color: control._splashBackground
    }

    // Breathe animation 呼吸动画
    SequentialAnimation {
        id: breatheAnim
        loops: Animation.Infinite

        NumberAnimation {
            target: iconContainer
            property: "scale"
            to: control._iconBreatheMaxScale
            duration: Enums.duration.splashBreathe
            easing.type: Easing.InOutSine
        }
        NumberAnimation {
            target: iconContainer
            property: "scale"
            to: control._iconBreatheMinScale
            duration: Enums.duration.splashBreathe
            easing.type: Easing.InOutSine
        }
    }

    // Title bar 标题栏
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
            height: Enums.window.titleBarHeight
            color: Enums.transparent
        }
    }

    // ==================== Content 内容 ====================
    Column {
        id: contentColumn

        objectName: "splashContent"
        anchors.centerIn: parent
        opacity: 1
        transformOrigin: Item.Center
        spacing: Enums.spacing.xl

        // Icon Container 图标容器
        Item {
            id: iconContainer

            objectName: "splashIconContainer"
            anchors.horizontalCenter: parent.horizontalCenter
            width: control.iconSize
            height: control.iconSize
            transformOrigin: Item.Center
            layer.enabled: control.enableShadow && !Enums.isVintageTicket
            layer.effect: MultiEffect {
                shadowEnabled: true
                shadowColor: Enums.shadowStrongColor
                shadowBlur: Enums.shadow.splashIcon.blurNormalized
                shadowVerticalOffset: Enums.shadow.splashIcon.offset
            }

            // Create only the selected icon renderer. 仅创建当前选中的图标渲染器。
            Loader {
                id: iconDisplayLoader

                anchors.fill: parent
                active: control.iconSource !== "" || (control.icon !== null && control.icon !== undefined)
                sourceComponent: control.iconSource !== "" ? imageDisplayComponent : fluentIconDisplayComponent
            }

            Component {
                id: fluentIconDisplayComponent

                Icon {
                    objectName: "splashFluentIconDisplay"
                    anchors.centerIn: parent
                    icon: control.icon
                    iconSize: control.iconSize
                }
            }

            Component {
                id: imageDisplayComponent

                Image {
                    objectName: "splashImageDisplay"
                    anchors.centerIn: parent
                    width: control.iconSize
                    height: control.iconSize
                    source: control.iconSource
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                }
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

            // Standard progress ring 标准进度环
            ProgressRing {
                objectName: "splashProgressRing"
                width: control._progressRingSize
                height: control._progressRingSize
                visible: control.showProgress
                anchors.verticalCenter: parent.verticalCenter
                indeterminate: true
                indeterminateStyle: Enums.progress.indeterminate_style_orbit_dot
                paused: !control.visible || !control.showProgress
                strokeWidth: control._progressRingBorderWidth
                spinDuration: Enums.duration.splashProgressSpin
                indeterminateDotSize: control._progressDotSize
                indeterminateDotRadius: control._progressDotRadius
                indeterminateDotTopMargin: control._progressDotTopMargin
                color: control._progressColor
                trackColorLight: Qt.rgba(control._progressColor.r, control._progressColor.g, control._progressColor.b, control._progressTrackOpacity)
                trackColorDark: trackColorLight
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

    // Create the shared lazy-switch transition only when finish starts.
    // 仅在开始退场时创建共享懒加载切换过渡。
    Loader {
        id: lazyExitLoader

        objectName: "splashLazyTransitionLoader"
        anchors.fill: parent
        active: false
        asynchronous: false

        sourceComponent: NavigationInternal.LazyPageCircleTransition {
            objectName: "splashLazyPageCircleTransition"

            onCollapseFinished: {
                control.visible = false
                control.finished()
            }
        }
    }
}
