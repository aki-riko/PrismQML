// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - NativeWindow 实现 (镜像 Python window/native_window.py)
#include "prism/NativeWindow.h"

#include <QWindow>
#include <QCoreApplication>
#include <QAbstractNativeEventFilter>
#include <QByteArray>
#include <QDebug>

#ifdef Q_OS_WIN
#  include <windows.h>
namespace {
// Win32 样式常量 (镜像 Python native_window.py)
constexpr LONG_PTR kWsCaption = 0x00C00000;
constexpr LONG_PTR kWsThickframe = 0x00040000;
constexpr LONG_PTR kWsSysmenu = 0x00080000;
constexpr LONG_PTR kWsMinimizebox = 0x00020000;
constexpr LONG_PTR kWsMaximizebox = 0x00010000;

// 拦 WM_NCCALCSIZE 让客户区 = 整个窗口 (镜像 Python _MsgFilter)
class MsgFilter : public QAbstractNativeEventFilter {
public:
    explicit MsgFilter(QSet<qulonglong> *hwnds) : m_hwnds(hwnds) {}

    bool nativeEventFilter(const QByteArray &eventType, void *message,
                           qintptr * /*result*/) override {
        if (eventType != "windows_generic_MSG")
            return false;
        MSG *msg = static_cast<MSG *>(message);
        if (!msg || msg->message != WM_NCCALCSIZE)
            return false;
        const qulonglong hwnd = reinterpret_cast<qulonglong>(msg->hwnd);
        if (!m_hwnds->contains(hwnd))
            return false;
        if (!msg->wParam)
            return false;
        // 最大化时扣 8px 防超出工作区
        if (IsZoomed(msg->hwnd)) {
            auto *params = reinterpret_cast<NCCALCSIZE_PARAMS *>(msg->lParam);
            params->rgrc[0].left += 8;
            params->rgrc[0].top += 8;
            params->rgrc[0].right -= 8;
            params->rgrc[0].bottom -= 8;
        }
        // 返回 true + result 0: 客户区扩展到整窗 (Qt 会把 result 设为我们要的 0)
        return true;
    }

private:
    QSet<qulonglong> *m_hwnds;
};
}  // namespace
#endif

namespace prism {

NativeWindow *NativeWindow::instance() {
    static NativeWindow *s = new NativeWindow();
    return s;
}

NativeWindow::NativeWindow(QObject *parent) : QObject(parent) {
#ifdef Q_OS_WIN
    if (auto *app = QCoreApplication::instance())
        app->installNativeEventFilter(new MsgFilter(&m_hwnds));
#endif
}

qulonglong NativeWindow::winIdFromVariant(const QVariant &window) {
    QObject *obj = qvariant_cast<QObject *>(window);
    if (!obj)
        return 0;
    if (auto *w = qobject_cast<QWindow *>(obj))
        return static_cast<qulonglong>(w->winId());
    const QVariant v = obj->property("winId");
    return v.isValid() ? v.toULongLong() : 0;
}

void NativeWindow::attach(const QVariant &window) {
#ifdef Q_OS_WIN
    const qulonglong hwnd = winIdFromVariant(window);
    if (!hwnd || m_hwnds.contains(hwnd))
        return;
    HWND h = reinterpret_cast<HWND>(hwnd);
    LONG_PTR original = GetWindowLongPtrW(h, GWL_STYLE);
    LONG_PTR neo = original | kWsCaption | kWsThickframe | kWsMinimizebox
                   | kWsMaximizebox | kWsSysmenu;
    SetWindowLongPtrW(h, GWL_STYLE, neo);
    m_hwnds.insert(hwnd);
    m_originalStyles.insert(hwnd, original);
    SetWindowPos(h, nullptr, 0, 0, 0, 0,
                 SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED);
#else
    Q_UNUSED(window);
#endif
}

void NativeWindow::detach(const QVariant &window) {
#ifdef Q_OS_WIN
    const qulonglong hwnd = winIdFromVariant(window);
    if (!m_hwnds.contains(hwnd))
        return;
    HWND h = reinterpret_cast<HWND>(hwnd);
    SetWindowLongPtrW(h, GWL_STYLE, static_cast<LONG_PTR>(m_originalStyles.value(hwnd)));
    SetWindowPos(h, nullptr, 0, 0, 0, 0,
                 SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED);
    m_hwnds.remove(hwnd);
    m_originalStyles.remove(hwnd);
#else
    Q_UNUSED(window);
#endif
}

}  // namespace prism
