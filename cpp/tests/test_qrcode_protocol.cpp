// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
#include "QRCodeTestSupport.h"
#include "prism/QRCodeGenerator.h"

#include "qrcodegen/qrcodegen.hpp"

#include <QColor>
#include <QMutexLocker>
#include <QSize>
#include <QStringList>
#include <QThread>

#include <atomic>
#include <limits>

namespace prism {

struct QRCodeImageProviderTestAccess {
    static int entryCount(QRCodeImageProvider &provider) {
        QMutexLocker locker(&provider.m_cacheMutex);
        return provider.m_cache.size();
    }

    static qsizetype byteCount(QRCodeImageProvider &provider) {
        QMutexLocker locker(&provider.m_cacheMutex);
        return provider.m_cacheBytes;
    }

    static bool contains(QRCodeImageProvider &provider, const QString &key) {
        QMutexLocker locker(&provider.m_cacheMutex);
        return provider.m_cache.contains(key);
    }

    static QImage generate(QRCodeImageProvider &provider, const QString &content,
                           int size, const QString &foreground,
                           const QString &background, const QString &level) {
        return provider.generateQrCode(content, size, foreground, background, level);
    }
};

namespace test {
namespace {

QString sourceFor(const QString &content, int size = kQrCodeDefaultSize,
                  const QString &foreground = QStringLiteral("#000000"),
                  const QString &background = QStringLiteral("#ffffff"),
                  const QString &level = QStringLiteral("M")) {
    return QRCodeGenerator::instance()->getImageSource(content, size, foreground,
                                                        background, level);
}

QString idFor(const QString &content, int size = kQrCodeDefaultSize) {
    return sourceFor(content, size).mid(QStringLiteral("image://qrcode/").size());
}

QString providerIdFromRaw(const QByteArray &raw) {
    return QStringLiteral("v1.") + QString::fromLatin1(
        raw.toBase64(QByteArray::Base64UrlEncoding | QByteArray::OmitTrailingEquals));
}

bool isTransparentPlaceholder(const QImage &image, int expectedSize) {
    return image.size() == QSize(expectedSize, expectedSize) &&
           image.pixelColor(0, 0).alpha() == 0;
}

void testGoldenVectors(QRChecks &checks) {
    checks.require(
        sourceFor(QStringLiteral("HELLO"), 120, QStringLiteral("#112233"),
                  QStringLiteral("#445566"), QStringLiteral("H")) ==
            QStringLiteral("image://qrcode/") +
                QStringLiteral(
                    "v1.WzEsIkhFTExPIiwxMjAsIiMxMTIyMzMiLCIjNDQ1NTY2IiwiSCJd"),
        QStringLiteral("C++ golden URL diverged from Python"));
    checks.require(
        sourceFor(QStringLiteral("X"), 32, QStringLiteral("#AABBCC"),
                  QStringLiteral("white"), QStringLiteral("l")) ==
            QStringLiteral("image://qrcode/") +
                QStringLiteral(
                    "v1.WzEsIlgiLDMyLCIjYWFiYmNjIiwiI2ZmZmZmZiIsIkwiXQ"),
        QStringLiteral("producer normalization failed"));
    checks.require(
        sourceFor(QString::fromUtf8("你好，PrismQML 🌈 / QR"), 120,
                  QStringLiteral("#112233"), QStringLiteral("#445566"),
                  QStringLiteral("H")) ==
            QStringLiteral("image://qrcode/") +
                QStringLiteral(
                    "v1.WzEsIuS9oOWlve-8jFByaXNtUU1MIPCfjIggLyBRUiIsMTIwLCIjMTEyMjMzIiwiIzQ0NTU2NiIsIkgiXQ"),
        QStringLiteral("Unicode golden URL diverged from Python"));
    checks.require(
        sourceFor(QString::fromUtf8("A|#%?/&=+\"\\\nB"), 120,
                  QStringLiteral("#112233"), QStringLiteral("#445566"),
                  QStringLiteral("H")) ==
            QStringLiteral("image://qrcode/") +
                QStringLiteral(
                    "v1.WzEsIkF8IyU_LyY9K1wiXFxcbkIiLDEyMCwiIzExMjIzMyIsIiM0NDU1NjYiLCJIIl0"),
        QStringLiteral("reserved-character golden URL diverged from Python"));
}

void testProtocolValidation(QRChecks &checks) {
    checks.require(sourceFor(QString(), 120).isEmpty(),
                   QStringLiteral("empty content was accepted"));
    checks.require(sourceFor(QStringLiteral("A"), 31).isEmpty(),
                   QStringLiteral("undersized QR was accepted"));
    checks.require(sourceFor(QStringLiteral("A"), 1025).isEmpty(),
                   QStringLiteral("oversized QR was accepted"));
    checks.require(sourceFor(QString(1025, QLatin1Char('a')), 120).isEmpty(),
                   QStringLiteral("oversized content was accepted"));
    checks.require(
        sourceFor(QStringLiteral("A"), 120, QStringLiteral("#ffffff"),
                  QStringLiteral("white"))
            .isEmpty(),
        QStringLiteral("identical colors were accepted"));
    const QString worstCase = sourceFor(QString(1024, QChar(0x0001)), 1024,
                                        QStringLiteral("#112233"),
                                        QStringLiteral("#445566"),
                                        QStringLiteral("H"));
    checks.require(worstCase.mid(QStringLiteral("image://qrcode/").size()).size() ==
                       8242,
                   QStringLiteral("worst-case provider id length drifted"));
}

QStringList invalidProviderIds() {
    const QByteArray validPrefix("[1,\"A\",120,\"#000000\",\"#ffffff\",\"M\"");
    return {
        QStringLiteral("HELLO|120|#112233|#445566|H"),
        QStringLiteral("v1."), QStringLiteral("v2.AA"), QStringLiteral("v1.A"),
        QStringLiteral("v1.AA=="), QStringLiteral("v1.A/B"),
        QStringLiteral("v1.A+B"), QStringLiteral("v1.A?B"),
        QStringLiteral("v1.A#B"), QStringLiteral("v1.A%2FB"),
        QStringLiteral("v1.") + QString(8240, QLatin1Char('A')),
        providerIdFromRaw(QByteArray("not-json")),
        providerIdFromRaw(QByteArray(1, static_cast<char>(0xFF))),
        providerIdFromRaw(QByteArray::fromHex("efbbbf") + validPrefix + QByteArray("]")),
        providerIdFromRaw(QByteArray(3000, '[') + QByteArray("0") +
                          QByteArray(3000, ']')),
        providerIdFromRaw(QByteArray("[1,\"A\",120,\"#000000\",\"#ffffff\"]")),
        providerIdFromRaw(
            QByteArray("[1,\"A\",120,\"#000000\",\"#ffffff\",\"M\",0]")),
        providerIdFromRaw(
            QByteArray("[1,true,120,\"#000000\",\"#ffffff\",\"M\"]")),
        providerIdFromRaw(
            QByteArray("[1,\"A\",true,\"#000000\",\"#ffffff\",\"M\"]")),
        providerIdFromRaw(
            QByteArray("[1,\"A\",120.0,\"#000000\",\"#ffffff\",\"M\"]")),
        providerIdFromRaw(
            QByteArray("[1,\"A\",120,\"#80000000\",\"#ffffff\",\"M\"]")),
        providerIdFromRaw(
            QByteArray("[1,\"A\",120,\"#abc\",\"#ffffff\",\"M\"]")),
        providerIdFromRaw(
            QByteArray("[1,\"A\",120,\"#000000\",\"#ffffff\",\"m\"]")),
    };
}

void testInvalidProviderIds(QRChecks &checks) {
    QRCodeImageProvider provider;
    for (const QString &providerId : invalidProviderIds()) {
        QSize reported;
        const QImage image = provider.requestImage(
            providerId, &reported,
            QSize(std::numeric_limits<int>::max(), std::numeric_limits<int>::max()));
        checks.require(isTransparentPlaceholder(image, kQrCodeDefaultSize),
                       QStringLiteral("invalid id escaped bounded placeholder"));
        checks.require(reported == image.size(),
                       QStringLiteral("invalid id reported the wrong size"));
    }
    checks.require(QRCodeImageProviderTestAccess::entryCount(provider) == 0,
                   QStringLiteral("invalid ids polluted the cache"));
}

void testEntryCacheLimit(QRChecks &checks) {
    QRCodeImageProvider provider;
    QStringList ids;
    for (int index = 0; index <= kQrCodeMaxCacheEntries; ++index)
        ids.append(idFor(QStringLiteral("small-%1").arg(index), 32));
    for (int index = 0; index < kQrCodeMaxCacheEntries; ++index)
        provider.requestImage(ids.at(index), nullptr, QSize());
    provider.requestImage(ids.first(), nullptr, QSize());
    provider.requestImage(ids.last(), nullptr, QSize());
    checks.require(QRCodeImageProviderTestAccess::entryCount(provider) ==
                       kQrCodeMaxCacheEntries,
                   QStringLiteral("entry-count cache limit failed"));
    checks.require(QRCodeImageProviderTestAccess::contains(provider, ids.first()) &&
                       !QRCodeImageProviderTestAccess::contains(provider, ids.at(1)),
                   QStringLiteral("LRU ordering failed"));
}

void testByteCacheLimit(QRChecks &checks) {
    QRCodeImageProvider provider;
    for (int index = 0; index < 9; ++index)
        provider.requestImage(idFor(QStringLiteral("large-%1").arg(index), 1024),
                              nullptr, QSize());
    checks.require(QRCodeImageProviderTestAccess::entryCount(provider) == 8 &&
                       QRCodeImageProviderTestAccess::byteCount(provider) ==
                           kQrCodeMaxCacheBytes,
                   QStringLiteral("byte-budget cache limit failed"));
}

void testReentrancy(QRChecks &checks) {
    QRCodeImageProvider provider;
    std::atomic_bool concurrentOk{true};
    QList<QThread *> threads;
    for (int index = 0; index < 24; ++index) {
        const QString providerId = idFor(QStringLiteral("thread-%1").arg(index % 4), 96);
        threads.append(QThread::create([&provider, &concurrentOk, providerId]() {
            if (provider.requestImage(providerId, nullptr, QSize()).size() !=
                QSize(96, 96)) {
                concurrentOk.store(false);
            }
        }));
    }
    for (QThread *thread : threads) thread->start();
    for (QThread *thread : threads) {
        thread->wait();
        delete thread;
    }
    checks.require(concurrentOk.load() &&
                       QRCodeImageProviderTestAccess::entryCount(provider) == 4,
                   QStringLiteral("reentrant provider requests failed"));
}

bool matchesMatrix(const QImage &image, const qrcodegen::QrCode &expected) {
    if (image.size() != QSize(116, 116)) return false;
    for (int y = 0; y < expected.getSize(); ++y) {
        for (int x = 0; x < expected.getSize(); ++x) {
            const bool dark = image.pixelColor((x + 4) * 4 + 2, (y + 4) * 4 + 2) ==
                              QColor(QStringLiteral("#000000"));
            if (dark != expected.getModule(x, y)) return false;
        }
    }
    return true;
}

void testExactEcc(QRChecks &checks) {
    struct EccCase {
        QString level;
        qrcodegen::QrCode::Ecc ecc;
    };
    const QList<EccCase> cases = {
        {QStringLiteral("L"), qrcodegen::QrCode::Ecc::LOW},
        {QStringLiteral("M"), qrcodegen::QrCode::Ecc::MEDIUM},
        {QStringLiteral("Q"), qrcodegen::QrCode::Ecc::QUARTILE},
        {QStringLiteral("H"), qrcodegen::QrCode::Ecc::HIGH},
    };
    const auto segments = qrcodegen::QrSegment::makeSegments("A");
    QRCodeImageProvider provider;
    for (const EccCase &testCase : cases) {
        const QString providerId = sourceFor(
            QStringLiteral("A"), 116, QStringLiteral("#000000"),
            QStringLiteral("#ffffff"), testCase.level)
                                       .mid(QStringLiteral("image://qrcode/").size());
        const QImage image = provider.requestImage(providerId, nullptr, QSize());
        const qrcodegen::QrCode expected = qrcodegen::QrCode::encodeSegments(
            segments, testCase.ecc, 1, 40, -1, false);
        checks.require(matchesMatrix(image, expected),
                       QStringLiteral("ECC matrix mismatch for %1").arg(testCase.level));
    }
}

void testEncoderOverflow(QRChecks &checks) {
    QRCodeImageProvider provider;
    const QImage overflow = QRCodeImageProviderTestAccess::generate(
        provider, QString(2000, QLatin1Char('a')), 1024, QStringLiteral("#000000"),
        QStringLiteral("#ffffff"), QStringLiteral("H"));
    checks.require(overflow.isNull(),
                   QStringLiteral("data_too_long escaped the generation boundary"));
}

void testMixedModeParity(QRChecks &checks) {
    QRCodeImageProvider provider;
    const QString providerId =
        sourceFor(QString(20, QLatin1Char('1')) + QLatin1Char('a'), 32,
                  QStringLiteral("#000000"), QStringLiteral("#ffffff"),
                  QStringLiteral("L"))
            .mid(QStringLiteral("image://qrcode/").size());
    const QImage image =
        provider.requestImage(providerId, nullptr, QSize(32, 32));
    checks.require(isTransparentPlaceholder(image, 32) &&
                       QRCodeImageProviderTestAccess::entryCount(provider) == 0,
                   QStringLiteral("Python/C++ mixed-mode capacity diverged"));
}

}  // namespace

void runQrProtocolTests(QRChecks &checks) {
    testGoldenVectors(checks);
    testProtocolValidation(checks);
    testInvalidProviderIds(checks);
    testEntryCacheLimit(checks);
    testByteCacheLimit(checks);
    testReentrancy(checks);
    testExactEcc(checks);
    testEncoderOverflow(checks);
    testMixedModeParity(checks);
}

}  // namespace test
}  // namespace prism
