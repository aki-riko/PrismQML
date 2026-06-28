// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - AcrylicHelper (镜像 Python window/mica_window.py AcrylicHelper)
#pragma once

#include <QObject>
#include <QImage>
#include <QVariant>
#include <QQuickImageProvider>

namespace prism {

// 亚克力图片提供器: 缓存最近一次模糊结果, image://acrylic/<id>
class AcrylicImageProvider : public QQuickImageProvider {
public:
    AcrylicImageProvider() : QQuickImageProvider(QQuickImageProvider::Image) {}
    QImage requestImage(const QString &id, QSize *size, const QSize &requestedSize) override;
    void setImage(const QImage &image);
    int currentImageId() const { return m_imageId; }
private:
    QImage m_image;
    int m_imageId = 0;
};

// AcrylicHelper - 截屏+模糊实现亚克力背景 (QML: isAvailable / grabAndBlur)
class AcrylicHelper : public QObject {
    Q_OBJECT
    Q_PROPERTY(bool isAvailable READ isAvailable CONSTANT)
    Q_PROPERTY(int blurRadius READ blurRadius WRITE setBlurRadius)
public:
    static AcrylicHelper *instance();
    bool isAvailable() const { return true; }
    int blurRadius() const { return m_blurRadius; }
    void setBlurRadius(int value);
    AcrylicImageProvider *imageProvider() { return m_provider; }
public slots:
    // QML: grabAndBlur(window, x, y, w, h) -> image url
    QString grabAndBlur(const QVariant &window, int x, int y, int width, int height);
    QString getImageUrl() const;
signals:
    void imageReady(const QString &url);
private:
    explicit AcrylicHelper(QObject *parent = nullptr);
    AcrylicImageProvider *m_provider;
    int m_blurRadius = 30;
};

}  // namespace prism
