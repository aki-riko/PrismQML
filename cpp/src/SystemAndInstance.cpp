// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - SystemTrayIcon + SingleInstance 实现
// 镜像 Python window/system_tray.py + core/single_instance.py
#include "prism/SystemTray.h"
#include "prism/SingleInstance.h"
#include "IconPath_p.h"

#include <QSystemTrayIcon>
#include <QMenu>
#include <QAction>
#include <QIcon>
#include <QSharedMemory>
#include <QLocalServer>
#include <QLocalSocket>
#include <QCryptographicHash>
#include <QDebug>

namespace prism {

// ==================== SystemTrayIcon ====================
SystemTrayIcon::SystemTrayIcon(const QString &icon, const QString &toolTip, QObject *parent)
    : QObject(parent) {
    m_tray = new QSystemTrayIcon(this);
    m_menu = new QMenu();
    m_tray->setContextMenu(m_menu);
    if (!icon.isEmpty())
        setIcon(icon);
    if (!toolTip.isEmpty())
        m_tray->setToolTip(toolTip);
    connect(m_tray, &QSystemTrayIcon::activated, this,
            [this](QSystemTrayIcon::ActivationReason reason) {
                emit activated(static_cast<int>(reason));
            });
}

SystemTrayIcon::~SystemTrayIcon() {
    delete m_menu;  // tray 是 child 自动释放, menu 手动
}

void SystemTrayIcon::setIcon(const QString &icon) {
    m_tray->setIcon(QIcon(detail::resolveIconPath(icon)));
}

void SystemTrayIcon::setToolTip(const QString &tip) { m_tray->setToolTip(tip); }

void SystemTrayIcon::addAction(const QString &text, std::function<void()> triggered,
                               const TrayActionOptions &options) {
    const QString actionId = options.actionId.isEmpty() ? text : options.actionId;
    if (m_actions.contains(actionId)) {
        qWarning() << "SystemTrayIcon: duplicate actionId" << actionId;
    }
    QAction *act = m_menu->addAction(text);
    act->setObjectName(actionId);
    act->setCheckable(options.checkable);
    act->setChecked(options.checked);
    act->setEnabled(options.enabled);
    act->setToolTip(options.toolTip);
    m_actions.insert(actionId, act);
    if (triggered) {
        connect(act, &QAction::triggered, this, [triggered]() { triggered(); });
    }
}

bool SystemTrayIcon::setActionChecked(const QString &actionId, bool checked) {
    const auto action = m_actions.constFind(actionId);
    if (action == m_actions.cend() || !action.value())
        return false;
    action.value()->setChecked(checked);
    return true;
}

void SystemTrayIcon::addSeparator() { m_menu->addSeparator(); }

void SystemTrayIcon::showMessage(const QString &title, const QString &message,
                                 MessageIcon icon, int msecs) {
    m_tray->showMessage(title, message,
                        static_cast<QSystemTrayIcon::MessageIcon>(icon), msecs);
}

void SystemTrayIcon::show() { m_tray->show(); }
void SystemTrayIcon::hide() { m_tray->hide(); }
bool SystemTrayIcon::isAvailable() { return QSystemTrayIcon::isSystemTrayAvailable(); }

// ==================== SingleInstance ====================
SingleInstance::SingleInstance(const QString &appId, std::function<void()> onSecondInstance,
                               QObject *parent)
    : QObject(parent), m_appId(appId), m_onSecondInstance(std::move(onSecondInstance)) {
    m_sharedMemory = new QSharedMemory(appId, this);
    // 尝试创建 1 字节共享内存: 成功 = 首个实例; 失败(已存在) = 第二实例
    if (m_sharedMemory->attach()) {
        m_isRunning = true;  // 已有实例
        notifyExistingInstance();
        return;
    }
    if (m_sharedMemory->create(1)) {
        m_isRunning = false;  // 本进程是首个实例
        startServer();
    } else {
        // create 失败也视为已有实例 (竞态兜底)
        m_isRunning = true;
        notifyExistingInstance();
    }
}

SingleInstance::~SingleInstance() {
    if (m_server)
        m_server->close();
    if (m_sharedMemory && m_sharedMemory->isAttached())
        m_sharedMemory->detach();
}

QString SingleInstance::serverName() const {
    // 用 hash 避免特殊字符 (镜像 Python _server_name)
    return QStringLiteral("prism_") +
           QString::fromLatin1(
               QCryptographicHash::hash(m_appId.toUtf8(), QCryptographicHash::Md5).toHex());
}

void SingleInstance::startServer() {
    QLocalServer::removeServer(serverName());
    m_server = new QLocalServer(this);
    if (m_server->listen(serverName())) {
        connect(m_server, &QLocalServer::newConnection, this, [this]() {
            // 第二实例连入 -> 唤起本实例
            if (QLocalSocket *sock = m_server->nextPendingConnection()) {
                sock->deleteLater();
            }
            emit secondInstanceStarted();
            if (m_onSecondInstance)
                m_onSecondInstance();
        });
    }
}

void SingleInstance::notifyExistingInstance() {
    // 连一下已有实例的 server, 触发其唤起
    QLocalSocket socket;
    socket.connectToServer(serverName());
    if (socket.waitForConnected(300)) {
        socket.write("raise");
        socket.flush();
        socket.waitForBytesWritten(300);
        socket.disconnectFromServer();
    }
}

}  // namespace prism
