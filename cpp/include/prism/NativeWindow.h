// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - NativeWindow (镜像 Python window/native_window.py)
// frameless 窗口加 WS_CAPTION + 拦 WM_NCCALCSIZE, 让 DWM 接管最小化/最大化动画
#pragma once

#include <QObject>
#include <QHash>
#include <QPointer>
#include <QSet>
#include <QVariant>
#include <memory>

namespace prism {

class NativeWindowPlatform;
struct NativeWindowTestAccess;

class NativeWindow : public QObject {
    Q_OBJECT

public:
    static NativeWindow *instance();
    ~NativeWindow() override;

public slots:
    // QML: NativeWindow.attach/finalizeAttach/detach(window)
    bool attach(const QVariant &window);
    bool finalizeAttach(const QVariant &window);
    bool detach(const QVariant &window);

private:
    struct OwnerBinding {
        QPointer<QObject> object;
        qulonglong hwnd = 0;
        quint64 generation = 0;
        bool retired = false;
    };

    struct OwnerReference {
        QObject *address = nullptr;
        quint64 generation = 0;
    };

    friend struct NativeWindowTestAccess;

    explicit NativeWindow(QObject *parent = nullptr);
    explicit NativeWindow(std::unique_ptr<NativeWindowPlatform> platform,
                          QObject *parent = nullptr);
    static QObject *objectFromVariant(const QVariant &window);
    static qulonglong winIdFromObject(QObject *window);
    static qlonglong nativeStyle(qlonglong style);
    bool prepareOwner(QObject *owner, qulonglong hwnd);
    qulonglong trackedHwnd(QObject *owner) const;
    void releaseOwner(QObject *owner, quint64 generation);
    void forgetHwnd(qulonglong hwnd);
    void retireHwndOwner(qulonglong hwnd);
    bool attachHwnd(qulonglong hwnd, bool applyFramechanged);
    bool reattachRestoredHwnd(qulonglong hwnd, bool applyFramechanged);
    bool finalizeHwnd(qulonglong hwnd);
    bool requestFramechangedHwnd(qulonglong hwnd, const char *operation);
    bool applyFramechangedHwnd(qulonglong hwnd);
    bool detachHwnd(qulonglong hwnd);

    std::unique_ptr<NativeWindowPlatform> m_platform;
    QSet<qulonglong> m_hwnds;
    QSet<qulonglong> m_framechangedHwnds;
    QSet<qulonglong> m_restorePendingHwnds;
    QHash<qulonglong, qlonglong> m_originalStyles;
    QHash<QObject *, OwnerBinding> m_ownerBindings;
    QHash<qulonglong, OwnerReference> m_hwndOwners;
    quint64 m_nextOwnerGeneration = 0;
};

}  // namespace prism
