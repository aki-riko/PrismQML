// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

import QtQuick

// TagKeyboardController - Tag keyboard selection and editing 标签键盘选择与编辑
QtObject {
    id: keyboard

    // ==================== Required Props 必需属性 ====================
    required property var control
    required property var editor

    // ==================== Internal Props 内部属性 ====================
    property int selectionAnchor: -1
    property int selectionCursor: -1
    property int suggestionIndex: -1
    property bool suggestionsDismissed: false
    property bool internalTagsChange: false
    property var _undoStack: []
    property var _redoStack: []
    property bool _lastEditWasTag: false

    // ==================== Readonly State 只读状态 ====================
    readonly property bool hasTagSelection: selectionAnchor >= 0 && selectionCursor >= 0
    readonly property int selectionStart: hasTagSelection
        ? Math.min(selectionAnchor, selectionCursor) : -1
    readonly property int selectionEnd: hasTagSelection
        ? Math.max(selectionAnchor, selectionCursor) : -1
    readonly property bool allTagsSelected: hasTagSelection
        && selectionStart === 0
        && selectionEnd === control._safeTags.length - 1

    // ==================== Public Methods 公开方法 ====================
    function isTagSelected(index) {
        return hasTagSelection && index >= selectionStart && index <= selectionEnd
    }

    function clearTagSelection() {
        selectionAnchor = -1
        selectionCursor = -1
    }

    function selectAllTags() {
        if (control._safeTags.length === 0) return false
        selectionAnchor = 0
        selectionCursor = control._safeTags.length - 1
        return true
    }

    function clear() {
        var hadText = editor.text.length > 0
        if (hadText) editor.text = ""
        if (control._safeTags.length > 0) return clearTags()
        clearTagSelection()
        return hadText
    }

    function selectAll() {
        if (editor.text.length > 0) {
            clearTagSelection()
            editor.selectAll()
            return true
        }
        return selectAllTags()
    }

    function undo() {
        if ((_lastEditWasTag || !editor.canUndo) && _undoTags()) return true
        if (!editor.canUndo) return false
        editor.undo()
        return true
    }

    function redo() {
        if ((_lastEditWasTag || !editor.canRedo) && _redoTags()) return true
        if (!editor.canRedo) return false
        editor.redo()
        return true
    }

    function copy() {
        if (_copySelectedTags()) return true
        editor.copy()
        return true
    }

    function cut() {
        if (_cutSelectedTags()) return true
        editor.cut()
        return true
    }

    function paste() {
        if (_pasteOverSelection()) return true
        editor.paste()
        return true
    }

    function resetForExternalTags() {
        _undoStack = []
        _redoStack = []
        _lastEditWasTag = false
        clearTagSelection()
    }

    function resetAfterTextEdit() {
        suggestionsDismissed = false
        suggestionIndex = -1
        _lastEditWasTag = false
        clearTagSelection()
    }

    function resetAfterFocusLoss() {
        suggestionsDismissed = false
        suggestionIndex = -1
        clearTagSelection()
    }

    function showAllSuggestions() {
        suggestionsDismissed = false
        suggestionIndex = -1
        control._forceShowAll = true
    }

    function addTag(text, recordHistory) {
        var trimmed = (text || "").trim()
        if (!control._canAcceptTag(trimmed)) return false
        if (recordHistory !== false) _recordHistory()
        var newTags = control._safeTags.slice()
        newTags.push(trimmed)
        _setTags(newTags)
        control.tagsModified(control.tags)
        control.tagAdded(trimmed)
        return true
    }

    function addTags(parts, recordHistory) {
        var recorded = recordHistory === false
        var added = false
        for (var i = 0; i < parts.length; i++) {
            var trimmed = (parts[i] || "").trim()
            if (!control._canAcceptTag(trimmed)) continue
            if (!recorded) {
                _recordHistory()
                recorded = true
            }
            addTag(trimmed, false)
            added = true
        }
        return added
    }

    function clearTags() {
        if (control._safeTags.length === 0) {
            clearTagSelection()
            control.tagsModified(control.tags)
            return true
        }
        _recordHistory()
        _setTags([])
        clearTagSelection()
        control.tagsModified(control.tags)
        return true
    }

    function removeTagAt(index) {
        var oldTags = control._safeTags.slice()
        if (index < 0 || index >= oldTags.length) return false
        _recordHistory()
        var removed = oldTags.splice(index, 1)[0]
        _setTags(oldTags)
        clearTagSelection()
        control.tagsModified(control.tags)
        control.tagRemoved(index, removed)
        return true
    }

    function removeSelectedTags(recordHistory) {
        if (!hasTagSelection) return false
        if (recordHistory !== false) _recordHistory()
        var start = selectionStart
        var end = selectionEnd
        var oldTags = control._safeTags.slice()
        var removed = oldTags.splice(start, end - start + 1)
        _setTags(oldTags)
        clearTagSelection()
        control.tagsModified(control.tags)
        for (var i = removed.length - 1; i >= 0; i--) {
            control.tagRemoved(start + i, removed[i])
        }
        return true
    }

    function handleKey(event) {
        if (_handleStandardShortcut(event)) return true
        if (_handleEscape(event)) return true
        if (_handleSuggestionToggle(event)) return true
        if (_handleSuggestionKey(event)) return true
        if (_handleDeletion(event)) return true
        if (_handleTagNavigation(event)) return true
        if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
            return _commitInput()
        }
        return false
    }

    // ==================== Internal Methods 内部方法 ====================
    function _setTags(newTags) {
        internalTagsChange = true
        control.tags = newTags
        internalTagsChange = false
    }

    function _recordHistory() {
        var stack = _undoStack.slice()
        stack.push(control._safeTags.slice())
        _undoStack = stack
        _redoStack = []
        _lastEditWasTag = true
    }

    function _restoreSnapshot(snapshot) {
        var oldTags = control._safeTags.slice()
        var newTags = snapshot.slice()
        _setTags(newTags)
        clearTagSelection()
        control.tagsModified(control.tags)
        _emitHistorySignals(oldTags, newTags)
        _lastEditWasTag = true
    }

    function _emitHistorySignals(oldTags, newTags) {
        for (var i = oldTags.length - 1; i >= 0; i--) {
            if (newTags.indexOf(oldTags[i]) < 0) control.tagRemoved(i, oldTags[i])
        }
        for (var j = 0; j < newTags.length; j++) {
            if (oldTags.indexOf(newTags[j]) < 0) control.tagAdded(newTags[j])
        }
    }

    function _undoTags() {
        if (_undoStack.length === 0) return false
        var undo = _undoStack.slice()
        var snapshot = undo.pop()
        var redo = _redoStack.slice()
        redo.push(control._safeTags.slice())
        _undoStack = undo
        _redoStack = redo
        _restoreSnapshot(snapshot)
        return true
    }

    function _redoTags() {
        if (_redoStack.length === 0) return false
        var redo = _redoStack.slice()
        var snapshot = redo.pop()
        var undo = _undoStack.slice()
        undo.push(control._safeTags.slice())
        _redoStack = redo
        _undoStack = undo
        _restoreSnapshot(snapshot)
        return true
    }

    function _copySelectedTags() {
        if (!hasTagSelection) return false
        var selected = control._safeTags.slice(selectionStart, selectionEnd + 1)
        ClipboardHelper.copy(selected.join(control.separator || "\n"))
        return true
    }

    function _cutSelectedTags() {
        if (!_copySelectedTags()) return false
        return removeSelectedTags(true)
    }

    function _pasteOverSelection() {
        if (!hasTagSelection) return false
        var raw = ClipboardHelper.paste()
        if (!raw) return true
        var parts = control._splitRaw(raw)
        if (parts === null) parts = [raw]
        var accepted = _acceptedPasteParts(parts)
        if (accepted.length === 0) return true
        _recordHistory()
        removeSelectedTags(false)
        addTags(accepted, false)
        return true
    }

    function _acceptedPasteParts(parts) {
        var remaining = control._safeTags.slice()
        remaining.splice(selectionStart, selectionEnd - selectionStart + 1)
        var accepted = []
        for (var i = 0; i < parts.length; i++) {
            var trimmed = (parts[i] || "").trim()
            if (!control._canAcceptTagInList(trimmed, remaining)) continue
            remaining.push(trimmed)
            accepted.push(trimmed)
        }
        return accepted
    }

    function _handleStandardShortcut(event) {
        if (event.matches(StandardKey.SelectAll)) {
            if (editor.text || control._safeTags.length === 0) return false
            return selectAllTags()
        }
        if (event.matches(StandardKey.Copy) && hasTagSelection) return _copySelectedTags()
        if (event.matches(StandardKey.Cut) && hasTagSelection) return _cutSelectedTags()
        if (event.matches(StandardKey.Paste) && hasTagSelection) return _pasteOverSelection()
        if (editor.text) return false
        if (event.matches(StandardKey.Undo)
                && (_lastEditWasTag || !editor.canUndo)) return _undoTags()
        if ((event.matches(StandardKey.Redo) || _isAlternateRedo(event))
                && (_lastEditWasTag || !editor.canRedo)) return _redoTags()
        return false
    }

    function _isAlternateRedo(event) {
        var shortcut = (event.modifiers & (Qt.ControlModifier | Qt.MetaModifier)) !== 0
        var shift = (event.modifiers & Qt.ShiftModifier) !== 0
        return shortcut && shift && event.key === Qt.Key_Z
    }

    function _handleEscape(event) {
        if (event.key !== Qt.Key_Escape) return false
        var handled = hasTagSelection || control._showSuggestions
        clearTagSelection()
        _dismissSuggestions()
        return handled
    }

    function _dismissSuggestions() {
        suggestionsDismissed = true
        suggestionIndex = -1
        control._forceShowAll = false
    }

    function _handleSuggestionToggle(event) {
        var alt = (event.modifiers & Qt.AltModifier) !== 0
        var toggle = event.key === Qt.Key_F4 || (alt && event.key === Qt.Key_Down)
        if (toggle && control._showSuggestions) {
            _dismissSuggestions()
            return true
        }
        if (toggle && control._safeSuggestions.length > 0) {
            showAllSuggestions()
            return true
        }
        if (alt && event.key === Qt.Key_Up && control._showSuggestions) {
            _dismissSuggestions()
            return true
        }
        return false
    }

    function _moveSuggestion(delta) {
        var count = control._filteredItems.length
        if (count === 0) return false
        if (suggestionIndex < 0) suggestionIndex = delta > 0 ? 0 : count - 1
        else suggestionIndex = Math.max(0, Math.min(count - 1, suggestionIndex + delta))
        return true
    }

    function _selectSuggestionBoundary(first) {
        if (control._filteredItems.length === 0) return false
        suggestionIndex = first ? 0 : control._filteredItems.length - 1
        return true
    }

    function _acceptSuggestion(useFirstAsFallback) {
        var index = suggestionIndex
        if (index < 0 && useFirstAsFallback) index = 0
        if (index < 0 || index >= control._filteredItems.length) return false
        var item = control._filteredItems[index]
        var text = typeof item === "string" ? item : (item ? (item.text || "") : "")
        if (addTag(text, true)) editor.text = ""
        control._forceShowAll = false
        suggestionsDismissed = false
        suggestionIndex = -1
        return true
    }

    function _handleSuggestionKey(event) {
        if (!control._showSuggestions) return false
        if (event.key === Qt.Key_Down) return _moveSuggestion(1)
        if (event.key === Qt.Key_Up) return _moveSuggestion(-1)
        if (event.key === Qt.Key_Home) return _selectSuggestionBoundary(true)
        if (event.key === Qt.Key_End) return _selectSuggestionBoundary(false)
        if (event.key === Qt.Key_Tab) return _acceptSuggestion(true)
        if ((event.key === Qt.Key_Return || event.key === Qt.Key_Enter)
                && suggestionIndex >= 0) {
            return _acceptSuggestion(false)
        }
        return false
    }

    function _handleDeletion(event) {
        if (event.key !== Qt.Key_Backspace && event.key !== Qt.Key_Delete) return false
        if (hasTagSelection) return removeSelectedTags(true)
        if (event.key === Qt.Key_Backspace && !editor.text
                && control._safeTags.length > 0) {
            return removeTagAt(control._safeTags.length - 1)
        }
        return false
    }

    function _setSingleSelection(index) {
        selectionAnchor = index
        selectionCursor = index
    }

    function _moveTagSelection(delta, extend) {
        var count = control._safeTags.length
        if (!hasTagSelection) {
            if (delta > 0 || count === 0) return false
            _setSingleSelection(count - 1)
            return true
        }
        if (!extend && selectionStart !== selectionEnd) {
            _setSingleSelection(delta < 0 ? selectionStart : selectionEnd)
            return true
        }
        var target = selectionCursor + delta
        if (target >= count && !extend) {
            clearTagSelection()
            return true
        }
        target = Math.max(0, Math.min(count - 1, target))
        if (extend) selectionCursor = target
        else _setSingleSelection(target)
        return true
    }

    function _handleTagNavigation(event) {
        if (editor.text || control._safeTags.length === 0) return false
        var modifiers = event.modifiers
        if ((modifiers & (Qt.ControlModifier | Qt.MetaModifier | Qt.AltModifier)) !== 0) {
            return false
        }
        var extend = (modifiers & Qt.ShiftModifier) !== 0
        if (event.key === Qt.Key_Left) return _moveTagSelection(-1, extend)
        if (event.key === Qt.Key_Right && hasTagSelection) {
            return _moveTagSelection(1, extend)
        }
        if (event.key === Qt.Key_Home) {
            if (extend && hasTagSelection) selectionCursor = 0
            else _setSingleSelection(0)
            return true
        }
        if (event.key === Qt.Key_End && hasTagSelection) {
            if (extend) selectionCursor = control._safeTags.length - 1
            else clearTagSelection()
            return true
        }
        return false
    }

    function _commitInput() {
        var trimmed = editor.text.trim()
        if (trimmed && addTag(trimmed, true)) editor.text = ""
        return true
    }
}
