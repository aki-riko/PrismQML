// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - QRCodeGenerator (镜像 Python providers/qrcode_generator.py)
//
// 说明: 完整 QR 编码(Reed-Solomon 纠错+掩码)约 600 行且无人值守无法扫码验证。
// 当前实现与 Python 端未安装 qrcode 库时的行为一致: available=false,
// QRCode.qml 据此优雅降级(显示占位)。getImageSource 仍返回规范 URL,
// provider 返回占位图。后续可替换为完整编码器(接口不变)。
#pragma once

#include <QObject>
#include <QString>
#include <QQuickImageProvider>
#include <QHash>
#include <QImage>

namespace prism {

class QRCodeImageProvider : public QQuickImageProvider {
public:
    QRCodeImageProvider() : QQuickImageProvider(QQuickImageProvider::Image) {}
    QImage requestImage(const QString &id, QSize *size, const QSize &requestedSize) override;
};

class QRCodeGenerator : public QObject {
    Q_OBJECT
    Q_PROPERTY(bool available READ available NOTIFY availableChanged)
public:
    static QRCodeGenerator *instance();
    // 是否有可用的 QR 编码后端 (当前降级实现返回 false, 与 Python 无 qrcode 库一致)
    bool available() const { return false; }
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
