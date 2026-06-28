// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - MicaManager 实现 (镜像 Python window/mica_window.py)
#include "prism/MicaManager.h"

#include <QWindow>
#include <QOperatingSystemVersion>
#include <QDebug>

#ifdef Q_OS_WIN
#  include <windows.h>
#  include <dwmapi.h>
// DWM 常量 (镜像 Python mica_window.py)
namespace {
constexpr int kDwmwaUseImmersiveDarkMode = 20;
constexpr int kDwmwaWindowCornerPreference = 33;
constexpr int kDwmwaSystemBackdropType = 38;   // 需 Build >= 22621
constexpr int kDwmwcpRound = 2;
constexpr int kDwmBackdropNone = 1;            // DWMSBT_NONE
constexpr int kDwmBackdropMica = 2;            // DWMSBT_MAINWINDOW (Mica)
constexpr int kWin11BuildThreshold = 22000;
constexpr int kWin11BackdropBuildThreshold = 22621;
}  // namespace
#endif

namespace prism {

MicaManager *MicaManager::instance() {
    static MicaManager *s = new MicaManager();
    return s;
}

MicaManager::MicaManager(QObject *parent)
    : QObject(parent), m_isWin11(detectWin11()) {}

bool MicaManager::detectWin11() {
#ifdef Q_OS_WIN
    // 用 RtlGetVersion 拿真实 build (镜像 Python sys.getwindowsversion().build >= 22000)
    typedef LONG(WINAPI * RtlGetVersionPtr)(PRTL_OSVERSIONINFOW);
    if (HMODULE hMod = GetModuleHandleW(L"ntdll.dll")) {
        auto fn = reinterpret_cast<RtlGetVersionPtr>(
            reinterpret_cast<void *>(GetProcAddress(hMod, "RtlGetVersion")));
        if (fn) {
            RTL_OSVERSIONINFOW info{};
            info.dwOSVersionInfoSize = sizeof(info);
            if (fn(&info) == 0)
                return info.dwBuildNumber >= kWin11BuildThreshold;
        }
    }
    return false;
#else
    return false;
#endif
}

qulonglong MicaManager::winIdFromVariant(const QVariant &window) {
    QObject *obj = qvariant_cast<QObject *>(window);
    if (!obj)
        return 0;
    if (auto *w = qobject_cast<QWindow *>(obj))
        return static_cast<qulonglong>(w->winId());
    const QVariant v = obj->property("winId");
    return v.isValid() ? v.toULongLong() : 0;
}

bool MicaManager::applyMica(qulonglong hwnd, bool enabled) {
#ifdef Q_OS_WIN
    if (!m_isWin11 || !hwnd)
        return false;
    HWND h = reinterpret_cast<HWND>(hwnd);
    m_currentHwnd = hwnd;

    // 圆角 (镜像 Python: DWMWCP_ROUND)
    int corner = kDwmwcpRound;
    DwmSetWindowAttribute(h, kDwmwaWindowCornerPreference, &corner, sizeof(corner));

    // 背景类型需 Build >= 22621
    typedef LONG(WINAPI * RtlGetVersionPtr)(PRTL_OSVERSIONINFOW);
    DWORD build = 0;
    if (HMODULE hMod = GetModuleHandleW(L"ntdll.dll")) {
        auto fn = reinterpret_cast<RtlGetVersionPtr>(
            reinterpret_cast<void *>(GetProcAddress(hMod, "RtlGetVersion")));
        if (fn) {
            RTL_OSVERSIONINFOW info{};
            info.dwOSVersionInfoSize = sizeof(info);
            if (fn(&info) == 0)
                build = info.dwBuildNumber;
        }
    }
    if (build < static_cast<DWORD>(kWin11BackdropBuildThreshold)) {
        qWarning() << "prism::MicaManager: 背景类型需 Build >=" << kWin11BackdropBuildThreshold
                   << "当前" << build;
        return false;
    }

    int backdrop = enabled ? kDwmBackdropMica : kDwmBackdropNone;
    HRESULT r = DwmSetWindowAttribute(h, kDwmwaSystemBackdropType, &backdrop, sizeof(backdrop));
    return SUCCEEDED(r);
#else
    Q_UNUSED(hwnd); Q_UNUSED(enabled);
    return false;
#endif
}

bool MicaManager::setMicaEffect(const QVariant &window, bool enabled, bool dark) {
#ifdef Q_OS_WIN
    if (!m_isWin11)
        return false;
    const qulonglong hwnd = winIdFromVariant(window);
    if (!hwnd) {
        qWarning() << "prism::MicaManager: 无法设置云母, 窗口句柄无效";
        return false;
    }
    m_currentHwnd = hwnd;
    HWND h = reinterpret_cast<HWND>(hwnd);

    // 深色模式 (镜像 Python: DWMWA_USE_IMMERSIVE_DARK_MODE)
    int darkVal = dark ? 1 : 0;
    DwmSetWindowAttribute(h, kDwmwaUseImmersiveDarkMode, &darkVal, sizeof(darkVal));

    const bool ok = applyMica(hwnd, enabled);
    if (ok) {
        m_micaEnabled = enabled;
        emit micaEnabledChanged(enabled);
    }
    return ok;
#else
    Q_UNUSED(window); Q_UNUSED(enabled); Q_UNUSED(dark);
    return false;
#endif
}

void MicaManager::updateDarkMode(bool dark) {
#ifdef Q_OS_WIN
    if (!m_isWin11 || !m_currentHwnd)
        return;
    HWND h = reinterpret_cast<HWND>(m_currentHwnd);
    int darkVal = dark ? 1 : 0;
    DwmSetWindowAttribute(h, kDwmwaUseImmersiveDarkMode, &darkVal, sizeof(darkVal));
#else
    Q_UNUSED(dark);
#endif
}

}  // namespace prism
