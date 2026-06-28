// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - Updater 实现 (镜像 Python core/updater.py)
#include "prism/Updater.h"

#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QFile>
#include <QDir>
#include <QStandardPaths>
#include <QUrl>
#include <QList>
#include <QPair>

namespace prism {

// ==================== 版本解析 (镜像 _parse_version) ====================
// 返回 core 段列表 + pre_marker, 用于逐段比较。
namespace {
struct Seg { int kind; long long num; QString str; };  // kind 0=数字, 1=非数字

QList<Seg> parseSegments(const QString &s) {
    QList<Seg> out;
    for (const QString &raw : s.split(QLatin1Char('.'))) {
        const QString seg = raw.trimmed();
        if (seg.isEmpty())
            continue;
        bool ok = false;
        const long long n = seg.toLongLong(&ok);
        if (ok)
            out.append({0, n, QString()});
        else
            out.append({1, 0, seg});
    }
    return out;
}

// 比较两个 Seg: <0 a<b, 0 相等, >0 a>b
int cmpSeg(const Seg &a, const Seg &b) {
    if (a.kind != b.kind)
        return a.kind < b.kind ? -1 : 1;  // 数字段(0)排在非数字段(1)之前
    if (a.kind == 0)
        return a.num < b.num ? -1 : (a.num > b.num ? 1 : 0);
    return a.str < b.str ? -1 : (a.str > b.str ? 1 : 0);
}

int cmpSegList(const QList<Seg> &a, const QList<Seg> &b) {
    const int n = qMax(a.size(), b.size());
    for (int i = 0; i < n; ++i) {
        if (i >= a.size()) return -1;  // a 短 = 较小
        if (i >= b.size()) return 1;
        const int c = cmpSeg(a[i], b[i]);
        if (c != 0) return c;
    }
    return 0;
}

// 解析版本为 (core, preMarker)
struct Version { QList<Seg> core; QList<Seg> preMarker; bool empty = false; };

Version parseVersion(const QString &tag) {
    Version v;
    QString t = tag.trimmed();
    if (t.isEmpty()) { v.empty = true; return v; }
    if (t[0] == QLatin1Char('v') || t[0] == QLatin1Char('V'))
        t = t.mid(1);
    const int dash = t.indexOf(QLatin1Char('-'));
    const QString coreStr = dash >= 0 ? t.left(dash) : t;
    const QString preStr = dash >= 0 ? t.mid(dash + 1) : QString();
    v.core = parseSegments(coreStr);
    if (dash >= 0) {
        // 预发布: pre_marker = (0,) + segs, 排在正式版之前
        v.preMarker.append({0, 0, QString()});
        v.preMarker.append(parseSegments(preStr));
    } else {
        // 正式版: (1,), 排在最后(更大)
        v.preMarker.append({0, 1, QString()});
    }
    return v;
}

int cmpVersion(const Version &a, const Version &b) {
    if (a.empty && b.empty) return 0;
    if (a.empty) return -1;
    if (b.empty) return 1;
    const int c = cmpSegList(a.core, b.core);
    if (c != 0) return c;
    return cmpSegList(a.preMarker, b.preMarker);
}
}  // namespace

bool versionIsNewer(const QString &latest, const QString &current) {
    return cmpVersion(parseVersion(latest), parseVersion(current)) > 0;
}

// PLACEHOLDER_UPDATER_IMPL
Updater::Updater(const QString &repo, const QString &currentVersion,
                 const QString &assetKeyword, QObject *parent)
    : QObject(parent), m_repo(repo), m_currentVersion(currentVersion),
      m_assetKeyword(assetKeyword), m_nam(new QNetworkAccessManager(this)) {}

Updater::~Updater() {
    if (m_downloadFile) {
        m_downloadFile->close();
        delete m_downloadFile;
    }
}

// 检查更新: GET GitHub releases/latest (镜像 checkForUpdate)
void Updater::checkForUpdate() {
    const QString url = QStringLiteral("https://api.github.com/repos/%1/releases/latest").arg(m_repo);
    QNetworkRequest req((QUrl(url)));
    req.setHeader(QNetworkRequest::UserAgentHeader, QStringLiteral("PrismQML-Updater"));
    req.setRawHeader("Accept", "application/vnd.github+json");
    m_checkReply = m_nam->get(req);
    connect(m_checkReply, &QNetworkReply::finished, this, &Updater::onCheckFinished);
}

void Updater::onCheckFinished() {
    QNetworkReply *reply = m_checkReply;
    m_checkReply = nullptr;
    if (!reply)
        return;
    reply->deleteLater();

    if (reply->error() != QNetworkReply::NoError) {
        emit checkFailed(reply->errorString());
        return;
    }
    const QByteArray data = reply->readAll();
    QJsonParseError err{};
    const QJsonDocument doc = QJsonDocument::fromJson(data, &err);
    if (err.error != QJsonParseError::NoError || !doc.isObject()) {
        emit checkFailed(QStringLiteral("解析 release JSON 失败: %1").arg(err.errorString()));
        return;
    }
    const QJsonObject obj = doc.object();
    const QString tag = obj.value(QStringLiteral("tag_name")).toString();
    const QString notes = obj.value(QStringLiteral("body")).toString();
    const QString htmlUrl = obj.value(QStringLiteral("html_url")).toString();

    if (!versionIsNewer(tag, m_currentVersion)) {
        emit upToDate(m_currentVersion);
        return;
    }
    // 挑选安装包 asset (镜像 _pick_asset: 含 keyword 的 .exe 优先)
    QString downloadUrl;
    const QJsonArray assets = obj.value(QStringLiteral("assets")).toArray();
    QString firstExe, firstAny;
    const QString kw = m_assetKeyword.toLower();
    for (const QJsonValue &v : assets) {
        const QJsonObject a = v.toObject();
        const QString name = a.value(QStringLiteral("name")).toString();
        const QString dl = a.value(QStringLiteral("browser_download_url")).toString();
        if (firstAny.isEmpty()) firstAny = dl;
        if (name.toLower().endsWith(QStringLiteral(".exe"))) {
            if (firstExe.isEmpty()) firstExe = dl;
            if (!kw.isEmpty() && name.toLower().contains(kw)) {
                downloadUrl = dl;
                break;
            }
        }
    }
    if (downloadUrl.isEmpty()) downloadUrl = !firstExe.isEmpty() ? firstExe : firstAny;

    emit updateAvailable(tag, notes, downloadUrl, htmlUrl);
}

// 下载更新包 (镜像 downloadUpdate)
void Updater::downloadUpdate(const QString &url) {
    if (url.isEmpty()) {
        emit downloadFailed(QStringLiteral("下载 URL 为空"));
        return;
    }
    const QString dir = QStandardPaths::writableLocation(QStandardPaths::TempLocation);
    const QString fileName = QUrl(url).fileName();
    const QString localPath = QDir(dir).filePath(fileName.isEmpty()
                                                     ? QStringLiteral("prismqml_update.bin")
                                                     : fileName);
    m_downloadFile = new QFile(localPath);
    if (!m_downloadFile->open(QIODevice::WriteOnly)) {
        emit downloadFailed(QStringLiteral("无法创建文件: %1").arg(localPath));
        delete m_downloadFile;
        m_downloadFile = nullptr;
        return;
    }
    QNetworkRequest req((QUrl(url)));
    req.setHeader(QNetworkRequest::UserAgentHeader, QStringLiteral("PrismQML-Updater"));
    req.setAttribute(QNetworkRequest::RedirectPolicyAttribute,
                     QNetworkRequest::NoLessSafeRedirectPolicy);
    m_downloadReply = m_nam->get(req);
    connect(m_downloadReply, &QNetworkReply::downloadProgress, this, &Updater::downloadProgress);
    connect(m_downloadReply, &QNetworkReply::readyRead, this, [this]() {
        if (m_downloadFile && m_downloadReply)
            m_downloadFile->write(m_downloadReply->readAll());
    });
    connect(m_downloadReply, &QNetworkReply::finished, this, &Updater::onDownloadFinished);
}

void Updater::onDownloadFinished() {
    QNetworkReply *reply = m_downloadReply;
    m_downloadReply = nullptr;
    if (!reply)
        return;
    reply->deleteLater();

    const QString localPath = m_downloadFile ? m_downloadFile->fileName() : QString();
    if (m_downloadFile) {
        m_downloadFile->write(reply->readAll());
        m_downloadFile->close();
        delete m_downloadFile;
        m_downloadFile = nullptr;
    }
    if (reply->error() != QNetworkReply::NoError) {
        emit downloadFailed(reply->errorString());
        return;
    }
    emit downloadFinished(localPath);
}

}  // namespace prism
