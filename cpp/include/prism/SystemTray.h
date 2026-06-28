// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - SystemTrayIcon (镜像 Python window/system_tray.py)
#pragma once

#include <QObject>
#include <QString>
#include <functional>

class QSystemTrayIcon;
class QMenu;

namespace prism {

// MessageIcon - 通知图标 (值对齐 QSystemTrayIcon::MessageIcon)
enum class MessageIcon { NoIcon = 0, Information = 1, Warning = 2, Critical = 3 };

// SystemTrayIcon - 系统托盘 (镜像 Python SystemTrayIcon, 封装 QSystemTrayIcon+QMenu)
class SystemTrayIcon : public QObject {
    Q_OBJECT
public:
    explicit SystemTrayIcon(const QString &icon = QString(),
                            const QString &toolTip = QString(),
                            QObject *parent = nullptr);
    ~SystemTrayIcon() override;

    void setIcon(const QString &icon);
    void setToolTip(const QString &tip);
    void addAction(const QString &text, std::function<void()> triggered = nullptr);
    void addSeparator();
    void showMessage(const QString &title, const QString &message,
                     MessageIcon icon = MessageIcon::Information, int msecs = 5000);
    void show();
    void hide();

    // 托盘是否可用 (无托盘环境返回 false)
    static bool isAvailable();

signals:
    void activated(int reason);  // 对齐 QSystemTrayIcon::ActivationReason int

private:
    QSystemTrayIcon *m_tray = nullptr;
    QMenu *m_menu = nullptr;
};

}  // namespace prism
