// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."
import QtQuick.Effects
import "../../data"
import "../../containers/ScrollBar"
import "_internal" as TextEditInternal

// TextEditCore - Multiline text input base (extends InputCore) 多行文本输入基类
// Use multilineType to switch modes 通过multilineType切换模式
// multiline_plain: editable plain text 可编辑纯文本
// multiline_browser: read-only rich text browser 只读富文本浏览器
InputCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    property int multilineType: Enums.input.multiline_plain
    property alias text: textEdit.text
    readonly property real textContentHeight: _usesTrimmingPresentation
        ? (trimmingLoader.item ? trimmingLoader.item.naturalHeight : textEdit.contentHeight)
        : (columnCount > 1 && columnsLoader.item
           ? columnsLoader.item._textHeight : textEdit.contentHeight)
    property string placeholderText: ""
    property bool readOnly: _isBrowser  // Browser mode is always read-only 浏览器模式始终只读
    property int wrapMode: TextEdit.Wrap
    // RichText for browser (read-only), PlainText for editable 富文本仅用于浏览器模式（只读），可编辑模式使用纯文本
    property int textFormat: _isBrowser ? TextEdit.RichText : TextEdit.PlainText
    property bool showScrollIndicator: false     // Scroll indicator 滚动条指示器
    property bool openExternalLinks: true        // For browser mode 浏览器模式用
    property bool smoothScroll: true
    property int scrollDuration: Enums.duration.scroll
    property real scrollStep: Enums.spacing.xxxl * 3
    property int scrollEasing: Easing.OutQuart
    // TextTrimming for the read-only presentation 只读呈现的文本裁剪方式
    property int textTrimming: Enums.label.trim_none
    // Newspaper columns for the read-only presentation (1 keeps the classic
    // single viewport) 只读呈现的报纸式列数 (1 保持经典单视口)
    property int columnCount: 1

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _isBrowser: multilineType === Enums.input.multiline_browser
    // Ellipsis trimming swaps in a read-only Text presentation 省略号裁剪改用只读 Text 呈现
    readonly property bool _usesTrimmingPresentation:
        textTrimming === Enums.label.trim_character_ellipsis
        || textTrimming === Enums.label.trim_word_ellipsis
    // Qt exposes one right-ellipsis mode; the two tokens differ by wrap mode
    // Qt 只提供右省略一种模式; 两个 token 通过换行方式区分
    readonly property int _trimWrapMode:
        textTrimming === Enums.label.trim_character_ellipsis
        ? Text.WrapAnywhere : wrapMode
    // True while the content cannot be shown in full 内容无法完整展示时为真
    readonly property bool hasOverflowContent: _usesTrimmingPresentation
        ? (trimmingLoader.item ? trimmingLoader.item.hasOverflow : false)
        : (columnCount > 1
           ? (columnsLoader.item ? columnsLoader.item.hasOverflow : false)
           : flickable.contentHeight > flickable.height)
    // Pointer-position-only effect: link hit-testing exists to shape the mouse cursor
    // 指针坐标专属效果: 链接命中测试只服务于鼠标光标, 触摸端关闭
    readonly property string _hoveredLink: {
        if (Touch.isTouch || !_isBrowser || !hoverHandler.hovered) return ""
        var position = hoverHandler.point.position
        var editorPosition = control.mapToItem(textEdit, position.x, position.y)
        return textEdit.linkAt(editorPosition.x, editorPosition.y)
    }

    // ==================== Signals 信号 ====================
    signal textEdited()
    signal editingFinished()
    signal linkActivated(string link)  // For browser mode 浏览器模式用
    signal cursorPositionChanged()  // Cursor position changed 光标位置变化
    signal selectionChanged()  // Selection changed 选择变化

    // ==================== Public Methods 公开方法 ====================
    function setFocus() { textEdit.forceActiveFocus() }

    // Append text 追加文本
    function append(text) { textEdit.text += text }

    function getText() { return textEdit.text }
    // Get plain text 获取纯文本
    function toPlainText() { return textEdit.getText(0, textEdit.length) }
    function isEnabled() { return enabled }
    // Has focus 是否有焦点
    function hasFocus() { return textEdit.activeFocus }
    function smoothScrollTo(targetY) { scrollHelper.scrollTo(targetY) }
    function smoothScrollBy(delta) { scrollHelper.scrollBy(delta) }
    function scrollToTop() { scrollHelper.scrollToStart() }
    function scrollToBottom() { scrollHelper.scrollToEnd() }

    // ==================== Internal Methods 内部方法 ====================
    function _handleSmoothWheel(event) {
        if (!smoothScroll || flickable.contentHeight <= flickable.height) {
            event.accepted = false
            return
        }
        scrollHelper.scrollBy(-WheelEventUtils.verticalDelta(event) / 120 * scrollStep)
        event.accepted = true
    }

    // Bind inherited InputCore state 绑定继承的 InputCore 状态
    focusTarget: _isBrowser ? null : textEdit
    editActionTarget: textEdit
    focused: _isBrowser ? false : textEdit.activeFocus  // Browser never focused 浏览器不聚焦
    hovered: _isBrowser ? false : hoverHandler.hovered  // Browser no hover state 浏览器无悬浮状态
    showFocusedBorder: !_isBrowser  // Browser has no focus line 浏览器无聚焦线
    // Browser links use a hand; other browser text remains arrow. 浏览器链接使用手型，其余文本保持箭头。
    cursorShape: _isBrowser
                 ? (_hoveredLink !== "" ? Qt.PointingHandCursor : Qt.ArrowCursor)
                 : Qt.IBeamCursor
    
    // ==================== Size 尺寸 ====================
    // Override InputCore content size 覆盖InputCore内容尺寸
    contentWidth: Enums.controlSize.inputDefaultWidth
    contentHeight: Enums.controlSize.inputDefaultWidth / 2  // 100 = 200/2
    radius: Enums.surfaceRadius(Enums.radius.small)
    
    // ==================== Content 内容 ====================
    // Scrollable text area 可滚动文本区域
    Flickable {
        id: flickable
        anchors.fill: parent
        anchors.leftMargin: control.paddingLeft
        anchors.rightMargin: control.paddingRight
        anchors.topMargin: control.paddingTop
        anchors.bottomMargin: control.paddingBottom
        contentWidth: textEdit.width
        contentHeight: textEdit.height
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        interactive: contentHeight > height  // Only enable scroll when needed 仅内容超出时启用滚动
        // Multi-column and trimming modes own their own viewport 多列与裁剪模式使用自己的视口
        visible: control.columnCount <= 1
                 && !control._usesTrimmingPresentation
        
        TextEdit {
            id: textEdit
            width: flickable.width
            
            font.family: Enums.fontFamily
            font.pixelSize: control.fontSize
            color: control._isBrowser ? Enums.textColor.primary : control.inputTextColor
            selectionColor: control._isBrowser ? Enums.transparent : control.selectionColor
            selectedTextColor: control._isBrowser ? Enums.textColor.primary : control.selectedTextColor
            selectByMouse: !control._isBrowser  // Browser cannot select 浏览器不可选
            wrapMode: control.wrapMode
            textFormat: control.textFormat
            readOnly: control.readOnly
            enabled: control.enabled
            activeFocusOnPress: !control._isBrowser  // Browser cannot focus 浏览器不可聚焦
            cursorVisible: activeFocus && !control._isBrowser  // Only show cursor when focused 仅聚焦时显示光标
            
            onTextEdited: control.textEdited()
            onEditingFinished: control.editingFinished()
            onLinkActivated: (link) => {
                control.linkActivated(link)
                if (control.openExternalLinks) Qt.openUrlExternally(link)
            }
            onCursorPositionChanged: control.cursorPositionChanged()
            onSelectedTextChanged: control.selectionChanged()
        }
    }

    // Newspaper columns, created only when more than one column is requested
    // 报纸式多列, 仅在请求多列时创建
    Loader {
        id: columnsLoader
        objectName: "textEditColumnsLoader"
        anchors.fill: parent
        anchors.leftMargin: control.paddingLeft
        anchors.rightMargin: control.paddingRight
        anchors.topMargin: control.paddingTop
        anchors.bottomMargin: control.paddingBottom
        active: control.columnCount > 1 && !control._usesTrimmingPresentation

        sourceComponent: TextEditInternal.RichTextColumns {
            editor: control
            columnGap: Enums.spacing.m
            textFontFamily: Enums.fontFamily
            textFontSize: control.fontSize
            textColor: Enums.textColor.primary
        }
    }

    // Ellipsis trimming presentation 省略号裁剪呈现
    Loader {
        id: trimmingLoader
        objectName: "textEditTrimmingLoader"
        anchors.fill: parent
        anchors.leftMargin: control.paddingLeft
        anchors.rightMargin: control.paddingRight
        anchors.topMargin: control.paddingTop
        anchors.bottomMargin: control.paddingBottom
        active: control._usesTrimmingPresentation
        visible: active

        sourceComponent: TextEditInternal.RichTextTrimView {
            editor: control
            textFontFamily: Enums.fontFamily
            textFontSize: control.fontSize
            textColor: Enums.textColor.primary
            trimWrapMode: control._trimWrapMode
            onLinkTriggered: (link) => {
                control.linkActivated(link)
                if (control.openExternalLinks) Qt.openUrlExternally(link)
            }
        }
    }

    SmoothScrollHelper {
        id: scrollHelper

        target: flickable
        orientation: Qt.Vertical
        enabled: control.smoothScroll
        duration: control.scrollDuration
        step: control.scrollStep
        easing: control.scrollEasing
        bounceEnabled: false
    }

    Connections {
        function onMovementEnded() { scrollHelper.syncPosition() }
        target: flickable
    }

    MouseArea {
        id: smoothWheelArea
        parent: flickable
        anchors.fill: parent
        z: Enums.zIndex.controlsAbove
        acceptedButtons: Qt.NoButton
        propagateComposedEvents: true
        enabled: control.smoothScroll
        cursorShape: control.cursorShape
        onWheel: (event) => control._handleSmoothWheel(event)
    }
    
    // InputCore handles click-to-focus centrally 点击聚焦由 InputCore 统一处理

    // Scroll indicator 滚动指示器
    Rectangle {
        anchors.right: parent.right
        anchors.rightMargin: Enums.spacing.xxs
        anchors.top: parent.top
        anchors.topMargin: Enums.spacing.l
        anchors.bottom: parent.bottom
        anchors.bottomMargin: Enums.spacing.l
        width: Enums.controlSize.progressBarHeight
        radius: Enums.radius.tiny
        color: control.innerButtonHover
        visible: control.showScrollIndicator && flickable.visible
                 && flickable.contentHeight > flickable.height
        
        Rectangle {
            anchors.right: parent.right
            width: parent.width
            radius: parent.radius
            color: Enums.stateColor.dropBorderHover
            height: Math.max(Enums.controlSize.textEditScrollThumbMinHeight, parent.height * flickable.height / flickable.contentHeight)
            y: flickable.contentHeight > flickable.height ? (parent.height - height) * (flickable.contentY / (flickable.contentHeight - flickable.height)) : 0
        }
    }
    
    // Placeholder 占位符
    Label {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.leftMargin: control.paddingLeft
        anchors.topMargin: control.paddingTop
        type: Enums.label.type_body
        text: control.placeholderText
        color: Enums.textColor.disabled
        visible: textEdit.text === "" && !textEdit.activeFocus
    }
    
    // Hover detection 悬浮检测
    HoverHandler {
        id: hoverHandler
    }
}
