// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - 工具类实现: Clipboard / WindowHelper / Acrylic
// 镜像 Python providers/clipboard.py + core/window_helper.py + mica_window.py(Acrylic)
#include "prism/ClipboardHelper.h"
#include "prism/WindowHelper.h"
#include "prism/AcrylicHelper.h"

#include <QGuiApplication>
#include <QClipboard>
#include <QIcon>
#include <QImage>
#include <QPixmap>
#include <QPainter>
#include <QSvgRenderer>
#include <QScreen>
#include <QWindow>
#include <QFileInfo>
#include <QDebug>

namespace prism {

// ==================== ClipboardHelper (镜像 clipboard.py) ====================
ClipboardHelper *ClipboardHelper::instance() {
    static ClipboardHelper *s = new ClipboardHelper();
    return s;
}
void ClipboardHelper::copy(const QString &text) {
    if (QClipboard *cb = QGuiApplication::clipboard())
        cb->setText(text);
}
QString ClipboardHelper::paste() {
    if (QClipboard *cb = QGuiApplication::clipboard())
        return cb->text();
    return QString();
}

// ==================== WindowHelper (镜像 window_helper.py) ====================
WindowHelper *WindowHelper::instance() {
    static WindowHelper *s = new WindowHelper();
    return s;
}

// 解析路径为本地文件路径 (镜像 _resolveIconPath)
QString WindowHelper::resolveIconPath(const QString &icon) {
    if (icon.isEmpty())
        return QString();
    if (icon.startsWith(QLatin1String("file:///")))
        return QString(icon).remove(0, 8);  // file:/// -> 本地路径
    if (icon.startsWith(QLatin1String("qrc:/")))
        return QLatin1Char(':') + icon.mid(4);
    if (icon.startsWith(QLatin1String(":/")))
        return icon;
    return icon;  // 本地绝对路径直接用
}

void WindowHelper::setAppIcon(const QString &icon) {
    if (icon.isEmpty())
        return;
    const QString path = resolveIconPath(icon);
    if (path.isEmpty()) {
        qWarning() << "prism::WindowHelper 无法解析图标路径:" << icon;
        return;
    }
    // SVG 渲染成多尺寸位图 (镜像 _renderSvgIcon)
    if (path.toLower().endsWith(QLatin1String(".svg"))) {
        QSvgRenderer renderer(path);
        if (renderer.isValid()) {
            QIcon qicon;
            for (int sz : {16, 24, 32, 48, 64, 128, 256}) {
                QImage img(sz, sz, QImage::Format_ARGB32_Premultiplied);
                img.fill(Qt::transparent);
                QPainter p(&img);
                p.setRenderHint(QPainter::Antialiasing);
                renderer.render(&p);
                p.end();
                qicon.addPixmap(QPixmap::fromImage(img));
            }
            if (!qicon.isNull()) {
                QGuiApplication::setWindowIcon(qicon);
                return;
            }
        }
    }
    QIcon qicon(path);
    if (!qicon.isNull())
        QGuiApplication::setWindowIcon(qicon);
    else
        qWarning() << "prism::WindowHelper 图标加载失败:" << path;
}

// ==================== AcrylicImageProvider + AcrylicHelper ====================
QImage AcrylicImageProvider::requestImage(const QString & /*id*/, QSize *size,
                                          const QSize & /*requestedSize*/) {
    if (size)
        *size = m_image.size();
    return m_image;
}
void AcrylicImageProvider::setImage(const QImage &image) {
    m_image = image;
    ++m_imageId;
}

AcrylicHelper *AcrylicHelper::instance() {
    static AcrylicHelper *s = new AcrylicHelper();
    return s;
}
AcrylicHelper::AcrylicHelper(QObject *parent)
    : QObject(parent), m_provider(new AcrylicImageProvider()) {}

void AcrylicHelper::setBlurRadius(int value) {
    m_blurRadius = qMax(1, qMin(100, value));
}

// 简易高斯模糊: 缩小再放大 (镜像 Python 注释 "Qt 内置缩放实现模糊, 无外部依赖")
static QImage scaleBlur(const QImage &src, int radius) {
    if (src.isNull())
        return src;
    const int factor = qMax(2, radius / 4);
    QSize small = src.size() / factor;
    if (small.width() < 1 || small.height() < 1)
        return src;
    QImage down = src.scaled(small, Qt::IgnoreAspectRatio, Qt::SmoothTransformation);
    return down.scaled(src.size(), Qt::IgnoreAspectRatio, Qt::SmoothTransformation);
}

QString AcrylicHelper::grabAndBlur(const QVariant &window, int x, int y, int width, int height) {
    if (width <= 0 || height <= 0)
        return QString();
    QObject *obj = qvariant_cast<QObject *>(window);
    QWindow *w = qobject_cast<QWindow *>(obj);
    QScreen *screen = w ? w->screen() : QGuiApplication::primaryScreen();
    if (!screen)
        return QString();

    const int winX = w ? w->x() : 0;
    const int winY = w ? w->y() : 0;
    const QRect sg = screen->geometry();
    const int grabX = winX + x - sg.x();
    const int grabY = winY + y - sg.y();

    QPixmap pix = screen->grabWindow(0, grabX, grabY, width, height);
    if (pix.isNull())
        return QString();

    QImage blurred = scaleBlur(pix.toImage(), m_blurRadius);
    m_provider->setImage(blurred);
    const QString url = QStringLiteral("image://acrylic/%1").arg(m_provider->currentImageId());
    emit imageReady(url);
    return url;
}

QString AcrylicHelper::getImageUrl() const {
    return QStringLiteral("image://acrylic/%1").arg(m_provider->currentImageId());
}

}  // namespace prism
