// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - ShadowManager 实现 (镜像 Python core/shadow.py)
#include "prism/ShadowManager.h"

#include <QWindow>
#include <QDebug>
#include <QCoreApplication>
#include <QAbstractNativeEventFilter>
#include <QByteArray>

#ifdef Q_OS_WIN
#  include <windows.h>
#  include <dwmapi.h>
#endif

namespace prism {

ShadowManager *ShadowManager::instance() {
    static ShadowManager *s = new ShadowManager();
    return s;
}

ShadowManager::ShadowManager(QObject *parent)
    : QObject(parent), m_mode(detectPlatformMode()) {}

ShadowMode ShadowManager::detectPlatformMode() {
#if defined(Q_OS_WIN) || defined(Q_OS_MACOS)
    return ShadowMode::Native;
#else
    return ShadowMode::Fallback;
#endif
}

QString ShadowManager::mode() const {
    switch (m_mode) {
        case ShadowMode::Native:   return QStringLiteral("native");
        case ShadowMode::Fallback: return QStringLiteral("fallback");
        case ShadowMode::None_:    return QStringLiteral("none");
    }
    return QStringLiteral("none");
}

bool ShadowManager::useNative() const { return m_mode == ShadowMode::Native; }
bool ShadowManager::useFallback() const { return m_mode == ShadowMode::Fallback; }

// 从 QML 传入的 QQuickWindow/QWindow QVariant 提取原生句柄
qulonglong ShadowManager::winIdFromVariant(const QVariant &window) {
    QObject *obj = qvariant_cast<QObject *>(window);
    if (!obj)
        return 0;
    if (auto *w = qobject_cast<QWindow *>(obj))
        return static_cast<qulonglong>(w->winId());
    // QQuickWindow 是 QWindow 子类, qobject_cast 已覆盖; 兜底读 winId 属性
    const QVariant v = obj->property("winId");
    return v.isValid() ? v.toULongLong() : 0;
}

bool ShadowManager::enableShadowForWindow(const QVariant &window) {
    if (m_mode != ShadowMode::Native)
        return false;
    const qulonglong hwnd = winIdFromVariant(window);
    if (!hwnd) {
        qWarning() << "prism::ShadowManager: 无法获取窗口句柄";
        return false;
    }
    return enableShadow(hwnd);
}

bool ShadowManager::disableShadowForWindow(const QVariant &window) {
    const qulonglong hwnd = winIdFromVariant(window);
    if (!hwnd)
        return false;
    return disableShadow(hwnd);
}

bool ShadowManager::enableShadow(qulonglong windowId) {
    if (m_mode != ShadowMode::Native)
        return false;
#ifdef Q_OS_WIN
    return enableDwmShadow(windowId);
#else
    Q_UNUSED(windowId);
    return false;
#endif
}

bool ShadowManager::disableShadow(qulonglong windowId) {
#ifdef Q_OS_WIN
    return disableDwmShadow(windowId);
#else
    Q_UNUSED(windowId);
    return false;
#endif
}

#ifdef Q_OS_WIN
// 启用 DWM 阴影 (镜像 Python _enableDwmShadow)
bool ShadowManager::enableDwmShadow(qulonglong hwnd) {
    HWND h = reinterpret_cast<HWND>(hwnd);

    // DWMWA_NCRENDERING_POLICY=2, DWMNCRP_ENABLED=2 启用非客户区渲染
    int policy = 2;  // DWMNCRP_ENABLED
    DwmSetWindowAttribute(h, 2 /*DWMWA_NCRENDERING_POLICY*/, &policy, sizeof(policy));

    // 1px MARGINS 触发阴影
    MARGINS margins = {1, 1, 1, 1};
    HRESULT r = DwmExtendFrameIntoClientArea(h, &margins);

    // 强制重绘
    SetWindowPos(h, nullptr, 0, 0, 0, 0,
                 SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER);
    return SUCCEEDED(r);
}

// 禁用 DWM 阴影 (镜像 Python _disableDwmShadow)
bool ShadowManager::disableDwmShadow(qulonglong hwnd) {
    HWND h = reinterpret_cast<HWND>(hwnd);
    int policy = 0;  // DWMNCRP_USEWINDOWSTYLE
    DwmSetWindowAttribute(h, 2 /*DWMWA_NCRENDERING_POLICY*/, &policy, sizeof(policy));
    MARGINS margins = {0, 0, 0, 0};
    DwmExtendFrameIntoClientArea(h, &margins);
    return true;
}
#endif

// ==================== DWM 同步事件过滤器 (镜像 Python DwmSyncFilter) ====================
#ifdef Q_OS_WIN
namespace {
// WM_SIZING/WM_SIZE/WM_MOVING 时调 DwmFlush, 消除无边框窗口 resize 撕裂
class DwmSyncFilter : public QAbstractNativeEventFilter {
public:
    bool nativeEventFilter(const QByteArray &eventType, void *message,
                           qintptr * /*result*/) override {
        if (eventType != "windows_generic_MSG")
            return false;
        MSG *msg = static_cast<MSG *>(message);
        if (!msg)
            return false;
        switch (msg->message) {
            case WM_SIZING:   // 0x0214
            case WM_SIZE:     // 0x0005
            case WM_MOVING:   // 0x0216
                DwmFlush();
                break;
            case WM_ENTERSIZEMOVE:  // 0x0231
                m_inResize = true;
                break;
            case WM_EXITSIZEMOVE:   // 0x0232
                m_inResize = false;
                break;
            default:
                break;
        }
        return false;  // 不拦截消息, 继续传递 (镜像 Python return False,0)
    }

private:
    bool m_inResize = false;
};
}  // namespace
#endif

bool ShadowManager::installDwmSyncFilter() {
#ifdef Q_OS_WIN
    static DwmSyncFilter *s_filter = nullptr;
    if (s_filter)
        return true;  // 已安装 (幂等)
    QCoreApplication *app = QCoreApplication::instance();
    if (!app) {
        qWarning() << "prism::installDwmSyncFilter: QCoreApplication 未创建";
        return false;
    }
    s_filter = new DwmSyncFilter();
    app->installNativeEventFilter(s_filter);
    qInfo() << "prism: DWM 同步过滤器已安装";
    return true;
#else
    // 非 Windows: 无 DWM, 诚实降级 no-op
    return false;
#endif
}

}  // namespace prism
