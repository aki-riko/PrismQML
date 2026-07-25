// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - Windows 弹层 owner 修复
#include "prism/WindowHelper.h"

#include <QWindow>

#ifdef Q_OS_WIN
#  include <windows.h>
#endif

namespace prism {

bool WindowHelper::ensurePopupWindowOwner(
    const QVariant &popupWindow, const QVariant &ownerWindow) {
#ifdef Q_OS_WIN
    QObject *popupObject = qvariant_cast<QObject *>(popupWindow);
    QObject *ownerObject = qvariant_cast<QObject *>(ownerWindow);
    auto *nativePopupWindow = qobject_cast<QWindow *>(popupObject);
    auto *nativeOwnerWindow = qobject_cast<QWindow *>(ownerObject);
    if (!nativePopupWindow || !nativeOwnerWindow
        || (nativePopupWindow->flags() & Qt::WindowType_Mask) != Qt::Popup) {
        return false;
    }

    const qulonglong popupId = static_cast<qulonglong>(nativePopupWindow->winId());
    const qulonglong ownerId = static_cast<qulonglong>(nativeOwnerWindow->winId());
    if (!popupId || !ownerId || popupId == ownerId)
        return false;

    const HWND popupHwnd = reinterpret_cast<HWND>(popupId);
    const HWND ownerHwnd = reinterpret_cast<HWND>(ownerId);
    DWORD popupProcessId = 0;
    DWORD ownerProcessId = 0;
    if (!GetWindowThreadProcessId(popupHwnd, &popupProcessId)
        || !GetWindowThreadProcessId(ownerHwnd, &ownerProcessId)
        || popupProcessId != GetCurrentProcessId()
        || ownerProcessId != popupProcessId) {
        return false;
    }

    if (GetWindow(popupHwnd, GW_OWNER) != ownerHwnd) {
        SetLastError(ERROR_SUCCESS);
        const LONG_PTR previousOwner = SetWindowLongPtrW(
            popupHwnd,
            GWLP_HWNDPARENT,
            reinterpret_cast<LONG_PTR>(ownerHwnd));
        if (!previousOwner && GetLastError() != ERROR_SUCCESS)
            return false;
        if (GetWindow(popupHwnd, GW_OWNER) != ownerHwnd)
            return false;
    }

    return SetWindowPos(
        popupHwnd,
        HWND_TOP,
        0,
        0,
        0,
        0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOOWNERZORDER);
#else
    Q_UNUSED(popupWindow);
    Q_UNUSED(ownerWindow);
    return false;
#endif
}

}  // namespace prism
