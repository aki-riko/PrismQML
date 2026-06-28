// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - ShadowManager (镜像 Python core/shadow.py, Win32 DWM 阴影)
#pragma once

#include <QObject>
#include <QString>
#include <QVariant>

namespace prism {

// ShadowMode - 阴影模式 (镜像 Python ShadowMode)
enum class ShadowMode { Native, Fallback, None_ };

// ShadowManager - 跨平台窗口阴影管理器(单例)
// QML 调用: enableShadowForWindow / disableShadowForWindow / useNative
class ShadowManager : public QObject {
    Q_OBJECT

    Q_PROPERTY(QString mode READ mode NOTIFY shadowModeChanged)
    Q_PROPERTY(bool useNative READ useNative NOTIFY shadowModeChanged)
    Q_PROPERTY(bool useFallback READ useFallback NOTIFY shadowModeChanged)

public:
    static ShadowManager *instance();

    QString mode() const;
    bool useNative() const;
    bool useFallback() const;

public slots:
    // QML 传入 QQuickWindow 对象 (镜像 @Slot("QVariant"))
    bool enableShadowForWindow(const QVariant &window);
    bool disableShadowForWindow(const QVariant &window);
    // 按句柄 (镜像 @Slot(int))
    bool enableShadow(qulonglong windowId);
    bool disableShadow(qulonglong windowId);

signals:
    void shadowModeChanged(const QString &mode);

private:
    explicit ShadowManager(QObject *parent = nullptr);
    static ShadowMode detectPlatformMode();
    static bool enableDwmShadow(qulonglong hwnd);
    static bool disableDwmShadow(qulonglong hwnd);
    static qulonglong winIdFromVariant(const QVariant &window);

    ShadowMode m_mode;
};

}  // namespace prism
