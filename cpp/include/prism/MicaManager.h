// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - MicaManager (镜像 Python window/mica_window.py, Win11 DWM 云母)
#pragma once

#include <QObject>
#include <QVariant>

namespace prism {

// MicaManager - Windows 11 云母背景管理器(单例)
// QML 调用: setMicaEffect(window, enabled, dark) / updateDarkMode(dark) / isWin11
class MicaManager : public QObject {
    Q_OBJECT

    Q_PROPERTY(bool isWin11 READ isWin11 CONSTANT)
    Q_PROPERTY(bool micaEnabled READ micaEnabled NOTIFY micaEnabledChanged)

public:
    static MicaManager *instance();

    bool isWin11() const { return m_isWin11; }
    bool micaEnabled() const { return m_micaEnabled; }

public slots:
    // QML: setMicaEffect(QQuickWindow, bool, bool) -> bool
    bool setMicaEffect(const QVariant &window, bool enabled, bool dark = false);
    void updateDarkMode(bool dark);

signals:
    void micaEnabledChanged(bool enabled);

private:
    explicit MicaManager(QObject *parent = nullptr);
    static bool detectWin11();
    bool applyMica(qulonglong hwnd, bool enabled);
    static qulonglong winIdFromVariant(const QVariant &window);

    bool m_isWin11;
    bool m_micaEnabled = false;
    qulonglong m_currentHwnd = 0;
};

}  // namespace prism
