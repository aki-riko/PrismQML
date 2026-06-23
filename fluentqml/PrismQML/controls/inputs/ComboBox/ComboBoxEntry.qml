// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of FluentQML, licensed under MIT.

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
    implicitWidth: loader.item ? loader.item.implicitWidth : 200
    implicitHeight: loader.item ? loader.item.implicitHeight : 32
    
    // ==================== Type/Style/Feature Props 类型/样式/功能 ====================
    property int type: Enums.comboBox.type_default
    property int style: Enums.comboBox.style_default
    property int feature: Enums.comboBox.feature_none
    
    // ==================== Common Props 通用属性 ====================
    property var model: []
    // 注意：currentIndex/currentText 使用双向同步，防止外部赋值打破绑定
    property int currentIndex: 0
    property string currentText: ""
    property string placeholderText: ""
    property bool _syncing: false  // 防止同步循环
    // 异步加载内部 ComboBox*.qml — 大列表 delegate 场景 (一屏 30+ ComboBox) 打开,
    // 让首次滚动不被同步实例化阻塞; 单个独立 ComboBox 用法默认同步 (避免首帧空)
    property bool asyncLoad: false
    
    // 外部 → 内部同步
    onCurrentIndexChanged: {
        if (!_syncing && loader.item && loader.item.currentIndex !== undefined
                && loader.item.currentIndex !== currentIndex) {
            _syncing = true
            loader.item.currentIndex = currentIndex
            _syncing = false
        }
    }
    
    // ==================== Tree Props 树形属性 ====================
    property bool showPathFromRoot: true  // Show full path or only leaf name 显示完整路径或仅叶子名称
    
    // ==================== Signals 信号 ====================
    signal activated(int index)
    signal indexChanged(int index)
    signal selectionChanged(var indices, var items)
    
    // ==================== 内部 → 外部同步 ====================
    Connections {
        target: loader.item
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
    }
    
    // ==================== Loader 动态加载 ====================
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
            // Always set up the model binding, even when control.model is
            // currently empty. The previous `length > 0` guard caused a
            // permanent skip when onLoaded fired before the external model
            // was populated (e.g. backend not yet injected): item.model
            // stayed at its default and never followed the external var.
            // 始终建立 model binding。之前 `length > 0` 守卫会在 onLoaded
            // 早于外部 model 填充时（例如 backend 尚未注入）永久跳过 binding，
            // 导致 item.model 永远停在默认值。
            item.model = Qt.binding(() => control.model)
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
            // 同步初始 currentText
            if (item.currentText !== undefined) {
                control.currentText = item.currentText || ""
            }
        }
    }
}

