// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.

pragma Singleton
import QtQuick

// BottomSheetStack - Open bottom sheets grouped by overlay host 按覆盖宿主分组的已打开底部弹层
// A sheet's host is its parent after open (normally the window content item), so one
// engine-wide list serves every window. Query functions take `sheets` explicitly so a
// binding that passes `openSheets` re-evaluates whenever the list is replaced.
// 弹层的宿主是打开后的父对象（通常是窗口内容项），因此一份引擎级列表即可服务所有窗口。
// 查询函数显式接收 `sheets`，绑定传入 `openSheets` 后，列表被替换时即重新求值。
QtObject {
    id: stack

    // ==================== Readonly State 只读状态 ====================
    // Replaced, never mutated in place, so bindings are notified 只整体替换不原地修改，绑定才会收到通知
    property var openSheets: []

    // ==================== Public Methods 公开方法 ====================
    // Put the sheet on top of its host stack 把弹层放到其宿主栈顶
    function push(sheet) {
        stack.openSheets = stack.openSheets
            .filter(function(item) { return item !== sheet })
            .concat([sheet])
    }

    function remove(sheet) {
        if (stack.openSheets.indexOf(sheet) < 0) return
        stack.openSheets = stack.openSheets.filter(function(item) { return item !== sheet })
    }

    // Sheets sharing the host, bottom first 同宿主的弹层，自底向上
    function hostSheets(host, sheets) {
        return sheets.filter(function(item) { return item.parent === host })
    }

    function indexOf(sheet, sheets) {
        return stack.hostSheets(sheet.parent, sheets).indexOf(sheet)
    }

    function countIn(host, sheets) {
        return stack.hostSheets(host, sheets).length
    }

    // The sheet directly above, or null 正上方的弹层，没有则为 null
    function above(sheet, sheets) {
        var hosted = stack.hostSheets(sheet.parent, sheets)
        var index = hosted.indexOf(sheet)
        return index >= 0 && index + 1 < hosted.length ? hosted[index + 1] : null
    }

    // Whether the sheet was declared inside ancestor. Open reparents sheets to the
    // host, so walk from the parent recorded before that reparenting.
    // 弹层是否声明在 ancestor 内部。打开会把弹层重挂到宿主，因此从重挂前记录的父对象向上查找。
    function isNestedIn(sheet, ancestor) {
        for (var item = sheet._originalParent; item; item = item.parent) {
            if (item === ancestor) return true
        }
        return false
    }

    // Close the sheets declared inside this one, topmost first; deeper levels close
    // through their own parent. Sibling sheets opened above stay open.
    // 自顶向下关闭声明在本弹层内部的子层；更深的层由各自父层级联关闭。上方并列的兄弟层保持打开。
    function closeNested(sheet) {
        var sheets = stack.openSheets
        for (var i = sheets.length - 1; i >= 0; --i) {
            if (stack.isNestedIn(sheets[i], sheet)) sheets[i].close()
        }
    }
}
