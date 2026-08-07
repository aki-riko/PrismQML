// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - NativeWindow 实现 (镜像 Python window/native_window.py)
#include "prism/NativeWindow.h"
#include "NativeWindow_p.h"

#include <QWindow>
#include <QCoreApplication>
#include <QAbstractNativeEventFilter>
#include <QByteArray>
#include <QDebug>
#include <memory>
#include <utility>

#ifdef Q_OS_WIN
#  include <windows.h>
#endif

namespace {
// Win32 样式常量 (镜像 Python native_window.py)
constexpr qlonglong kWsCaption = 0x00C00000;
constexpr qlonglong kWsThickframe = 0x00040000;
constexpr qlonglong kWsSysmenu = 0x00080000;
constexpr qlonglong kWsMinimizebox = 0x00020000;
constexpr qlonglong kWsMaximizebox = 0x00010000;
constexpr quint32 kScMaximize = 0xF030;
constexpr quint32 kScRestore = 0xF120;

#ifdef Q_OS_WIN
constexpr UINT kFrameChangedFlags =
    SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED;

class Win32NativeWindowRawApi final : public prism::NativeWindowRawApi {
public:
    void clearLastError() override {
        SetLastError(ERROR_SUCCESS);
    }

    quint32 lastError() override {
        return static_cast<quint32>(GetLastError());
    }

    qlonglong getWindowLongPtr(qulonglong hwnd) override {
        return static_cast<qlonglong>(
            GetWindowLongPtrW(reinterpret_cast<HWND>(hwnd), GWL_STYLE));
    }

    qlonglong setWindowLongPtr(qulonglong hwnd, qlonglong style) override {
        return static_cast<qlonglong>(SetWindowLongPtrW(
            reinterpret_cast<HWND>(hwnd), GWL_STYLE,
            static_cast<LONG_PTR>(style)));
    }

    bool setWindowPos(qulonglong hwnd) override {
        return SetWindowPos(
            reinterpret_cast<HWND>(hwnd), nullptr, 0, 0, 0, 0,
            kFrameChangedFlags) != FALSE;
    }

    bool postSystemCommand(qulonglong hwnd, quint32 command) override {
        return PostMessageW(
                   reinterpret_cast<HWND>(hwnd), WM_SYSCOMMAND,
                   static_cast<WPARAM>(command), 0) != FALSE;
    }
};

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
#endif
}  // namespace

namespace prism {

CheckedNativeWindowPlatform::CheckedNativeWindowPlatform(
    std::unique_ptr<NativeWindowRawApi> rawApi)
    : m_rawApi(std::move(rawApi)) {}

CheckedNativeWindowPlatform::~CheckedNativeWindowPlatform() = default;

bool CheckedNativeWindowPlatform::getStyle(qulonglong hwnd, qlonglong *style,
                                           quint32 *errorCode) {
    if (!m_rawApi || !style || !errorCode)
        return false;
    m_rawApi->clearLastError();
    const qlonglong result = m_rawApi->getWindowLongPtr(hwnd);
    const quint32 error = m_rawApi->lastError();
    if (!nativeLongPtrCallSucceeded(result, error)) {
        *errorCode = error;
        return false;
    }
    *style = result;
    *errorCode = 0;
    return true;
}

bool CheckedNativeWindowPlatform::setStyle(qulonglong hwnd, qlonglong style,
                                           qlonglong *previousStyle,
                                           quint32 *errorCode) {
    if (!m_rawApi || !previousStyle || !errorCode)
        return false;
    m_rawApi->clearLastError();
    const qlonglong result = m_rawApi->setWindowLongPtr(hwnd, style);
    const quint32 error = m_rawApi->lastError();
    if (!nativeLongPtrCallSucceeded(result, error)) {
        *errorCode = error;
        return false;
    }
    *previousStyle = result;
    *errorCode = 0;
    return true;
}

bool CheckedNativeWindowPlatform::applyFrameChanged(qulonglong hwnd,
                                                     quint32 *errorCode) {
    if (!m_rawApi || !errorCode)
        return false;
    m_rawApi->clearLastError();
    const bool succeeded = m_rawApi->setWindowPos(hwnd);
    *errorCode = m_rawApi->lastError();
    return succeeded;
}

bool CheckedNativeWindowPlatform::postSystemCommand(
    qulonglong hwnd, quint32 command, quint32 *errorCode) {
    if (!m_rawApi || !errorCode)
        return false;
    m_rawApi->clearLastError();
    const bool succeeded = m_rawApi->postSystemCommand(hwnd, command);
    *errorCode = m_rawApi->lastError();
    return succeeded;
}

namespace {

std::unique_ptr<NativeWindowPlatform> makeNativeWindowPlatform() {
#ifdef Q_OS_WIN
    return std::make_unique<CheckedNativeWindowPlatform>(
        std::make_unique<Win32NativeWindowRawApi>());
#else
    return nullptr;
#endif
}

void logNativeFailure(const char *operation, qulonglong hwnd,
                      quint32 errorCode) {
    qWarning() << "NativeWindow" << operation << "failed for hwnd" << hwnd
               << "error" << errorCode;
}

}  // namespace

NativeWindow *NativeWindow::instance() {
    static NativeWindow *s = new NativeWindow();
    return s;
}

NativeWindow::NativeWindow(QObject *parent)
    : NativeWindow(makeNativeWindowPlatform(), parent) {
#ifdef Q_OS_WIN
    if (auto *app = QCoreApplication::instance())
        app->installNativeEventFilter(new MsgFilter(&m_hwnds));
#endif
}

NativeWindow::NativeWindow(std::unique_ptr<NativeWindowPlatform> platform,
                           QObject *parent)
    : QObject(parent), m_platform(std::move(platform)) {}

NativeWindow::~NativeWindow() = default;

QObject *NativeWindow::objectFromVariant(const QVariant &window) {
    return qvariant_cast<QObject *>(window);
}

qulonglong NativeWindow::winIdFromObject(QObject *window) {
    if (!window)
        return 0;
    if (auto *w = qobject_cast<QWindow *>(window))
        return static_cast<qulonglong>(w->winId());
    const QVariant v = window->property("winId");
    return v.isValid() ? v.toULongLong() : 0;
}

qlonglong NativeWindow::nativeStyle(qlonglong style) {
    return style | kWsCaption | kWsThickframe | kWsMinimizebox |
           kWsMaximizebox | kWsSysmenu;
}

bool NativeWindow::prepareOwner(QObject *owner, qulonglong hwnd) {
    if (!owner || !hwnd)
        return false;

    auto bindingIt = m_ownerBindings.find(owner);
    if (bindingIt != m_ownerBindings.end() && bindingIt->object == owner) {
        if (bindingIt->retired) {
            if (bindingIt->hwnd == hwnd)
                return false;
            m_ownerBindings.erase(bindingIt);
        } else if (bindingIt->hwnd == hwnd) {
            m_hwndOwners.insert(hwnd, {owner, bindingIt->generation});
            return true;
        } else {
            forgetHwnd(bindingIt->hwnd);
        }
    } else if (bindingIt != m_ownerBindings.end()) {
        m_ownerBindings.erase(bindingIt);
    }

    const auto existingOwner = m_hwndOwners.constFind(hwnd);
    if (existingOwner != m_hwndOwners.cend() &&
        (existingOwner->address != owner ||
         !m_ownerBindings.contains(existingOwner->address) ||
         m_ownerBindings.value(existingOwner->address).object != owner ||
         m_ownerBindings.value(existingOwner->address).generation !=
             existingOwner->generation)) {
        retireHwndOwner(hwnd);
    }

    ++m_nextOwnerGeneration;
    if (m_nextOwnerGeneration == 0)
        ++m_nextOwnerGeneration;
    const quint64 generation = m_nextOwnerGeneration;
    m_ownerBindings.insert(
        owner, {QPointer<QObject>(owner), hwnd, generation, false});
    m_hwndOwners.insert(hwnd, {owner, generation});
    connect(owner, &QObject::destroyed, this,
            [this, owner, generation]() { releaseOwner(owner, generation); });
    return true;
}

qulonglong NativeWindow::trackedHwnd(QObject *owner) const {
    const auto bindingIt = m_ownerBindings.constFind(owner);
    if (bindingIt == m_ownerBindings.cend() || bindingIt->object != owner ||
        bindingIt->retired) {
        return 0;
    }
    const auto ownerIt = m_hwndOwners.constFind(bindingIt->hwnd);
    if (ownerIt == m_hwndOwners.cend() || ownerIt->address != owner ||
        ownerIt->generation != bindingIt->generation) {
        return 0;
    }
    return bindingIt->hwnd;
}

void NativeWindow::releaseOwner(QObject *owner, quint64 generation) {
    const auto bindingIt = m_ownerBindings.find(owner);
    if (bindingIt == m_ownerBindings.end() ||
        bindingIt->generation != generation) {
        return;
    }
    const qulonglong hwnd = bindingIt->hwnd;
    const auto ownerIt = m_hwndOwners.constFind(hwnd);
    if (ownerIt != m_hwndOwners.cend() && ownerIt->address == owner &&
        ownerIt->generation == generation) {
        forgetHwnd(hwnd);
        return;
    }
    m_ownerBindings.erase(bindingIt);
}

void NativeWindow::forgetHwnd(qulonglong hwnd) {
    const OwnerReference owner = m_hwndOwners.take(hwnd);
    if (owner.address) {
        const auto bindingIt = m_ownerBindings.find(owner.address);
        if (bindingIt != m_ownerBindings.end() &&
            bindingIt->generation == owner.generation &&
            bindingIt->hwnd == hwnd) {
            m_ownerBindings.erase(bindingIt);
        }
    }
    m_hwnds.remove(hwnd);
    m_framechangedHwnds.remove(hwnd);
    m_restorePendingHwnds.remove(hwnd);
    m_originalStyles.remove(hwnd);
}

void NativeWindow::retireHwndOwner(qulonglong hwnd) {
    const OwnerReference owner = m_hwndOwners.take(hwnd);
    if (owner.address) {
        const auto bindingIt = m_ownerBindings.find(owner.address);
        if (bindingIt != m_ownerBindings.end() &&
            bindingIt->generation == owner.generation &&
            bindingIt->hwnd == hwnd) {
            bindingIt->retired = true;
        }
    }
    m_hwnds.remove(hwnd);
    m_framechangedHwnds.remove(hwnd);
    m_restorePendingHwnds.remove(hwnd);
    m_originalStyles.remove(hwnd);
}

bool NativeWindow::attach(const QVariant &window) {
    if (!m_platform)
        return true;
    QObject *owner = objectFromVariant(window);
    const qulonglong hwnd = winIdFromObject(owner);
    return owner && hwnd && prepareOwner(owner, hwnd) && attachHwnd(hwnd, true);
}

bool NativeWindow::finalizeAttach(const QVariant &window) {
    if (!m_platform)
        return true;
    QObject *owner = objectFromVariant(window);
    const qulonglong hwnd = winIdFromObject(owner);
    return owner && hwnd && prepareOwner(owner, hwnd) && finalizeHwnd(hwnd);
}

bool NativeWindow::requestMaximize(const QVariant &window) {
    return requestSystemCommand(window, kScMaximize, "PostMessageW maximize");
}

bool NativeWindow::requestRestore(const QVariant &window) {
    return requestSystemCommand(window, kScRestore, "PostMessageW restore");
}

bool NativeWindow::detach(const QVariant &window) {
    if (!m_platform)
        return true;
    QObject *owner = objectFromVariant(window);
    if (!owner)
        return false;
    const qulonglong hwnd = trackedHwnd(owner);
    return !hwnd || detachHwnd(hwnd);
}

bool NativeWindow::attachHwnd(qulonglong hwnd, bool applyFramechanged) {
    if (!hwnd || !m_platform)
        return false;
    if (m_restorePendingHwnds.contains(hwnd))
        return reattachRestoredHwnd(hwnd, applyFramechanged);
    if (m_hwnds.contains(hwnd))
        return !applyFramechanged || applyFramechangedHwnd(hwnd);
    qlonglong observedStyle = 0;
    quint32 errorCode = 0;
    if (!m_platform->getStyle(hwnd, &observedStyle, &errorCode)) {
        logNativeFailure("GetWindowLongPtrW", hwnd, errorCode);
        return false;
    }
    qlonglong previousStyle = 0;
    if (!m_platform->setStyle(hwnd, nativeStyle(observedStyle), &previousStyle,
                              &errorCode)) {
        logNativeFailure("SetWindowLongPtrW", hwnd, errorCode);
        return false;
    }
    m_hwnds.insert(hwnd);
    m_originalStyles.insert(hwnd, previousStyle);
    return !applyFramechanged || applyFramechangedHwnd(hwnd);
}

bool NativeWindow::reattachRestoredHwnd(qulonglong hwnd,
                                        bool applyFramechanged) {
    qlonglong observedStyle = 0;
    quint32 errorCode = 0;
    if (!m_platform ||
        !m_platform->getStyle(hwnd, &observedStyle, &errorCode)) {
        logNativeFailure("GetWindowLongPtrW", hwnd, errorCode);
        return false;
    }
    qlonglong previousStyle = 0;
    if (!m_platform->setStyle(hwnd, nativeStyle(observedStyle), &previousStyle,
                              &errorCode)) {
        logNativeFailure("SetWindowLongPtrW", hwnd, errorCode);
        return false;
    }
    m_originalStyles.insert(hwnd, previousStyle);
    m_restorePendingHwnds.remove(hwnd);
    m_framechangedHwnds.remove(hwnd);
    return !applyFramechanged || applyFramechangedHwnd(hwnd);
}

bool NativeWindow::finalizeHwnd(qulonglong hwnd) {
    if (m_restorePendingHwnds.contains(hwnd))
        return reattachRestoredHwnd(hwnd, true);
    return m_hwnds.contains(hwnd) ? applyFramechangedHwnd(hwnd)
                                  : attachHwnd(hwnd, true);
}

bool NativeWindow::requestFramechangedHwnd(qulonglong hwnd,
                                           const char *operation) {
    quint32 errorCode = 0;
    if (!m_platform || !m_platform->applyFrameChanged(hwnd, &errorCode)) {
        logNativeFailure(operation, hwnd, errorCode);
        return false;
    }
    return true;
}

bool NativeWindow::requestSystemCommand(const QVariant &window,
                                        quint32 command,
                                        const char *operation) {
    if (!m_platform)
        return false;
    QObject *owner = objectFromVariant(window);
    const qulonglong hwnd = winIdFromObject(owner);
    if (!owner || !hwnd)
        return false;
    quint32 errorCode = 0;
    if (!m_platform->postSystemCommand(hwnd, command, &errorCode)) {
        logNativeFailure(operation, hwnd, errorCode);
        return false;
    }
    return true;
}

bool NativeWindow::applyFramechangedHwnd(qulonglong hwnd) {
    if (m_framechangedHwnds.contains(hwnd))
        return true;
    if (!requestFramechangedHwnd(hwnd, "SetWindowPos"))
        return false;
    m_framechangedHwnds.insert(hwnd);
    return true;
}

bool NativeWindow::detachHwnd(qulonglong hwnd) {
    if (!m_hwnds.contains(hwnd)) {
        forgetHwnd(hwnd);
        return true;
    }
    if (!m_originalStyles.contains(hwnd) || !m_platform) {
        qCritical() << "NativeWindow missing tracked style for hwnd" << hwnd;
        return false;
    }
    if (m_restorePendingHwnds.contains(hwnd)) {
        if (!requestFramechangedHwnd(hwnd, "restore SetWindowPos"))
            return false;
        forgetHwnd(hwnd);
        return true;
    }
    quint32 errorCode = 0;
    qlonglong discardedStyle = 0;
    if (!m_platform->setStyle(hwnd, m_originalStyles.value(hwnd),
                              &discardedStyle, &errorCode)) {
        logNativeFailure("restore SetWindowLongPtrW", hwnd, errorCode);
        return false;
    }
    m_framechangedHwnds.remove(hwnd);
    m_restorePendingHwnds.insert(hwnd);
    if (!requestFramechangedHwnd(hwnd, "restore SetWindowPos"))
        return false;
    forgetHwnd(hwnd);
    return true;
}

}  // namespace prism
