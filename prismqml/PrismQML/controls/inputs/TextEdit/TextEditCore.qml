// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."
import QtQuick.Effects
import "../../data"

// TextEditCore - Multiline text input base (extends InputCore) 多行文本输入基类
// Use multilineType to switch modes 通过multilineType切换模式
// multiline_plain: editable plain text 可编辑纯文本
// multiline_browser: read-only rich text browser 只读富文本浏览器
InputCore {
    id: control

    // ==================== Public Props 公开属性 ====================
    property int multilineType: Enums.input.multiline_plain
    property alias text: textEdit.text
    readonly property real textContentHeight: textEdit.contentHeight  // Native text layout height 原生文本布局高度
    property string placeholderText: ""
    property bool readOnly: _isBrowser  // Browser mode is always read-only 浏览器模式始终只读
    property int wrapMode: TextEdit.Wrap
    // RichText for browser (read-only), PlainText for editable 富文本仅用于浏览器模式（只读），可编辑模式使用纯文本
    property int textFormat: _isBrowser ? TextEdit.RichText : TextEdit.PlainText
    property bool showScrollIndicator: false     // Scroll indicator 滚动条指示器
    property bool openExternalLinks: true        // For browser mode 浏览器模式用

    // ==================== Readonly State 只读状态 ====================
    readonly property bool _isBrowser: multilineType === Enums.input.multiline_browser
    readonly property string _hoveredLink: {
        if (!_isBrowser || !hoverHandler.hovered) return ""
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
    function clear() { textEdit.text = "" }
    function selectAll() { textEdit.selectAll() }
    function setFocus() { textEdit.forceActiveFocus() }

    // Undo last edit 撤销
    function undo() { textEdit.undo() }

    // Redo last undone edit 重做
    function redo() { textEdit.redo() }


    // Copy selected text 复制
    function copy() { textEdit.copy() }

    // Cut selected text 剪切
    function cut() { textEdit.cut() }

    // Paste from clipboard 粘贴
    function paste() { textEdit.paste() }

    // Append text 追加文本
    function append(text) { textEdit.text += text }

    function getText() { return textEdit.text }
    // Get plain text 获取纯文本
    function toPlainText() { return textEdit.getText(0, textEdit.length) }
    function isEnabled() { return enabled }
    // Has focus 是否有焦点
    function hasFocus() { return textEdit.activeFocus }

    // Bind inherited InputCore state 绑定继承的 InputCore 状态
    focusTarget: _isBrowser ? null : textEdit
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
    radius: Enums.radius.small
    
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
        visible: control.showScrollIndicator && flickable.contentHeight > flickable.height
        
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
