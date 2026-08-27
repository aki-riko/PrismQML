// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import ".."
import "../controls/containers"
import "../controls/feedback"

// WindowsPageStack - Shared page stack and lazy-loading overlay for window shells
// WindowsPageStack - 三种窗口外壳共用的页面栈与懒加载覆盖层
//
// Single owner of the StackedWidget bindings, the overlay Loader lifecycle and the
// host signal forwarding. WindowsFilled, WindowsSplit and WindowsBarContent kept
// three copies of this that differed only in the navigation id they read, whether
// the host may be null, and where the loading text comes from. Those three are
// parameters here; the loading state machine itself stays in
// NavigationWindowLoading.js, which this only forwards into.
// StackedWidget 绑定、overlay Loader 生命周期与宿主信号转发的唯一归属。
// WindowsFilled、WindowsSplit、WindowsBarContent 原先各持一份，差异只有读哪个
// 导航 id、宿主是否可为空、文案来源三点，这三点在此参数化。loading 状态机本身
// 仍在 NavigationWindowLoading.js，此处只做转发。
Item {
    id: root

    // ==================== Public Props 公开属性 ====================
    // Host window. May be null while a bar-style shell has no host yet.
    // 宿主窗口。栏式外壳尚无宿主时可为 null。
    required property var host
    // Drives lazyActivationDelay. Callers pass their own navigation item's flag.
    // 驱动 lazyActivationDelay，调用方传入自己导航项的开关。
    required property bool navAnimationEnabled
    // Overlay visibility condition, owned by the caller. overlay 显隐条件由调用方持有。
    required property bool overlayActive
    // Loading caption, owned by the caller so translation deps stay there.
    // 文案由调用方持有，翻译依赖因此留在调用方。
    required property string overlayText

    readonly property alias stackAlias: stack
    readonly property alias overlayLoader: loadingOverlayLoader

    anchors.fill: parent

    // ==================== Content 内容 ====================
    StackedWidget {
        id: stack

        anchors.fill: parent
        animationType: Enums.animation.popup
        // Budget measured from collapse start; the helper subtracts the elapsed
        // collapse to get the remaining indicator time. Derived from
        // coverDuration so tuning the collapse cannot starve the indicator.
        // 预算从收紧开始计算, helper 减去已花掉的收紧时长得到剩余指示器时间。
        // 由 coverDuration 推导, 因此调收紧节奏不会饿死指示器。
        lazyActivationDelay: root.navAnimationEnabled
            ? Enums.lazyLoadingTransitionMetrics.coverDuration
              + Enums.lazyLoadingTransitionMetrics.loaderActivationHeadroom
            : Enums.duration.none
        pageSources: root.host ? root.host.pageSources : []
        lazyLoading: root.host ? root.host.lazyLoading : false
        lazyAnimationType: root.host
            && typeof root.host.lazyAnimationType === "number"
                ? root.host.lazyAnimationType : Enums.animation.lazy_circle
        _pythonPageMode: root.host ? root.host._pythonPageMode : false
        // Bind host.currentIndex to stack.currentIndex in one direction.
        // 单向绑定 host.currentIndex 到 stack.currentIndex；内部显示由 _displayIndex 驱动。
        currentIndex: root.host ? root.host.currentIndex : 0
        onCurrentChanged: (index) => {
            // Synchronize back after animation when needed. 动画结束后按需反向同步。
            if (root.host && root.host.currentIndex !== index) {
                root.host.currentIndex = index
            }
        }
        onPythonLazyCollapseFinished: (index) => {
            if (root.host) root.host._handlePythonLazyCollapseFinished(index)
        }
        onPythonLazyExpansionStarted: (index) => {
            if (root.host) root.host._beginPythonLoadingVisualExit(index)
        }
        onPythonLazyTransitionFinished: (index) => {
            if (root.host) root.host._completePythonLoadingVisual(index)
        }
    }

    // Python lazy-loading overlay. Python 懒加载覆盖层。
    Loader {
        id: loadingOverlayLoader

        property bool transitionActive: false

        objectName: "loadingOverlayLoader"
        anchors.fill: parent
        active: root.overlayActive || transitionActive
        asynchronous: false
        onLoaded: {
            transitionActive = false
            if (root.host) {
                root.host._pythonLoadingOverlay = item
                root.host._handlePythonLoadingOverlayReady()
            }
        }
        onItemChanged: {
            if (!item) {
                transitionActive = false
                if (root.host) root.host._pythonLoadingOverlay = null
            }
        }
        sourceComponent: QMLPage {
            property bool loading: root.overlayActive

            objectName: "loadingOverlay"
            backgroundColor: Enums.transparent
            running: visible && !finishing
            text: root.overlayText
            Component.onCompleted: if (loading) start()
            onLoadingChanged: {
                if (loading) start()
                else finish()
            }
        }

        Connections {
            function onFinishingChanged() {
                loadingOverlayLoader.transitionActive = target.finishing
            }

            target: loadingOverlayLoader.item
            ignoreUnknownSignals: true
        }
    }
}
