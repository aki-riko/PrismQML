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
#include <QSaveFile>
#include <QDir>
#include <QStandardPaths>
#include <QUrl>
#include <QDesktopServices>
#include <QList>
#include <QPair>
#include <QProcess>
#include <QCoreApplication>
#include <QFileInfo>
#include <QStringList>
#include <QUuid>
#include <QDebug>
#include <QCryptographicHash>
#include <algorithm>

#ifdef Q_OS_WIN
#  include <windows.h>
#  include <shellapi.h>
#endif

namespace prism {

// ==================== 版本解析 (镜像 _parse_version) ====================
// 返回 core 段列表 + pre_marker, 用于逐段比较。
namespace {
struct Seg { int kind; QString value; };  // kind 0=数字, 1=非数字

bool isAsciiDigits(const QString &value) {
    if (value.isEmpty())
        return false;
    for (const QChar character : value) {
        if (character < QLatin1Char('0') || character > QLatin1Char('9'))
            return false;
    }
    return true;
}

QString normalizeNumericSegment(const QString &value) {
    qsizetype firstNonZero = 0;
    while (firstNonZero < value.size() && value[firstNonZero] == QLatin1Char('0'))
        ++firstNonZero;
    return firstNonZero == value.size() ? QStringLiteral("0") : value.mid(firstNonZero);
}

QList<Seg> parseSegments(const QString &s) {
    QList<Seg> out;
    for (const QString &raw : s.split(QLatin1Char('.'))) {
        const QString seg = raw.trimmed();
        if (seg.isEmpty())
            continue;
        if (isAsciiDigits(seg))
            out.append({0, normalizeNumericSegment(seg)});
        else
            out.append({1, seg});
    }
    return out;
}

// 比较两个 Seg: <0 a<b, 0 相等, >0 a>b
int cmpSeg(const Seg &a, const Seg &b) {
    if (a.kind != b.kind)
        return a.kind < b.kind ? -1 : 1;  // 数字段(0)排在非数字段(1)之前
    if (a.kind == 0 && a.value.size() != b.value.size())
        return a.value.size() < b.value.size() ? -1 : 1;
    return a.value < b.value ? -1 : (a.value > b.value ? 1 : 0);
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

struct ReleaseAsset { QString name; QString downloadUrl; QString digest; };
struct ReleaseData {
    QString tag;
    QString notes;
    QString htmlUrl;
    QList<ReleaseAsset> assets;
};

Version parseVersion(const QString &tag) {
    Version v;
    QString t = tag.trimmed();
    if (t.isEmpty()) { v.empty = true; return v; }
    if (t[0] == QLatin1Char('v') || t[0] == QLatin1Char('V'))
        t = t.mid(1);
    const int plus = t.indexOf(QLatin1Char('+'));
    if (plus >= 0)
        t.truncate(plus);
    t = t.trimmed();
    if (t.isEmpty()) { v.empty = true; return v; }
    const int dash = t.indexOf(QLatin1Char('-'));
    const QString coreStr = dash >= 0 ? t.left(dash) : t;
    const QString preStr = dash >= 0 ? t.mid(dash + 1) : QString();
    v.core = parseSegments(coreStr);
    if (dash >= 0) {
        // 预发布: pre_marker = (0,) + segs, 排在正式版之前
        v.preMarker.append({0, QStringLiteral("0")});
        v.preMarker.append(parseSegments(preStr));
    } else {
        // 正式版: (1,), 排在最后(更大)
        v.preMarker.append({0, QStringLiteral("1")});
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

bool readOptionalString(const QJsonObject &object, const QString &key,
                        QString *output, QString *error) {
    const QJsonValue value = object.value(key);
    if (value.isUndefined() || value.isNull()) {
        output->clear();
        return true;
    }
    if (!value.isString()) {
        *error = QStringLiteral("release field '%1' must be a string or null").arg(key);
        return false;
    }
    *output = value.toString();
    return true;
}

bool parseReleaseAssets(const QJsonValue &value, QList<ReleaseAsset> *assets,
                        QString *error) {
    if (value.isUndefined() || value.isNull())
        return true;
    if (!value.isArray()) {
        *error = QStringLiteral("release field 'assets' must be an array or null");
        return false;
    }
    for (const QJsonValue &item : value.toArray()) {
        if (!item.isObject()) {
            *error = QStringLiteral("each release asset must be an object");
            return false;
        }
        ReleaseAsset asset;
        const QJsonObject object = item.toObject();
        if (!readOptionalString(object, QStringLiteral("name"), &asset.name, error)
            || !readOptionalString(object, QStringLiteral("browser_download_url"),
                                   &asset.downloadUrl, error)
            || !readOptionalString(object, QStringLiteral("digest"), &asset.digest, error))
            return false;
        assets->append(asset);
    }
    return true;
}

bool parseReleaseData(const QByteArray &raw, ReleaseData *release, QString *error) {
    QJsonParseError parseError{};
    const QJsonDocument document = QJsonDocument::fromJson(raw, &parseError);
    if (parseError.error != QJsonParseError::NoError || !document.isObject()) {
        *error = QStringLiteral("invalid release JSON: %1").arg(parseError.errorString());
        return false;
    }
    const QJsonObject object = document.object();
    const QJsonValue tag = object.value(QStringLiteral("tag_name"));
    if (!tag.isString() || tag.toString().trimmed().isEmpty()) {
        *error = QStringLiteral("release field 'tag_name' must be a non-empty string");
        return false;
    }
    release->tag = tag.toString().trimmed();
    return readOptionalString(object, QStringLiteral("body"), &release->notes, error)
        && readOptionalString(object, QStringLiteral("html_url"), &release->htmlUrl, error)
        && parseReleaseAssets(object.value(QStringLiteral("assets")),
                              &release->assets, error);
}

bool isSafeUpdateUrl(const QString &value, bool allowLocalHttp = true) {
    const QUrl url(value.trimmed(), QUrl::StrictMode);
    if (!url.isValid() || url.host().isEmpty() || !url.userInfo().isEmpty())
        return false;
    const QString scheme = url.scheme().toLower();
    if (scheme == QStringLiteral("https"))
        return true;
    return allowLocalHttp && scheme == QStringLiteral("http")
        && (url.host().compare(QStringLiteral("localhost"), Qt::CaseInsensitive) == 0
            || url.host() == QStringLiteral("127.0.0.1")
            || url.host() == QStringLiteral("::1"));
}

bool isSha256Digest(const QString &value) {
    const QStringList parts = value.trimmed().split(QLatin1Char(':'), Qt::KeepEmptyParts);
    if (parts.size() != 2 || parts[0].compare(QStringLiteral("sha256"), Qt::CaseInsensitive) != 0
        || parts[1].size() != 64)
        return false;
    for (const QChar character : parts[1]) {
        const QChar lower = character.toLower();
        if ((character < QLatin1Char('0') || character > QLatin1Char('9'))
            && (lower < QLatin1Char('a') || lower > QLatin1Char('f')))
            return false;
    }
    return true;
}

QStringList installerSuffixes() {
#ifdef Q_OS_WIN
    return {QStringLiteral(".exe")};
#elif defined(Q_OS_MACOS)
    return {QStringLiteral(".dmg"), QStringLiteral(".pkg")};
#elif defined(Q_OS_LINUX) && !defined(Q_OS_ANDROID)
    return {QStringLiteral(".appimage"), QStringLiteral(".run"), QStringLiteral(".deb")};
#else
    return {};
#endif
}

bool verifyFileDigest(const QString &path, const QString &digest) {
    if (!isSha256Digest(digest))
        return false;
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly))
        return false;
    QCryptographicHash hash(QCryptographicHash::Sha256);
    while (!file.atEnd()) {
        const QByteArray chunk = file.read(1024 * 1024);
        if (chunk.isEmpty() && !file.atEnd())
            return false;
        hash.addData(chunk);
    }
    return QStringLiteral("sha256:%1").arg(QString::fromLatin1(hash.result().toHex()))
        .compare(digest.trimmed(), Qt::CaseInsensitive) == 0;
}

QString pickDownloadUrl(const QList<ReleaseAsset> &assets, const QString &keyword,
                        QString *digest = nullptr) {
    const QString normalizedKeyword = keyword.toLower();
    const QStringList suffixes = installerSuffixes();
    const ReleaseAsset *firstInstaller = nullptr;
    for (const ReleaseAsset &asset : assets) {
        const QString name = asset.name.toLower();
        if (asset.downloadUrl.isEmpty()
            || !std::any_of(suffixes.cbegin(), suffixes.cend(),
                            [&name](const QString &suffix) { return name.endsWith(suffix); }))
            continue;
        if (!firstInstaller)
            firstInstaller = &asset;
        if (!normalizedKeyword.isEmpty() && name.contains(normalizedKeyword)) {
            if (digest)
                *digest = asset.digest;
            return asset.downloadUrl;
        }
    }
    if (firstInstaller) {
        if (digest)
            *digest = firstInstaller->digest;
        return firstInstaller->downloadUrl;
    }
    if (digest)
        digest->clear();
    return QString();
}

QNetworkRequest updaterRequest(const QString &url) {
    QNetworkRequest request{QUrl(url)};
    request.setHeader(QNetworkRequest::UserAgentHeader,
                      QStringLiteral("PrismQML-Updater"));
    request.setAttribute(QNetworkRequest::RedirectPolicyAttribute,
                         QNetworkRequest::NoLessSafeRedirectPolicy);
    request.setAttribute(QNetworkRequest::ConnectionCacheExpiryTimeoutSecondsAttribute, 0);
    return request;
}

QString uniqueDownloadPath(const QString &url) {
    QString tempDirectory = QStandardPaths::writableLocation(QStandardPaths::TempLocation);
    if (tempDirectory.isEmpty())
        tempDirectory = QDir::tempPath();
    const QString suffix = QFileInfo(QUrl(url).fileName()).suffix();
    const QString extension = suffix.isEmpty() ? QStringLiteral(".bin")
                                               : QStringLiteral(".%1").arg(suffix);
    const QString token = QUuid::createUuid().toString(QUuid::WithoutBraces);
    return QDir(tempDirectory).filePath(
        QStringLiteral("prismqml-update-%1%2").arg(token, extension));
}

QString writeDownloadBytes(QSaveFile *file, const QByteArray &payload) {
    if (payload.isEmpty())
        return QString();
    const qint64 written = file ? file->write(payload) : -1;
    if (written == payload.size())
        return QString();
    return QStringLiteral("写入下载文件失败: %1")
        .arg(file ? file->errorString() : QStringLiteral("file unavailable"));
}
}  // namespace

bool versionIsNewer(const QString &latest, const QString &current) {
    return cmpVersion(parseVersion(latest), parseVersion(current)) > 0;
}

QString resolveUpdaterApiBaseUrl(const QString &configured) {
    const auto normalize = [](QString value) {
        value = value.trimmed();
        while (value.endsWith(QLatin1Char('/')))
            value.chop(1);
        return value;
    };

    QString apiBaseUrl = normalize(configured);
    if (apiBaseUrl.isEmpty())
        apiBaseUrl = normalize(qEnvironmentVariable(kUpdaterApiBaseUrlEnvironment));
    if (apiBaseUrl.isEmpty())
        apiBaseUrl = QString::fromLatin1(kDefaultUpdaterApiBaseUrl);
    return apiBaseUrl;
}

QString latestReleaseApiUrl(const QString &repo, const QString &apiBaseUrl) {
    QString normalizedRepo = repo.trimmed();
    while (normalizedRepo.startsWith(QLatin1Char('/')))
        normalizedRepo.remove(0, 1);
    while (normalizedRepo.endsWith(QLatin1Char('/')))
        normalizedRepo.chop(1);
    return QStringLiteral("%1/repos/%2/releases/latest")
        .arg(resolveUpdaterApiBaseUrl(apiBaseUrl), normalizedRepo);
}

Updater::Updater(const QString &repo, const QString &currentVersion,
                 const QString &assetKeyword, QObject *parent)
    : Updater(repo, currentVersion, assetKeyword, QString(), parent) {}

Updater::Updater(const QString &repo, const QString &currentVersion,
                 const QString &assetKeyword, const QString &apiBaseUrl,
                 QObject *parent)
    : QObject(parent), m_repo(repo), m_currentVersion(currentVersion),
      m_assetKeyword(assetKeyword), m_apiBaseUrl(resolveUpdaterApiBaseUrl(apiBaseUrl)),
      m_nam(new QNetworkAccessManager(this)) {}

Updater::~Updater() {
    if (m_downloadFile) {
        m_downloadFile->cancelWriting();
        delete m_downloadFile;
    }
}

void Updater::setApiBaseUrl(const QString &apiBaseUrl) {
    m_apiBaseUrl = resolveUpdaterApiBaseUrl(apiBaseUrl);
}

// 检查更新: GET GitHub releases/latest (镜像 checkForUpdate)
void Updater::checkForUpdate() {
    if (m_checkReply || m_downloadReply) {
        qWarning() << "[Updater] 已有更新事务在进行, 拒绝重复检测";
        emit checkFailed(QStringLiteral("更新检查已在进行"));
        return;
    }
    m_expectedDownloadUrl.clear();
    m_expectedDigest.clear();
    const QString url = latestReleaseApiUrl(m_repo, m_apiBaseUrl);
    if (!isSafeUpdateUrl(url)) {
        emit checkFailed(QStringLiteral("更新 API 地址不安全"));
        return;
    }
    QNetworkRequest req = updaterRequest(url);
    req.setRawHeader("Accept", "application/vnd.github+json");
    m_checkReply = m_nam->get(req);
    QNetworkReply *reply = m_checkReply;
    connect(reply, &QNetworkReply::finished, this,
            [this, reply]() { onCheckFinished(reply); });
}

void Updater::onCheckFinished(QNetworkReply *reply) {
    if (reply != m_checkReply) {
        if (reply)
            reply->deleteLater();
        return;
    }
    m_checkReply = nullptr;
    if (!reply)
        return;
    reply->deleteLater();

    if (reply->error() != QNetworkReply::NoError) {
        emit checkFailed(reply->errorString());
        return;
    }
    ReleaseData release;
    QString error;
    if (!parseReleaseData(reply->readAll(), &release, &error)) {
        emit checkFailed(QStringLiteral("解析更新信息失败: %1").arg(error));
        return;
    }
    if (!versionIsNewer(release.tag, m_currentVersion)) {
        m_expectedDownloadUrl.clear();
        m_expectedDigest.clear();
        emit upToDate(m_currentVersion);
        return;
    }
    QString digest;
    const QString downloadUrl = pickDownloadUrl(release.assets, m_assetKeyword, &digest);
    if (!downloadUrl.isEmpty() && !isSafeUpdateUrl(downloadUrl)) {
        emit checkFailed(QStringLiteral("更新资产下载地址不安全"));
        return;
    }
    if (!downloadUrl.isEmpty() && m_requireArtifactDigest && !isSha256Digest(digest)) {
        emit checkFailed(QStringLiteral("更新资产缺少有效 SHA-256 摘要"));
        return;
    }
    m_expectedDownloadUrl = downloadUrl;
    m_expectedDigest = digest;
    emit updateAvailable(release.tag, release.notes,
                         downloadUrl,
                         release.htmlUrl);
}

// 下载更新包 (镜像 downloadUpdate)
void Updater::downloadUpdate(const QString &url) {
    if (m_checkReply || m_downloadReply) {
        const QString message = m_checkReply ? QStringLiteral("更新检查已在进行")
                                             : QStringLiteral("下载已在进行");
        qWarning() << "[Updater] 已有更新事务在进行, 拒绝下载:" << message;
        emit downloadFailed(message);
        return;
    }
    if (url.isEmpty()) {
        emit downloadFailed(QStringLiteral("下载 URL 为空"));
        return;
    }
    if (!isSafeUpdateUrl(url)) {
        emit downloadFailed(QStringLiteral("下载地址不安全"));
        return;
    }
    if (url != m_expectedDownloadUrl)
        m_expectedDigest.clear();
    if (m_requireArtifactDigest && !isSha256Digest(m_expectedDigest)) {
        emit downloadFailed(QStringLiteral("下载地址未绑定有效 SHA-256 摘要"));
        return;
    }
    if (!openDownloadFile(url))
        return;
    startDownloadRequest(url);
}

bool Updater::openDownloadFile(const QString &url) {
    m_downloadPath = uniqueDownloadPath(url);
    m_downloadError.clear();
    m_downloadFile = new QSaveFile(m_downloadPath);
    m_downloadFile->setDirectWriteFallback(false);
    if (m_downloadFile->open(QIODevice::WriteOnly))
        return true;
    const QString message = QStringLiteral("无法创建文件: %1")
        .arg(m_downloadFile->errorString());
    failDownload(message);
    return false;
}

void Updater::startDownloadRequest(const QString &url) {
    QNetworkRequest req = updaterRequest(url);
    m_downloadReply = m_nam->get(req);
    QNetworkReply *reply = m_downloadReply;
    connect(reply, &QNetworkReply::downloadProgress, this, &Updater::downloadProgress);
    connect(reply, &QNetworkReply::readyRead, this,
            [this, reply]() { onDownloadReadyRead(reply); });
    connect(reply, &QNetworkReply::finished, this,
            [this, reply]() { onDownloadFinished(reply); });
}

void Updater::onDownloadReadyRead(QNetworkReply *reply) {
    if (reply != m_downloadReply || !m_downloadFile || !m_downloadError.isEmpty())
        return;
    m_downloadError = writeDownloadBytes(m_downloadFile, reply->readAll());
    if (!m_downloadError.isEmpty()) {
        qWarning() << "[Updater]" << m_downloadError;
        reply->abort();
    }
}

void Updater::onDownloadFinished(QNetworkReply *reply) {
    if (reply != m_downloadReply) {
        if (reply)
            reply->deleteLater();
        return;
    }
    m_downloadReply = nullptr;
    if (!reply)
        return;
    reply->deleteLater();
    const QString error = finalizeDownload(reply);
    if (!error.isEmpty()) {
        failDownload(error);
        return;
    }
    const QString completedPath = m_downloadPath;
    m_downloadError.clear();
    emit downloadFinished(completedPath);
}

QString Updater::finalizeDownload(QNetworkReply *reply) {
    if (!m_downloadError.isEmpty())
        return m_downloadError;
    if (reply->error() != QNetworkReply::NoError)
        return reply->errorString();
    const QString writeError = writeDownloadBytes(m_downloadFile, reply->readAll());
    if (!writeError.isEmpty())
        return writeError;
    if (!m_downloadFile || !m_downloadFile->commit())
        return QStringLiteral("提交下载文件失败: %1")
            .arg(m_downloadFile ? m_downloadFile->errorString()
                                : QStringLiteral("file unavailable"));
    delete m_downloadFile;
    m_downloadFile = nullptr;
    const QFileInfo fileInfo(m_downloadPath);
    if (!fileInfo.isFile() || fileInfo.size() <= 0)
        return QStringLiteral("下载文件无效");
    if (!m_expectedDigest.isEmpty() && !verifyFileDigest(m_downloadPath, m_expectedDigest))
        return QStringLiteral("下载文件摘要校验失败");
    return QString();
}

void Updater::failDownload(const QString &message) {
    qWarning() << "[Updater] 下载失败:" << message;
    cleanupDownloadArtifacts();
    emit downloadFailed(message);
}

void Updater::cleanupDownloadArtifacts() {
    if (m_downloadFile) {
        m_downloadFile->cancelWriting();
        delete m_downloadFile;
        m_downloadFile = nullptr;
    }
    if (!m_downloadPath.isEmpty() && QFileInfo::exists(m_downloadPath)
        && !QFile::remove(m_downloadPath))
        qWarning() << "[Updater] 清理下载残留失败:" << m_downloadPath;
    m_downloadPath.clear();
    m_downloadError.clear();
}

// ==================== 安装并退出 (镜像 Python runInstallerAndQuit) ====================
bool Updater::runInstallerAndQuit(const QString &installerPath, const QString &silentArgs) {
    if (installerPath.isEmpty() || !QFileInfo(installerPath).isFile()) {
        qWarning() << "[Updater] 安装包不存在:" << installerPath;
        return false;
    }
    // 拆分参数 (空格分隔, 过滤空段; 镜像 Python args 解析)
    QStringList args;
    const QString trimmed = silentArgs.trimmed();
    if (!trimmed.isEmpty()) {
        for (const QString &a : trimmed.split(QLatin1Char(' '), Qt::SkipEmptyParts))
            args << a;
    }

#ifdef Q_OS_WIN
    // Windows: ShellExecuteW open 动词。安装包(InnoSetup)若 manifest 标记需管理员权限,
    // 系统自动弹标准 UAC 提权 (无需主动 runas, 主动 runas 在部分 UAC 配置下会卡住)。
    const std::wstring file = installerPath.toStdWString();
    const QString joined = args.join(QLatin1Char(' '));
    const std::wstring params = joined.toStdWString();
    HINSTANCE ret = ShellExecuteW(nullptr, L"open", file.c_str(),
                                  params.empty() ? nullptr : params.c_str(),
                                  nullptr, SW_SHOWNORMAL);
    // ShellExecuteW 返回值 <= 32 表示失败
    if (reinterpret_cast<INT_PTR>(ret) <= 32) {
        qWarning() << "[Updater] 启动安装包失败(ShellExecute 返回"
                   << reinterpret_cast<INT_PTR>(ret) << "):" << installerPath;
        discardCompletedDownload(installerPath);
        return false;
    }
    qInfo() << "[Updater] 已启动安装包, 应用即将退出:" << installerPath << args;
    QCoreApplication::quit();
    return true;
#elif defined(Q_OS_IOS) || defined(Q_OS_ANDROID)
    // Mobile sandboxes do not support launching an external installer process.
    qWarning() << "[Updater] 当前平台不支持启动外部安装包:" << installerPath;
    discardCompletedDownload(installerPath);
    return false;
#elif defined(Q_OS_MACOS)
    // macOS DMG/PKG must be opened by the system Installer/Finder handler.
    const bool ok = QProcess::startDetached(QStringLiteral("/usr/bin/open"), {installerPath});
    if (!ok) {
        qWarning() << "[Updater] 打开 macOS 安装包失败:" << installerPath;
        discardCompletedDownload(installerPath);
        return false;
    }
    qInfo() << "[Updater] 已打开 macOS 安装包, 应用即将退出:" << installerPath;
    QCoreApplication::quit();
    return true;
#elif defined(Q_OS_LINUX)
    bool ok = false;
    if (installerPath.endsWith(QStringLiteral(".deb"), Qt::CaseInsensitive)) {
        ok = QDesktopServices::openUrl(QUrl::fromLocalFile(installerPath));
    } else {
        QFile::Permissions permissions = QFile::permissions(installerPath);
        if (!(permissions & QFileDevice::ExeOwner)
            && !QFile::setPermissions(installerPath, permissions | QFileDevice::ExeOwner)) {
            qWarning() << "[Updater] 设置 Linux 安装包执行权限失败:" << installerPath;
            discardCompletedDownload(installerPath);
            return false;
        }
        ok = QProcess::startDetached(installerPath, args);
    }
    if (!ok) {
        qWarning() << "[Updater] 启动 Linux 安装包失败:" << installerPath;
        discardCompletedDownload(installerPath);
        return false;
    }
    qInfo() << "[Updater] 已启动 Linux 安装包, 应用即将退出:" << installerPath << args;
    QCoreApplication::quit();
    return true;
#else
    // 非 Windows: QProcess detached 启动
    const bool ok = QProcess::startDetached(installerPath, args);
    if (!ok) {
        qWarning() << "[Updater] 启动安装包失败:" << installerPath;
        discardCompletedDownload(installerPath);
        return false;
    }
    qInfo() << "[Updater] 已启动安装包, 应用即将退出:" << installerPath << args;
    QCoreApplication::quit();
    return true;
#endif
}

// ==================== 浏览器打开 (镜像 Python openInBrowser) ====================
bool Updater::openInBrowser(const QString &url) {
    if (!isSafeUpdateUrl(url, false)) {
        qWarning() << "[Updater] openInBrowser: URL 不安全或为空";
        return false;
    }
    const bool ok = QDesktopServices::openUrl(QUrl(url));
    if (!ok)
        qWarning() << "[Updater] 打开浏览器失败:" << url;
    return ok;
}

void Updater::discardCompletedDownload(const QString &installerPath) {
    if (installerPath != m_downloadPath)
        return;
    if (!QFile::remove(installerPath)) {
        qWarning() << "[Updater] 清理安装包失败:" << installerPath;
        return;
    }
    m_downloadPath.clear();
}

}  // namespace prism
