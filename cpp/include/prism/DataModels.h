// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - 内存数据模型 (镜像 Python models/table_models.py 等)
#pragma once

#include <QAbstractListModel>
#include <QVariantList>
#include <QVariantMap>
#include <QStringList>
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

// DbRouter: 多 shard 路由基类 (镜像 Python models/sql_list_model.py DbRouter)。
// route(params) 根据 SQL 参数返回需查询的 shard 数据库文件路径列表:
//   - 返回 1 个: 走单 shard 路径 (与传单一 db_path 等价)
//   - 返回 N 个: 走 fan-out 路径 (SqlListModel 对每 shard 执行查询后归并 + 全局排序分页)
// 业务子类重写 route() 按 params (如 book_id / date_range) 决定 shard 集合。
class DbRouter {
public:
    explicit DbRouter(const QString &dbPath = QString()) : m_dbPath(dbPath) {}
    virtual ~DbRouter() = default;

    // 兼容访问器: 单库路径 (多 shard 场景无意义, 返回空)
    QString dbPath() const { return m_dbPath; }

    // 路由: 返回本次查询需命中的 shard db 路径列表 (镜像 Python route)。
    // 默认实现返回构造时的单库路径 (等价 SingleDbRouter); 空路径返回空列表。
    virtual QStringList route(const QVariantList & /*params*/) const {
        if (m_dbPath.isEmpty())
            return {};
        return {m_dbPath};
    }

protected:
    QString m_dbPath;
};

// SingleDbRouter: 单库默认 router, 恒返单一 db_path (镜像 Python _SingleDbRouter)。
class SingleDbRouter : public DbRouter {
public:
    explicit SingleDbRouter(const QString &dbPath) : DbRouter(dbPath) {}
    QStringList route(const QVariantList & /*params*/) const override {
        return {m_dbPath};
    }
};

}  // namespace prism
