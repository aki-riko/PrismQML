// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - SvgImageProvider (镜像 Python providers/svg_provider.py)
#pragma once

#include <QQuickImageProvider>
#include <QHash>
#include <QString>

class QSvgRenderer;

namespace prism {

// image://svg/<provider-id> - URL 组件只解码一次，再按 file/qrc 路径渲染 SVG
class SvgImageProvider : public QQuickImageProvider {
public:
    SvgImageProvider();
    ~SvgImageProvider() override;
    QImage requestImage(const QString &id, QSize *size, const QSize &requestedSize) override;

private:
    static constexpr int kDefaultSize = 128;
    static constexpr int kMaxCacheSize = 256;
    QSvgRenderer *getRenderer(const QString &path);
    QHash<QString, QSvgRenderer *> m_cache;
};

}  // namespace prism
