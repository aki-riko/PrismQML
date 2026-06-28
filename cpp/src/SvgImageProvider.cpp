// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - SvgImageProvider 实现 (镜像 Python svg_provider.py)
#include "prism/SvgImageProvider.h"

#include <QImage>
#include <QPainter>
#include <QSvgRenderer>

namespace prism {

SvgImageProvider *SvgImageProvider::instance() {
    static SvgImageProvider *s = new SvgImageProvider();
    return s;
}

SvgImageProvider::SvgImageProvider()
    : QQuickImageProvider(QQuickImageProvider::Image) {}

SvgImageProvider::~SvgImageProvider() {
    qDeleteAll(m_cache);
    m_cache.clear();
}

QImage SvgImageProvider::requestImage(const QString &id, QSize *size,
                                      const QSize &requestedSize) {
    // 路径处理 (镜像 Python: qrc:/ -> :/)
    QString path = id;
    if (id.startsWith(QLatin1String("qrc:/")))
        path = QLatin1Char(':') + id.mid(4);

    QSvgRenderer *renderer = getRenderer(path);
    if (!renderer || !renderer->isValid())
        return QImage();

    // 确定渲染尺寸 (镜像 Python: requestedSize > defaultSize > DEFAULT_SIZE)
    QSize renderSize;
    if (requestedSize.isValid() && requestedSize.width() > 0 && requestedSize.height() > 0) {
        renderSize = requestedSize;
    } else {
        const QSize def = renderer->defaultSize();
        renderSize = def.isValid() ? def : QSize(kDefaultSize, kDefaultSize);
    }

    QImage image(renderSize, QImage::Format_ARGB32_Premultiplied);
    image.fill(Qt::transparent);
    QPainter painter(&image);
    painter.setRenderHint(QPainter::Antialiasing);
    painter.setRenderHint(QPainter::SmoothPixmapTransform);
    renderer->render(&painter);
    painter.end();

    if (size)
        *size = renderSize;
    return image;
}

QSvgRenderer *SvgImageProvider::getRenderer(const QString &path) {
    auto it = m_cache.find(path);
    if (it != m_cache.end())
        return it.value();

    auto *renderer = new QSvgRenderer(path);
    if (!renderer->isValid()) {
        delete renderer;
        return nullptr;
    }
    // 缓存上限: 超出清一半 (镜像 Python MAX_CACHE_SIZE)
    if (m_cache.size() >= kMaxCacheSize) {
        int toRemove = kMaxCacheSize / 2;
        auto i = m_cache.begin();
        while (i != m_cache.end() && toRemove-- > 0) {
            delete i.value();
            i = m_cache.erase(i);
        }
    }
    m_cache.insert(path, renderer);
    return renderer;
}

}  // namespace prism
