// coding: utf-8
// Copyright 2026 aki-riko
// SPDX-License-Identifier: MIT
// This file is part of PrismQML, licensed under MIT.
// PrismQML C++ 宿主 - SqlListModel (镜像 Python models/sql_list_model.py)
//
// 说明: Python 版用 Rust crate prismqml_rs(PyO3, 仅 Python ABI)加速分页 + keyset
// 游标 + 多 shard fan-out。C++ 无法直接复用该 Python 扩展, 故改用 Qt 原生 QtSql
// (QSqlQuery + SQLite) 实现等价功能: setQuery/count/getRow/data/roleNames + 分页缓存。
// keyset 游标 / 多 shard 为高级优化, 当前用 LIMIT/OFFSET 路径(<100M 行场景正常)。
#pragma once

#include <QAbstractListModel>
#include <QString>
#include <QStringList>
#include <QVariant>
#include <QVariantList>
#include <QVariantMap>
#include <QHash>
#include <QByteArray>

namespace prism {

class DbRouter;  // DataModels.h

class SqlListModel : public QAbstractListModel {
    Q_OBJECT
    Q_PROPERTY(int count READ rowCount NOTIFY countChanged)
public:
    explicit SqlListModel(QObject *parent = nullptr);

    // 打开数据库 (SQLite 文件路径, 单库路径)
    Q_INVOKABLE bool openDatabase(const QString &dbPath);

    // 设置多 shard 路由 (镜像 Python 传 DbRouter): setQuery 时用 router.route(params)
    // 决定命中的 shard 集合。返回单库=单 shard 路径(等价 openDatabase); N 库=fan-out
    // (对每 shard 执行查询后内存归并 + 全局 ORDER BY 排序分页)。不持有 router 所有权。
    void setRouter(DbRouter *router);

    // 设置 keyset 游标列 (镜像 Python cursor_columns): ORDER BY 前缀列名, 如 {"date","id"}。
    // 设置后翻页用 keyset 谓词 (WHERE (cols) > 末行游标) 替代大 OFFSET(仅单 shard 生效)。
    // 传空恢复 LIMIT/OFFSET 路径。sql 的 ORDER BY 必须与这些列(同序)一致。
    Q_INVOKABLE void setCursorColumns(const QStringList &columns);

    // 设置分页大小 (镜像 Python page_size 参数, 默认 100)。须在 setQuery 前调用。
    Q_INVOKABLE void setPageSize(int pageSize) { if (pageSize > 0) m_pageSize = pageSize; }

    // 设置查询 (镜像 setQuery 核心): sql 不含 LIMIT/OFFSET, countSql 为 COUNT(*)
    Q_INVOKABLE void setQuery(const QString &sql, const QString &countSql,
                              const QVariantList &params = QVariantList());

    Q_INVOKABLE int count() const { return m_rowCount; }
    Q_INVOKABLE void refresh();
    Q_INVOKABLE QVariantMap getRow(int index);

    // QAbstractListModel 接口
    int rowCount(const QModelIndex &parent = QModelIndex()) const override;
    QVariant data(const QModelIndex &index, int role = Qt::DisplayRole) const override;
    QHash<int, QByteArray> roleNames() const override;

signals:
    void queryChanged();
    void countChanged();

private:
    int computeCount();
    void resolveColumns();
    QVariantList fetchPage(int pageIdx) const;
    // 多 shard: 对所有 shard 执行查询, 归并 + 全局 ORDER BY 排序后返回第 pageIdx 页
    QVariantList fetchPageFanOut(int pageIdx) const;
    // keyset: 用缓存末行游标做 WHERE 谓词取下一页 (仅单 shard)
    QVariantList fetchPageKeyset(int pageIdx) const;
    int pageOf(int row) const { return row / m_pageSize; }
    bool isMultiShard() const { return m_shardConns.size() > 1; }
    bool useKeyset() const { return !m_cursorColumns.isEmpty() && !isMultiShard(); }
    // 从 SQL 的 ORDER BY 子句解析游标列的排序方向 (ASC/DESC), 供 keyset 谓词方向
    void resolveCursorDirections();

    QString m_connName;          // 单库 QSqlDatabase 连接名 (兼容路径)
    QStringList m_shardConns;    // 多 shard 时各库连接名 (含单库时为 1 个)
    DbRouter *m_router = nullptr;    // 多 shard 路由 (不持有所有权)
    QString m_sql;
    QString m_countSql;
    QVariantList m_params;
    int m_rowCount = 0;
    int m_pageSize = 100;
    QStringList m_columns;
    QStringList m_cursorColumns;              // keyset 游标列名
    QList<bool> m_cursorDesc;                 // 各游标列是否 DESC (与 m_cursorColumns 对齐)
    QHash<int, QByteArray> m_roleNames;   // role -> 列名
    QHash<QString, int> m_colToRole;
    mutable QHash<int, QVariantList> m_cache;  // pageIdx -> rows(每行 QVariantMap)
    mutable QList<int> m_lruOrder;
    // keyset: pageIdx -> 该页末行游标列值 (供下一页 WHERE 谓词, 镜像 Python end_cursor)
    mutable QHash<int, QVariantList> m_endCursors;
    static constexpr int kMaxCachedPages = 16;
};

}  // namespace prism
