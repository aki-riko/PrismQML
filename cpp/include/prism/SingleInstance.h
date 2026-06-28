// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - SingleInstance (镜像 Python core/single_instance.py)
// QSharedMemory 检测 + QLocalServer/Socket 轻量 IPC 唤起已有实例
#pragma once

#include <QObject>
#include <QString>
#include <functional>

class QSharedMemory;
class QLocalServer;

namespace prism {

class SingleInstance : public QObject {
    Q_OBJECT
public:
    // app_id: 全局唯一标识; onSecondInstance: 第二实例启动时已有实例的回调
    explicit SingleInstance(const QString &appId,
                            std::function<void()> onSecondInstance = nullptr,
                            QObject *parent = nullptr);
    ~SingleInstance() override;

    // 是否已有实例在运行 (true = 本进程是第二实例, 应退出)
    bool isRunning() const { return m_isRunning; }

signals:
    void secondInstanceStarted();

private:
    QString serverName() const;
    void startServer();
    void notifyExistingInstance();

    QString m_appId;
    QSharedMemory *m_sharedMemory = nullptr;
    QLocalServer *m_server = nullptr;
    bool m_isRunning = false;
    std::function<void()> m_onSecondInstance;
};

}  // namespace prism
