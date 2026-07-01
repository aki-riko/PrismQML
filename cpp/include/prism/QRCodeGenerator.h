// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - QRCodeGenerator (镜像 Python providers/qrcode_generator.py)
//
// QR encoding backend 二维码编码后端: 内建完整编码(Reed-Solomon 纠错+掩码),
// 基于 nayuki QR-Code-generator (third_party/qrcodegen, MIT)。available=true。
// getImageSource 返回规范 URL image://qrcode/content|size|fg|bg|level,
// QRCodeImageProvider 据此真实渲染二维码 (镜像 Python _generate_qrcode + 128 条 LRU 缓存)。
#pragma once

#include <QObject>
#include <QString>
#include <QQuickImageProvider>
#include <QHash>
#include <QList>
#include <QImage>

namespace prism {

class QRCodeImageProvider : public QQuickImageProvider {
public:
    QRCodeImageProvider() : QQuickImageProvider(QQuickImageProvider::Image) {}
    QImage requestImage(const QString &id, QSize *size, const QSize &requestedSize) override;

private:
    // 最大缓存条目数 (镜像 Python MAX_CACHE_SIZE)
    static constexpr int kMaxCacheSize = 128;
    QHash<QString, QImage> m_cache;   // cacheKey -> QImage
    QList<QString> m_lruOrder;        // LRU 顺序 (队首最旧)

    // 真实生成二维码 (镜像 Python _generate_qrcode); content 为空/编码失败返回占位图
    QImage generateQrCode(const QString &content, int size, const QString &fgColor,
                          const QString &bgColor, const QString &errorLevel) const;
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
    // 返回 image://qrcode/content|size|fg|bg|level (镜像 getImageSource)
    QString getImageSource(const QString &content, int size = 150,
                           const QString &fgColor = QStringLiteral("#000000"),
                           const QString &bgColor = QStringLiteral("#ffffff"),
                           const QString &errorLevel = QStringLiteral("M"));
signals:
    void availableChanged();
private:
    explicit QRCodeGenerator(QObject *parent = nullptr) : QObject(parent) {}
};

}  // namespace prism
