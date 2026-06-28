// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - QRCodeGenerator 实现 (降级版, 见头文件说明)
#include "prism/QRCodeGenerator.h"

#include <QImage>
#include <QColor>
#include <QSize>

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

// 降级: 返回占位图 (镜像 Python _create_placeholder, 无 qrcode 库时行为)
QImage QRCodeImageProvider::requestImage(const QString &id, QSize *size,
                                         const QSize &requestedSize) {
    int s = (requestedSize.width() > 0) ? requestedSize.width() : 150;
    // 从 id 解析目标尺寸 content|size|...
    const QStringList parts = id.split(QLatin1Char('|'));
    if (parts.size() > 1) {
        bool ok = false;
        const int sz = parts[1].toInt(&ok);
        if (ok && sz > 0) s = sz;
    }
    QImage img(s, s, QImage::Format_RGB32);
    img.fill(QColor(QStringLiteral("#f0f0f0")));
    if (size) *size = img.size();
    return img;
}

}  // namespace prism
