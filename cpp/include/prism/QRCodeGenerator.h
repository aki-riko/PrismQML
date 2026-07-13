// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - QRCodeGenerator (镜像 Python providers/qrcode_generator.py)
//
// QR encoding backend 二维码编码后端: 内建完整编码(Reed-Solomon 纠错+掩码),
// 基于 nayuki QR-Code-generator (third_party/qrcodegen, MIT)。available=true。
// getImageSource 返回版本化单段 URL, provider 严格解码后真实渲染二维码。
#pragma once

#include <QHash>
#include <QImage>
#include <QList>
#include <QMutex>
#include <QObject>
#include <QQuickImageProvider>
#include <QString>

namespace prism {

inline constexpr int kQrCodeDefaultSize = 128;
inline constexpr int kQrCodeMinimumSize = 32;
inline constexpr int kQrCodeMaximumSize = 1024;
inline constexpr int kQrCodeQuietZoneModules = 4;
inline constexpr int kQrCodeMaxCacheEntries = 64;
inline constexpr qsizetype kQrCodeMaxCacheBytes = 32 * 1024 * 1024;

struct QRCodeImageProviderTestAccess;

class QRCodeImageProvider : public QQuickImageProvider {
public:
    QRCodeImageProvider() : QQuickImageProvider(QQuickImageProvider::Image) {}
    QImage requestImage(const QString &id, QSize *size, const QSize &requestedSize) override;

private:
    friend struct QRCodeImageProviderTestAccess;

    mutable QMutex m_cacheMutex;
    QHash<QString, QImage> m_cache;
    QList<QString> m_lruOrder;
    qsizetype m_cacheBytes = 0;

    QImage generateQrCode(const QString &content, int size, const QString &fgColor,
                          const QString &bgColor,
                          const QString &errorLevel) const noexcept;
    QImage cachedImage(const QString &key, bool *found);
    QImage storeCachedImage(const QString &key, const QImage &image);
    static int boundedPlaceholderSize(const QSize &requestedSize);
    static QImage createPlaceholder(int size);
};

class QRCodeGenerator : public QObject {
    Q_OBJECT
    Q_PROPERTY(bool available READ available NOTIFY availableChanged)
public:
    static QRCodeGenerator *instance();
    // 是否有可用的 QR 编码后端 (内建 nayuki 编码器, 恒 true)
    bool available() const { return true; }
public slots:
    QString getImageSource(const QString &content, int size = kQrCodeDefaultSize,
                           const QString &fgColor = QStringLiteral("#000000"),
                           const QString &bgColor = QStringLiteral("#ffffff"),
                           const QString &errorLevel = QStringLiteral("M"));
signals:
    void availableChanged();
private:
    explicit QRCodeGenerator(QObject *parent = nullptr) : QObject(parent) {}
};

}  // namespace prism
