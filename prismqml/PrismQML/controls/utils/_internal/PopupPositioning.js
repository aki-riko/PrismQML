// PopupPositioning - Popup placement helpers 弹层定位辅助
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT

.pragma library

function boundsFromGeometry(geometry) {
    if (!geometry || geometry.width <= 0 || geometry.height <= 0) return null
    return {
        left: geometry.x,
        top: geometry.y,
        right: geometry.x + geometry.width,
        bottom: geometry.y + geometry.height
    }
}

function screenBoundsAt(control, globalX, globalY, windowHelper, fallbackScreen) {
    var geometry = null
    if (windowHelper) {
        if (control.constrainToAvailableScreen
                && typeof windowHelper.availableScreenGeometryAt === "function") {
            geometry = windowHelper.availableScreenGeometryAt(
                Math.round(globalX), Math.round(globalY))
        } else if (!control.constrainToAvailableScreen
                && typeof windowHelper.screenGeometryAt === "function") {
            geometry = windowHelper.screenGeometryAt(
                Math.round(globalX), Math.round(globalY))
        }
        var injectedBounds = boundsFromGeometry(geometry)
        if (injectedBounds) return injectedBounds
    }

    var screen = fallbackScreen
    if (screen && screen.width > 0 && screen.height > 0) {
        var virtualX = typeof screen.virtualX === "number" ? screen.virtualX : 0
        var virtualY = typeof screen.virtualY === "number" ? screen.virtualY : 0
        return boundsFromGeometry({
            x: virtualX, y: virtualY,
            width: screen.width, height: screen.height
        })
    }
    return null
}

function calcControlsPopupPosition(control, globalX, globalY, qt) {
    if (!control._inlineParent) return qt.point(0, 0)
    // Popup.Window owns a top-level Qt::Popup surface and may cross the host window boundary. Popup.Window由Qt管理顶层弹层，可越过宿主窗口边界。
    // Only Popup.Item needs host-window clamping. 仅页内Popup.Item需要宿主窗口边界夹紧。
    if (control.useQtPopupWindow) {
        var bounds = control._screenBoundsAt(globalX, globalY, control.targetControl)
        if (bounds) {
            globalX = Math.max(
                bounds.left,
                Math.min(globalX, bounds.right - control._outerWidth)
            )
            globalY = Math.max(
                bounds.top,
                Math.min(globalY, bounds.bottom - control._outerHeight)
            )
        }
        return control._inlineParent.mapFromGlobal(globalX, globalY)
    }
    var localPos = control._inlineParent.mapFromGlobal(globalX, globalY)
    var fitsHorizontally = control._outerWidth <= control._inlineParent.width
    var fitsVertically = control._outerHeight <= control._inlineParent.height
    var maxX = control._inlineParent.width - control._outerWidth
    var maxY = control._inlineParent.height - control._outerHeight
    return qt.point(
        fitsHorizontally ? Math.max(0, Math.min(localPos.x, maxX)) : localPos.x,
        fitsVertically ? Math.max(0, Math.min(localPos.y, maxY)) : localPos.y
    )
}

function calcSubmenuPosition(control, qt, enums) {
    if (!control.targetControl || !control.targetControl.mapToGlobal) {
        return qt.point(0, 0)
    }

    var actionTop = control.targetControl.mapToGlobal(0, 0)
    var actionRight = control.targetControl.mapToGlobal(control.targetControl.width, 0)
    var actionCenter = control.targetControl.mapToGlobal(
        control.targetControl.width / 2, control.targetControl.height / 2)
    var outerWidth = control._outerWidth
    var outerHeight = control._outerHeight
    var panelOffset = control._panelOffset
    var gap = enums.spacing.xs + enums.popupMetrics.controlGap
    var posX = actionRight.x + gap - panelOffset
    var posY = actionTop.y - panelOffset - enums.spacing.xs
    var bounds = control._screenBoundsAt(
        actionCenter.x,
        actionCenter.y,
        control.targetControl
    )

    if (bounds) {
        var leftPosX = actionTop.x - gap - outerWidth + panelOffset
        if (posX + outerWidth > bounds.right && leftPosX >= bounds.left) {
            posX = leftPosX
        }
        posX = Math.max(bounds.left, Math.min(posX, bounds.right - outerWidth))
        posY = Math.max(bounds.top, Math.min(posY, bounds.bottom - outerHeight))
    }
    return qt.point(posX, posY)
}

function calcPickerPosition(control, targetCtrl, qt, enums, screen) {
    var controlPos = targetCtrl.mapToGlobal(0, 0)
    // Wheel area height. 滚轮区域高度。
    var wheelAreaHeight = enums.controlSize.wheelPickerAreaHeight
    // Selected row is at center of wheel area. 选中行在滚轮区域中心。
    var selectedRowCenterY = wheelAreaHeight / 2

    // Align selected row center with control center, fine-tune offset.
    // 选中行中心对齐控件中心，微调偏移。
    var posY = controlPos.y + targetCtrl.height / 2 - selectedRowCenterY
        - enums.spacing.xs - control._panelOffset
    var posX = controlPos.x
        + (targetCtrl.width - control.popupWidth) / 2 - control._panelOffset
    // Screen boundary check. 屏幕边界检查。
    if (screen) {
        posX = Math.max(0, Math.min(posX, screen.width - control._outerWidth))
        posY = Math.max(0, Math.min(posY, screen.height - control._outerHeight))
    }
    return qt.point(posX, posY)
}

function applyTrackedPosition(control, inlinePopup, currentGlobalPos,
                              qt, enums, screen) {
    var newX, newY
    if (control._submenuPlacement) {
        var submenuPos = calcSubmenuPosition(control, qt, enums)
        newX = submenuPos.x
        newY = submenuPos.y
    } else if (control._isPickerMode) {
        var pickerPos = calcPickerPosition(
            control, control.targetControl, qt, enums, screen
        )
        newX = pickerPos.x
        newY = pickerPos.y
    } else {
        newX = currentGlobalPos.x - control._panelOffset
        newY = currentGlobalPos.y + control.targetControl.height
            + enums.popupMetrics.controlGap - control._panelOffset
    }
    if (control._usesControlsPopup && control._inlineParent) {
        var localPos = calcControlsPopupPosition(control, newX, newY, qt)
        inlinePopup.x = localPos.x
        inlinePopup.y = localPos.y
    } else if (control._popupWindow) {
        control._popupWindow.x = newX
        control._popupWindow.y = newY
    }
}
