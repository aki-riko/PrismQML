// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import "../../menus"
import "../../utils"
import "../../icons"
import "../../containers/ScrollBar"
import "../../containers/Separator"

// ButtonDropdown - Dropdown menu and split button features 下拉菜单功能
// Internal module for Button Button内部模块
Item {
    id: dropdownFeature
    
    // ==================== Required Props 必需属性 ====================
    required property bool isToolButton
    required property int feature
    required property var menuItems
    required property var menu
    required property bool controlEnabled
    required property bool loading
    required property real parentRadius
    required property int fontSize
    required property color textColor  // Parent button text color 父按钮文字颜色

    // ==================== Public Props 公开属性 ====================
    property int parentStyle: 0

    // ==================== Internal Props 内部属性 ====================
    property bool _geometryPrewarmScheduled: false
    property bool _geometryPrepared: false
    property bool _invalidMenuWarningIssued: false
    property bool _menuContentRequested: false
    property int _animationDuration

    readonly property var _safeMenuItems:
        menuItems === null || menuItems === undefined ? []
        : (typeof menuItems.length === "number" ? menuItems : [])
    readonly property bool _hasExternalMenu: menu !== null && menu !== undefined
    readonly property bool _hasMenuContent: _hasExternalMenu || _safeMenuItems.length > 0

    // ==================== Readonly State 只读状态 ====================
    // Expose menu open state for arrow animation 暴露菜单打开状态供箭头动画使用
    readonly property bool isMenuOpen: _hasExternalMenu && typeof menu.isOpen === "boolean"
        ? menu.isOpen : dropDownMenu.isOpen
    // Expose hover states for parent button color calculation 暴露悬浮状态供父按钮颜色计算
    readonly property bool mainHovered: splitMainMouse.containsMouse
    readonly property bool mainPressed: splitMainMouse.pressed
    readonly property bool dropHovered: splitDropMouse.containsMouse
    readonly property bool dropPressed: splitDropMouse.pressed

    // Check if style uses accent foreground (white text/icon) 检查是否使用强调前景色（白色文字/图标）
    readonly property bool _useAccentForeground: parentStyle === Enums.button.style_primary ||
                                                  parentStyle === Enums.button.style_filled ||
                                                  parentStyle === Enums.button.style_gradient

    // Split button hover/pressed colors based on parent style Split按钮悬浮/按下颜色
    // For accent styles (primary/filled/gradient): use on-accent overlays 强调样式用主色上状态层
    // For other styles: use transparent button colors 其他样式用透明按钮颜色
    readonly property color _splitHoverColor: _useAccentForeground
        ? Enums.stateColor.onAccentHoverOverlay
        : Enums.stateColor.transparentHover
    readonly property color _splitPressedColor: _useAccentForeground
        ? Enums.stateColor.onAccentPressedOverlay
        : Enums.stateColor.transparentPressed
    readonly property color _splitTransparent: _useAccentForeground
        ? Enums.stateColor.whiteTransparent
        : Enums.stateColor.controlBgTransparent

    // Arrow color based on parent style 箭头颜色
    readonly property color _arrowColor: {
        if (!dropdownFeature.controlEnabled) return Enums.stateColor.indicatorActive
        if (_useAccentForeground) return Enums.accentForeground
        return Enums.textColor.secondary
    }

    // Separator line color 分隔线颜色
    readonly property color _separatorColor: _useAccentForeground
        ? Enums.stateColor.onAccentOverlay
        : Enums.stateColor.separator

    // ==================== Signals 信号 ====================
    signal menuItemClicked(int index, string text)
    signal mainButtonClicked()
    signal menuAboutToOpen()

    // ==================== Public Methods 公开方法 ====================
    function prewarmMenu() {
        if (controlEnabled && !loading && _hasMenuContent) {
            if (_hasExternalMenu) {
                if (!_externalMenuIsValid()) {
                    _warnInvalidExternalMenu()
                    return
                }
                menu.prewarm()
                return
            }
            if (!_geometryPrewarmScheduled) {
                _geometryPrewarmScheduled = true
                geometryPrewarmTimer.start()
            }
            _menuContentRequested = true
            dropDownMenu.prewarm()
        }
    }

    // Calculate max content width from menu items (imperative, avoid binding loop)
    // 根据菜单项计算最大内容宽度（命令式调用，避免绑定循环）
    function _calcContentWidth() {
        _menuContentRequested = true
        var textMeasure = menuContentLoader.item
                          ? menuContentLoader.item.textMeasure : null
        if (!textMeasure) return 0
        var maxW = 0
        // Total horizontal padding: contentContainer margins(xs*2) + itemBg margins(xs*2) + text margins(l*2)
        // 总水平内边距：内容容器边距(xs*2) + 项背景边距(xs*2) + 文本边距(l*2)
        var itemPadding = Enums.spacing.l * 2 + Enums.spacing.xs * 4
        // Check if any item has icon 检查是否有图标项
        var hasIcon = false
        for (var i = 0; i < _safeMenuItems.length; i++) {
            var item = _safeMenuItems[i]
            if (item && typeof item === "object" && item.icon && item.icon !== "") {
                hasIcon = true
                break
            }
        }
        // Add icon space if any item has icon 有图标时加上图标占位空间
        var iconSpace = hasIcon ? (Enums.iconSize.m + Enums.spacing.m) : 0
        for (var j = 0; j < _safeMenuItems.length; j++) {
            var mi = _safeMenuItems[j]
            var text = mi && typeof mi === "object" ? (mi.text || mi) : (mi || "")
            if (text === "-") continue  // Skip separator 跳过分隔线
            textMeasure.text = text
            maxW = Math.max(maxW, textMeasure.advanceWidth + itemPadding + iconSpace)
        }
        return Math.ceil(maxW)
    }

    function _updatePopupWidth() {
        var contentW = _calcContentWidth()
        // Keep dropdown and split menus at least as wide as their parent button.
        // 下拉与分离按钮菜单最小宽度均与父按钮一致。
        dropDownMenu.popupWidth = Math.max(contentW, parent.width)
        _geometryPrepared = true
    }

    function _prewarmMenuGeometry() {
        if (!_geometryPrewarmScheduled) return
        _geometryPrewarmScheduled = false
        if (controlEnabled && !loading && _safeMenuItems.length > 0) {
            _updatePopupWidth()
        }
    }

    function openMenu() {
        if (!_hasMenuContent) return
        if (_hasExternalMenu) {
            if (!_externalMenuIsValid()) {
                _warnInvalidExternalMenu()
                return
            }
            if (menu.isOpen) {
                menu.close()
                return
            }
            menuAboutToOpen()
            menu.openAtControl(parent)
            return
        }
        if (dropDownMenu.isOpen) {
            dropDownMenu.close()
            return
        }
        _menuContentRequested = true
        menuAboutToOpen()
        _geometryPrewarmScheduled = false
        geometryPrewarmTimer.stop()
        // Re-measure authoritatively so click geometry never relies on stale prewarm data.
        // 点击时权威重测，避免继续使用已过期的预热几何数据。
        _updatePopupWidth()
        dropDownMenu.openAtControl(parent)
        _geometryPrepared = false
    }

    function _externalMenuIsValid() {
        return typeof menu.isOpen === "boolean" &&
               typeof menu.prewarm === "function" &&
               typeof menu.openAtControl === "function" &&
               typeof menu.close === "function"
    }

    function _warnInvalidExternalMenu() {
        if (_invalidMenuWarningIssued) return
        _invalidMenuWarningIssued = true
        console.warn("PrismQML Button.menu must expose isOpen, prewarm(), openAtControl(), and close()")
    }

    Component.onCompleted: _animationDuration = Enums.duration.fast

    // ==================== Content 内容 ====================
    Timer {
        id: geometryPrewarmTimer
        interval: 0
        onTriggered: dropdownFeature._prewarmMenuGeometry()
    }

    // Split main button hover area 主按钮悬浮区域
    Rectangle {
        id: splitMainArea
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.right: splitLine.left
        anchors.margins: Enums.spacing.micro
        radius: dropdownFeature.parentRadius > 0 ? dropdownFeature.parentRadius - 1 : Enums.radius.small - 1
        color: splitMainMouse.pressed ? dropdownFeature._splitPressedColor :
               (splitMainMouse.containsMouse ? dropdownFeature._splitHoverColor : dropdownFeature._splitTransparent)
        visible: feature === Enums.button.feature_split
        
        Behavior on color {
            ColorAnimation { duration: dropdownFeature._animationDuration }
        }
    }
    
    // Split separator line 分离线
    Separator {
        id: splitLine
        type: Enums.separator.vertical
        anchors.right: splitDropArea.left
        anchors.verticalCenter: parent.verticalCenter
        lineLength: parent.height - Enums.spacing.l
        lineColor: dropdownFeature._separatorColor
        visible: feature === Enums.button.feature_split
    }
    
    // Split dropdown area 下拉区域
    Rectangle {
        id: splitDropArea
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.margins: Enums.spacing.micro
        width: Enums.spacing.xxxl
        radius: dropdownFeature.parentRadius > 0 ? dropdownFeature.parentRadius - 1 : Enums.radius.small - 1
        color: splitDropMouse.pressed ? dropdownFeature._splitPressedColor :
               (splitDropMouse.containsMouse ? dropdownFeature._splitHoverColor : dropdownFeature._splitTransparent)
        visible: feature === Enums.button.feature_split
        
        Behavior on color {
            ColorAnimation { duration: dropdownFeature._animationDuration }
        }
        
        ChevronIcon {
            id: splitArrow
            animated: true
            isOpen: dropdownFeature.isMenuOpen
            color: dropdownFeature._arrowColor
            anchors.centerIn: parent
        }
        
        MouseArea {
            id: splitDropMouse
            anchors.fill: parent
            hoverEnabled: true
            enabled: dropdownFeature.controlEnabled && !dropdownFeature.loading
            onContainsMouseChanged: {
                if (splitDropMouse.containsMouse) dropdownFeature.prewarmMenu()
            }
            onClicked: dropdownFeature.openMenu()
        }
    }
    
    // Split main button interaction 主按钮交互
    MouseArea {
        id: splitMainMouse
        anchors.fill: splitMainArea
        hoverEnabled: true
        enabled: dropdownFeature.controlEnabled && !dropdownFeature.loading && feature === Enums.button.feature_split
        visible: feature === Enums.button.feature_split
        onClicked: dropdownFeature.mainButtonClicked()
    }
    
    // Dropdown menu 下拉菜单
    PopupWindowCore {
        id: dropDownMenu

        // Calculate item height without the core-owned popup padding.
        // 计算不含基类弹层内边距的项目高度。
        readonly property int _itemsHeight: {
            var h = 0
            for (var i = 0; i < dropdownFeature._safeMenuItems.length; i++) {
                var item = dropdownFeature._safeMenuItems[i]
                var text = item && typeof item === "object" ? (item.text || item) : (item || "")
                h += (text === "-") ? Enums.controlSize.menuSeparatorHeight : Enums.comboBoxMetrics.itemHeight
            }
            return h
        }
        readonly property int _maxContentHeight: Math.max(
            0, Enums.comboBoxMetrics.popupMaxHeight - 2 * contentPadding)
        readonly property bool _needsScroll: _itemsHeight > _maxContentHeight

        implicitContentHeight: Math.min(_itemsHeight, _maxContentHeight)
        closeOnClickOutside: true
        // Keep button menus in a native popup so they may cross the owner boundary.
        // 按钮菜单使用原生弹窗，以保持左侧锚定并允许跨越宿主窗口边界。
        useQtPopupWindow: true
        
        Loader {
            id: menuContentLoader
            anchors.fill: parent
            active: dropdownFeature._menuContentRequested

            sourceComponent: Item {
                readonly property alias textMeasure: textMeasure

                // TextMetrics to measure menu item text width 用TextMetrics测量菜单项文本宽度
                TextMetrics {
                    id: textMeasure
                    font.family: Enums.fontFamily
                    font.pixelSize: fontSize > 0 ? fontSize : Enums.typography.body
                }

                Flickable {
                    id: menuFlickable
                    anchors.fill: parent
                    anchors.rightMargin: dropDownMenu._needsScroll
                                         ? Enums.comboBoxMetrics.scrollBarRightMargin : 0
                    contentWidth: width
                    contentHeight: menuColumn.height
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    interactive: false  // Disable native scroll, use smooth scroll 禁用原生滚动，使用平滑滚动

                    // Smooth scroll 平滑滚动
                    PopupSmoothScroll {
                        flickable: menuFlickable
                        enabled: dropDownMenu._needsScroll
                    }

                    Column {
                        id: menuColumn
                        width: parent.width

                        Repeater {
                            model: dropdownFeature._safeMenuItems

                            MenuDelegate {
                                width: menuColumn.width
                                text: modelData && typeof modelData === "object"
                                      ? (modelData.text || modelData) : (modelData || "")
                                icon: modelData && typeof modelData === "object"
                                      ? (modelData.icon || "") : ""
                                isSeparator: text === "-"
                                onPressed: dropDownMenu.stabilizeInteraction()
                                onClicked: {
                                    dropDownMenu.close()
                                    dropdownFeature.menuItemClicked(index, text)
                                }
                            }
                        }
                    }
                }

                // Scrollbar 滚动条
                Loader {
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.margins: Enums.spacing.xxs
                    width: Enums.comboBoxMetrics.scrollBarWidth
                    active: dropDownMenu._needsScroll
                    sourceComponent: ScrollBarEntry {
                        flickable: menuFlickable
                        width: Enums.comboBoxMetrics.scrollBarWidth
                    }
                }
            }
        }
    }
}
