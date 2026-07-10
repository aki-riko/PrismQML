// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - AcrylicHelper (镜像 Python window/mica_window.py AcrylicHelper)
#pragma once

#include <QObject>
#include <QImage>
#include <QMutex>
#include <QVariant>
#include <QQuickImageProvider>
#include <memory>

namespace prism {

// 亚克力共享状态: 不归任何 QML engine 所有, provider 仅持有 shared_ptr。
class AcrylicImageState {
public:
    QImage image() const;
    void setImage(const QImage &image);
    int imageId() const;

private:
    mutable QMutex m_mutex;
    QImage m_image;
    int m_imageId = 0;
};

// 亚克力图片提供器: 每个 QML engine 独占一个 adapter。
class AcrylicImageProvider : public QQuickImageProvider {
public:
    AcrylicImageProvider();
    explicit AcrylicImageProvider(std::shared_ptr<AcrylicImageState> state);
    QImage requestImage(const QString &id, QSize *size, const QSize &requestedSize) override;
    void setImage(const QImage &image);
    int currentImageId() const;

private:
    std::shared_ptr<AcrylicImageState> m_state;
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
    AcrylicImageProvider *createImageProvider() const;
public slots:
    // QML: grabAndBlur(window, x, y, w, h) -> image url
    QString grabAndBlur(const QVariant &window, int x, int y, int width, int height);
    QString getImageUrl() const;
signals:
    void imageReady(const QString &url);
private:
    explicit AcrylicHelper(QObject *parent = nullptr);
    std::shared_ptr<AcrylicImageState> m_state;
    int m_blurRadius = 30;
};

}  // namespace prism
