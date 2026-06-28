// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - Icon (镜像 Python core/icon_base.py 的图标 API)
//
// 说明: Python 的 2592 个图标名常量是 QML 自带 FluentEnums/Icons.qml 的数据,
// C++ 重复存储无意义且易过时。C++ 侧用图标名字符串(与 addPage 一致), 本模块
// 提供名称->svg路径解析 + QIcon 构造/绘制/染色的功能 API。
#pragma once

#include "prism/Theme.h"
#include <QObject>
#include <QString>
#include <QIcon>
#include <QColor>

class QPainter;
class QRectF;
class QQmlEngine;

namespace prism {

// IconCore - 图标描述 (镜像 Python IconCore): 持有图标名, 解析到 fluent svg 路径
class IconCore {
public:
    explicit IconCore(const QString &name) : m_name(name) {}
    QString name() const { return m_name; }
    // 解析到 svg 资源路径 (优先 importPath 下 controls/icons/fluent/<Name>.svg)
    QString path(Theme theme = Theme::Auto) const;
private:
    QString m_name;
};

using Icon = IconCore;  // Python Icon 别名

// resolveIconColor: 按主题解析图标默认色 (镜像 resolveIconColor)
QString resolveIconColor(Theme theme = Theme::Auto, bool reverse = false);

// make_icon: 由图标名/IconCore 构造 QIcon, 可选 SVG 染色 (镜像 make_icon)
QIcon make_icon(const IconCore &icon, Theme theme = Theme::Auto,
                const QColor &color = QColor());
QIcon make_icon(const QString &name, const QColor &color = QColor());

// make_theme_icon: 跟随主题的 QIcon (镜像 make_theme_icon; C++ 简化为当前主题快照)
QIcon make_theme_icon(const IconCore &icon, bool reverse = false);

// paint_icon: 把图标绘制到 rect (镜像 paint_icon)
void paint_icon(QPainter *painter, const QRectF &rect, const IconCore &icon,
                Theme theme = Theme::Auto);

// 设置图标资源根 (importPath, 默认从环境/App 解析)
void setIconResourceRoot(const QString &root);

// IconProvider - 把图标 API 暴露给 QML context "Icon" (镜像 Python IconProvider)
// 注: QML 控件实测用自带 FluentEnums/Icons.qml, 不依赖此 context; 仅对称提供。
class IconProvider : public QObject {
    Q_OBJECT
public:
    static IconProvider *instance();
public slots:
    QString getPath(const QString &name) const;  // 名称 -> svg 路径
    bool isValid(const QString &name) const;      // 图标资源是否存在
private:
    explicit IconProvider(QObject *parent = nullptr) : QObject(parent) {}
};

inline IconProvider *get_icon_provider() { return IconProvider::instance(); }

// register_icon_provider: 注入 "Icon" context 到引擎 (镜像 register_icon_provider)
void register_icon_provider(QQmlEngine *engine);

}  // namespace prism
