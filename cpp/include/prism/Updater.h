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
