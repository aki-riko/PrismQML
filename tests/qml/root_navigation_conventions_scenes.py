# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QML scene data strings used by root_navigation_conventions_shared."""

SCENE_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML

Window {
    id: root
    objectName: "window"

    readonly property int viewModelCount: navigationView.model.length
    readonly property string viewCurrentKey: navigationView.currentKey
    readonly property bool viewExpanded: navigationView.isExpanded
    readonly property bool viewCompact: navigationView.isCompact
    readonly property int navigationScrollDuration: Enums.duration.navigationScroll
    readonly property real defaultScrollStep: Enums.spacing.navigationScrollStep
    readonly property bool barSmoothScroll: navigationBar.smoothScroll
    readonly property bool toggleSmoothScroll: toggleBar.smoothScroll
    readonly property int barScrollDuration: navigationBar.scrollDuration
    readonly property int toggleScrollDuration: toggleBar.scrollDuration

    function expandView() { navigationView.expand() }
    function collapseView() { navigationView.collapse() }
    function toggleView() { navigationView.toggle() }
    function selectViewProfile() { navigationView.setCurrentItem("profile") }
    function addViewDynamic() {
        navigationView.addItem("dynamic", "", "Dynamic", null, true, "", "top")
    }
    function removeViewDynamic() { navigationView.removeWidget("dynamic") }
    function smoothScrollNavigationBar() { navigationBar.smoothScrollBy(120) }
    function beginLazyIndicatorSwitch() {
        navigationView.delayIndicatorAnimation = true
        navigationView._isPageLoading = true
        navigationView.currentIndex = 2
    }
    function finishLazyIndicatorSwitch() {
        navigationView._isPageLoading = false
        navigationView.playPendingIndicatorAnimation()
    }
    function smoothScrollToggleBar() { toggleBar.smoothScrollBy(toggleBar.scrollStep) }

    width: 900
    height: 420
    visible: true

    NavigationView {
        id: navigationView
        objectName: "navigationView"
        width: isExpanded ? implicitWidth : Enums.controlSize.navPanelCompactWidth
        height: parent.height
        showReturnButton: false
        indicatorAnimationEnabled: false
        model: [
            { "key": "home", "text": "Home" },
            { "key": "profile", "text": "Profile" },
            { "key": "reports", "text": "Reports" }
        ]
        bottomItems: [
            { "key": "settings", "text": "Settings", "selectable": true },
            { "text": "Help", "selectable": false }
        ]
        _bottomPageIndexMap: ({ "settings": 3 })
    }

    NavigationBar {
        id: navigationBar
        objectName: "navigationBar"
        x: 300
        width: implicitWidth
        height: parent.height
        indicatorAnimationEnabled: false
        model: [
            { "key": "one", "text": "One" },
            { "key": "two", "text": "Two" },
            { "key": "three", "text": "Three" },
            { "key": "four", "text": "Four" },
            { "key": "five", "text": "Five" },
            { "key": "six", "text": "Six" },
            { "key": "seven", "text": "Seven" },
            { "key": "eight", "text": "Eight" },
            { "key": "nine", "text": "Nine" }
        ]
        bottomItems: [{ "key": "bar-settings", "text": "Settings", "selectable": true }]
        _bottomPageIndexMap: ({ "bar-settings": 6 })
    }

    ToggleNavigationBar {
        id: toggleBar
        objectName: "toggleNavigationBar"
        x: 430
        y: 20
        width: 260
        height: 300
        model: [
            { "key": "alpha", "text": "Alpha" },
            { "key": "beta", "text": "Beta" },
            { "key": "gamma", "text": "Gamma" },
            { "key": "delta", "text": "Delta" },
            { "key": "epsilon", "text": "Epsilon" },
            { "key": "zeta", "text": "Zeta" },
            { "key": "eta", "text": "Eta" },
            { "key": "theta", "text": "Theta" }
        ]
        bottomItems: [{ "key": "toggle-settings", "text": "Settings", "selectable": true }]
        _bottomPageIndexMap: ({ "toggle-settings": 3 })
    }
}
"""

HIDDEN_ITEMS_SOURCE = b"""
import QtQuick
import QtQuick.Window
import PrismQML
import "../../prismqml/PrismQML/navigation"

Window {
    width: 1200
    height: 520
    visible: true

    NavigationView {
        id: hiddenView
        objectName: "hiddenView"
        width: 300
        height: parent.height
        isExpanded: true
        showReturnButton: false
        indicatorAnimationEnabled: false
        model: [
            { "key": "view-home", "text": "View Home" },
            { "key": "view-hidden", "text": "View Hidden", "visible": false },
            { "key": "view-settings", "text": "View Settings" }
        ]
        bottomItems: [
            { "key": "view-account", "text": "View Account", "selectable": true },
            { "key": "view-hidden-bottom", "text": "View Hidden Bottom", "selectable": true, "visible": false },
            { "key": "view-about", "text": "View About", "selectable": true }
        ]
        _bottomPageIndexMap: ({
            "view-account": 3,
            "view-hidden-bottom": 4,
            "view-about": 5
        })
    }

    NavigationBar {
        id: hiddenBar
        objectName: "hiddenBar"
        x: 340
        width: implicitWidth
        height: parent.height
        indicatorAnimationEnabled: false
        model: [
            { "key": "bar-home", "text": "Bar Home" },
            { "key": "bar-hidden", "text": "Bar Hidden", "visible": false },
            { "key": "bar-settings", "text": "Bar Settings" }
        ]
        bottomItems: [
            { "key": "bar-account", "text": "Bar Account", "selectable": true },
            { "key": "bar-hidden-bottom", "text": "Bar Hidden Bottom", "selectable": true, "visible": false },
            { "key": "bar-about", "text": "Bar About", "selectable": true }
        ]
        _bottomPageIndexMap: ({
            "bar-account": 3,
            "bar-hidden-bottom": 4,
            "bar-about": 5
        })
    }

    ToggleNavigationBar {
        id: hiddenToggle
        objectName: "hiddenToggle"
        x: 460
        y: 20
        width: 300
        height: 360
        model: [
            { "key": "toggle-home", "text": "Toggle Home" },
            { "key": "toggle-hidden", "text": "Toggle Hidden", "visible": false },
            { "key": "toggle-settings", "text": "Toggle Settings" }
        ]
        bottomItems: [
            { "key": "toggle-account", "text": "Toggle Account", "selectable": true },
            { "key": "toggle-hidden-bottom", "text": "Toggle Hidden Bottom", "selectable": true, "visible": false },
            { "key": "toggle-about", "text": "Toggle About", "selectable": true }
        ]
        _bottomPageIndexMap: ({
            "toggle-account": 3,
            "toggle-hidden-bottom": 4,
            "toggle-about": 5
        })
    }

    BottomTabBar {
        id: hiddenTabs
        objectName: "hiddenTabs"
        x: 800
        y: 20
        width: 360
        model: [
            { "key": "tab-home", "text": "Tab Home" },
            { "key": "tab-hidden", "text": "Tab Hidden", "visible": false },
            { "key": "tab-about", "text": "Tab About" }
        ]
    }
}
"""
