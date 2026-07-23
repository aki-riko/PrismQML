// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - SystemTrayIcon (镜像 Python window/system_tray.py)
#pragma once

#include <QHash>
#include <QObject>
#include <QPointer>
#include <QString>
#include <functional>

class QAction;
class QQmlComponent;
class QQmlEngine;
class QSystemTrayIcon;
class QMenu;
class QVariant;

namespace prism {

// MessageIcon - 通知图标 (值对齐 QSystemTrayIcon::MessageIcon)
enum class MessageIcon { NoIcon = 0, Information = 1, Warning = 2, Critical = 3 };

// ActivationReason - 托盘激活原因 (值对齐 QSystemTrayIcon::ActivationReason,
// 镜像 Python tray_types.ActivationReason IntEnum)。activated(int) 信号的参数
// 可直接与本枚举比对: if (reason == int(ActivationReason::Trigger)) ...
enum class ActivationReason {
    Unknown = 0,      // QSystemTrayIcon::Unknown
    Context = 1,      // 右键上下文菜单请求
    DoubleClick = 2,  // 双击
    Trigger = 3,      // 单击
    MiddleClick = 4,  // 中键点击
};

struct TrayActionOptions {
    QString actionId;
    QString icon;
    QString shortcut;
    bool checkable = false;
    bool checked = false;
    bool enabled = true;
    QString toolTip;
};

// SystemTrayIcon - 系统托盘 (镜像 Python SystemTrayIcon；优先使用 PrismQML
// 菜单，无 QML 引擎时回退原生 QMenu)
class SystemTrayIcon : public QObject {
    Q_OBJECT
public:
    explicit SystemTrayIcon(const QString &icon = QString(),
                            const QString &toolTip = QString(),
                            QObject *parent = nullptr,
                            QQmlEngine *engine = nullptr,
                            bool menuOnLeftClick = true);
    ~SystemTrayIcon() override;

    void setIcon(const QString &icon);
    void setToolTip(const QString &tip);
    void addAction(const QString &text, std::function<void()> triggered = nullptr,
                   const TrayActionOptions &options = {});
    bool setActionChecked(const QString &actionId, bool checked);
    bool setActionEnabled(const QString &actionId, bool enabled);
    void addSeparator();
    void showMenu();
    void showMessage(const QString &title, const QString &message,
                     MessageIcon icon = MessageIcon::Information, int msecs = 5000);
    void show();
    void hide();
    bool usesPrismMenu() const { return !m_qmlMenu.isNull(); }

    // 托盘是否可用 (无托盘环境返回 false)
    static bool isAvailable();

signals:
    // 托盘被激活。reason 值对齐 QSystemTrayIcon::ActivationReason,
    // 可与 prism::ActivationReason 枚举比对 (如 int(ActivationReason::Trigger))。
    void activated(int reason);
    void messageClicked();
    void aboutToShow();

private slots:
    void onQmlActionTriggered(const QString &actionId);

private:
    bool createPrismMenu(QQmlEngine *engine);
    bool initializePrismMenu();
    void destroyPrismMenu(bool forceReset);
    void addActionToPrismMenu(const QString &text,
                              const TrayActionOptions &options);
    void updatePrismAction(const QString &actionId, const QString &property,
                           const QVariant &value);

    QSystemTrayIcon *m_tray = nullptr;
    QMenu *m_menu = nullptr;
    QQmlComponent *m_qmlComponent = nullptr;
    QPointer<QObject> m_qmlMenu;
    QHash<QString, QAction *> m_actions;
    QHash<QString, std::function<void()>> m_callbacks;
    bool m_menuOnLeftClick = true;
};

}  // namespace prism
