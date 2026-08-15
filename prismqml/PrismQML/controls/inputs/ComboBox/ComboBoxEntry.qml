// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick
import "../../.."
import ".."

// ComboBox - Unified combo box with type/style/feature control 统一下拉框组件
// Usage 用法:
//   ComboBox { model: [...] }                                    // Default
//   ComboBox { type: Enums.comboBox.type_multi }           // Multi-select
//   ComboBox { type: Enums.comboBox.type_tree }            // Tree
//   ComboBox { type: Enums.comboBox.type_font }            // Font
//   ComboBox { style: Enums.comboBox.style_primary }       // Primary
//   ComboBox { feature: Enums.comboBox.feature_editable }  // Editable
Item {
    id: control

    // ==================== Public Props 公开属性 ====================
    property int type: Enums.comboBox.type_default
    property int style: Enums.comboBox.style_default
    property int feature: Enums.comboBox.feature_none
    property var model: []
    // Keep currentIndex/currentText synchronized in both directions.
    // 保持 currentIndex/currentText 双向同步。
    property int currentIndex: 0
    property string currentText: ""
    property string placeholderText: ""
    property bool asyncLoad: false
    property bool showPathFromRoot: true  // Show full path or only leaf name 显示完整路径或仅叶子名称

    // ==================== Internal Props 内部属性 ====================
    property bool _syncing: false  // Prevent synchronization loops 防止同步循环

    // ==================== Readonly State 只读状态 ====================
    readonly property int selectionStart: loader.item && loader.item.selectionStart !== undefined
        ? loader.item.selectionStart : 0
    readonly property int selectionEnd: loader.item && loader.item.selectionEnd !== undefined
        ? loader.item.selectionEnd : 0
    readonly property string selectedText: loader.item && loader.item.selectedText !== undefined
        ? loader.item.selectedText : ""

    // ==================== Signals 信号 ====================
    signal activated(int index)
    signal indexChanged(int index)
    signal selectionChanged(var indices, var items)
    signal itemSelected(string text, var path)

    // ==================== Public Methods 公开方法 ====================
    function clearEditText() { return _dispatchLoadedEditAction("clearEditText") }
    function selectAll() { return _dispatchLoadedEditAction("selectAll") }
    function undo() { return _dispatchLoadedEditAction("undo") }
    function redo() { return _dispatchLoadedEditAction("redo") }
    function copy() { return _dispatchLoadedEditAction("copy") }
    function cut() { return _dispatchLoadedEditAction("cut") }
    function paste() { return _dispatchLoadedEditAction("paste") }

    // ==================== Internal Methods 内部方法 ====================
    function _dispatchLoadedEditAction(actionName) {
        if (!loader.item || typeof loader.item[actionName] !== "function") return false
        return loader.item[actionName]()
    }

    // Preserve the font picker's built-in list until an external list is provided.
    // 外部列表为空时保留字体选择框的内置列表。
    function _modelForLoadedItem(item) {
        if (type !== Enums.comboBox.type_font || item.fonts === undefined)
            return model
        var externalModel = model
        return externalModel !== null && externalModel !== undefined
                && typeof externalModel.length === "number" && externalModel.length > 0
            ? externalModel : item.fonts
    }

    // ==================== Size 尺寸 ====================
    implicitWidth: loader.item ? loader.item.implicitWidth : 200
    implicitHeight: loader.item ? loader.item.implicitHeight : 32

    // External to internal synchronization 外部到内部同步
    onCurrentIndexChanged: {
        if (!_syncing && loader.item && loader.item.currentIndex !== undefined
                && loader.item.currentIndex !== currentIndex) {
            _syncing = true
            loader.item.currentIndex = currentIndex
            if (loader.item.currentText !== undefined) {
                currentText = loader.item.currentText || ""
            }
            _syncing = false
        }
    }

    // ==================== Content 内容 ====================
    // Internal to external synchronization 内部到外部同步
    Connections {
        function onCurrentIndexChanged() {
            if (!control._syncing && loader.item
                    && loader.item.currentIndex !== undefined
                    && control.currentIndex !== loader.item.currentIndex) {
                control._syncing = true
                control.currentIndex = loader.item.currentIndex
                control._syncing = false
            }
        }

        function onCurrentTextChanged() {
            if (!control._syncing && loader.item
                    && loader.item.currentText !== undefined) {
                control._syncing = true
                control.currentText = loader.item.currentText || ""
                control._syncing = false
            }
        }

        target: loader.item
    }

    // Dynamic loader 动态加载器
    Loader {
        id: loader
        anchors.fill: parent
        asynchronous: control.asyncLoad
        source: {
            switch (control.type) {
                case Enums.comboBox.type_multi: return "ComboBoxMulti.qml"
                case Enums.comboBox.type_tree: return "ComboBoxTree.qml"
                case Enums.comboBox.type_multi_tree: return "ComboBoxMultiTree.qml"
                case Enums.comboBox.type_font: return "ComboBoxFont.qml"
                default: return "ComboBoxDefault.qml"
            }
        }
        onLoaded: {
            if (!item) return
            // Keep following late model updates while preserving Font defaults.
            // 持续跟随后续模型更新，同时保留 Font 默认列表。
            item.model = Qt.binding(() => control._modelForLoadedItem(item))
            item.enabled = Qt.binding(() => control.enabled)
            if (item.placeholderText !== undefined && control.placeholderText !== "")
                item.placeholderText = Qt.binding(() => control.placeholderText)
            // 同步 currentIndex 到内部 ComboBoxCore（默认值 -1 — 即显示
            // placeholder）。用 Qt.binding 让外部 currentIndex 后续变化也
            // 跟随到内部组件。
            // NB: 外部点选时内部 ComboBoxCore 会触发 onCurrentIndexChanged
            // → Connections 反向同步到 control.currentIndex —— 这条反向路径
            // 的命令式赋值会破坏这里建立的 Qt.binding，但对用户体验无害
            // （用户点击后 index 已经是"用户显式选择的值"，后续外部数据源
            // 变化不需要再改写视图）。
            if (item.currentIndex !== undefined) {
                item.currentIndex = Qt.binding(() => control.currentIndex)
            }
            if (control.type === Enums.comboBox.type_default) {
                item.style = Qt.binding(() => control.style)
                item.feature = Qt.binding(() => control.feature)
            }
            // Tree specific props 树形特有属性
            if (control.type === Enums.comboBox.type_tree || control.type === Enums.comboBox.type_multi_tree) {
                if (item.showPathFromRoot !== undefined)
                    item.showPathFromRoot = Qt.binding(() => control.showPathFromRoot)
            }
            // Connect signals 连接信号
            if (item.activated) item.activated.connect(control.activated)
            if (item.indexChanged) item.indexChanged.connect((i) => control.indexChanged(i))
            if (item.selectionChanged) item.selectionChanged.connect(control.selectionChanged)
            if (item.itemSelected) item.itemSelected.connect(control.itemSelected)
            // 同步初始 currentText
            if (item.currentText !== undefined) {
                control.currentText = item.currentText || ""
            }
        }
    }
}
