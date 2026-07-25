// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - WindowHelper (镜像 Python core/window_helper.py)
#pragma once

#include <QAbstractNativeEventFilter>
#include <QByteArray>
#include <QHash>
#include <QObject>
#include <QString>
#include <QUrl>
#include <QVariant>
#include <QVariantMap>

namespace prism {

// WindowHelper - 任务栏/Alt-Tab 应用图标 (QML: WindowHelper.setAppIcon)
class WindowHelper : public QObject, public QAbstractNativeEventFilter {
    Q_OBJECT
public:
    static WindowHelper *instance();
public slots:
    void setAppIcon(const QString &icon);
    QString resolveDroppedFolderPath(const QUrl &folderUrl) const;
    QVariantMap availableScreenGeometryAt(int x, int y) const;
    bool ensurePopupWindowOwner(
        const QVariant &popupWindow, const QVariant &ownerWindow);
    bool registerWindowFollower(
        const QVariant &hostWindow, const QVariant &followerWindow,
        int edge, qreal logicalExtent);
    bool updateWindowFollowerGeometry(
        const QVariant &hostWindow, const QVariant &followerWindow,
        int edge, qreal logicalExtent);
    bool unregisterWindowFollower(const QVariant &followerWindow);

public:
    bool nativeEventFilter(
        const QByteArray &eventType, void *message, qintptr *result) override;

private:
    explicit WindowHelper(QObject *parent = nullptr) : QObject(parent) {}
    static QString resolveIconPath(const QString &icon);
    static qulonglong winIdFromVariant(const QVariant &window);
    bool ensureFollowerFilterInstalled();
    bool activateWindowGroup(qulonglong windowHwnd);

    struct WindowFollowerBinding {
        qulonglong hostHwnd;
        qulonglong followerHwnd;
        int edge;
        int outwardExtent;
    };

    QHash<qulonglong, WindowFollowerBinding> m_followers;
    bool m_followerFilterInstalled = false;
};

}  // namespace prism
