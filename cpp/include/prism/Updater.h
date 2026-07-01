// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - Updater (镜像 Python core/updater.py)
// 基于 GitHub Releases 检测/下载更新, QNetworkAccessManager 异步, 信号回传
#pragma once

#include <QObject>
#include <QString>

class QNetworkAccessManager;
class QNetworkReply;
class QFile;

namespace prism {

// 版本比较 (镜像 _parse_version/_is_newer): latest 是否比 current 新
bool versionIsNewer(const QString &latest, const QString &current);

class Updater : public QObject {
    Q_OBJECT
public:
    explicit Updater(const QString &repo, const QString &currentVersion,
                     const QString &assetKeyword = QStringLiteral("Setup"),
                     QObject *parent = nullptr);
    ~Updater() override;

public slots:
    void checkForUpdate();
    void downloadUpdate(const QString &url);

    // 启动安装包并退出当前应用, 让安装包覆盖文件 (镜像 Python runInstallerAndQuit)。
    // Windows 用 ShellExecuteW open 动词 (安装包 manifest 标记需管理员权限时系统自动弹 UAC);
    // 非 Windows 用 QProcess::startDetached。installerPath 通常是 downloadFinished 给出的 localPath;
    // silentArgs 为传给安装包的参数(空格分隔), 留空走可见安装向导。
    // 成功发起安装时本应用即将退出并返回 true; 文件不存在/启动失败返回 false 且不退出。
    bool runInstallerAndQuit(const QString &installerPath,
                             const QString &silentArgs = QString());

signals:
    void updateAvailable(const QString &version, const QString &notes,
                         const QString &downloadUrl, const QString &htmlUrl);
    void upToDate(const QString &currentVersion);
    void checkFailed(const QString &errorMessage);
    void downloadProgress(qint64 received, qint64 total);
    void downloadFinished(const QString &localPath);
    void downloadFailed(const QString &errorMessage);

private:
    void onCheckFinished();
    void onDownloadFinished();

    QString m_repo;
    QString m_currentVersion;
    QString m_assetKeyword;
    QNetworkAccessManager *m_nam;
    QNetworkReply *m_checkReply = nullptr;
    QNetworkReply *m_downloadReply = nullptr;
    QFile *m_downloadFile = nullptr;
};

}  // namespace prism
