// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ Updater transaction tests. C++ Updater 下载事务测试。

#include <QCoreApplication>
#include <QDir>
#include <QElapsedTimer>
#include <QFile>
#include <QFileInfo>
#include <QHostAddress>
#include <QNetworkReply>
#include <QSaveFile>
#include <QStandardPaths>
#include <QTcpServer>
#include <QTcpSocket>
#include <QThread>
#include <QUrl>
#include <cstdio>
#include <functional>

#define private public
#include "prism/Updater.h"
#undef private

#include "TestProcess.h"

static int g_failed = 0;
#define CHECK(cond, name) do { \
    if (cond) qInfo() << "  PASS:" << name; \
    else { qCritical() << "  FAIL:" << name; std::fprintf(stderr, "FAIL: %s\n", name); ++g_failed; } \
} while (0)

static bool waitUntil(const std::function<bool()> &predicate, int timeoutMs = 3000) {
    QElapsedTimer timer;
    timer.start();
    while (!predicate() && timer.elapsed() < timeoutMs) {
        QCoreApplication::processEvents(QEventLoop::AllEvents, 20);
        QThread::msleep(1);
    }
    return predicate();
}

static void spinEvents(int durationMs) {
    QElapsedTimer timer;
    timer.start();
    while (timer.elapsed() < durationMs) {
        QCoreApplication::processEvents(QEventLoop::AllEvents, 20);
        QThread::msleep(1);
    }
}

class HttpFixture {
public:
    HttpFixture() {
        QObject::connect(&server, &QTcpServer::newConnection, [&]() {
            while (server.hasPendingConnections())
                attach(server.nextPendingConnection());
        });
        CHECK(server.listen(QHostAddress::LocalHost, 0), "Updater loopback server listen");
    }

    QString url(const QString &path = QStringLiteral("/payload")) const {
        return QStringLiteral("http://127.0.0.1:%1%2").arg(server.serverPort()).arg(path);
    }

    void queue(const QByteArray &body, bool delayed = false,
               const QByteArray &status = QByteArrayLiteral("200 OK")) {
        responseBody = body;
        delayResponse = delayed;
        responseStatus = status;
    }

    void releasePending() {
        const auto sockets = pendingSockets;
        pendingSockets.clear();
        for (QTcpSocket *socket : sockets)
            send(socket);
    }

    int requestCount = 0;

private:
    void attach(QTcpSocket *socket) {
        QObject::connect(socket, &QTcpSocket::readyRead, [this, socket]() {
            requestBuffer[socket] += socket->readAll();
            if (!requestBuffer[socket].contains("\r\n\r\n"))
                return;
            requestBuffer.remove(socket);
            ++requestCount;
            if (delayResponse)
                pendingSockets.append(socket);
            else
                send(socket);
        });
        QObject::connect(socket, &QTcpSocket::disconnected,
                         socket, &QObject::deleteLater);
        QObject::connect(socket, &QObject::destroyed, [this, socket]() {
            pendingSockets.removeAll(socket);
            requestBuffer.remove(socket);
        });
    }

    void send(QTcpSocket *socket) {
        const QByteArray header = QByteArrayLiteral("HTTP/1.1 ") + responseStatus
            + QByteArrayLiteral("\r\nContent-Length: ")
            + QByteArray::number(responseBody.size())
            + QByteArrayLiteral("\r\nContent-Type: application/octet-stream\r\n"
                                "Connection: close\r\n\r\n");
        socket->write(header + responseBody);
        socket->disconnectFromHost();
    }

    QTcpServer server;
    QByteArray responseBody;
    QByteArray responseStatus = QByteArrayLiteral("200 OK");
    bool delayResponse = false;
    QList<QTcpSocket *> pendingSockets;
    QHash<QTcpSocket *, QByteArray> requestBuffer;
};

static QStringList updaterArtifacts() {
    const QString temp = QStandardPaths::writableLocation(QStandardPaths::TempLocation);
    return QDir(temp).entryList({QStringLiteral("prismqml-update-*")},
                                QDir::Files | QDir::Dirs, QDir::Name);
}

static void testInvalidReleaseSchemas(HttpFixture &http) {
    const QList<QByteArray> invalid = {
        QByteArrayLiteral("[]"),
        QByteArrayLiteral("{\"tag_name\":104}"),
        QByteArrayLiteral("{\"tag_name\":\"   \"}"),
        QByteArrayLiteral("{\"tag_name\":\"v1.0.4\",\"body\":[]}"),
        QByteArrayLiteral("{\"tag_name\":\"v1.0.4\",\"html_url\":{}}"),
        QByteArrayLiteral("{\"tag_name\":\"v1.0.4\",\"assets\":{}}"),
        QByteArrayLiteral("{\"tag_name\":\"v1.0.4\",\"assets\":[7]}"),
        QByteArrayLiteral("{\"tag_name\":\"v1.0.4\",\"assets\":[{\"name\":[]}]}"),
        QByteArrayLiteral("{\"tag_name\":\"v1.0.4\",\"assets\":[{\"browser_download_url\":7}]}"),
        QByteArrayLiteral("{\"tag_name\":\"v1.\xff\"}"),
        QByteArray("{\"tag_name\":\"v1.0.4\"}\xff", 24),
    };
    for (const QByteArray &payload : invalid) {
        int failed = 0, succeeded = 0;
        prism::Updater updater(QStringLiteral("owner/repo"), QStringLiteral("v1.0.3"),
                               QStringLiteral("Setup"), http.url());
        QObject::connect(&updater, &prism::Updater::checkFailed,
                         [&](const QString &) { ++failed; });
        QObject::connect(&updater, &prism::Updater::updateAvailable,
                         [&](const QString &, const QString &, const QString &, const QString &) {
                             ++succeeded;
                         });
        http.queue(payload);
        updater.checkForUpdate();
        CHECK(waitUntil([&]() { return failed == 1; }), "invalid release fails once");
        CHECK(succeeded == 0, "invalid release has no success signal");
    }
}

static void testValidReleaseAndDuplicateCheck(HttpFixture &http) {
    prism::Updater updater(QStringLiteral("owner/repo"), QStringLiteral("v1.0.3"),
                           QStringLiteral("Setup"), http.url());
    int available = 0;
    QStringList received;
    QObject::connect(&updater, &prism::Updater::updateAvailable,
                     [&](const QString &tag, const QString &notes,
                         const QString &download, const QString &html) {
        ++available;
        received = {tag, notes, download, html};
    });
    http.queue(QByteArrayLiteral(
        "{\"tag_name\":\"v1.0.4\",\"body\":null,\"html_url\":null,"
        "\"assets\":[{\"name\":\"App-Setup.exe\","
        "\"browser_download_url\":\"https://example.test/setup.exe\"}]}"), true);
    const int before = http.requestCount;
    updater.checkForUpdate();
    updater.checkForUpdate();
    CHECK(waitUntil([&]() { return http.requestCount == before + 1; }),
          "duplicate check creates one request");
    http.releasePending();
    CHECK(waitUntil([&]() { return available == 1; }), "valid release emits update");
    CHECK(received == QStringList({"v1.0.4", "", "https://example.test/setup.exe", ""}),
          "valid nullable release fields normalize");
}

static QString runDownload(HttpFixture &http, const QByteArray &payload,
                           int *failed = nullptr) {
    prism::Updater updater(QStringLiteral("owner/repo"), QStringLiteral("v1.0.0"));
    QString completed;
    int failureCount = 0;
    QObject::connect(&updater, &prism::Updater::downloadFinished,
                     [&](const QString &path) { completed = path; });
    QObject::connect(&updater, &prism::Updater::downloadFailed,
                     [&](const QString &) { ++failureCount; });
    http.queue(payload);
    updater.downloadUpdate(http.url(QStringLiteral("/App-Setup.exe")));
    waitUntil([&]() { return !completed.isEmpty() || failureCount > 0; });
    if (failed)
        *failed = failureCount;
    return completed;
}

static void testUniqueAtomicDownloads(HttpFixture &http) {
    const QString first = runDownload(http, QByteArrayLiteral("first"));
    const QString second = runDownload(http, QByteArrayLiteral("second"));
    CHECK(!first.isEmpty() && !second.isEmpty(), "downloads complete");
    CHECK(first != second, "same URL uses distinct files");
    QFile firstFile(first), secondFile(second);
    CHECK(firstFile.open(QIODevice::ReadOnly) && firstFile.readAll() == "first",
          "first completed file preserved");
    CHECK(secondFile.open(QIODevice::ReadOnly) && secondFile.readAll() == "second",
          "second completed file preserved");
    firstFile.close();
    secondFile.close();
    QFile::remove(first);
    QFile::remove(second);
}

static void testEmptyDownloadCleansArtifacts(HttpFixture &http) {
    const QStringList before = updaterArtifacts();
    int failed = 0;
    const QString completed = runDownload(http, QByteArray(), &failed);
    CHECK(failed == 1 && completed.isEmpty(), "empty download fails once");
    CHECK(updaterArtifacts() == before, "empty download leaves no artifact");
}

static void testNetworkFailureCleansArtifacts(HttpFixture &http) {
    const QStringList before = updaterArtifacts();
    prism::Updater updater(QStringLiteral("owner/repo"), QStringLiteral("v1.0.0"));
    int failed = 0, finished = 0;
    QObject::connect(&updater, &prism::Updater::downloadFailed,
                     [&](const QString &) { ++failed; });
    QObject::connect(&updater, &prism::Updater::downloadFinished,
                     [&](const QString &) { ++finished; });
    http.queue(QByteArrayLiteral("server error"), false,
               QByteArrayLiteral("500 Internal Server Error"));
    updater.downloadUpdate(http.url(QStringLiteral("/network-error.exe")));
    CHECK(waitUntil([&]() { return failed == 1; }), "network failure emits once");
    CHECK(finished == 0 && updaterArtifacts() == before,
          "network failure never succeeds or leaks");
}

static void testDuplicateDownloadUsesOneReply(HttpFixture &http) {
    prism::Updater updater(QStringLiteral("owner/repo"), QStringLiteral("v1.0.0"));
    QString completed;
    QObject::connect(&updater, &prism::Updater::downloadFinished,
                     [&](const QString &path) { completed = path; });
    http.queue(QByteArrayLiteral("payload"), true);
    const int requestBefore = http.requestCount;
    updater.downloadUpdate(http.url(QStringLiteral("/first.exe")));
    updater.downloadUpdate(http.url(QStringLiteral("/second.exe")));
    CHECK(waitUntil([&]() { return http.requestCount == requestBefore + 1; }),
          "duplicate download creates one request");
    http.releasePending();
    CHECK(waitUntil([&]() { return !completed.isEmpty(); }),
          "accepted download completes");
    QFile file(completed);
    CHECK(file.open(QIODevice::ReadOnly) && file.readAll() == "payload",
          "accepted download content intact");
    file.close();
    QFile::remove(completed);
}

static void testWriteAndCommitFailures(HttpFixture &http) {
    const QStringList before = updaterArtifacts();
    prism::Updater updater(QStringLiteral("owner/repo"), QStringLiteral("v1.0.0"));
    int failed = 0, finished = 0;
    QString failureMessage;
    QObject::connect(&updater, &prism::Updater::downloadFailed,
                     [&](const QString &message) { ++failed; failureMessage = message; });
    QObject::connect(&updater, &prism::Updater::downloadFinished,
                     [&](const QString &) { ++finished; });
    http.queue(QByteArrayLiteral("payload"), true);
    const int requestBefore = http.requestCount;
    updater.downloadUpdate(http.url(QStringLiteral("/App-Setup.exe")));
    CHECK(waitUntil([&]() { return http.requestCount == requestBefore + 1; }),
          "download request reaches loopback server");
    updater.m_downloadFile->cancelWriting();
    http.releasePending();
    CHECK(waitUntil([&]() { return failed == 1; }), "cancelled transaction fails once");
    CHECK(failureMessage.contains(QStringLiteral("失败")), "failure reason is explicit");
    CHECK(finished == 0 && updaterArtifacts() == before,
          "cancelled transaction never succeeds or leaks");
}

static void testDestroyActiveDownloadCleansTransaction(HttpFixture &http) {
    const QStringList before = updaterArtifacts();
    http.queue(QByteArrayLiteral("late payload"), true);
    const int requestBefore = http.requestCount;
    {
        prism::Updater updater(QStringLiteral("owner/repo"), QStringLiteral("v1.0.0"));
        updater.downloadUpdate(http.url(QStringLiteral("/late.exe")));
        CHECK(waitUntil([&]() { return http.requestCount == requestBefore + 1; }),
              "active download reaches server before destruction");
    }
    spinEvents(50);
    http.releasePending();
    spinEvents(50);
    CHECK(updaterArtifacts() == before,
          "destroying active updater removes transaction artifacts");
}

int main(int argc, char *argv[]) {
    if (!prism::test::configureNonInteractiveProcess())
        return 2;
    QCoreApplication app(argc, argv);
    HttpFixture http;
    testInvalidReleaseSchemas(http);
    testValidReleaseAndDuplicateCheck(http);
    testUniqueAtomicDownloads(http);
    testEmptyDownloadCleansArtifacts(http);
    testNetworkFailureCleansArtifacts(http);
    testDuplicateDownloadUsesOneReply(http);
    testWriteAndCommitFailures(http);
    testDestroyActiveDownloadCleansTransaction(http);
    qInfo() << (g_failed == 0 ? "ALL PASSED" : "FAILED") << g_failed;
    return g_failed == 0 ? 0 : 1;
}
