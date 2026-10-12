// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

.pragma library

// Handle suggestion-list shortcuts and navigation.
// 处理建议列表快捷键与导航。
function handleToggle(controller, event) {
    var control = controller.control
    var alt = (event.modifiers & Qt.AltModifier) !== 0
    var toggle = event.key === Qt.Key_F4 || (alt && event.key === Qt.Key_Down)
    if (toggle && control._showSuggestions) {
        controller._dismissSuggestions()
        return true
    }
    if (toggle && control._safeSuggestions.length > 0) {
        controller.showAllSuggestions()
        return true
    }
    if (alt && event.key === Qt.Key_Up && control._showSuggestions) {
        controller._dismissSuggestions()
        return true
    }
    return false
}

function handleKey(controller, event) {
    var control = controller.control
    if (!control._showSuggestions) return false
    if (event.key === Qt.Key_Down) return _moveSuggestion(controller, 1)
    if (event.key === Qt.Key_Up) return _moveSuggestion(controller, -1)
    if (event.key === Qt.Key_Home) return _selectSuggestionBoundary(controller, true)
    if (event.key === Qt.Key_End) return _selectSuggestionBoundary(controller, false)
    if (event.key === Qt.Key_Tab) return _acceptSuggestion(controller, true)
    if ((event.key === Qt.Key_Return || event.key === Qt.Key_Enter)
            && controller.suggestionIndex >= 0) {
        return _acceptSuggestion(controller, false)
    }
    return false
}

function _moveSuggestion(controller, delta) {
    var count = controller.control._filteredItems.length
    if (count === 0) return false
    if (controller.suggestionIndex < 0) {
        controller.suggestionIndex = delta > 0 ? 0 : count - 1
    } else {
        controller.suggestionIndex = Math.max(
            0, Math.min(count - 1, controller.suggestionIndex + delta)
        )
    }
    return true
}

function _selectSuggestionBoundary(controller, first) {
    var count = controller.control._filteredItems.length
    if (count === 0) return false
    controller.suggestionIndex = first ? 0 : count - 1
    return true
}

function _acceptSuggestion(controller, useFirstAsFallback) {
    var control = controller.control
    var index = controller.suggestionIndex
    if (index < 0 && useFirstAsFallback) index = 0
    if (index < 0 || index >= control._filteredItems.length) return false
    var item = control._filteredItems[index]
    var text = typeof item === "string" ? item : (item ? (item.text || "") : "")
    if (controller.addTag(text, true)) controller.editor.text = ""
    control._forceShowAll = false
    controller.suggestionsDismissed = false
    controller.suggestionIndex = -1
    return true
}
