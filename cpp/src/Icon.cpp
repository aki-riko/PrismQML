// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - Icon 实现 (镜像 Python core/icon_base.py)
#include "prism/Icon.h"
#include "prism/Registry.h"
#include "prism/ThemeManager.h"

#include <QPainter>
#include <QRectF>
#include <QSvgRenderer>
#include <QFile>
#include <QDir>

namespace prism {

namespace {
QString g_iconRoot;  // 图标资源根, 空则从 importPath 解析

QString iconRoot() {
    if (!g_iconRoot.isEmpty())
        return g_iconRoot;
    const QString imp = resolveImportPath();
    if (imp.startsWith(QStringLiteral("qrc:")))
        return QStringLiteral("qrc:/PrismQML/controls/icons/fluent");
    if (!imp.isEmpty())
        return QDir(imp).filePath(QStringLiteral("PrismQML/controls/icons/fluent"));
    return QString();
}

bool isSvg(const QString &p) { return p.endsWith(QStringLiteral(".svg"), Qt::CaseInsensitive); }
}  // namespace

void setIconResourceRoot(const QString &root) { g_iconRoot = root; }

QString IconCore::path(Theme /*theme*/) const {
    const QString root = iconRoot();
    if (root.isEmpty())
        return QString();
    return root + QLatin1Char('/') + m_name + QStringLiteral(".svg");
}

QString resolveIconColor(Theme theme, bool reverse) {
    bool dark = (theme == Theme::Dark);
    if (theme == Theme::Auto)
        dark = ThemeManager::instance()->isDark();
    if (reverse)
        dark = !dark;
    // 深色主题用浅色图标, 反之 (镜像 Python resolveIconColor)
    return dark ? QStringLiteral("#ffffff") : QStringLiteral("#1a1a1a");
}

// SVG 染色: 重写 fill 属性
static QByteArray tintSvg(const QString &path, const QString &color) {
    QString actual = path;
    if (path.startsWith(QStringLiteral("qrc:")))
        actual = QLatin1Char(':') + path.mid(4);
    QFile f(actual);
    if (!f.open(QIODevice::ReadOnly))
        return QByteArray();
    QByteArray data = f.readAll();
    // 简易: 给 <svg 或 <path 注入 fill (镜像 _rewrite_svg_attrs 的填色)
    QByteArray colorAttr = QStringLiteral("fill=\"%1\"").arg(color).toUtf8();
    if (data.contains("fill=")) {
        // 已有 fill, 不重复注入(简化处理)
        return data;
    }
    int pos = data.indexOf("<svg");
    if (pos >= 0) {
        int insert = data.indexOf('>', pos);
        if (insert > 0)
            data.insert(insert, " " + colorAttr);
    }
    return data;
}

QIcon make_icon(const IconCore &icon, Theme theme, const QColor &color) {
    const QString p = icon.path(theme);
    if (p.isEmpty())
        return QIcon();
    if (!color.isValid() || !isSvg(p)) {
        QString actual = p.startsWith(QStringLiteral("qrc:")) ? QLatin1Char(':') + p.mid(4) : p;
        return QIcon(actual);
    }
    const QByteArray tinted = tintSvg(p, color.name());
    if (tinted.isEmpty())
        return QIcon();
    QPixmap pm(64, 64);
    pm.fill(Qt::transparent);
    QPainter painter(&pm);
    QSvgRenderer renderer(tinted);
    renderer.render(&painter);
    painter.end();
    return QIcon(pm);
}

QIcon make_icon(const QString &name, const QColor &color) {
    return make_icon(IconCore(name), Theme::Auto, color);
}

QIcon make_theme_icon(const IconCore &icon, bool reverse) {
    const QColor c(resolveIconColor(Theme::Auto, reverse));
    return make_icon(icon, Theme::Auto, c);
}

void paint_icon(QPainter *painter, const QRectF &rect, const IconCore &icon, Theme theme) {
    if (!painter)
        return;
    const QString p = icon.path(theme);
    if (p.isEmpty())
        return;
    if (!isSvg(p)) {
        QString actual = p.startsWith(QStringLiteral("qrc:")) ? QLatin1Char(':') + p.mid(4) : p;
        const QIcon ic(actual);
        painter->drawPixmap(rect.toRect(), ic.pixmap(rect.size().toSize()));
        return;
    }
    QString actual = p.startsWith(QStringLiteral("qrc:")) ? QLatin1Char(':') + p.mid(4) : p;
    QSvgRenderer renderer(actual);
    renderer.render(painter, rect);
}

// ==================== IconProvider ====================
IconProvider *IconProvider::instance() {
    static IconProvider *s = new IconProvider();
    return s;
}

QString IconProvider::getPath(const QString &name) const {
    return IconCore(name).path();
}

bool IconProvider::isValid(const QString &name) const {
    const QString p = IconCore(name).path();
    if (p.isEmpty())
        return false;
    QString actual = p.startsWith(QStringLiteral("qrc:")) ? QLatin1Char(':') + p.mid(4) : p;
    return QFile::exists(actual);
}

}  // namespace prism

#include <QQmlEngine>
#include <QQmlContext>
namespace prism {
void register_icon_provider(QQmlEngine *engine) {
    if (engine)
        engine->rootContext()->setContextProperty(QStringLiteral("Icon"),
                                                   IconProvider::instance());
}
}  // namespace prism
