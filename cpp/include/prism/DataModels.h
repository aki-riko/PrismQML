// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - 内存数据模型 (镜像 Python models/table_models.py 等)
#pragma once

#include <QAbstractListModel>
#include <QVariantList>
#include <QVariantMap>
#include <QHash>
#include <QByteArray>

namespace prism {

// TableListModel - 内存表格模型 (镜像 Python TableListModel)
// setItems(QVariantList of QVariantMap), role 名从首行 keys 动态生成。
class TableListModel : public QAbstractListModel {
    Q_OBJECT
    Q_PROPERTY(int count READ count NOTIFY countChanged)
public:
    explicit TableListModel(QObject *parent = nullptr) : QAbstractListModel(parent) {}

    Q_INVOKABLE void setItems(const QVariantList &items);
    Q_INVOKABLE QVariantMap getRow(int index) const;
    int count() const { return m_data.size(); }

    int rowCount(const QModelIndex &parent = QModelIndex()) const override;
    QVariant data(const QModelIndex &index, int role = Qt::DisplayRole) const override;
    QHash<int, QByteArray> roleNames() const override { return m_roleNames; }

signals:
    void countChanged();

private:
    QVariantList m_data;                  // 每项 QVariantMap
    QHash<int, QByteArray> m_roleNames;   // role -> 列名
    QHash<QString, int> m_keyToRole;
};

// is_rust_accelerated: C++ 宿主用 QtSql, 非 Rust prismqml_rs (镜像 Python 函数)
// 诚实返回 false: C++ 侧数据层是 Qt 原生, 无 Rust 加速路径。
inline bool is_rust_accelerated() { return false; }

// DbRouter: Python 用于多 shard 路由(配合 Rust fan_out)。C++ 单库 QtSql 无多 shard
// 概念, 此处为对称占位 — 单库场景直接用 SqlListModel.openDatabase 即可。
class DbRouter {
public:
    explicit DbRouter(const QString &dbPath = QString()) : m_dbPath(dbPath) {}
    QString dbPath() const { return m_dbPath; }
    // 多 shard 路由在 C++ QtSql 单库下不适用; 返回唯一库路径。
    QString routeFor(const QVariant & /*cursor*/) const { return m_dbPath; }
private:
    QString m_dbPath;
};

}  // namespace prism
