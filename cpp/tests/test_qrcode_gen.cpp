// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// Real QQmlEngine -> QRCode.qml -> ImageProvider regression.
#include "QRCodeTestSupport.h"
#include "TestProcess.h"
#include "prism/ConfigManager.h"
#include "prism/QRCodeGenerator.h"
#include "prism/Registry.h"

#include <QColor>
#include <QCoreApplication>
#include <QDir>
#include <QElapsedTimer>
#include <QEventLoop>
#include <QFile>
#include <QGuiApplication>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QMutex>
#include <QMutexLocker>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QQmlError>
#include <QSet>
#include <QSize>
#include <QTemporaryDir>
#include <QThread>
#include <QTimer>
#include <QUrl>
#include <QVariantMap>

#include <functional>
#include <memory>
#include <optional>

using namespace prism;
using prism::test::QRChecks;

namespace {

constexpr int kQmlTimeoutMs = 5000;
const QString kGoldenProviderId = QStringLiteral(
    "v1.WzEsIkhFTExPIiwxMjAsIiMxMTIyMzMiLCIjNDQ1NTY2IiwiSCJd");

struct Snapshot {
    QString providerId;
    QSize requestedSize;
    QImage image;
};

struct DecodeCase {
    QString content;
    int size;
    QString level;
};

class CapturingQRCodeProvider final : public QRCodeImageProvider {
public:
    QImage requestImage(const QString &id, QSize *size,
                        const QSize &requestedSize) override {
        const QImage image = QRCodeImageProvider::requestImage(id, size, requestedSize);
        QMutexLocker locker(&m_mutex);
        m_snapshots.append(Snapshot{id, requestedSize, image.copy()});
        return image;
    }

    bool snapshotFor(const QString &providerId, Snapshot *snapshot) const {
        QMutexLocker locker(&m_mutex);
        for (auto iterator = m_snapshots.crbegin(); iterator != m_snapshots.crend();
             ++iterator) {
            if (iterator->providerId != providerId) continue;
            *snapshot = *iterator;
            return true;
        }
        return false;
    }

private:
    mutable QMutex m_mutex;
    QList<Snapshot> m_snapshots;
};

bool waitUntil(const std::function<bool()> &predicate) {
    QElapsedTimer timer;
    timer.start();
    while (!predicate() && timer.elapsed() < kQmlTimeoutMs) {
        QCoreApplication::processEvents(QEventLoop::AllEvents, 20);
        QThread::msleep(1);
    }
    return predicate();
}

bool waitForComponent(QQmlComponent &component) {
    if (component.isLoading()) {
        QEventLoop loop;
        QObject::connect(&component, &QQmlComponent::statusChanged, &loop,
                         [&loop](QQmlComponent::Status status) {
                             if (status != QQmlComponent::Loading) loop.quit();
                         });
        QTimer::singleShot(kQmlTimeoutMs, &loop, &QEventLoop::quit);
        loop.exec();
    }
    if (component.isReady()) return true;
    for (const QQmlError &error : component.errors()) qCritical() << error.toString();
    return false;
}

QString sourceFor(const QString &content, int size, const QString &foreground,
                  const QString &background, const QString &level) {
    return QRCodeGenerator::instance()->getImageSource(content, size, foreground,
                                                        background, level);
}

QJsonArray decodedPayload(const QString &providerId) {
    const QByteArray raw = QByteArray::fromBase64(
        providerId.mid(3).toLatin1(),
        QByteArray::Base64UrlEncoding | QByteArray::AbortOnBase64DecodingErrors);
    return QJsonDocument::fromJson(raw).array();
}

QSet<QString> renderedColors(const QImage &image) {
    QSet<QString> colors;
    for (int y = 0; y < image.height(); ++y)
        for (int x = 0; x < image.width(); ++x)
            colors.insert(image.pixelColor(x, y).name().toLower());
    return colors;
}

QVariantMap initialProperties(const QString &content, int size,
                              const QString &foreground, const QString &background,
                              const QString &level) {
    return {{QStringLiteral("content"), content},
            {QStringLiteral("size"), size},
            {QStringLiteral("foregroundColor"), QColor(foreground)},
            {QStringLiteral("backgroundColor"), QColor(background)},
            {QStringLiteral("errorLevel"), level}};
}

std::optional<Snapshot> waitForSnapshot(CapturingQRCodeProvider &provider,
                                        const QString &expectedId, QObject &root) {
    Snapshot snapshot;
    const bool ready = waitUntil([&]() {
        return provider.snapshotFor(expectedId, &snapshot) &&
               root.property("imageReady").toBool();
    });
    if (!ready) return std::nullopt;
    root.setProperty("content", QString());
    waitUntil([&]() { return !root.property("imageReady").toBool(); });
    return snapshot;
}

std::optional<Snapshot> renderRealQml(QQmlEngine &engine,
                                      CapturingQRCodeProvider &provider,
                                      const QString &content, int size,
                                      const QString &foreground,
                                      const QString &background,
                                      const QString &level) {
    static const QByteArray qml = "import QtQuick\nimport PrismQML\nQRCode {}\n";
    QQmlComponent component(&engine);
    component.setData(qml, QUrl(QStringLiteral("inline:qrcode-contract.qml")));
    if (!waitForComponent(component)) return std::nullopt;
    std::unique_ptr<QObject> root(component.beginCreate(engine.rootContext()));
    if (!root) return std::nullopt;
    component.setInitialProperties(
        root.get(), initialProperties(content, size, foreground, background, level));
    component.completeCreate();
    const QString expectedId =
        sourceFor(content, size, foreground, background, level)
            .mid(QStringLiteral("image://qrcode/").size());
    return waitForSnapshot(provider, expectedId, *root);
}

void verifyOriginalQml(QRChecks &checks, QQmlEngine &engine,
                       CapturingQRCodeProvider &provider) {
    const auto original = renderRealQml(
        engine, provider, QStringLiteral("HELLO"), 120, QStringLiteral("#112233"),
        QStringLiteral("#445566"), QStringLiteral("H"));
    checks.require(original.has_value(),
                   QStringLiteral("real QML failure vector did not render"));
    if (!original) return;

    const QJsonArray payload = decodedPayload(original->providerId);
    checks.require(original->providerId == kGoldenProviderId,
                   QStringLiteral("QML changed the canonical provider id"));
    checks.require(payload.size() == 6 &&
                       payload.at(1).toString() == QStringLiteral("HELLO") &&
                       payload.at(2).toInt() == 120 &&
                       payload.at(3).toString() == QStringLiteral("#112233") &&
                       payload.at(4).toString() == QStringLiteral("#445566") &&
                       payload.at(5).toString() == QStringLiteral("H"),
                   QStringLiteral("real QML fields were not preserved"));
    checks.require(original->requestedSize == QSize(120, 120) &&
                       original->image.size() == QSize(120, 120),
                   QStringLiteral("real QML size was not preserved"));
    const QSet<QString> colors = renderedColors(original->image);
    checks.require(colors.contains(QStringLiteral("#112233")) &&
                       colors.contains(QStringLiteral("#445566")),
                   QStringLiteral("real QML colors were not rendered"));
}

QList<DecodeCase> decodeCases() {
    return {
        {QStringLiteral("https://github.com/aki-riko/PrismQML"), 320,
         QStringLiteral("M")},
        {QString::fromUtf8("你好，PrismQML 😀 |#%?/&=+\"\\\n第二行"), 384,
         QStringLiteral("H")},
    };
}

QJsonArray writeDecodeImages(QRChecks &checks, QQmlEngine &engine,
                             CapturingQRCodeProvider &provider,
                             const QString &outputDirectory) {
    QJsonArray manifest;
    const QList<DecodeCase> cases = decodeCases();
    for (int index = 0; index < cases.size(); ++index) {
        const DecodeCase &testCase = cases.at(index);
        const auto snapshot = renderRealQml(
            engine, provider, testCase.content, testCase.size,
            QStringLiteral("#000000"), QStringLiteral("#ffffff"), testCase.level);
        checks.require(snapshot.has_value(),
                       QStringLiteral("real QML decode case did not render"));
        if (!snapshot) continue;
        const QString fileName = QStringLiteral("qr_%1.png").arg(index);
        checks.require(snapshot->image.save(QDir(outputDirectory).filePath(fileName), "PNG"),
                       QStringLiteral("failed to save real QML QR image"));
        manifest.append(QJsonObject{{QStringLiteral("file"), fileName},
                                    {QStringLiteral("content"), testCase.content}});
    }
    return manifest;
}

void writeManifest(QRChecks &checks, const QString &outputDirectory,
                   const QJsonArray &manifest) {
    QFile file(QDir(outputDirectory).filePath(QStringLiteral("manifest.json")));
    checks.require(file.open(QIODevice::WriteOnly),
                   QStringLiteral("failed to open QR manifest"));
    if (!file.isOpen()) return;
    file.write(QJsonDocument(manifest).toJson(QJsonDocument::Indented));
    file.close();
}

void testRealQml(QRChecks &checks, const QString &importPath,
                 const QString &outputDirectory) {
    QQmlEngine engine;
    registerTypes(&engine, importPath);
    engine.removeImageProvider(QStringLiteral("qrcode"));
    auto *provider = new CapturingQRCodeProvider();
    engine.addImageProvider(QStringLiteral("qrcode"), provider);
    verifyOriginalQml(checks, engine, *provider);
    writeManifest(checks, outputDirectory,
                  writeDecodeImages(checks, engine, *provider, outputDirectory));
}

}  // namespace

int main(int argc, char *argv[]) {
    if (!prism::test::configureNonInteractiveProcess()) return 2;
    QTemporaryDir configDirectory(
        QDir::tempPath() + QStringLiteral("/prism-qrcode-config-XXXXXX"));
    if (!configDirectory.isValid()) return 2;
    qputenv(kConfigFilePathEnvironment,
            QFile::encodeName(configDirectory.filePath(QStringLiteral("app.json"))));
    QGuiApplication application(argc, argv);

    if (argc < 3) {
        qCritical() << "Usage: prism_test_qrcode_gen <output-dir> <qml-import-path>";
        return 2;
    }
    const QString outputDirectory = QString::fromLocal8Bit(argv[1]);
    const QString importPath = QString::fromLocal8Bit(argv[2]);
    if (!QDir().mkpath(outputDirectory) || !QDir(importPath).exists()) return 2;

    QRChecks checks;
    prism::test::runQrProtocolTests(checks);
    testRealQml(checks, importPath, outputDirectory);
    qInfo() << "QR_GEN_DONE failures" << checks.failures;
    return checks.failures == 0 ? 0 : 1;
}
