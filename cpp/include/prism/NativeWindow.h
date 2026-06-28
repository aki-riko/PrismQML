// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - NativeWindow (镜像 Python window/native_window.py)
// frameless 窗口加 WS_CAPTION + 拦 WM_NCCALCSIZE, 让 DWM 接管最小化/最大化动画
#pragma once

#include <QObject>
#include <QVariant>
#include <QSet>
#include <QHash>

namespace prism {

class NativeWindow : public QObject {
    Q_OBJECT

public:
    static NativeWindow *instance();

public slots:
    // QML: NativeWindow.attach(window) / detach(window)
    void attach(const QVariant &window);
    void detach(const QVariant &window);

private:
    explicit NativeWindow(QObject *parent = nullptr);
    static qulonglong winIdFromVariant(const QVariant &window);

    QSet<qulonglong> m_hwnds;
    QHash<qulonglong, qlonglong> m_originalStyles;
};

}  // namespace prism
