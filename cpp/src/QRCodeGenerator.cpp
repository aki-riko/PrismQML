// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ host - strict QR protocol, rendering, and bounded cache.
#include "prism/QRCodeGenerator.h"

#include "QRCodeProtocol_p.h"
#include "qrcodegen/qrcodegen.hpp"

#include <QColor>
#include <QDebug>
#include <QMutexLocker>
#include <QPainter>
#include <QRect>

#include <new>
#include <optional>
#include <vector>

namespace prism {
namespace {

std::optional<qrcodegen::QrCode::Ecc> mapEcc(const QString &level) {
    if (level == QStringLiteral("L")) return qrcodegen::QrCode::Ecc::LOW;
    if (level == QStringLiteral("M")) return qrcodegen::QrCode::Ecc::MEDIUM;
    if (level == QStringLiteral("Q")) return qrcodegen::QrCode::Ecc::QUARTILE;
    if (level == QStringLiteral("H")) return qrcodegen::QrCode::Ecc::HIGH;
    return std::nullopt;
}

QImage reportSize(const QImage &image, QSize *reportedSize) {
    if (reportedSize) *reportedSize = image.size();
    return image;
}

QImage renderCode(const qrcodegen::QrCode &code, int size,
                  const QColor &foreground, const QColor &background) {
    const int modules = code.getSize() + kQrCodeQuietZoneModules * 2;
    const int moduleSize = size / modules;
    if (moduleSize < 1) return QImage();

    const int offset = (size - modules * moduleSize) / 2;
    QImage image(size, size, QImage::Format_RGB32);
    if (image.isNull()) return image;
    image.fill(background);

    QPainter painter(&image);
    for (int y = 0; y < code.getSize(); ++y) {
        for (int x = 0; x < code.getSize(); ++x) {
            if (!code.getModule(x, y)) continue;
            painter.fillRect(
                QRect(offset + (x + kQrCodeQuietZoneModules) * moduleSize,
                      offset + (y + kQrCodeQuietZoneModules) * moduleSize,
                      moduleSize, moduleSize),
                foreground);
        }
    }
    painter.end();
    return image;
}

QImage encodeAndRender(const QString &content, int size, const QColor &foreground,
                       const QColor &background, qrcodegen::QrCode::Ecc ecc) {
    const QByteArray utf8 = content.toUtf8();
    const std::vector<qrcodegen::QrSegment> segments =
        qrcodegen::QrSegment::makeSegments(utf8.constData());
    const qrcodegen::QrCode code = qrcodegen::QrCode::encodeSegments(
        segments, ecc, qrcodegen::QrCode::MIN_VERSION,
        qrcodegen::QrCode::MAX_VERSION, -1, false);
    return renderCode(code, size, foreground, background);
}

}  // namespace

QRCodeGenerator *QRCodeGenerator::instance() {
    static QRCodeGenerator *instance = new QRCodeGenerator();
    return instance;
}

QString QRCodeGenerator::getImageSource(const QString &content, int size,
                                        const QString &fgColor,
                                        const QString &bgColor,
                                        const QString &errorLevel) {
    return qrcode_protocol::buildImageSource(content, size, fgColor, bgColor,
                                             errorLevel);
}

QImage QRCodeImageProvider::generateQrCode(const QString &content, int size,
                                           const QString &fgColor,
                                           const QString &bgColor,
                                           const QString &errorLevel) const noexcept {
    try {
        const auto ecc = mapEcc(errorLevel);
        const QColor foreground(fgColor);
        const QColor background(bgColor);
        if (!ecc || size < kQrCodeMinimumSize || size > kQrCodeMaximumSize ||
            !foreground.isValid() || foreground.alpha() != 255 ||
            !background.isValid() || background.alpha() != 255) {
            return QImage();
        }

        return encodeAndRender(content, size, foreground, background, *ecc);
    } catch (const qrcodegen::data_too_long &) {
        qWarning() << "QRCode data exceeds encoder capacity";
    } catch (const std::bad_alloc &) {
        qWarning() << "QRCode allocation failed within bounded request";
    } catch (const std::exception &error) {
        qWarning() << "QRCode generation failed:" << error.what();
    } catch (...) {
        qWarning() << "QRCode generation failed with a non-standard exception";
    }
    return QImage();
}

QImage QRCodeImageProvider::cachedImage(const QString &key, bool *found) {
    QMutexLocker locker(&m_cacheMutex);
    const auto iterator = m_cache.constFind(key);
    if (iterator == m_cache.cend()) {
        *found = false;
        return QImage();
    }
    const QImage image = iterator.value();
    m_lruOrder.removeAll(key);
    m_lruOrder.append(key);
    *found = true;
    return image;
}

QImage QRCodeImageProvider::storeCachedImage(const QString &key,
                                             const QImage &image) {
    const qsizetype cost = image.sizeInBytes();
    if (image.isNull() || cost <= 0 || cost > kQrCodeMaxCacheBytes) return image;

    QMutexLocker locker(&m_cacheMutex);
    const auto existing = m_cache.constFind(key);
    if (existing != m_cache.cend()) {
        const QImage cached = existing.value();
        m_lruOrder.removeAll(key);
        m_lruOrder.append(key);
        return cached;
    }
    while (!m_lruOrder.isEmpty() &&
           (m_cache.size() + 1 > kQrCodeMaxCacheEntries ||
            m_cacheBytes + cost > kQrCodeMaxCacheBytes)) {
        const QString evictedKey = m_lruOrder.takeFirst();
        const QImage evicted = m_cache.take(evictedKey);
        m_cacheBytes -= evicted.sizeInBytes();
    }
    m_cache.insert(key, image);
    m_lruOrder.append(key);
    m_cacheBytes += cost;
    return image;
}

int QRCodeImageProvider::boundedPlaceholderSize(const QSize &requestedSize) {
    if (requestedSize.width() == requestedSize.height() &&
        requestedSize.width() >= kQrCodeMinimumSize &&
        requestedSize.width() <= kQrCodeMaximumSize) {
        return requestedSize.width();
    }
    return kQrCodeDefaultSize;
}

QImage QRCodeImageProvider::createPlaceholder(int size) {
    const int bounded =
        size >= kQrCodeMinimumSize && size <= kQrCodeMaximumSize
            ? size
            : kQrCodeDefaultSize;
    QImage image(bounded, bounded, QImage::Format_ARGB32_Premultiplied);
    image.fill(Qt::transparent);
    return image;
}

QImage QRCodeImageProvider::requestImage(const QString &id, QSize *size,
                                         const QSize &requestedSize) {
    const auto request = qrcode_protocol::decodeProviderId(id);
    if (!request) {
        return reportSize(createPlaceholder(boundedPlaceholderSize(requestedSize)),
                          size);
    }

    bool found = false;
    const QImage cached = cachedImage(id, &found);
    if (found) return reportSize(cached, size);

    const QImage generated =
        generateQrCode(request->content, request->size, request->foreground,
                       request->background, request->errorLevel);
    if (generated.isNull()) {
        return reportSize(createPlaceholder(boundedPlaceholderSize(requestedSize)),
                          size);
    }
    return reportSize(storeCachedImage(id, generated), size);
}

}  // namespace prism
