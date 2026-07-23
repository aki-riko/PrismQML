// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - SystemTrayIcon + SingleInstance 实现
// 镜像 Python window/system_tray.py + core/single_instance.py
#include "prism/SystemTray.h"
#include "prism/SingleInstance.h"
#include "IconPath_p.h"

#include <QAction>
#include <QCryptographicHash>
#include <QCursor>
#include <QDebug>
#include <QDir>
#include <QFileInfo>
#include <QIcon>
#include <QLocalServer>
#include <QLocalSocket>
#include <QMenu>
#include <QMetaObject>
#include <QQmlComponent>
#include <QQmlContext>
#include <QQmlEngine>
#include <QSharedMemory>
#include <QStringList>
#include <QSystemTrayIcon>
#include <QUrl>
#include <QVariant>
#include <QVariantMap>

namespace prism {
namespace {

constexpr char kPrismTrayMenuRelativePath[] =
    "PrismQML/controls/menus/SystemTrayMenu.qml";

QUrl prismTrayMenuUrl(QQmlEngine *engine) {
    const QString relativePath = QString::fromLatin1(kPrismTrayMenuRelativePath);
    for (const QString &importPath : engine->importPathList()) {
        if (importPath.startsWith(QStringLiteral("qrc:"))) {
            QString root = importPath;
            if (!root.endsWith(QLatin1Char('/')))
                root.append(QLatin1Char('/'));
            const QUrl candidate(root + relativePath);
            if (QFileInfo::exists(QStringLiteral(":") + candidate.path()))
                return candidate;
            continue;
        }
        const QUrl importUrl(importPath);
        const QString localRoot = importUrl.isLocalFile()
                                      ? importUrl.toLocalFile()
                                      : importPath;
        const QString candidate = QDir(localRoot).filePath(relativePath);
        if (QFileInfo::exists(candidate))
            return QUrl::fromLocalFile(candidate);
    }
    return {};
}

QVariantMap qmlActionOptions(const QString &actionId,
                             const TrayActionOptions &options) {
    return {
        {QStringLiteral("actionId"), actionId},
        {QStringLiteral("checkable"), options.checkable},
        {QStringLiteral("checked"), options.checked},
        {QStringLiteral("enabled"), options.enabled},
        {QStringLiteral("toolTip"), options.toolTip},
    };
}

}  // namespace

// ==================== SystemTrayIcon ====================
SystemTrayIcon::SystemTrayIcon(const QString &icon, const QString &toolTip,
                               QObject *parent, QQmlEngine *engine,
                               bool menuOnLeftClick)
    : QObject(parent), m_menuOnLeftClick(menuOnLeftClick) {
    m_tray = new QSystemTrayIcon(this);
    m_menu = new QMenu();
    if (!createPrismMenu(engine))
        m_tray->setContextMenu(m_menu);
    if (!icon.isEmpty())
        setIcon(icon);
    if (!toolTip.isEmpty())
        m_tray->setToolTip(toolTip);
    connect(m_menu, &QMenu::aboutToShow, this, &SystemTrayIcon::aboutToShow);
    connect(m_tray, &QSystemTrayIcon::activated, this,
            [this](QSystemTrayIcon::ActivationReason reason) {
                const bool shouldShowMenu =
                    reason == QSystemTrayIcon::Context ||
                    (reason == QSystemTrayIcon::Trigger && m_menuOnLeftClick);
                if (shouldShowMenu && (usesPrismMenu() ||
                                       reason == QSystemTrayIcon::Trigger)) {
                    showMenu();
                }
                emit activated(static_cast<int>(reason));
            });
    connect(m_tray, &QSystemTrayIcon::messageClicked,
            this, &SystemTrayIcon::messageClicked);
}

SystemTrayIcon::~SystemTrayIcon() {
    m_tray->hide();
    destroyPrismMenu(true);
    delete m_menu;  // tray 是 child 自动释放, menu 手动
}

bool SystemTrayIcon::createPrismMenu(QQmlEngine *engine) {
    if (!engine)
        return false;
    const QUrl menuUrl = prismTrayMenuUrl(engine);
    if (menuUrl.isEmpty()) {
        qWarning() << "SystemTrayIcon: PrismQML SystemTrayMenu.qml not found";
        return false;
    }
    m_qmlComponent = new QQmlComponent(
        engine, menuUrl, QQmlComponent::PreferSynchronous);
    if (m_qmlComponent->isError()) {
        QStringList errors;
        for (const QQmlError &error : m_qmlComponent->errors())
            errors.append(error.toString());
        qWarning().noquote()
            << "SystemTrayIcon: failed to load PrismQML menu:\n"
            << errors.join(QLatin1Char('\n'));
        destroyPrismMenu(false);
        return false;
    }
    m_qmlMenu = m_qmlComponent->create(engine->rootContext());
    if (!m_qmlMenu) {
        qWarning() << "SystemTrayIcon: failed to create PrismQML menu";
        destroyPrismMenu(false);
        return false;
    }
    return initializePrismMenu();
}

bool SystemTrayIcon::initializePrismMenu() {
    m_qmlMenu->setObjectName(QStringLiteral("prismSystemTrayMenu"));
    m_qmlMenu->setParent(this);
    const bool connected = connect(m_qmlMenu, SIGNAL(actionTriggered(QString)),
                                   this, SLOT(onQmlActionTriggered(QString)));
    if (connected)
        return true;
    qWarning() << "SystemTrayIcon: PrismQML action signal unavailable";
    destroyPrismMenu(false);
    return false;
}

void SystemTrayIcon::destroyPrismMenu(bool forceReset) {
    if (m_qmlMenu) {
        if (forceReset) {
            QMetaObject::invokeMethod(m_qmlMenu, "forceReset",
                                      Qt::DirectConnection);
        }
        delete m_qmlMenu.data();
        m_qmlMenu = nullptr;
    }
    delete m_qmlComponent;
    m_qmlComponent = nullptr;
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
    if (!options.icon.isEmpty()) {
        const QIcon actionIcon(detail::resolveIconPath(options.icon));
        if (!actionIcon.isNull())
            act->setIcon(actionIcon);
    }
    if (!options.shortcut.isEmpty())
        act->setShortcut(options.shortcut);
    m_actions.insert(actionId, act);
    if (triggered)
        m_callbacks.insert(actionId, std::move(triggered));
    connect(act, &QAction::triggered, this,
            [this, actionId]() { onQmlActionTriggered(actionId); });
    addActionToPrismMenu(text, options);
}

void SystemTrayIcon::addActionToPrismMenu(
    const QString &text, const TrayActionOptions &options) {
    if (!m_qmlMenu)
        return;
    const QString actionId = options.actionId.isEmpty() ? text : options.actionId;
    const QVariant textArg(text);
    const QVariant iconArg(options.icon);
    const QVariant shortcutArg(options.shortcut);
    const QVariant optionsArg(qmlActionOptions(actionId, options));
    if (!QMetaObject::invokeMethod(
            m_qmlMenu, "addAction", Qt::DirectConnection,
            Q_ARG(QVariant, textArg), Q_ARG(QVariant, iconArg),
            Q_ARG(QVariant, shortcutArg), Q_ARG(QVariant, optionsArg))) {
        qWarning() << "SystemTrayIcon: PrismQML addAction failed" << actionId;
    }
}

void SystemTrayIcon::onQmlActionTriggered(const QString &actionId) {
    const std::function<void()> callback = m_callbacks.value(actionId);
    if (callback)
        callback();
}

void SystemTrayIcon::updatePrismAction(const QString &actionId,
                                       const QString &property,
                                       const QVariant &value) {
    if (!m_qmlMenu)
        return;
    const QVariant actionArg(actionId);
    const QVariant propertiesArg(QVariantMap{{property, value}});
    if (!QMetaObject::invokeMethod(
            m_qmlMenu, "updateAction", Qt::DirectConnection,
            Q_ARG(QVariant, actionArg), Q_ARG(QVariant, propertiesArg))) {
        qWarning() << "SystemTrayIcon: PrismQML updateAction failed" << actionId;
    }
}

bool SystemTrayIcon::setActionChecked(const QString &actionId, bool checked) {
    const auto action = m_actions.constFind(actionId);
    if (action == m_actions.cend() || !action.value())
        return false;
    action.value()->setChecked(checked);
    updatePrismAction(actionId, QStringLiteral("checked"), checked);
    return true;
}

bool SystemTrayIcon::setActionEnabled(const QString &actionId, bool enabled) {
    const auto action = m_actions.constFind(actionId);
    if (action == m_actions.cend() || !action.value())
        return false;
    action.value()->setEnabled(enabled);
    updatePrismAction(actionId, QStringLiteral("enabled"), enabled);
    return true;
}

void SystemTrayIcon::addSeparator() {
    m_menu->addSeparator();
    if (m_qmlMenu && !QMetaObject::invokeMethod(
                         m_qmlMenu, "addSeparator", Qt::DirectConnection)) {
        qWarning() << "SystemTrayIcon: PrismQML addSeparator failed";
    }
}

void SystemTrayIcon::showMenu() {
    const QPoint position = QCursor::pos();
    if (m_qmlMenu) {
        emit aboutToShow();
        const QVariant xArg(position.x());
        const QVariant yArg(position.y());
        if (!QMetaObject::invokeMethod(
                m_qmlMenu, "showAtPosition", Qt::DirectConnection,
                Q_ARG(QVariant, xArg), Q_ARG(QVariant, yArg))) {
            qWarning() << "SystemTrayIcon: PrismQML showAtPosition failed";
        }
        return;
    }
    m_menu->popup(position);
}

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
