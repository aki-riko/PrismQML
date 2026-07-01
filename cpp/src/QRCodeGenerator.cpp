// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - QRCodeGenerator 实现 (真实编码, 镜像 Python _generate_qrcode)
// 编码后端: nayuki QR-Code-generator (third_party/qrcodegen, MIT)。
#include "prism/QRCodeGenerator.h"

#include <QImage>
#include <QColor>
#include <QSize>
#include <QRect>
#include <QPainter>
#include <QStringList>

#include "qrcodegen/qrcodegen.hpp"

namespace prism {

QRCodeGenerator *QRCodeGenerator::instance() {
    static QRCodeGenerator *s = new QRCodeGenerator();
    return s;
}

QString QRCodeGenerator::getImageSource(const QString &content, int size,
                                        const QString &fgColor, const QString &bgColor,
                                        const QString &errorLevel) {
    // URL 编码 content 中的 | (镜像 Python: replace("|","%7C"))
    QString safe = content;
    safe.replace(QLatin1Char('|'), QStringLiteral("%7C"));
    return QStringLiteral("image://qrcode/%1|%2|%3|%4|%5")
        .arg(safe).arg(size).arg(fgColor, bgColor, errorLevel);
}

// 错误纠正级别映射 (镜像 Python error_map: L/M/Q/H)
static qrcodegen::QrCode::Ecc mapEcc(const QString &level) {
    const QString l = level.toUpper();
    if (l == QStringLiteral("L")) return qrcodegen::QrCode::Ecc::LOW;
    if (l == QStringLiteral("Q")) return qrcodegen::QrCode::Ecc::QUARTILE;
    if (l == QStringLiteral("H")) return qrcodegen::QrCode::Ecc::HIGH;
    return qrcodegen::QrCode::Ecc::MEDIUM;  // 默认 M (与 Python 一致)
}

// 真实生成二维码 QImage (镜像 Python _generate_qrcode: border=2, 模块整数缩放)
QImage QRCodeImageProvider::generateQrCode(const QString &content, int size,
                                           const QString &fgColor, const QString &bgColor,
                                           const QString &errorLevel) const {
    if (content.isEmpty())
        return createPlaceholder(size);

    qrcodegen::QrCode qr = qrcodegen::QrCode::encodeText(
        content.toUtf8().constData(), mapEcc(errorLevel));
    const int border = 2;                              // 边框 2 个模块 (镜像 Python)
    const int modules = qr.getSize() + border * 2;     // 含边框的模块数

    // 计算模块像素大小以适应目标尺寸 (镜像 Python module_size)
    const int moduleSize = qMax(1, size / modules);
    const int actualSize = modules * moduleSize;

    QImage image(actualSize, actualSize, QImage::Format_RGB32);
    const QColor fg(fgColor);
    const QColor bg(bgColor);
    image.fill(bg.isValid() ? bg : QColor(QStringLiteral("#ffffff")));

    QPainter painter(&image);
    const QColor dark = fg.isValid() ? fg : QColor(QStringLiteral("#000000"));
    for (int y = 0; y < qr.getSize(); ++y) {
        for (int x = 0; x < qr.getSize(); ++x) {
            if (qr.getModule(x, y)) {
                painter.fillRect(QRect((x + border) * moduleSize,
                                       (y + border) * moduleSize,
                                       moduleSize, moduleSize),
                                 dark);
            }
        }
    }
    painter.end();

    // 缩放到目标尺寸 (镜像 Python image.scaled)
    if (actualSize != size && size > 0)
        image = image.scaled(size, size);
    return image;
}

QImage QRCodeImageProvider::createPlaceholder(int size) {
    const int s = size > 0 ? size : 150;
    QImage image(s, s, QImage::Format_RGB32);
    image.fill(QColor(QStringLiteral("#f0f0f0")));
    return image;
}

// 请求二维码图片 (镜像 Python requestImage: 解析 content|size|fg|bg|level + LRU 缓存)
QImage QRCodeImageProvider::requestImage(const QString &id, QSize *size,
                                         const QSize &requestedSize) {
    // 解析参数 content|size|fg|bg|level
    const QStringList parts = id.split(QLatin1Char('|'));
    const QString content = parts.value(0);
    int targetSize = 150;
    if (parts.size() > 1) {
        bool ok = false;
        const int sz = parts[1].toInt(&ok);
        if (ok && sz > 0) targetSize = sz;
    }
    const QString fg = parts.size() > 2 ? parts[2] : QStringLiteral("#000000");
    const QString bg = parts.size() > 3 ? parts[3] : QStringLiteral("#ffffff");
    const QString level = parts.size() > 4 ? parts[4] : QStringLiteral("M");

    if (content.isEmpty()) {
        QImage img = createPlaceholder(requestedSize.width() > 0 ? requestedSize.width() : targetSize);
        if (size) *size = img.size();
        return img;
    }

    // 缓存 key (镜像 Python cache_key)
    const QString cacheKey = QStringLiteral("%1|%2|%3|%4|%5")
        .arg(content).arg(targetSize).arg(fg, bg, level);
    if (m_cache.contains(cacheKey)) {
        m_lruOrder.removeAll(cacheKey);
        m_lruOrder.append(cacheKey);
        const QImage &img = m_cache[cacheKey];
        if (size) *size = img.size();
        return img;
    }

    QImage img = generateQrCode(content, targetSize, fg, bg, level);

    // 缓存限制: 超出时清除最早的一半 (镜像 Python evict oldest half)
    if (m_cache.size() >= kMaxCacheSize) {
        const int removeCount = kMaxCacheSize / 2;
        for (int i = 0; i < removeCount && !m_lruOrder.isEmpty(); ++i)
            m_cache.remove(m_lruOrder.takeFirst());
    }
    m_cache.insert(cacheKey, img);
    m_lruOrder.append(cacheKey);

    if (size) *size = img.size();
    return img;
}

}  // namespace prism
